import csv
import json
import os

def extract_verified(level: int):
    input_file = f"data/raw/level{level}.tsv"
    output_file = f"data/raw/level{level}_verified_only.tsv"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    verified_rows = []
    
    with open(input_file, "r", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in, delimiter="\t")
        for row in reader:
            if row.get("verification") == "human":
                verified_rows.append(row)
    
    if not verified_rows:
        print(f"No human-verified cards found in level {level}.")
        return

    # Write to a clean TSV
    with open(output_file, "w", encoding="utf-8", newline="") as f_out:
        fieldnames = ["headword", "raw_string", "response", "verification", "comment", "attempts"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(verified_rows)
        
    print(f"Successfully extracted {len(verified_rows)} human-verified cards to {output_file}")
    return output_file

if __name__ == "__main__":
    extract_verified(3)
