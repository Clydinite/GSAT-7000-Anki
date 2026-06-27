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
    
    # 1. Header Block
    html_parts.append(f'<h1 class="headword">{html.escape(card.headword)}</h1>')
    if card.explanation:
        html_parts.append(f'<div class="general-explanation">{html.escape(card.explanation)}</div>')

    # 2. Meta Section (This container is targeted by back.html to create the dropdown)
    html_parts.append('<div class="meta-section">')
    
    # Section A: Morphology
    html_parts.append('<div class="meta-block">')
    html_parts.append('<h3 class="meta-label">Morphology</h3>')
    html_parts.append(f'<p class="morphology-text">{html.escape(card.relatives.morphology)}</p>')
    html_parts.append('</div>')
    
    # Section B: Related Words (Using Unordered List)
    if card.relatives.related:
        html_parts.append('<div class="meta-block">')
        html_parts.append('<h3 class="meta-label">Related Words</h3>')
        html_parts.append('<ul class="meta-list">')
        for rel in card.relatives.related:
            html_parts.append(
                f'<li class="meta-list-item">'
                f'<span class="item-word">{html.escape(rel.word)}</span>'
                f'<span class="pos-badge pos-{rel.pos.value.lower()}">{rel.pos.value.lower()}.</span>'
                f'<span class="item-trans">{html.escape(rel.translation)}</span>'
                f'</li>'
            )
        html_parts.append('</ul></div>')
    
    # Section C: Conjugations
    if card.conjugations:
        html_parts.append('<div class="meta-block">')
        html_parts.append('<h3 class="meta-label">Conjugations</h3>')
        html_parts.append('<div class="conjugations-grid">')
        html_parts.append(f'<div class="conj-card"><span class="conj-header">Past</span><span class="conj-value">{html.escape(card.conjugations.past_tense)}</span></div>')
        html_parts.append(f'<div class="conj-card"><span class="conj-header">Past Part.</span><span class="conj-value">{html.escape(card.conjugations.past_participle)}</span></div>')
        html_parts.append('</div></div>')

    # Section D: Synonyms (Using Unordered List, standard styling)
    if card.synonyms:
        html_parts.append('<div class="meta-block">')
        html_parts.append('<h3 class="meta-label">Synonyms</h3>')
        html_parts.append('<ul class="meta-list">')
        for s in card.synonyms:
            html_parts.append(
                f'<li class="meta-list-item">'
                f'<span class="item-word">{html.escape(s.word)}</span>'
                f'<span class="pos-badge pos-{s.pos.value.lower()}">{s.pos.value.lower()}.</span>'
                f'<span class="item-trans">{html.escape(s.translation)}</span>'
                f'</li>'
            )
        html_parts.append('</ul></div>')

    # Section E: Antonyms (Using Unordered List, standard styling)
    if card.antonyms:
        html_parts.append('<div class="meta-block">')
        html_parts.append('<h3 class="meta-label">Antonyms</h3>')
        html_parts.append('<ul class="meta-list">')
        for a in card.antonyms:
            html_parts.append(
                f'<li class="meta-list-item">'
                f'<span class="item-word">{html.escape(a.word)}</span>'
                f'<span class="pos-badge pos-{a.pos.value.lower()}">{a.pos.value.lower()}.</span>'
                f'<span class="item-trans">{html.escape(a.translation)}</span>'
                f'</li>'
            )
        html_parts.append('</ul></div>')

    html_parts.append('</div>') # End of meta-section dropdown

    # 3. Core Senses & Layout (Keeping the acceptable bottom layout, polishing spacing)
    html_parts.append('<div class="senses-container">')
    for i, sense in enumerate(card.senses, 1):
        html_parts.append(f'<div class="sense-heading"><span class="sense-idx">{i:02d}</span><h2 class="sense-title">{html.escape(sense.sense)}</h2></div>')
        for entry in sense.entries:
            html_parts.append('<div class="entry-card">')
            pos_badge = f'<span class="pos-tag pos-{entry.pos.value.lower()}">{entry.pos.value.lower()}</span>'
            html_parts.append(f'<div class="pattern-header">{pos_badge}<span class="pattern-code">{html.escape(entry.pattern)}</span></div>')
            html_parts.append(f'<div class="pattern-translation">{html.escape(entry.translation)}</div>')
            
            # Context Sentences
            for s in entry.sentences:
                html_parts.append(f'<div class="sentence-item"><p class="sentence-en">{format_sentence(s.sentence)}</p><p class="sentence-zh">{html.escape(s.translation)}</p></div>')
            
            if entry.explanation:
                html_parts.append(f'<div class="entry-note">{html.escape(entry.explanation)}</div>')
            html_parts.append('</div>')
    html_parts.append('</div>')

    html_parts.append('</div>')
    return "".join(html_parts)

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
