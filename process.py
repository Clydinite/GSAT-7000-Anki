# %%
# Setup

import json
import time
import os
import csv
import re
from typing import Any, Dict, List, Literal, Optional
from google import genai
from google.api_core import exceptions
from google.genai import types
from dotenv import load_dotenv
from utils import BatchWordResult, append_to_raw_tsv, SYSTEM_PROMPT, EXAMPLE_RESPONSE, get_random_human_examples

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable.")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# %%
# Information

print(f"System prompt:\n{SYSTEM_PROMPT}")

# %%
# Configuration

origin = "data/vocabulary"

level = 4
output_file = f"data/raw/level{level}.tsv"

# %%
def generate_batch(batch_items: list[str], human_examples: List[Dict[str, Any]]) -> BatchWordResult:
    few_shot = "### GOLD STANDARD EXAMPLES:\n"
    for ex in human_examples:
        few_shot += f"Word: {ex['headword']}\nJSON: {json.dumps(ex['response'], ensure_ascii=False)}\n---\n"
    
    batch_prompt = SYSTEM_PROMPT
    batch_prompt += few_shot
    batch_prompt += f"\n\n ### BATCH TO GENERATE {batch_items}"
    
    response = client.models.generate_content(
        model="gemma-4-31b-it",
        contents=batch_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BatchWordResult,
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

existing_words = set()
if os.path.exists(output_file):
    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader, None)  # Skip header
        for row in reader:
            if row: existing_words.add(row[1]) # the raw_string is in the second column

# filter out words already processed
words_to_process = [w for w in word_list if w not in existing_words]

print(f"Resuming Level {level}: {len(existing_words)} already done. {len(words_to_process)} remaining.")

# %%
# Processing loop

chunk_size = 10
total_chunks = (len(words_to_process) + chunk_size - 1) // chunk_size

for start_idx in range(0, len(words_to_process), chunk_size):
    chunk = words_to_process[start_idx : start_idx + chunk_size]
    current_chunk_idx = start_idx // chunk_size + 1
    print(f"Processing chunk {current_chunk_idx} of {total_chunks}...")
    
    success = False
    attempts = 0
    
    human_examples = get_random_human_examples(10)
    
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
