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

import html

def render_word_pos_list(title, items):
    if not items: return ""
    res = ['<div class="meta-block">']
    res.append(f'<div class="meta-block-title">{title}</div>')
    res.append('<div class="relatives-group">')
    for item in items:
        pos = item.pos.value.lower()
        explanation_html = f'<div class="rel-explanation">{html.escape(item.explanation)}</div>' if item.explanation else ""
        res.append(
            f'<div class="relative-badge">'
            f'<div class="rel-main">'
            f'<span class="rel-pos pos-{pos}">{pos}</span>'
            f'<span class="rel-word">{html.escape(item.word)}</span>'
            f'<span class="rel-trans">{html.escape(item.translation)}</span>'
            f'</div>'
            f'{explanation_html}'
            f'</div>'
        )
    res.append('</div></div>')
    return "".join(res)

def generate_html(card: Flashcard) -> str:
    html_parts = ['<div class="anki-card-content">']
    
    # 1. Headword
    html_parts.append(f'<h1 class="card-headword">{html.escape(card.headword)}</h1>')

    # 2. Animated Dropdown Section (General Explanation & Meta Data)
    # Check if we have any meta content left
    has_meta = card.conjugations or (card.relatives and (card.relatives.morphology or card.relatives.related))
    
    if card.explanation or has_meta:
        html_parts.append('<div class="meta-section" data-label="Word Origin, Details & Explanation">')
        html_parts.append('<div class="accordion-inner">') 
        html_parts.append('<div class="accordion-inner-padding">')
        
        if card.explanation:
            html_parts.append(f'<div class="general-explanation">{html.escape(card.explanation)}</div>')
            
        if has_meta:
            html_parts.append('<div class="meta-content-inner">')
            
            # Conjugations
            if card.conjugations:
                html_parts.append('<div class="meta-block">')
                html_parts.append('<div class="meta-block-title">Conjugations</div>')
                html_parts.append('<div class="meta-grid">')
                html_parts.append(f'<div class="meta-card"><span class="meta-card-label">Past</span><span class="meta-card-value">{html.escape(card.conjugations.past_tense)}</span></div>')
                html_parts.append(f'<div class="meta-card"><span class="meta-card-label">Past Participle</span><span class="meta-card-value">{html.escape(card.conjugations.past_participle)}</span></div>')
                html_parts.append('</div></div>')
                
            # Morphology
            if card.relatives and card.relatives.morphology:
                html_parts.append('<div class="meta-block">')
                html_parts.append('<div class="meta-block-title">Morphology</div>')
                html_parts.append(f'<div class="morphology-text">{html.escape(card.relatives.morphology)}</div>')
                html_parts.append('</div>')
                
            if card.relatives and card.relatives.related:
                html_parts.append(render_word_pos_list("Related Words", card.relatives.related))
                
            html_parts.append('</div>')
            
        html_parts.append('</div></div></div>')

    # 3. Core Senses
    if card.senses:
        html_parts.append('<div class="senses-container">')
        for i, sense in enumerate(card.senses, 1):
            html_parts.append('<div class="sense-group">')
            html_parts.append('<div class="sense-heading">')
            html_parts.append(f'<span class="sense-idx">{i:02d}</span>')
            html_parts.append(f'<h2 class="sense-title">{html.escape(sense.sense)}</h2>')
            html_parts.append('<button class="sense-reveal-btn" onclick="this.closest(\'.sense-group\').classList.toggle(\'expanded\')">Reveal</button>')
            html_parts.append('</div>')
            
            html_parts.append('<div class="entry-list">')
            for entry in sense.entries:
                html_parts.append('<div class="entry-item">')
                pos_class = f"pos-{entry.pos.value.lower()}"
                html_parts.append('<div class="entry-header">')
                html_parts.append(f'<span class="pos-badge {pos_class}">{html.escape(entry.pos.value.lower())}</span>')
                html_parts.append(f'<span class="entry-pattern">{html.escape(entry.pattern)}</span>')
                html_parts.append(f'<span class="entry-translation hideable">{html.escape(entry.translation)}</span>')
                html_parts.append('</div>')
                
                if entry.explanation:
                    html_parts.append(f'<div class="entry-explanation hideable">{html.escape(entry.explanation)}</div>')
                
                if entry.sentences:
                    html_parts.append('<div class="sentences">')
                    for s in entry.sentences:
                        html_parts.append('<div class="sentence">')
                        html_parts.append(f'<p class="sentence-en">{format_sentence(s.sentence)}</p>')
                        html_parts.append(f'<p class="sentence-zh hideable">{html.escape(s.translation)}</p>')
                        html_parts.append('</div>')
                    html_parts.append('</div>')
                html_parts.append('</div>') # end entry-item
            
            # Nested Section: Synonyms & Antonyms
            if sense.synonyms or sense.antonyms:
                html_parts.append('<div class="sense-meta-extras hideable">')
                if sense.synonyms:
                    html_parts.append(render_word_pos_list("Synonyms", sense.synonyms))
                if sense.antonyms:
                    html_parts.append(render_word_pos_list("Antonyms", sense.antonyms))
                html_parts.append('</div>')
            
            html_parts.append('</div>') # end entry-list
            html_parts.append('</div>') # end sense-group
        html_parts.append('</div>') # end senses-container

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
