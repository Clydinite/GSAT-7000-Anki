# %%
# Setup

import json
import time
import os
import csv
import re
from typing import List, Literal, Optional
from google import genai
from google.api_core import exceptions
from google.genai import types
from dotenv import load_dotenv
from utils import BatchWordResult, append_to_raw_tsv, SYSTEM_PROMPT, EXAMPLE_RESPONSE

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

level = 3
output_file = f"data/raw/level{level}.tsv"

# %%
def generate_data(batch_words: list[str]) -> BatchWordResult:
    # Use SYSTEM_PROMPT from utils.py
    full_prompt = SYSTEM_PROMPT.format(example_json=json.dumps(EXAMPLE_RESPONSE, ensure_ascii=False))
    full_prompt += f"\n\nHere are the words: {batch_words}"
    
    # Using the latest 2026 SDK 'generate' method
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=full_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BatchWordResult,
            temperature=0.8,
            # Correct nesting for thinking levels
            thinking_config=types.ThinkingConfig(thinking_level="low")
        ),
    )
    
    return response.parsed

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
def is_quota_error(e):
    err_str = str(e).lower()
    return "429" in err_str or "resource_exhausted" in err_str

# %%
# Processing loop

chunk_size = 10
total_chunks = (len(words_to_process) + chunk_size - 1) // chunk_size

for start_idx in range(0, len(words_to_process), chunk_size):
    chunk = words_to_process[start_idx : start_idx + chunk_size]
    print(f"Processing chunk {start_idx//chunk_size + 1} of {total_chunks}...")
    
    success = False
    while not success:
        try:
            batch_results = generate_data(chunk)
            append_to_raw_tsv(level, chunk, batch_results)
            success = True # This breaks the 'while not success' loop
            
            # Optional small breath to keep the API happy
            time.sleep(5)
            
        except Exception as e:
            err_msg = str(e)
            if is_quota_error(err_msg):
                retry_match = re.search(r"'retryDelay':\s*'(\d+)s'", err_msg)
            
                if retry_match:
                    delay = int(retry_match.group(1)) + 2 # Adding safety buffer
                    print(f"    Quota hit. Waiting {delay}s per API request...")
                    time.sleep(delay)
                else:
                    print("    Quota hit. No delay found, waiting 30s...")
                    time.sleep(30)
            else:
                # 'success' remains False, so the 'while' loop tries the same chunk again
                print(f"    Permanent error at {chunk}: {e}")
                print("    Waiting 10s before retrying current chunk...")
                time.sleep(10)
                
                # break out of the "while" loop on permanent error (to avoid infinite loop)
                break

# %%
