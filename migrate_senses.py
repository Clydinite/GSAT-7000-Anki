import csv
import json
import os
import re

# Regex for full-width brackets at the end of the string
# Matches （content） at the end of the line
BRACKET_REGEX = re.compile(r'（([^（）]*)）$')

def migrate_tsv(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return
    
    rows = []
    modified = False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        fieldnames = reader.fieldnames
        for row in reader:
            try:
                # The response column contains the JSON
                data = json.loads(row['response'])
                
                # Handle both BatchFlashcard and single Flashcard formats
                flashcards = data['results'] if 'results' in data else [data]
                
                for card in flashcards:
                    if 'senses' not in card:
                        continue
                        
                    new_senses = []
                    for sense in card['senses']:
                        sense_text = sense.get('sense', '')
                        match = BRACKET_REGEX.search(sense_text)
                        
                        if match:
                            # Extract content
                            explanation = match.group(1)
                            clean_sense = sense_text[:match.start()].strip()
                            
                            # Create a new dictionary to ensure field order: 
                            # 'sense' then 'explanation' then the rest.
                            # Python 3.7+ dicts preserve insertion order.
                            new_sense = {}
                            new_sense['sense'] = clean_sense
                            new_sense['explanation'] = explanation
                            
                            # Copy remaining fields from original sense
                            for key, value in sense.items():
                                if key not in ['sense', 'explanation']:
                                    new_sense[key] = value
                                    
                            new_senses.append(new_sense)
                            modified = True
                        else:
                            new_senses.append(sense)
                            
                    card['senses'] = new_senses
                
                # Update the response column with the modified JSON
                row['response'] = json.dumps(data, ensure_ascii=False)
                rows.append(row)
            except Exception as e:
                print(f"Error processing row in {file_path}: {e}")
                rows.append(row)

    if modified:
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
            writer.writeheader()
            writer.writerows(rows)
        print(f"Successfully migrated {file_path}")
    else:
        print(f"No changes needed for {file_path}")

def main():
    raw_dir = 'data/raw'
    if not os.path.exists(raw_dir):
        print(f"Directory {raw_dir} not found.")
        return
        
    for filename in os.listdir(raw_dir):
        if filename.endswith('.tsv'):
            migrate_tsv(os.path.join(raw_dir, filename))

if __name__ == '__main__':
    main()
