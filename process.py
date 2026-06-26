# %%
# Setup

import json
import time
import os
import csv
import re
from typing import Any, Dict, List, Literal, Optional, Tuple
from google import genai
from google.api_core import exceptions
from google.genai import types
from dotenv import load_dotenv
from utils import BatchFlashcard, append_to_raw_tsv, SYSTEM_PROMPT, get_few_shots, get_common_parser, ScriptArgs, Flashcard

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable.")

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"), 
    http_options={
        "timeout": 180_000 # 3 minutes
    }
)

# %%
# Information

# print(f"System prompt:\n{SYSTEM_PROMPT}")

# %%
# Configuration

parser = get_common_parser("Generate vocabulary cards.")
parser.add_argument("--replace", "-r", action="store_true", help="Replace existing AI entries (preserving human ones).")

args = parser.parse_args()

origin = "data/vocabulary"

level = args.level
replace_mode = args.replace

output_file = f"data/raw/level{level}.tsv"

# %%
# Card generation

def generate_batch(batch_items: list[str], human_examples: List[Tuple[str, Flashcard]]) -> BatchFlashcard:
    few_shot = "### GOLD STANDARD EXAMPLES:\n"
    for ex in human_examples:
        (headword, flashcard) = ex
        few_shot += f"Word: {headword}\nJSON: {flashcard.model_dump_json()}\n---\n"
    
    batch_prompt = SYSTEM_PROMPT
    batch_prompt += few_shot
    batch_prompt += f"\n\n ### BATCH TO GENERATE {batch_items}"
    
    response = client.models.generate_content(
        model="gemma-4-31b-it",
        contents=batch_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BatchFlashcard,
            temperature=0.8,
            thinking_config=types.ThinkingConfig(thinking_level="high") # type: ignore
        ),
    )
    
    return response.parsed # type: ignore

# %%
# Loading word list

word_list = []
with open(f"{origin}/level{level}.txt", "r", encoding="utf-8") as f:
    word_list = [line.strip() for line in f.readlines()]

print(f"Loaded {len(word_list)} words from level {level}.")
print(word_list[:5])

# %%
# Check progress and filter words

def get_processed_words(output_file: str) -> set[str]:
    processed = set()
    # 1. Check current level file
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                if row.get("raw_string"): processed.add(row["raw_string"])
    
    return processed

# If replace mode is on, we clear the current level file but keep human rows
if replace_mode and os.path.exists(output_file):
    print(f"Replace mode active. Clearing AI entries from {output_file}...")
    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    # Keep only human verified rows in the level file
    human_rows = [r for r in rows if r.get("verification") == "human"]
    
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t") 
        writer.writeheader()
        writer.writerows(human_rows)

# filter out words already processed
processed_words = get_processed_words(output_file)
words_to_process = [w for w in word_list if w not in processed_words]

print(f"Level {level} Status: {len(processed_words)} words protected/done. {len(words_to_process)} words to process.")

# %%
# Processing loop

chunk_size = 5
total_chunks = (len(words_to_process) + chunk_size - 1) // chunk_size

for start_idx in range(0, len(words_to_process), chunk_size):
    chunk = words_to_process[start_idx : start_idx + chunk_size]
    current_chunk_idx = start_idx // chunk_size + 1
    print(f"Processing chunk {current_chunk_idx} of {total_chunks}...")
    
    success = False
    attempts = 0
    
    human_examples = get_few_shots()
    
    while not success:
        try:
            batch_results = generate_batch(chunk, human_examples)
            append_to_raw_tsv(level, chunk, batch_results)
            success = True # This breaks the 'while not success' loop
        except Exception as e:
            # 'success' remains False, so the 'while' loop tries the same chunk again
            if attempts >= 3:
                print("    Max attempts reached. Skipping to next chunk...")
                
                # break out of the "while" loop on permanent error (to avoid infinite loop)
                break
            
            attempts += 1
            print(f"    Error at {current_chunk_idx} of {total_chunks} (attempt {attempts}): {e}")
            
            # Wait 10 seconds before trying again
            time.sleep(10)

    # Optional small breath to keep the API happy
    time.sleep(2)

# %%
# Completion

print("Done! All words processed.")
