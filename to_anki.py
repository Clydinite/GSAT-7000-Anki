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
    # Big Headword
    html_parts.append(f'<h1 class="headword">{html.escape(card.headword)}</h1>')
    
    # Conjugations
    if card.conjugations:
        html_parts.append(f'<div class="conjugations">Past: {card.conjugations.past_tense} | PP: {card.conjugations.past_participle}</div>')

    # Headword explanation
    if card.explanation:
        html_parts.append(f'<div class="general-explanation">{html.escape(card.explanation)}</div>')

    # Morphology dropdown
    html_parts.append('<div class="meta-section">')
    html_parts.append('<button class="accordion-trigger"><span>Morphology & Relatives</span></button>')
    html_parts.append('<div class="accordion-content">')
    html_parts.append(f'<div class="morphology">{html.escape(card.relatives.morphology)}</div>')
    for rel in card.relatives.related:
        html_parts.append(f'<div class="related-item">{html.escape(rel.word)} ({rel.pos.value}): {html.escape(rel.translation)}</div>')
    html_parts.append('</div></div>')

    # Senses and Entries
    html_parts.append('<div class="senses-container">')
    for i, sense in enumerate(card.senses, 1):
        html_parts.append(f'<div class="sense"><div class="sense-number">{i}.</div> <div class="sense-text">{html.escape(sense.sense)}</div></div>')
        
        for entry in sense.entries:
            html_parts.append('<div class="entry">')
            
            # Pattern/POS Row
            html_parts.append('<div class="pattern-container">')
            pos_class = f"pos-{entry.pos.value.lower()}"
            pos_display = entry.pos.value.lower() + "."
            html_parts.append(f'<span class="pos-tag {pos_class}">{html.escape(pos_display)}</span>')
            html_parts.append(f'<span class="pattern-label">{html.escape(entry.pattern)} — {html.escape(entry.translation)}</span>')
            html_parts.append('</div>')
            
            # Sentences
            for s in entry.sentences:
                clean_tts = html.escape(clean_for_tts(s.sentence), quote=True)
                html_parts.append('<div class="sentence-row">')
                html_parts.append(f'<div class="sentence">{format_sentence(s.sentence)}</div>')
                html_parts.append(f'<button class="tts-button" data-tts="{clean_tts}" onclick="window.playTTS(this.getAttribute(\'data-tts\'))"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg></button>')
                html_parts.append('</div>')
                html_parts.append(f'<div class="translation" style="margin-bottom: 12px; font-size: 0.9em; opacity: 0.8;">{html.escape(s.translation)}</div>')
            
            # Entry Explanation
            if entry.explanation:
                html_parts.append(f'<div class="entry-explanation" style="margin-bottom: 12px;">{html.escape(entry.explanation)}</div>')
            html_parts.append('</div>') # end entry

            
    html_parts.append('</div>') # end senses-container

    # 4. Synonyms / Antonyms
    if card.synonyms or card.antonyms:
        html_parts.append('<div class="related-forms">')
        if card.synonyms:
            syns = [f"{s.word} ({s.translation})" for s in card.synonyms]
            html_parts.append(f'<div class="related-item">Synonyms: {", ".join(syns)}</div>')
        if card.antonyms:
            ants = [f"{a.word} ({a.translation})" for a in card.antonyms]
            html_parts.append(f'<div class="related-item">Antonyms: {", ".join(ants)}</div>')
        html_parts.append('</div>')
            
    html_parts.append('</div>') # end anki-card-content
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
