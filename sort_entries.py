import csv
import os
import json
from utils import get_common_parser

def sort_level_tsv(level: int):
    vocab_path = f"data/vocabulary/level{level}.txt"
    tsv_path = f"data/raw/level{level}.tsv"
    
    if not os.path.exists(vocab_path):
        print(f"Error: Vocabulary file {vocab_path} not found.")
        return
    if not os.path.exists(tsv_path):
        print(f"Error: TSV file {tsv_path} not found.")
        return

    # 1. Load the reference order
    with open(vocab_path, "r", encoding="utf-8") as f:
        vocab_order = [line.strip() for line in f.readlines() if line.strip()]
    
    # Create a mapping for quick lookup
    order_map = {word: i for i, word in enumerate(vocab_order)}

    # 2. Read existing rows
    rows = []
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not rows:
        print("No data found in TSV.")
        return

    # 3. Sort rows based on the vocab index
    # We use .get(row['raw_string'], 9999) to handle any edge cases
    rows.sort(key=lambda r: order_map.get(r["raw_string"], 9999))

    # 4. Write back the sorted data
    with open(tsv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Successfully sorted {len(rows)} words in {tsv_path} based on {vocab_path}")

if __name__ == "__main__":
    parser = get_common_parser("Sort a raw TSV file based on its source vocabulary list.")
    args = parser.parse_args()
    sort_level_tsv(args.level)
