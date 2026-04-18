import json
import os
import csv
import time
from typing import List, Dict, Optional
from google import genai
from dotenv import load_dotenv
from utils import BatchWordResult, SYSTEM_PROMPT

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- Editor Prompt ---
EDITOR_SYSTEM_PROMPT = f"""
You are a high-precision Senior Editor for GSAT English Vocabulary. 
Your goal is to FIX cards that failed a strict quality audit.

### THE CORE PROBLEM TO FIX:
The previous AI was "lazy" and often tagged generic nouns (e.g., <target>accurate</target> <pattern>data</pattern>). 
This is a FAILURE. Nouns like 'data', 'information', or 'method' are rarely high-value collocations.

### YOUR FIXING MANDATE:
1. Identify the REAL GSAT-style grammatical collocation. This is almost always:
   - A Preposition (e.g., <target>accurate</target> <pattern>in</pattern>).
   - A Phrasal Verb Particle (e.g., <pattern>set</pattern> <target>aside</target>).
   - A specific functional verb (e.g., <pattern>take</pattern> <target>advantage</target> <pattern>of</pattern>).
2. If the Auditor flags a "Generic Noun" or "Tag Scope Error", you MUST move the <pattern> tags to the correct grammatical connector.
3. If the current sentence doesn't have a good collocation, YOU MUST REWRITE the sentence to demonstrate a high-value GSAT pattern.
4. Output the ENTIRE fixed card as valid JSON matching the schema.
5. DO NOT CHANGE UNMENTIONED FIELDS.

Original System Prompt for reference:
{SYSTEM_PROMPT}
"""

def edit_batch(batch_items: List[Dict[str, str]]) -> Optional[BatchWordResult]:
    batch_prompt = "### BATCH TO FIX:\n"
    for i, item in enumerate(batch_items):
        batch_prompt += f"Card {i+1} ({item['headword']}):\n"
        batch_prompt += f"  Current Data: {item['response']}\n"
        batch_prompt += f"  Auditor Feedback: {item['comment']}\n---\n"
    
    try:
        response = client.models.generate_content(
            model="gemma-4-31b-it",
            contents=batch_prompt,
            config={
                "system_instruction": EDITOR_SYSTEM_PROMPT,
                "response_mime_type": "application/json",
                "response_schema": BatchWordResult,
                "temperature": 1.0,
                "thinking_config": {
                    "include_thoughts": False,
                    "thinking_level": "high"
                }
            }
        )
        return response.parsed
    except Exception as e:
        print(f"Error fixing batch: {e}")
        return None

def main() -> None:
    # Change level here
    edit_level = 3

    file_path = f"data/raw/level{edit_level}.tsv"
    if not os.path.exists(file_path): return

    rows = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not fieldnames: return

    # Target cards marked ai_fail with less than 3 attempts
    pending_indices = [
        i for i, r in enumerate(rows) 
        if r.get("verification") == "ai_fail" and int(r.get("attempts", 0)) < 3
    ]
    
    if not pending_indices:
        print("No cards need fixing.")
        return


    updated_count = 0
    batch_size = 10
    
    print(f"Surgically fixing {len(pending_indices)} cards in batches of {batch_size} for Level {edit_level}...")
    
    for i in range(0, len(pending_indices), batch_size):
        batch_idx_chunk = pending_indices[i : i + batch_size]
        batch_items = [rows[idx] for idx in batch_idx_chunk]
        
        print(f"  Fixing batch {i//batch_size + 1} ({len(batch_items)} cards)...")
        fixed_batch = edit_batch(batch_items)
        
        if fixed_batch and len(fixed_batch.results) == len(batch_items):
            for fixed_data, row_idx in zip(fixed_batch.results, batch_idx_chunk):
                # Use json.dumps for readable spacing
                rows[row_idx]["response"] = json.dumps(fixed_data.model_dump(), ensure_ascii=False)
                rows[row_idx]["verification"] = "none" # Reset to none for re-audit
                rows[row_idx]["comment"] = "" # Clear old auditor feedback
                rows[row_idx]["attempts"] = str(int(rows[row_idx].get("attempts", 0)) + 1)
                updated_count += 1
            
            # Incremental save
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
                writer.writeheader()
                writer.writerows(rows)
            print(f"    Batch complete and saved. Total fixed: {updated_count}")
        else:
            print("    Error: API failure or batch size mismatch. Skipping.")
        
        time.sleep(2)

    print(f"\nEditing complete. Fixed {updated_count} cards and moved them back to 'none' for re-verification.")

if __name__ == "__main__":
    main()
