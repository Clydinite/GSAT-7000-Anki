# %%
# Setup

import asyncio
import os
import csv
import time
from typing import List, Tuple, Optional
from google import genai
from google.genai import types
from google.genai.errors import APIError  # Clean exception tracking
from dotenv import load_dotenv
from utils import BatchFlashcard, append_to_raw_tsv, SYSTEM_PROMPT, get_few_shots, get_common_parser, Flashcard

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable.")

# Configuration

parser = get_common_parser("Generate vocabulary cards.")
parser.add_argument("--replace", "-r", action="store_true", help="Replace existing AI entries (preserving human ones).")

args = parser.parse_args()

origin = "data/vocabulary"

level = args.level
replace_mode = args.replace

output_file = f"data/raw/level{level}.tsv"

# %%
# Async Card generation using the Async client from google.genai

async def generate_batch_async(client, batch_items: list[str], human_examples: List[Tuple[str, Flashcard]]) -> Optional[BatchFlashcard]:
    few_shot = "### GOLD STANDARD EXAMPLES:\n"
    for headword, flashcard in human_examples:
        few_shot += f"Word: {headword}\nJSON: {flashcard.model_dump_json()}\n---\n"
    
    batch_prompt = f"{SYSTEM_PROMPT}\n{few_shot}\n\n ### BATCH TO GENERATE {batch_items}"
    
    response = await client.models.generate_content(
        model="gemma-4-31b-it",
        contents=batch_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BatchFlashcard,
            temperature=0.8,
            thinking_config=types.ThinkingConfig(thinking_level="high") # type: ignore
        ),
    )
    
    return response.parsed

# %%
# Loading and processing logic

def get_processed_words(output_file: str) -> set[str]:
    processed = set()
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                if row.get("raw_string"):
                    processed.add(row["raw_string"])
    return processed

async def process_chunk(client, chunk: List[str], human_examples: List[Tuple[str, Flashcard]], file_lock: asyncio.Lock, chunk_idx: int, total_chunks: int):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] Processing chunk {chunk_idx} of {total_chunks}...")
    start_time = time.perf_counter()
    
    success = False
    attempts = 0
    while not success:
        try:
            batch_results = await generate_batch_async(client, chunk, human_examples)
            
            if batch_results is None:
                raise ValueError("API returned an empty response layout or failed schema decoding.")
            
            # CRITICAL FIX: Bind the success flag directly to the file append operation
            async with file_lock:
                await asyncio.to_thread(append_to_raw_tsv, level, chunk, batch_results)
                success = True # Once written to disk, this chunk is officially complete
            
            elapsed = time.perf_counter() - start_time
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] Successfully processed chunk {chunk_idx} of {total_chunks} in {elapsed:.2f}s.")
            success = True
        except (APIError, Exception) as e:
            attempts += 1
            if attempts >= 3:
                print(f"    Max attempts reached for chunk {chunk_idx}. Skipping data points.")
                break
            print(f"    Error at chunk {chunk_idx} (attempt {attempts}): {e}")
            await asyncio.sleep(12)  # Generous padding to clear server bottleneck queues

# Worker wrapper that executes within a controlled concurrency slot
async def worker_pool_slot(semaphore: asyncio.Semaphore, client, chunk: List[str], human_examples: List[Tuple[str, Flashcard]], file_lock: asyncio.Lock, chunk_idx: int, total_chunks: int):
    """Acquires a slot from the semaphore to guarantee exactly 5 tasks run concurrently."""
    async with semaphore:
        await process_chunk(client, chunk, human_examples, file_lock, chunk_idx, total_chunks)

async def main():
    if not os.path.exists(f"{origin}/level{level}.txt"):
        print(f"Level file {origin}/level{level}.txt not found.")
        return

    with open(f"{origin}/level{level}.txt", "r", encoding="utf-8") as f:
        word_list = [line.strip() for line in f.readlines()]

    if replace_mode and os.path.exists(output_file):
        print(f"Replace mode active. Clearing AI entries from {output_file}...")
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            fieldnames = reader.fieldnames
            rows = [r for r in reader if r.get("verification") == "human"]
        
        # Open in 'w' to truncate the file completely before rewriting
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t") # type: ignore
            writer.writeheader()
            writer.writerows(rows)

    processed_words = get_processed_words(output_file)
    words_to_process = [w for w in word_list if w not in processed_words]
    print(f"Processing {len(words_to_process)} words.")

    chunk_size = 1
    workers = 5
    chunks = [words_to_process[i : i + chunk_size] for i in range(0, len(words_to_process), chunk_size)]
    total_chunks = len(chunks)
    human_examples = get_few_shots()
    
    # Primitives to synchronize your tasks safely
    file_lock = asyncio.Lock()
    pool_semaphore = asyncio.Semaphore(workers) # Limits total concurrency to exactly 5 slots
    
    # Use the async client context manager
    async with genai.Client(api_key=API_KEY, http_options=types.HttpOptions(timeout=300_000)).aio as aclient:
        tasks = []
        for idx, chunk in enumerate(chunks):
            # Wrap each task in our semaphore slot coordinator
            task = worker_pool_slot(
                pool_semaphore, 
                aclient, 
                chunk, 
                human_examples, 
                file_lock, 
                idx + 1, 
                total_chunks
            )
            tasks.append(task)
        
        # Fire all tasks into the event loop concurrently. 
        # The semaphore restricts execution so that only 5 operate simultaneously.
        # As soon as one ends, the next task in line picks up instantly.
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
