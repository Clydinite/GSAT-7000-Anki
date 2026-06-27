from utils import get_common_parser, Flashcard
import html
import json
import re
import os
import csv

def format_sentence(sentence: str) -> str:
    """Adds styling spans to the sentence markers."""
    sentence = re.sub(r'<target>(.*?)</target>', r'<span class="target-word">\1</span>', sentence)
    sentence = re.sub(r'<pattern>(.*?)</pattern>', r'<span class="collocation">\1</span>', sentence)
    return sentence

def clean_for_tts(sentence: str) -> str:
    """Removes marker characters for clean speech synthesis."""
    return re.sub(r'<[^>]*>', '', sentence).strip()

def strip_tags(text: str) -> str:
    """Removes XML-style tags for clean display."""
    return re.sub(r'<[^>]*>', '', text).strip()

def generate_html(card: Flashcard) -> str:
    html_parts = ['<div class="anki-card-content">']

    # 1. Past Tense / Conjugations header
    if card.conjugations:
        html_parts.append(f'<div class="conjugations">Past: {card.conjugations.past_tense} | PP: {card.conjugations.past_participle}</div>')

    # 2. Morphology dropdown
    html_parts.append('<div class="meta-section">')
    html_parts.append('<button class="accordion-trigger"><span>Morphology & Relatives</span></button>')
    html_parts.append('<div class="accordion-content">')
    html_parts.append(f'<div class="morphology">{html.escape(card.relatives.morphology)}</div>')
    for rel in card.relatives.related:
        html_parts.append(f'<div class="related-item">{html.escape(rel.word)} ({rel.pos.value}): {html.escape(rel.translation)}</div>')
    html_parts.append('</div></div>')

    # 3. Senses and Entries
    html_parts.append('<div class="senses-container">')
    for i, sense in enumerate(card.senses, 1):
        html_parts.append(f'<div class="sense"><div class="sense-number">{i}.</div> <div class="sense-text">{html.escape(sense.sense)}</div></div>')
        
        for entry in sense.entries:
            html_parts.append('<div class="entry">')
            html_parts.append(f'<div class="pattern-label">{html.escape(entry.pattern)}</div>')
            
            # Sentence Loop
            for s in entry.sentences:
                clean_tts = html.escape(clean_for_tts(s.sentence), quote=True)
                html_parts.append('<div class="sentence-row">')
                html_parts.append(f'<div class="sentence">{format_sentence(s.sentence)}</div>')
                html_parts.append(f'<button class="tts-button" data-tts="{clean_tts}" onclick="window.playTTS(this.getAttribute(\'data-tts\'))"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg></button>')
                html_parts.append('</div>')
            
            # Translation/Explanation
            html_parts.append('<div class="meta-section">')
            html_parts.append(f'<div class="translation">{html.escape(entry.translation)}</div>')
            if entry.explanation:
                html_parts.append(f'<div class="entry-explanation">{html.escape(entry.explanation)}</div>')
            html_parts.append('</div></div>')
            
    html_parts.append('</div></div>')
    return re.sub(r'\s+', ' ', "".join(html_parts)).strip()

def convert_to_anki(input_file: str, output_file: str):
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
                card = Flashcard.model_validate_json(row["response"])
                writer.writerow([card.headword, generate_html(card)])
                count += 1
            except Exception as e:
                print(f"Error processing word {row.get('headword')}: {e}")
        print(f"Successfully converted {count} words to {output_file}")

if __name__ == "__main__":
    parser = get_common_parser("Level to convert to Anki TSV")
    args = parser.parse_args()
    
    level = args.level
    os.makedirs("data/Anki", exist_ok=True)
    convert_to_anki(f"data/raw/level{level}.tsv", f"data/Anki/level{level}_import.tsv")
