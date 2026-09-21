import asyncio
import os
import csv
import time
import random
import argparse
from typing import List, Dict, Any, Optional, Literal
from google import genai
from google.genai import types
from dotenv import load_dotenv
from utils import get_common_parser, get_few_shots, Flashcard, BatchFlashcard
from pydantic import BaseModel, Field

load_dotenv()

# Initialize global SDK client engine matching edit.py/verify.py
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"), 
    http_options={
        "timeout": 180_000
    }
)

# --- Migration Schema ---

class EntryTierMigration(BaseModel):
    pattern: str = Field(..., description="The pattern string to identify the entry")
    tier: Literal["primary", "secondary", "tertiary", "untestable"] = Field(..., description="Assigned priority tier")

class SenseTierMigration(BaseModel):
    sense: str = Field(..., description="The sense string to identify the sense")
    tier: Literal["primary", "secondary", "tertiary", "untestable"] = Field(..., description="Assigned priority tier")
    entries: List[EntryTierMigration]

class CardTierMigration(BaseModel):
    headword: str
    senses: List[SenseTierMigration]
    
class BatchMigrationResult(BaseModel):
    results: List[CardTierMigration]

# --- Prompting ---
MIGRATION_SYSTEM_PROMPT = """
You are a senior GSAT English lexicographer and curriculum expert. 
Your task is to assign priority tiers ("primary", "secondary", "tertiary", "untestable") to every sense and every collocation pattern (entry) of a word.

Tier Rubric:
- primary: Must know. Exactly one core primary sense per headword (or primary sense(s) crucial for the main meaning), and essential high-yield collocation pattern(s).
- secondary: Should know. Important secondary definitions and standard exam-frequency collocations.
- tertiary: Could know. Peripheral, less frequent nuances or specialized usages.
- untestable: Informal, regional, archaic, slang, or obsolete variants.

Instructions:
1. Analyze the provided senses and patterns for the headword.
2. Assign the correct tier to each sense and each pattern.
3. Return the results in the requested structured format.
4. Be precise. Do not add senses or patterns that were not provided.
"""

def get_relevant_few_shot_tier_data() -> str:
    examples = get_few_shots()
    output = "### GOLD STANDARD EXAMPLES (TIER FOCUS):\n"
    for headword, flashcard in examples:
        output += f"Word: {headword}\n"
        for sense in flashcard.senses:
            sense_tier = getattr(sense, "tier")
            output += f"- Sense: '{sense.sense}' [Tier: {sense_tier}]\n"
            for entry in sense.entries:
                entry_tier = getattr(entry, "tier")
                output += f"  - Pattern: '{entry.pattern}' [Tier: {entry_tier}]\n"
        output += "---\n"
    return output

async def migrate_batch_async(few_shot: str, batch_items: List[Dict[str, Any]]) -> Optional[BatchMigrationResult]:
    prompt = f"{few_shot}\n\n### BATCH TO MIGRATE:\n"
    for i, item in enumerate(batch_items):
        prompt += f"Card {i+1} ({item['headword']}):\n"
        for s in item['senses']:
            prompt += f"  Sense: '{s['sense']}'\n"
            for p in s['patterns']:
                prompt += f"    - Pattern: '{p}'\n"
        prompt += "---\n"
    
    try:
        response = await client.aio.models.generate_content(
            model="gemma-4-31b-it",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=MIGRATION_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=BatchMigrationResult,
                temperature=0.2,
                thinking_config=types.ThinkingConfig(thinking_level="high") # type: ignore
            ),
        )
        return response.parsed # type: ignore
    except Exception as e:
        print(f"API Error during migration: {e}")
        return None

def write_entire_tsv(file_path: str, fieldnames: List[str], rows: List[Dict[str, str]]) -> None:
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

async def migrate_chunk_slot(
    semaphore: asyncio.Semaphore,
    file_path: str,
    fieldnames: List[str],
    rows: List[Dict[str, str]],
    batch_idx_chunk: List[int],
    few_shot: str,
    file_lock: asyncio.Lock,
    batch_num: int,
    total_batches: int,
    counter_dict: Dict[str, int]
):
    async with semaphore:
        await asyncio.sleep(random.uniform(0, 3))
        
        batch_items = []
        valid_indices = []
        for idx in batch_idx_chunk:
            row = rows[idx]
            try:
                data = Flashcard.model_validate_json(row["response"])
                senses_payload = [
                    {
                        "sense": sense.sense,
                        "patterns": [entry.pattern for entry in sense.entries]
                    }
                    for sense in data.senses
                ]
                batch_items.append({"headword": data.headword, "senses": senses_payload})
                valid_indices.append(idx)
            except Exception as e:
                print(f"Error parsing row {idx}: {e}")
                
        if not batch_items:
            return

        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] Processing migration batch {batch_num} of {total_batches} ({len(batch_items)} items)...")
        start_time = time.perf_counter()

        success = False
        attempts = 0
        while not success:
            try:
                migration_results = await migrate_batch_async(few_shot, batch_items)
                if not migration_results or len(migration_results.results) != len(batch_items):
                    raise ValueError(f"API response mismatch (expected {len(batch_items)}, got {len(migration_results.results) if migration_results else 0}).")

                async with file_lock:
                    for result, row_idx in zip(migration_results.results, valid_indices):
                        card_data = Flashcard.model_validate_json(rows[row_idx]["response"])
                        
                        # Map returned sense and entry tiers back to card_data
                        sense_map = {s.sense.lower().strip(): s for s in result.senses}
                        
                        for s_idx, sense in enumerate(card_data.senses):
                            sense_key = sense.sense.lower().strip()
                            matched_sense = sense_map.get(sense_key)
                            if not matched_sense and s_idx < len(result.senses):
                                matched_sense = result.senses[s_idx]
                                
                            if matched_sense:
                                sense.tier = matched_sense.tier
                                entry_map = {e.pattern.lower().strip(): e.tier for e in matched_sense.entries}
                                for e_idx, entry in enumerate(sense.entries):
                                    pattern_key = entry.pattern.lower().strip()
                                    if pattern_key in entry_map:
                                        entry.tier = entry_map[pattern_key]
                                    elif e_idx < len(matched_sense.entries):
                                        entry.tier = matched_sense.entries[e_idx].tier
                                    else:
                                        entry.tier = "primary" # default fallback
                            else:
                                sense.tier = "primary"
                                for entry in sense.entries:
                                    entry.tier = "primary"

                        rows[row_idx]["response"] = card_data.model_dump_json()
                        rows[row_idx]["attempts"] = str(int(rows[row_idx].get("attempts", 0)) + 1)
                        counter_dict["updated_count"] += 1
                    
                    await asyncio.to_thread(write_entire_tsv, file_path, fieldnames, rows)
                    elapsed = time.perf_counter() - start_time
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] Successfully migrated batch {batch_num} in {elapsed:.2f}s.")
                    success = True
            except Exception as e:
                attempts += 1
                if attempts >= 3:
                    print(f"    Max attempts reached for migration batch {batch_num}. Skipping.")
                    break
                print(f"    Error at migration batch {batch_num} (attempt {attempts}): {e}")
                await asyncio.sleep(12)

async def main():
    parser = get_common_parser("Migrate senses and patterns to tier system.")
    parser.add_argument("--batch-size", "-b", type=int, default=5, help="Batch size.")
    parser.add_argument("--worker-count", "-w", type=int, default=5, help="Worker count.")
    args = parser.parse_args()
    
    file_path = f"data/raw/level{args.level}.tsv"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if not reader.fieldnames:
            print("No fieldnames found in TSV.")
            return
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    # Identify indices that actually need migration (skip cards where all senses and entries already have a tier assigned)
    pending_indices = []
    for i, row in enumerate(rows):
        try:
            data = Flashcard.model_validate_json(row["response"])
            needs_migration = False
            for sense in data.senses:
                if not getattr(sense, "tier", None):
                    needs_migration = True
                    break
                for entry in sense.entries:
                    if not getattr(entry, "tier", None):
                        needs_migration = True
                        break
            if needs_migration:
                pending_indices.append(i)
        except Exception:
            pending_indices.append(i)

    if not pending_indices:
        print("No cards need migration.")
        return

    print(f"Found {len(pending_indices)} cards needing tier migration for Level {args.level} ({len(rows) - len(pending_indices)} already migrated).")
    few_shot = get_relevant_few_shot_tier_data()
    counter_dict = {"updated_count": 0}
    file_lock = asyncio.Lock()
    pool_semaphore = asyncio.Semaphore(args.worker_count)
    
    batches = [pending_indices[i : i + args.batch_size] for i in range(0, len(pending_indices), args.batch_size)]
    total_batches = len(batches)
    
    tasks = [
        migrate_chunk_slot(
            pool_semaphore, 
            file_path, 
            fieldnames, 
            rows, 
            b, 
            few_shot, 
            file_lock, 
            i+1, 
            total_batches, 
            counter_dict
        ) 
        for i, b in enumerate(batches)
    ]
    await asyncio.gather(*tasks)

    print(f"Migration finished. Updated {counter_dict['updated_count']} cards.")

if __name__ == "__main__":
    asyncio.run(main())
