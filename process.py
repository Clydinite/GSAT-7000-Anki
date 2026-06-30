# %%
# Setup

import asyncio
import os
import csv
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

# Added file_lock, chunk_idx, and total_chunks parameters for clean output visibility
async def process_chunk(client, chunk: List[str], human_examples: List[Tuple[str, Flashcard]], file_lock: asyncio.Lock, chunk_idx: int, total_chunks: int):
    success = False
    attempts = 0
    while not success:
        try:
            batch_results = await generate_batch_async(client, chunk, human_examples)
            
            if batch_results is None:
                raise ValueError("API returned an empty response layout or failed schema decoding.")
            
            async with file_lock:
                await asyncio.to_thread(append_to_raw_tsv, level, chunk, batch_results)
            
            print(f"Successfully processed chunk {chunk_idx} of {total_chunks}.")
            success = True
        except (APIError, Exception) as e:
            attempts += 1
            if attempts >= 3:
                print(f"    Max attempts reached for chunk {chunk_idx}. Skipping data points.")
                break
            print(f"    Error at chunk {chunk_idx} (attempt {attempts}): {e}")
            await asyncio.sleep(12)  # Generous padding to clear server bottleneck queues

async def main():
    if not os.path.exists(f"{origin}/level{level}.txt"):
        print(f"Level file {origin}/level{level}.txt not found.")
        return

    with open(f"{origin}/level{level}.txt", "r", encoding="utf-8") as f:
        word_list = [line.strip() for line in f.readlines()]

    if replace_mode and os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            fieldnames = reader.fieldnames
            rows = [r for r in reader if r.get("verification") == "human"]
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)

    processed_words = get_processed_words(output_file)
    words_to_process = [w for w in word_list if w not in processed_words]
    print(f"Processing {len(words_to_process)} words.")

    chunk_size = 5
    workers = 2
    chunks = [words_to_process[i : i + chunk_size] for i in range(0, len(words_to_process), chunk_size)]
    total_chunks = len(chunks)
    human_examples = get_few_shots()
    
    # Initialize a shared lock to completely insulate your TSV file
    file_lock = asyncio.Lock()
    
    # Use the async client context manager
    async with genai.Client(api_key=API_KEY, http_options=types.HttpOptions(timeout=300_000)).aio as aclient:
        tasks = []
        for idx, chunk in enumerate(chunks):
            # Pass metrics down to the handler functions
            tasks.append(process_chunk(aclient, chunk, human_examples, file_lock, idx + 1, total_chunks))
        
        # Process in batches to avoid overwhelming the API
        for i in range(0, len(tasks), workers):
            batch = tasks[i : i + 2]
            await asyncio.gather(*batch)
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())