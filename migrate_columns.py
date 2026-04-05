import csv
import os

def migrate_tsv_columns(file_path, default_attempts=0):
    if not os.path.exists(file_path):
        print(f"Skipping {file_path} (not found).")
        return

    print(f"Migrating columns for {file_path}...")
    temp_path = file_path + ".cols"
    
    with open(file_path, "r", encoding="utf-8") as f_in, \
         open(temp_path, "w", encoding="utf-8", newline="") as f_out:
        
        reader = csv.reader(f_in, delimiter="\t")
        writer = csv.writer(f_out, delimiter="\t")
        
        header = next(reader, None)
        if not header:
            return

        # Check if already migrated
        if "attempts" in header:
            print(f"{file_path} is already migrated.")
            return

        # Write new header
        writer.writerow(header + ["attempts"])
            
        for row in reader:
            if not row: continue
            # Append default values
            writer.writerow(row + [default_attempts])

    os.replace(temp_path, file_path)
    print(f"Successfully migrated columns in {file_path}")

if __name__ == "__main__":
    # Level 3 is finished, so mark as human-verified
    migrate_tsv_columns("data/raw/level3.tsv", default_attempts=0)
    # Level 4 is in progress, so mark as none
    migrate_tsv_columns("data/raw/level4.tsv", default_attempts=0)
