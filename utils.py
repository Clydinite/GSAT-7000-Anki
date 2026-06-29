import csv
import json
import os
import random
from argparse import Namespace, ArgumentParser
from enum import Enum
from typing import List, Optional, Literal, Dict, Any, Tuple
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
    synonyms: List[WordPosTranslation] = Field(default_factory=list)
    antonyms: List[WordPosTranslation] = Field(default_factory=list)

class Flashcard(BaseModel):
    headword: str = Field(..., description="Headword")
    explanation: str = Field(..., description="Usage/Grammar note in Traditional Chinese")
    senses: List[Sense]
    conjugations: Optional[Conjugations]
    relatives: Relatives = Field(..., description="Word families")
    
class BatchFlashcard(BaseModel):
    results: List[Flashcard]
    
# --- Verification ---

class VerificationResult(BaseModel):
    headword: str
    status: Literal["pass", "fail"]
    comment: str  # Natural language description of the problem

class BatchVerificationResult(BaseModel):
    results: List[VerificationResult]
    
# --- File Management ---

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
- senses: A list of core semantic clusters. Please split the meanings into separate senses if they would not be considered related by a student. (not to linguists, but to GSAT students) 
- entries: A list of distinct collocation patterns or phrases belonging to that specific sense.
    - pattern: The specific grammatical structure or formula (e.g., "accuse sb. of sth.", "object to sth./doing sth."). Please provide a significant amount of patterns to prepare the student for the test.
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

def get_few_shots() -> List[Tuple[str, Flashcard]]:
    """Return human-verified examples to use as a few-shot seed."""

    examples: List[Tuple[str, Flashcard]] = [
        (
            "predict v.",
            Flashcard.model_validate(
                {
                    "headword": "predict",
                    "explanation": "「predict」由字根「pre- (預先)」與「dict (說、言語)」組合而成，字面意為「預先說出」。不論在閱讀測驗的天氣、科技發展預測，或寫作論述中都極為常見，通常接抽象名詞或名詞子句作受詞。",
                    "senses": [
                        {
                            "sense": "預測；預言（根據跡象或科學推測未來）",
                            "entries": [
                                {
                                    "pattern": "predict sth.",
                                    "pos": "verb",
                                    "translation": "預測某事",
                                    "explanation": "及物動詞直接接受詞，受詞常為未來發生的事件、結果或天氣變化。",
                                    "sentences": [
                                        {
                                            "sentence": "Meteorologists use advanced satellite data to <target>predict</target> the exact path of the approaching typhoon.",
                                            "translation": "氣象學家利用先進的衛星數據來預測即將來襲的颱風的精確路徑。",
                                        }
                                    ],
                                },
                                {
                                    "pattern": "predict that...",
                                    "pos": "phrase",
                                    "translation": "預測…（後接子句）",
                                    "explanation": "動詞後接名詞子句作為完整的預測內容，是寫作時論述趨勢的高頻句型。",
                                    "sentences": [
                                        {
                                            "sentence": "Economists <target>predict</target> <pattern>that</pattern> global oil prices will continue to fluctuate over the next quarter.",
                                            "translation": "經濟學家預測，全球油價在下一季度將繼續波動。",
                                        }
                                    ],
                                },
                            ],
                        }
                    ],
                    "conjugations": {
                        "past_tense": "predicted",
                        "past_participle": "predicted",
                    },
                    "relatives": {
                        "morphology": "字根 dict (說、言語) 與字首 pre- (預先)",
                        "related": [
                            {
                                "word": "predictable",
                                "pos": "adjective",
                                "translation": "可預測的；墨守成規的",
                                "explanation": "由動詞 predict 加上形容詞字尾 -able 延伸而來。",
                            },
                            {
                                "word": "prediction",
                                "pos": "noun",
                                "translation": "預測；預言",
                                "explanation": "由動詞 predict 加上名詞字尾 -tion 延伸而來。",
                            },
                            {
                                "word": "contradict",
                                "pos": "verb",
                                "translation": "反駁；與…矛盾",
                                "explanation": "字根組合：contra- (相反) + dict (說)，意為說反話。",
                            },
                            {
                                "word": "dictate",
                                "pos": "verb",
                                "translation": "口述；命令；支配",
                                "explanation": "字根 dict 延伸，引申為依據命令或話語來支配他人。",
                            },
                        ],
                    },
                    "synonyms": [
                        {"word": "foresee", "pos": "verb", "translation": "預見；預知"},
                        {
                            "word": "forecast",
                            "pos": "verb",
                            "translation": "預測（常用於天氣或經濟狀況）",
                        },
                    ],
                    "antonyms": [
                        {
                            "word": "hindsight",
                            "pos": "noun",
                            "translation": "事後諸葛；後見之明",
                        }
                    ],
                }
            ),
        ),
        (
            "object n./v.",
            Flashcard.model_validate(
                {
                    "headword": "object",
                    "explanation": "「object」字根為「ob- (朝向、反對)」+「ject (投擲)」，字面意為「投向對立面」。其名詞與動詞語意截然不同且皆為精華考點：名詞指物理上的「物體」或抽象的「目標」；動詞則表示強烈的「反對」，務必注意其動詞搭配的介系詞 to。",
                    "senses": [
                        {
                            "sense": "物體；目標；受詞（名詞字義）",
                            "entries": [
                                {
                                    "pattern": "object",
                                    "pos": "noun",
                                    "translation": "物體；實體",
                                    "explanation": "指肉眼可見或物理存在的實體物品。",
                                    "sentences": [
                                        {
                                            "sentence": "The radar detected a strange, unidentified <target>object</target> moving at an incredible speed over the ocean.",
                                            "translation": "雷達偵測到一個奇特、不明的物體在海面上以令人難以置信的速度移動。",
                                        }
                                    ],
                                },
                                {
                                    "pattern": "the object of sth.",
                                    "pos": "phrase",
                                    "translation": "…的目的、目標",
                                    "explanation": "抽象語意，等同於 purpose 或 aim。在寫作中用來表明行動的核心意圖。",
                                    "sentences": [
                                        {
                                            "sentence": "The <target>object</target> <pattern>of</pattern> this community project is to provide free medical care for the elderly.",
                                            "translation": "這個社區計畫的目的是為長者提供免費的醫療照顧。",
                                        }
                                    ],
                                },
                            ],
                        },
                        {
                            "sense": "反對；提出異議（動詞字義）",
                            "entries": [
                                {
                                    "pattern": "object to sth./doing sth.",
                                    "pos": "phrase",
                                    "translation": "反對某事／反對做某事",
                                    "explanation": "這裡的 to 是介系詞，因此後面如果接動詞，必須使用動名詞 V-ing 或直接接名詞。",
                                    "sentences": [
                                        {
                                            "sentence": "Many local residents strongly <target>objected</target> <pattern>to</pattern> building a chemical plant near their neighborhood.",
                                            "translation": "許多當地居民強烈反對在他們社區附近建造化學工廠。",
                                        }
                                    ],
                                }
                            ],
                        },
                    ],
                    "conjugations": {
                        "past_tense": "objected",
                        "past_participle": "objected",
                    },
                    "relatives": {
                        "morphology": "字根 ject (投擲、射) 與字首 ob- (反對、朝向)",
                        "related": [
                            {
                                "word": "objection",
                                "pos": "noun",
                                "translation": "反對；異議",
                                "explanation": "由動詞 object 加上名詞字尾 -tion 延伸而來。",
                            },
                            {
                                "word": "objective",
                                "pos": "adjective",
                                "translation": "客觀的",
                                "explanation": "高頻形容詞，字面指像對待客觀物體一樣不夾帶個人情感。",
                            },
                            {
                                "word": "reject",
                                "pos": "verb",
                                "translation": "拒絕；排斥",
                                "explanation": "字根組合：re- (向後) + ject (投擲)，意為往回扔、不要。",
                            },
                        ],
                    },
                    "synonyms": [
                        {"word": "oppose", "pos": "verb", "translation": "反對；對抗"},
                        {"word": "item", "pos": "noun", "translation": "物件；項目"},
                    ],
                    "antonyms": [
                        {"word": "approve", "pos": "verb", "translation": "贊成；批准"},
                        {"word": "subjective", "pos": "adjective", "translation": "主觀的"},
                    ],
                }
            ),
        ),
        (
            "undergo v.",
            Flashcard.model_validate(
                {
                    "headword": "undergo",
                    "explanation": "「undergo」字面意為「在…下方走過」，引申為「經歷、遭受」。變形如同 go (go/went/gone)。在克漏字中，它常作為關鍵動詞出現，受詞幾乎全為特定的抽象破壞、變革、考驗或醫療手術名詞，屬於高度依賴後接名詞搭配的單字。",
                    "senses": [
                        {
                            "sense": "經歷；遭受（變革、檢查或苦難）",
                            "entries": [
                                {
                                    "pattern": "undergo a change / transformation",
                                    "pos": "phrase",
                                    "translation": "經歷轉變／變革",
                                    "explanation": "動詞加名詞搭配。主詞常為國家、社會、城市或系統，用來描述巨大的演變歷程。",
                                    "sentences": [
                                        {
                                            "sentence": "Over the past decade, the traditional farming village has <target>undergone</target> a complete <pattern>transformation</pattern> into a tech hub.",
                                            "translation": "在過去十年中，這個傳統的農村已經完全轉變（經歷了完全的變革）為一個科技中心。",
                                        }
                                    ],
                                },
                                {
                                    "pattern": "undergo surgery / treatment",
                                    "pos": "phrase",
                                    "translation": "接受手術／治療",
                                    "explanation": "醫療情境的特定搭配。注意在英文中不論是動手術還是接受療程，病人作為主詞時皆用 undergo 表達主動經歷，而非被動式。",
                                    "sentences": [
                                        {
                                            "sentence": "The star athlete had to <target>undergo</target> emergency <pattern>surgery</pattern> after tearing his ligament during the match.",
                                            "translation": "那名明星運動員在比賽中撕裂韌帶後，必須接受緊急手術。",
                                        }
                                    ],
                                },
                            ],
                        }
                    ],
                    "conjugations": {
                        "past_tense": "underwent",
                        "past_participle": "undergone",
                    },
                    "relatives": {
                        "morphology": "字首 under- (在…之下) 與核心動詞 go",
                        "related": [
                            {
                                "word": "undertake",
                                "pos": "verb",
                                "translation": "承擔；著手進行",
                                "explanation": "字面意為接下某物並放在自己肩膀之下負擔起來。",
                            },
                            {
                                "word": "underline",
                                "pos": "verb",
                                "translation": "劃線強調",
                                "explanation": "字面意為在文字下方畫線以示重要。",
                            },
                        ],
                    },
                    "synonyms": [
                        {"word": "experience", "pos": "verb", "translation": "經歷；體驗"},
                        {
                            "word": "endure",
                            "pos": "verb",
                            "translation": "忍受；熬過（偏向痛苦的經歷）",
                        },
                    ],
                    "antonyms": [
                        {"word": "avoid", "pos": "verb", "translation": "規避；躲過"}
                    ],
                }
            ),
        ),
    ]

    return examples