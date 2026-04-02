import csv
import json
import re
import os
import html

def format_sentence(sentence):
    """Adds styling spans to the sentence markers."""
    # Replace <word> with <span class="target-word">word</span>
    sentence = re.sub(r'<(.*?)>', r'<span class="target-word">\1</span>', sentence)
    # Replace *collocation* with <span class="collocation">collocation</span>
    sentence = re.sub(r'\*(.*?)\*', r'<span class="collocation">\1</span>', sentence)
    return sentence

def clean_for_tts(sentence):
    """Removes marker characters for clean speech synthesis."""
    return sentence.replace("<", "").replace(">", "").replace("*", "").strip()

def generate_html(data):
    html_parts = []
    html_parts.append('<div class="anki-card-content">')

    # General Explanation
    if data.get("explanation"):
        html_parts.append(f'<div class="general-explanation">{html.escape(data["explanation"])}</div>')

    # Entries
    html_parts.append('<div class="entries-container">')
    for entry in data.get("entries", []):
        sentence_raw = entry.get("sentence", "")
        clean_tts = clean_for_tts(sentence_raw)
        safe_tts = html.escape(clean_tts, quote=True)
        
        html_parts.append('<div class="entry">')
        html_parts.append('<div class="sentence-row">')
        html_parts.append(f'<div class="sentence">{format_sentence(sentence_raw)}</div>')
        
        # We use this.getAttribute to avoid the JS quote escaping issue entirely.
        html_parts.append(f'<button class="tts-button" data-tts="{safe_tts}" onclick="window.playTTS(this.getAttribute(\'data-tts\'))">')
        html_parts.append('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>')
        html_parts.append('</button></div>')

        if entry.get("translation") or entry.get("explanation"):
            html_parts.append('<div class="meta-section">')
            if entry.get("translation"):
                html_parts.append(f'<div class="translation">{html.escape(entry["translation"])}</div>')
            if entry.get("explanation"):
                html_parts.append(f'<div class="entry-explanation">{html.escape(entry["explanation"])}</div>')
            html_parts.append('</div>')
        html_parts.append('</div>')
    html_parts.append('</div>')

    # Related Forms
    if data.get("related_forms"):
        forms = html.escape(", ".join(data["related_forms"]))
        html_parts.append(f'<div class="related-forms"><span class="label">Related:</span> {forms}</div>')

    html_parts.append('</div>')
    # Flatten to single line
    return re.sub(r'\s+', ' ', "".join(html_parts)).strip()

def convert_to_anki(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return
    with open(input_file, "r", encoding="utf-8") as f_in, \
         open(output_file, "w", encoding="utf-8", newline="") as f_out:
        reader = csv.DictReader(f_in, delimiter="\t")
        writer = csv.writer(f_out, delimiter="\t")
        
        count = 0
        for row in reader:
            try:
                data = json.loads(row["response"])
                writer.writerow([row["headword"], generate_html(data)])
                count += 1
            except Exception as e:
                print(f"Error processing word {row.get('headword')}: {e}")
        print(f"Successfully converted {count} words to {output_file}")

if __name__ == "__main__":
    convert_to_anki("raw_gsat_data.tsv", "anki_import.tsv")
