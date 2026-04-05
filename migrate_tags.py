import csv
import json
import os
import re

def convert_content(text):
    # 1. Convert headword markers: <word> -> <target>word</target>
    # Note: Using non-greedy match to handle multiple markers in one sentence
    text = re.sub(r'<(.*?)>', r'<target>\1</target>', text)
    
    # 2. Convert collocation markers: *collocation* -> <pattern>collocation</pattern>
    text = re.sub(r'\*(.*?)\*', r'<pattern>\1</pattern>', text)
    
    return text

def migrate_file(file_path):
    if not os.path.exists(file_path):
        print(f"Skipping {file_path} (not found).")
        return

    print(f"Migrating {file_path}...")
    temp_path = file_path + ".tmp"
    
    with open(file_path, "r", encoding="utf-8") as f_in, \
         open(temp_path, "w", encoding="utf-8", newline="") as f_out:
        
        reader = csv.reader(f_in, delimiter="\t")
        writer = csv.writer(f_out, delimiter="\t")
        
        # Handle Header
        header = next(reader, None)
        if header:
            writer.writerow(header)
            
        count = 0
        for row in reader:
            if len(row) < 3:
                writer.writerow(row)
                continue
                
            headword, raw_string, response_json = row
            
            try:
                # Parse JSON, migrate its internal strings, then dump back
                data = json.loads(response_json)
                
                # Migrate explanation
                if "explanation" in data:
                    data["explanation"] = convert_content(data["explanation"])
                
                # Migrate entries
                if "entries" in data:
                    for entry in data["entries"]:
                        if "sentence" in entry:
                            entry["sentence"] = convert_content(entry["sentence"])
                        if "explanation" in entry:
                            entry["explanation"] = convert_content(entry["explanation"])
                
                # Re-dump JSON with ensure_ascii=False to preserve Chinese characters
                new_response = json.dumps(data, ensure_ascii=False)
                writer.writerow([headword, raw_string, new_response])
                count += 1
            except Exception as e:
                print(f"Error in row {headword}: {e}")
                writer.writerow(row)

    # Replace original with migrated version
    os.replace(temp_path, file_path)
    print(f"Successfully migrated {count} records in {file_path}")

if __name__ == "__main__":
    migrate_file("data/raw/level3.tsv")
    migrate_file("data/raw/level4.tsv")
