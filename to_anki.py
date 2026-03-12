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

def escape_js(text):
    """Safely escape text for use in a single-quoted JS onclick attribute."""
    return text.replace("\\", "\\\\").replace("'", "\\'").replace('"', '&quot;')

def generate_html(data):
    html = []
    html.append('<div class="anki-card-content">')

    # General Explanation (Usage Note)
    explanation = data.get("explanation")
    if explanation:
        html.append(f'  <div class="general-explanation">{explanation}</div>')

    # Entries
    html.append('  <div class="entries-container">')
    for entry in data.get("entries", []):
        sentence_raw = entry.get("sentence", "")
        # Clean sentence for TTS: remove the marker characters < > * *
        clean_tts = sentence_raw.replace("<", "").replace(">", "").replace("*", "")
        escaped_tts = escape_js(clean_tts)

        formatted_sentence = format_sentence(sentence_raw)
        translation = entry.get("translation", "")
        entry_note = entry.get("explanation", "")

        html.append('    <div class="entry">')
        html.append('      <div class="sentence-row">')
        html.append(f'        <div class="sentence">{formatted_sentence}</div>')
        html.append(f'        <button class="tts-button" onclick="window.playTTS(\'{escaped_tts}\')">')
        html.append('          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">')
        html.append('            <polygon points="5 3 19 12 5 21 5 3"></polygon>')
        html.append('          </svg>')
        html.append('        </button>')
        html.append('      </div>')

        if translation or entry_note:
            html.append('      <div class="meta-section">')
            if translation:
                html.append(f'        <div class="translation">{translation}</div>')
            if entry_note:
                html.append(f'        <div class="entry-explanation">{entry_note}</div>')
            html.append('      </div>')
        html.append('    </div>')
    html.append('  </div>')

    # Related Forms
    related = data.get("related_forms")
    if related:
        forms_str = ", ".join(related)
        html.append(f'  <div class="related-forms"><span class="label">Related:</span> {forms_str}</div>')

    html.append('</div>')
    return "\n".join(html)

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
                headword = row["headword"]
                html_content = generate_html(data)
                
                # We output: Word, HTML
                writer.writerow([headword, html_content])
                count += 1
            except Exception as e:
                print(f"Error processing word {row.get('headword')}: {e}")
        
        print(f"Successfully converted {count} words to {output_file}")

if __name__ == "__main__":
    convert_to_anki("raw_gsat_data.tsv", "anki_import.tsv")
