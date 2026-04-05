import csv
import json
import os
import re

def strip_tags(text):
    """Removes <pattern> and <target> tags, leaving the inner text."""
    if not isinstance(text, str):
        return text
    # Remove opening and closing tags
    text = re.sub(r'</?(pattern|target)>', '', text)
    return text

def repair_file(file_path):
    if not os.path.exists(file_path):
        print(f"Skipping {file_path} (not found).")
        return

    print(f"Repairing tags in non-sentence fields: {file_path}...")
    temp_path = file_path + ".repair"
    
    with open(file_path, "r", encoding="utf-8") as f_in, \
         open(temp_path, "w", encoding="utf-8", newline="") as f_out:
        
        reader = csv.reader(f_in, delimiter="\t")
        writer = csv.writer(f_out, delimiter="\t")
        
        header = next(reader, None)
        if header:
            writer.writerow(header)
            
        for row in reader:
            if len(row) < 3:
                writer.writerow(row)
                continue
                
            headword, raw_string, response_json = row
            
            try:
                data = json.loads(response_json)
                
                # 1. Clean General Explanation
                if "explanation" in data:
                    data["explanation"] = strip_tags(data["explanation"])
                
                # 2. Clean Entry fields except 'sentence'
                if "entries" in data:
                    for entry in data["entries"]:
                        if "translation" in entry:
                            entry["translation"] = strip_tags(entry["translation"])
                        if "explanation" in entry:
                            entry["explanation"] = strip_tags(entry["explanation"])
                        # NOTE: entry["sentence"] is LEFT ALONE (keeps tags)
                
                new_response = json.dumps(data, ensure_ascii=False)
                writer.writerow([headword, raw_string, new_response])
            except Exception as e:
                print(f"Error in row {headword}: {e}")
                writer.writerow(row)

    os.replace(temp_path, file_path)
    print(f"Repair complete for {file_path}")

if __name__ == "__main__":
    repair_file("data/raw/level3.tsv")
    repair_file("data/raw/level4.tsv")
