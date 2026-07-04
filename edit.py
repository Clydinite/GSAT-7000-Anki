import json
import os
import csv
import time
import asyncio
import argparse
from typing import List, Dict, Optional, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv
from utils import BatchFlashcard, SYSTEM_PROMPT, get_common_parser, get_few_shots, Flashcard

load_dotenv()

# Initialize global SDK client engine
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"), 
    http_options={
        "timeout": 180_000  # 3 minutes
    }
)

# --- Editor Prompt ---
EDITOR_SYSTEM_PROMPT = f"""
You are a high-precision Senior Editor for GSAT English Vocabulary. 
Your goal is to FIX cards that have already failed a strict quality audit.

### YOUR FIXING MANDATE:
- Fix the flashcard based on the Auditor's feedback.
- If the Auditor flags an issue, you MUST modify the JSON to correct the structure, content, or tags.
- Output the ENTIRE fixed card as valid JSON matching the Flashcard schema.
- NEVER include any conversational explanation.
- DO NOT CHANGE ANY FIELDS UNLESS THEY ARE PART OF THE FIX.

### SCHEMA REFERENCE:
{Flashcard.model_json_schema()}

Original System Prompt for reference:
{SYSTEM_PROMPT}
"""

async def edit_batch_async(batch_items: List[Dict[str, str]]) -> Optional[BatchFlashcard]:
    batch_prompt = "### BATCH TO FIX:\n"
    for i, item in enumerate(batch_items):
        batch_prompt += f"Card {i+1} ({item['headword']}):\n"
        batch_prompt += f"  Current Data: {item['response']}\n"
        batch_prompt += f"  Auditor Feedback: {item['comment']}\n---\n"
    
    try:
        # Utilize the non-blocking asynchronous SDK endpoint .aio
        response = await client.aio.models.generate_content(
            model="gemma-4-31b-it",
            contents=batch_prompt,
            config=types.GenerateContentConfig(
                system_instruction=EDITOR_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=BatchFlashcard,
                temperature=1.0,
                thinking_config=types.ThinkingConfig(
                    include_thoughts=False,
                    thinking_level="high" # type: ignore
                )
            )
        )
        return response.parsed  # type: ignore
    except Exception as e:
        print(f"Error fixing batch: {e}")
        return None

def write_entire_tsv(file_path: str, fieldnames: List[str], rows: List[Dict[str, str]]) -> None:
    """Helper used to safely execute blocking disk serialization inside an OS threadpool."""
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

async def fix_chunk_slot(
    semaphore: asyncio.Semaphore,
    file_path: str,
    fieldnames: List[str],
    rows: List[Dict[str, str]],
    batch_idx_chunk: List[int],
    file_lock: asyncio.Lock,
    batch_num: int,
    total_batches: int,
    counter_dict: Dict[str, int]
):
    """Executes a batch fix using a strict semaphore-controlled async slot wrapper."""
    async with semaphore:
        batch_items = [rows[idx] for idx in batch_idx_chunk]
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] Processing batch {batch_num} of {total_batches}...")
        start_time = time.perf_counter()
        
        success = False
        attempts = 0
        while not success:
            try:
                # API network transactions execute concurrently outside the file lock
                fixed_batch = await edit_batch_async(batch_items)
                
                if not fixed_batch or len(fixed_batch.results) != len(batch_items):
                    if fixed_batch:
                        raise ValueError(f"Batch size mismatch (required {len(batch_items)}, got {len(fixed_batch.results)}).")
                    else:
                        raise ValueError("API returned an empty payload or malformed structural block.")

                # Mutate shared memory elements and flush data safely inside the lock context
                async with file_lock:
                    for fixed_data, row_idx in zip(fixed_batch.results, batch_idx_chunk):
                        rows[row_idx]["response"] = fixed_data.model_dump_json()
                        rows[row_idx]["verification"] = "none"  # Reset status tracking line
                        rows[row_idx]["comment"] = ""           # Clear historical error strings
                        rows[row_idx]["attempts"] = str(int(rows[row_idx].get("attempts", 0)) + 1)
                        counter_dict["updated_count"] += 1
                    
                    await asyncio.to_thread(write_entire_tsv, file_path, fieldnames, rows)
                    elapsed = time.perf_counter() - start_time
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] Successfully processed batch {batch_num} of {total_batches} in {elapsed:.2f}s.")

                success = True
                
            except Exception as e:
                attempts += 1
                if attempts >= 3:
                    print(f"    Max attempts reached for batch {batch_num}. Skipping data slice.")
                    break
                print(f"    Error at batch {batch_num} (attempt {attempts}): {e}")
                await asyncio.sleep(12)  # Generous backoff buffer to drain connection pipelines

async def main_async() -> None:
    # Configurations
    parser = get_common_parser("Level of audited cards to actually fix.")
    parser.add_argument("--batch-size", "-b", type=int, default=1, help="Batch size for processing.")
    parser.add_argument("--worker-count", "-w", type=int, default=5, help="Number of concurrent workers.")
    args = parser.parse_args()
    
    edit_level = args.level
    batch_size = args.batch_size
    workers = args.worker_count

    file_path = f"data/raw/level{edit_level}.tsv"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    # Read complete array layout into local scope memory
    with open(file_path, "r", encoding="utf-8") as f:  
        reader = csv.DictReader(f, delimiter="\t")
        if not reader.fieldnames:
            raise Exception("No fieldnames found in TSV file.")
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    if not fieldnames: 
        return

    # Target cards marked ai_fail with less than or equal to 3 attempts
    pending_indices = [
        i for i, r in enumerate(rows) 
        if r.get("verification") == "ai_fail" and int(r.get("attempts", 0)) <= 3
    ]
    
    total_pending = len(pending_indices)
    if not pending_indices:
        print("No cards need fixing.")
        return

    print(f"Fixing {total_pending} cards in batches of {batch_size} for Level {edit_level}...")

    # Initialize task structures and execution locks
    counter_dict = {"updated_count": 0}
    file_lock = asyncio.Lock()
    pool_semaphore = asyncio.Semaphore(workers)
    
    batches_indices = [pending_indices[i : i + batch_size] for i in range(0, total_pending, batch_size)]
    total_batches = len(batches_indices)

    tasks = []
    for idx, batch_idx_chunk in enumerate(batches_indices):
        task = fix_chunk_slot(
            semaphore=pool_semaphore,
            file_path=file_path,
            fieldnames=fieldnames,
            rows=rows,
            batch_idx_chunk=batch_idx_chunk,
            file_lock=file_lock,
            batch_num=idx + 1,
            total_batches=total_batches,
            counter_dict=counter_dict
        )
        tasks.append(task)

    # Concurrently execute all batches through the event loop
    await asyncio.gather(*tasks)

    updated_count = counter_dict["updated_count"]
    print(f"\nEditing complete. Fixed {updated_count} cards and moved them back to 'none' for re-verification.")

if __name__ == "__main__":
    asyncio.run(main_async())