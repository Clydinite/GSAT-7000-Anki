import csv
import json
import os
import random
from argparse import Namespace, ArgumentParser
from enum import Enum
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

# --- State Management ---

VerificationState = Literal["none", "ai_pass", "ai_fail", "human"]

# --- Flashcard ---

class PartOfSpeech(str, Enum):
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PRONOUN = "pronoun"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    INTERJECTION = "interjection"
    DETERMINER = "determiner"
    PHRASE = "phrase"

class WordPosTranslation(BaseModel):
    word: str = Field(..., description="Word")
    pos: PartOfSpeech = Field(..., description="Part of speech")
    translation: str = Field(..., description="Traditional Chinese translation")
    explanation: Optional[str] = Field(None, description="Additional notes in Traditional Chinese")

class Conjugations(BaseModel):
    past_tense: str = Field(..., description="Past tense")
    past_participle: str = Field(..., description="Past participle")
    
class Relatives(BaseModel):
    morphology: str = Field(..., description="The morphology of the headword")
    related: List[WordPosTranslation]

class Sentence(BaseModel):
    sentence: str = Field(..., description="Example sentence (e.g., He <target>accused</target> him <pattern>of</pattern> theft.)")
    translation: str = Field(..., description="Traditional Chinese translation")

class Entry(BaseModel):
    pattern: str = Field(..., description="Collocation pattern, can be the word itself or a phrase (e.g. to accuse sb. of sth.)")
    pos: PartOfSpeech = Field(..., description="Part of speech")
    translation: str = Field(..., description="Traditional Chinese translation")
    explanation: Optional[str] = Field(None, description="Usage/Grammar note in Traditional Chinese")
    sentences: List[Sentence]

class Sense(BaseModel):
    sense: str = Field(..., description="Core meaning in Traditional Chinese")
    entries: List[Entry]

class Flashcard(BaseModel):
    headword: str = Field(..., description="Headword")
    explanation: str = Field(..., description="Usage/Grammar note in Traditional Chinese")
    senses: List[Sense]
    conjugations: Optional[Conjugations]
    relatives: Relatives = Field(..., description="Word families")
    synonyms: List[WordPosTranslation] = Field(default_factory=list)
    antonyms: List[WordPosTranslation] = Field(default_factory=list)
    
class BatchFlashcard(BaseModel):
    results: List[Flashcard]
    
# --- Verification ---

class VerificationResult(BaseModel):
    headword: str
    status: Literal["pass", "fail"]
    comment: str  # Natural language description of the problem

class BatchVerificationResult(BaseModel):
    results: List[VerificationResult]

def get_random_human_examples(count: int = 10) -> List[dict]:
    """Fetches random human-verified examples to use as a few-shot seed."""
    file_path = "data/verified_examples.tsv"
    
    if not os.path.exists(file_path): 
        print(f"Warning: Verified examples not found at {file_path}.")
        return []
    
    examples: List[dict] = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            rows: List[dict] = list(reader)
            if not rows: return []
        
            selected: List[dict] = random.sample(rows, min(len(rows), count))
            for row in selected:
                try:
                    examples.append({
                        "headword": row["headword"], 
                        "response": json.loads(row["response"])
                    })
                except: continue
    except Exception as e:
        print(f"Error sampling human examples: {e}")
        return []

    return examples

def append_to_raw_tsv(level: int, words: List[str], batch_results: BatchFlashcard, verification: VerificationState = "none", comment: str = "", attempts: int = 0) -> None:
    output_file: str = f"data/raw/level{level}.tsv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    file_exists: bool = os.path.exists(output_file) and os.path.getsize(output_file) > 0
    with open(output_file, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        if not file_exists:
            writer.writerow(["headword", "raw_string", "response", "verification", "comment", "attempts"])
        for idx, r in enumerate(batch_results.results):
            raw_string: str = words[idx] if idx < len(words) else r.headword
            writer.writerow([r.headword, raw_string, r.model_dump_json(), verification, comment, attempts])
        f.flush()

# --- CLI configuration ---
class ScriptArgs(Namespace):
    level: int
    
def get_common_parser(description: str) -> ArgumentParser:
    """Common parser for all scripts."""
    parser = ArgumentParser(description=description)
    parser.add_argument("--level", "-l", type=int, choices=range(1, 7), required=True, help="Level to be generated/verified/edited. Must be between 1 and 6.")
    return parser

SYSTEM_PROMPT = """
Act as a Taiwanese GSAT English teacher and provide Anki flashcard content for the given words. Follow the instructions and format strictly.

Rules:
- Parts of Speech & Senses: Include all common senses and all common parts of speech for the given word. Do not leave out high-yield definitions that are frequently tested on the GSAT.
- The i+1 Principle & Sentence Difficulty Scaling: Example sentences must provide rich, descriptive context so that the meaning of the target word is highly clear and guessable. To ensure absolute comprehensibility for GSAT students, the vocabulary surrounding the target word must be at a slightly lower difficulty level than the target word itself (e.g., if the target word is Level 4, the sentence should primarily use Level 2 and Level 3 words). Never use surrounding words that are more difficult than the target word itself.
- Sentence Length & Themes: Each example sentence must be between 15 and 35 words long. Contexts should revolve around academic, social, environmental, or school-life themes common in the GSAT, though lighthearted or relatable scenario prompts are also highly encouraged.

Fields Guide:
- headword: The base form of the word. Do not include any POS tags, parentheses, or suffix variations here (e.g., use "achieve", not "achieve (v.)" or "achieve(ment)").
- explanation: A high-value usage note in Traditional Chinese focusing on syntax, common errors, or core conceptual metaphors. Avoid filler words or explicitly mentioning the acronym "GSAT".
- senses: A list of core semantic clusters.
- entries: A list of distinct collocation patterns or phrases belonging to that specific sense.
    - pattern: The specific grammatical structure or formula (e.g., "accuse sb. of sth.", "object to sth./doing sth.").
    - pos: The part of speech enum value matching the pattern ("phrase" should be used when the entry represents a multi-word idiom or fixed prepositional structure rather than a standalone word class).
    - explanation: A clear grammatical or contextual usage note in Traditional Chinese. Crucial: This field must remain plain text. Do not use Markdown styling (* or **) or XML tags (<target> or <pattern>) inside this specific field.
    - sentences: A list of example sentences matching the pattern.
        - Text Marking Rules: 
            - Wrap the exact inflected, conjugated, or derived form of the headword inside `<target>...</target>` tags. The entire word variant must be enclosed (e.g., `<target>accused</target>`, NOT `<target>accuse</target>d`). Never span these tags across multiple words.
            - Wrap the essential accompanying elements of the collocation formula (such as fixed prepositions, dependent verbs, or nouns) inside `<pattern>...</pattern>` tags. Never wrap the headword itself in pattern tags.
- conjugations: Provide the past tense and past participle strings if the headword functions as a verb. Set to null if the word does not have verb inflections.
- relatives: A structured word-family object.
    - morphology: A brief textual breakdown in Traditional Chinese highlighting the shared prefix, root, or suffix blocks (e.g., "字首 pre- (預先) + 字根 dict (說)").
    - related: A list of words sharing this morphological framework. Use these entries to expand the student's pattern recognition of word stems and structural suffixes.
- synonyms / antonyms: Lists of contextual equivalents or opposites using the `WordPosTranslation` model to ensure parts of speech align cleanly.
"""