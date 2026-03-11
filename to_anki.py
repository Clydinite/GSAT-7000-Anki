import csv
import json
import re
import os

def format_sentence(sentence):
    # Replace <word> with <span class="target-word">word</span>
    sentence = re.sub(r'<(.*?)>', r'<span class="target-word">\1</span>', sentence)
    # Replace *collocation* with <span class="collocation">collocation</span>
    sentence = re.sub(r'\*(.*?)\*', r'<span class="collocation">\1</span>', sentence)
    return sentence

def generate_html(data):
    html = []
    html.append('<div class="anki-card-content">')
    
    # General Explanation (Usage Note)
    if data.get("explanation"):
        html.append(f'  <div class="general-explanation">{data["explanation"]}</div>')
    
    # Entries
    html.append('  <div class="entries-container">')
    for entry in data.get("entries", []):
        html.append('    <div class="entry">')
        html.append(f'      <div class="sentence">{format_sentence(entry["sentence"])}</div>')
        html.append(f'      <div class="translation">{entry["translation"]}</div>')
        if entry.get("explanation"):
            html.append(f'      <div class="entry-explanation">{entry["explanation"]}</div>')
        html.append('    </div>')
    html.append('  </div>')
    
    # Related Forms
    if data.get("related_forms"):
        forms = ", ".join(data["related_forms"])
        html.append(f'  <div class="related-forms"><span class="label">Related:</span> {forms}</div>')
    
    html.append('</div>')
    return "".join(html)

def convert_to_anki(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, "r", encoding="utf-8") as f_in, \
         open(output_file, "w", encoding="utf-8", newline="") as f_out:
        
        reader = csv.DictReader(f_in, delimiter="\t")
        writer = csv.writer(f_out, delimiter="\t")
        
        # Anki TSV typically doesn't need a header, but we'll write one for reference 
        # (Anki allows skipping the first line)
        # Fields: Front (Headword), Back (HTML)
        
        count = 0
        for row in reader:
            try:
                data = json.loads(row["response"])
                headword = row["headword"]
                html_content = generate_html(data)
                
                writer.writerow([headword, html_content])
                count += 1
            except Exception as e:
                print(f"Error processing word {row.get('headword')}: {e}")
        
        print(f"Successfully converted {count} words to {output_file}")

if __name__ == "__main__":
    convert_to_anki("raw_gsat_data.tsv", "anki_import.tsv")
