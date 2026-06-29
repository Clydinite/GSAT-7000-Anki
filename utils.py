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
                    "explanation": "「predict」在學測中是探討未來趨勢、氣候變遷以及科技發展時必備的核心動詞。理解這個字時，要注意其後方常連接抽象名詞或完整的名詞子句（that 子句）作為預測之具體內容。",
                    "senses": [
                        {
                            "sense": "預測；預言（根據已知跡象或數據推測未來）",
                            "entries": [
                                {
                                    "pattern": "predict sth.",
                                    "pos": "verb",
                                    "translation": "預測某事",
                                    "explanation": "及物動詞直接接受詞，受詞通常是天災、科學結果或未來動態。",
                                    "sentences": [
                                        {
                                            "sentence": "By analyzing historical weather records, meteorologists can <target>predict</target> upcoming droughts months before they actually happen.",
                                            "translation": "藉由分析歷史氣象紀錄，氣象學家能在乾旱實際發生前幾個月就預測其到來。"
                                        },
                                        {
                                            "sentence": "The psychic claimed she could <target>predict</target> the future, but none of her fortunes about the lottery numbers ever came true.",
                                            "translation": "那名巫婆聲稱自己能夠預言未來，但她關於樂透號碼的占卜卻從未實現過。"
                                        }
                                    ]
                                },
                                {
                                    "pattern": "predict that...",
                                    "pos": "phrase",
                                    "translation": "預測…（後接子句）",
                                    "explanation": "動詞後接名詞子句，用來交代一整串複雜的趨勢演變，在寫作論述中極為高頻。",
                                    "sentences": [
                                        {
                                            "sentence": "Based on current economic data, experts <target>predict</target> <pattern>that</pattern> global oil prices will rise rapidly during the next quarter.",
                                            "translation": "根據目前的經濟數據，專家預測全球油價在下一季度將會快速上漲。"
                                        },
                                        {
                                            "sentence": "Tech leaders <target>predict</target> <pattern>that</pattern> artificial intelligence will replace most repetitive desk jobs within the next decade.",
                                            "translation": "科技龍頭們預測，人工智慧將在未來十年內取代大部分重複性的辦公室工作。"
                                        }
                                    ]
                                }
                            ],
                            "synonyms": [
                                {"word": "foresee", "pos": "verb", "translation": "預見；預知", "explanation": "強調在事情發生前就在腦海中看見或察覺"},
                                {"word": "forecast", "pos": "verb", "translation": "預測", "explanation": "常用於天氣、經濟等基於數據的專業預測"}
                            ],
                            "antonyms": []
                        }
                    ],
                    "conjugations": {
                        "past_tense": "predicted",
                        "past_participle": "predicted"
                    },
                    "relatives": {
                        "morphology": "字首 pre- (預先) 與字根 dict (說、言語)",
                        "related": [
                            {
                                "word": "predictable",
                                "pos": "adjective",
                                "translation": "可預測的；墨守成規的",
                                "explanation": "由動詞 predict 加上形容詞字尾 -able 延伸而來。"
                            },
                            {
                                "word": "prediction",
                                "pos": "noun",
                                "translation": "預測；預言",
                                "explanation": "由動詞 predict 加上名詞字尾 -tion 延伸而來。"
                            },
                            {
                                "word": "contradict",
                                "pos": "verb",
                                "translation": "反駁；與…矛盾",
                                "explanation": "字首 contra- (相反) + 字根 dict (說)，字面意為說反話。"
                            }
                        ]
                    }
                }
            )
        ),
        (
            "object n./v.",
            Flashcard.model_validate(
                {
                    "headword": "object",
                    "explanation": "「object」在學測中為核心必考字彙。由於名詞與動詞的語意、用法截然不同，且名詞本身又包含具體的「物理實體」與抽象的「行動目標」，這三種語意在學生的直覺中很難串聯在一起，因此將它們拆分為三個獨立的語意區塊，以便於精準記憶與複習。",
                    "senses": [
                        {
                            "sense": "物體；物品（物理上可見或存在的實體）",
                            "entries": [
                                {
                                    "pattern": "object",
                                    "pos": "noun",
                                    "translation": "物體；實體",
                                    "explanation": "指肉眼可見或實體存在的單一物品。",
                                    "sentences": [
                                        {
                                            "sentence": "When the lights went out, I stumbled in the pitch-black room and my foot struck a heavy, metallic <target>object</target> left on the floor.",
                                            "translation": "當燈火熄滅時，我在漆黑的房間裡跌跌撞撞，腳踢到了遺留在地板上的一個沉重金屬物體。"
                                        },
                                        {
                                            "sentence": "Archaeologists digging in the desert found ancient everyday <target>objects</target> like clay pots and iron knives, revealing how people lived centuries ago.",
                                            "translation": "考古學家在沙漠中挖掘時，發現了陶罐和鐵刀等古老的日常物品，揭示了幾個世紀前人們的生活方式。"
                                        }
                                    ]
                                },
                                {
                                    "pattern": "a physical object",
                                    "pos": "phrase",
                                    "translation": "有形物體；物理實體",
                                    "explanation": "寫作時強調具體存在、佔有空間的實物，常與抽象概念做對比。",
                                    "sentences": [
                                        {
                                            "sentence": "Ghosts are just imaginary figures in scary stories; they do not have a solid, physical <target>object</target> that you can actually touch or hold.",
                                            "translation": "鬼魂只是恐怖故事中虛構的人物；它們並沒有一個你實際上可以觸摸或握住的堅固、有形物體。"
                                        }
                                    ]
                                }
                            ],
                            "synonyms": [
                                {"word": "item", "pos": "noun", "translation": "物件；項目", "explanation": "指個別的物品實體"},
                                {"word": "article", "pos": "noun", "translation": "物品；一件商品", "explanation": "常用於特定類別的物品"}
                            ],
                            "antonyms": []
                        },
                        {
                            "sense": "目標；目的（行動或企圖的核心意圖）",
                            "entries": [
                                {
                                    "pattern": "the object of sth.",
                                    "pos": "phrase",
                                    "translation": "…的目的、目標",
                                    "explanation": "等同於 purpose 或 aim。在寫作中用來明確表明某項行動的核心目的。",
                                    "sentences": [
                                        {
                                            "sentence": "The ultimate <target>object</target> <pattern>of</pattern> his grueling four-year medical training was finally realized when he opened his own clinic.",
                                            "translation": "當他開設自己的診所時，他那長達四年、令人筋疲力盡的醫學訓練的最終目的終於實現了。"
                                        },
                                        {
                                            "sentence": "With the sole <target>object</target> <pattern>of</pattern> saving the company from bankruptcy, the boss decided to cut budgets and lay off half of the staff.",
                                            "translation": "純粹為了（以…為唯一目標）挽救公司免於破產，老闆決定縮減預算並解雇一半的員工。"
                                        }
                                    ]
                                }
                            ],
                            "synonyms": [
                                {"word": "purpose", "pos": "noun", "translation": "目的；意圖", "explanation": "指做某事的初衷或意圖"},
                                {"word": "aim", "pos": "noun", "translation": "目標；宗旨", "explanation": "指努力想要達到的終點"},
                                {"word": "goal", "pos": "noun", "translation": "目標", "explanation": "指長期的理想或目的地"}
                            ],
                            "antonyms": []
                        },
                        {
                            "sense": "反對；提出異議（對某事表示不贊同或抗議）",
                            "entries": [
                                {
                                    "pattern": "object to sth./doing sth.",
                                    "pos": "phrase",
                                    "translation": "反對某事／反對做某事",
                                    "explanation": "這裡的 to 是介系詞，因此後面如果接動詞，必須使用動名詞 (V-ing) 或直接接名詞。此語意與用法為學測片語大熱門。",
                                    "sentences": [
                                        {
                                            "sentence": "Because they loved nature and hated pollution, many local residents strongly <target>objected</target> <pattern>to</pattern> building a chemical plant near their neighborhood.",
                                            "translation": "因為熱愛自然且痛恨污染，許多當地居民強烈反對在他們社區附近建造化學工廠。"
                                        },
                                        {
                                            "sentence": "I love working and want to finish this project tonight, so I certainly won't <target>object</target> <pattern>to</pattern> staying late at the office.",
                                            "translation": "我熱愛工作並希望今晚能完成這個專案，所以我當然不會反對在辦公室加班。"
                                        }
                                    ]
                                },
                                {
                                    "pattern": "object that...",
                                    "pos": "phrase",
                                    "translation": "反對說…；提出異議認為…",
                                    "explanation": "後接名詞子句（that 子句），用來具體敘述反對的理由或論點，多用於閱讀測驗中的論辯語境。",
                                    "sentences": [
                                        {
                                            "sentence": "While the mayor claimed the tax increase was necessary, angry citizens <target>objected</target> <pattern>that</pattern> it would unfairly hurt poor families who were already struggling.",
                                            "translation": "儘管市長聲聲句句稱加稅是必要的，但憤怒的市民提出異議認為，這將會不公平地傷害那些已經在苦苦掙扎的貧困家庭。"
                                        }
                                    ]
                                }
                            ],
                            "synonyms": [
                                {"word": "oppose", "pos": "verb", "translation": "反對；對抗", "explanation": "及物動詞，直接接名詞受詞，不加 to"},
                                {"word": "protest", "pos": "verb", "translation": "抗議；反對", "explanation": "強調公開表達不滿與抗議"}
                            ],
                            "antonyms": [
                                {"word": "approve", "pos": "verb", "translation": "贊成；批准", "explanation": "指官方或口頭上的認可"},
                                {"word": "consent", "pos": "verb", "translation": "同意；答應", "explanation": "常搭配介系詞 consent to"}
                            ]
                        }
                    ],
                    "conjugations": {
                        "past_tense": "objected",
                        "past_participle": "objected"
                    },
                    "relatives": {
                        "morphology": "字首 ob- (反對、朝向) 與字根 ject (投擲、射)",
                        "related": [
                            {
                                "word": "objection",
                                "pos": "noun",
                                "translation": "反對；異議",
                                "explanation": "由動詞 object 加上名詞字尾 -tion 延伸而來。"
                            },
                            {
                                "word": "objective",
                                "pos": "adjective",
                                "translation": "客觀的",
                                "explanation": "字面指像對待客觀物體一樣不夾帶個人情感，與主觀對立。"
                            },
                            {
                                "word": "reject",
                                "pos": "verb",
                                "translation": "拒絕；排斥",
                                "explanation": "字根組合：re- (向後) + ject (投擲)，意為往回扔、不要。"
                            }
                        ]
                    }
                }
            )
        ),
        (
            "undergo v.",
            Flashcard.model_validate(
                {
                    "headword": "undergo",
                    "explanation": "「undergo」在學測綜合測驗與文意選填中非常高頻。這個字高度依賴後方接續的名詞來決定中文翻譯（如轉變、手術、考驗等），學生必須學會辨識特定的核心名詞搭配來解題。",
                    "senses": [
                        {
                            "sense": "經歷；遭受（巨大的變革、重大的醫療或痛苦的試煉）",
                            "entries": [
                                {
                                    "pattern": "undergo a change / transformation",
                                    "pos": "phrase",
                                    "translation": "經歷轉變／變革",
                                    "explanation": "常用於描述社會、城市、產業系統的大幅演變與進化歷史。",
                                    "sentences": [
                                        {
                                            "sentence": "Over the past decade, the sleepy traditional farming village has <target>undergone</target> a complete <pattern>transformation</pattern> into a bustling high-tech valley.",
                                            "translation": "在過去十年中，這個原本寂靜的傳統農村已經完全轉變（經歷了完整的變革）為一個繁華的高科技山谷。"
                                        },
                                        {
                                            "sentence": "The education system is currently <target>undergoing</target> a massive <pattern>change</pattern> to incorporate more digital learning tools into high school classrooms.",
                                            "translation": "教育系統目前正經歷一場巨大的轉變，好將更多數位學習工具整合進高中的課堂中。"
                                        }
                                    ]
                                },
                                {
                                    "pattern": "undergo surgery / treatment",
                                    "pos": "phrase",
                                    "translation": "接受手術／治療",
                                    "explanation": "醫療情境的強搭配。注意英文中病患做主詞時用主動態的 undergo 表示「經歷」，而非被動態。",
                                    "sentences": [
                                        {
                                            "sentence": "The star athlete had to <target>undergo</target> emergency knee <pattern>surgery</pattern> after tearing his ligament, putting an end to his season.",
                                            "translation": "那名明星運動員在撕裂韌帶後不得不接受緊急膝蓋手術，這也為他的賽季畫下了句點。"
                                        },
                                        {
                                            "sentence": "Cancer patients often have to <target>undergo</target> painful chemical <pattern>treatments</pattern> to ensure all dangerous cells are destroyed.",
                                            "translation": "癌症患者通常必須接受痛苦的化學治療，以確保所有危險的細胞都被消滅。"
                                        }
                                    ]
                                }
                            ],
                            "synonyms": [
                                {"word": "experience", "pos": "verb", "translation": "經歷；體驗", "explanation": "泛指生命中所遭遇、體驗到的各類大小事件"},
                                {"word": "endure", "pos": "verb", "translation": "忍受；熬過", "explanation": "特別強調咬牙撐過痛苦、折磨或艱難的處境"}
                            ],
                            "antonyms": [
                                {"word": "avoid", "pos": "verb", "translation": "規避；躲過", "explanation": "指成功繞道而不去經歷某種狀況"}
                            ]
                        }
                    ],
                    "conjugations": {
                        "past_tense": "underwent",
                        "past_participle": "undergone"
                    },
                    "relatives": {
                        "morphology": "字首 under- (在…之下) 與核心動詞 go",
                        "related": [
                            {
                                "word": "undertake",
                                "pos": "verb",
                                "translation": "承擔；著手進行",
                                "explanation": "字面意為接下某項艱鉅的工作或專案，並挑在自己肩膀下負擔起來。"
                            },
                            {
                                "word": "underline",
                                "pos": "verb",
                                "translation": "劃線強調",
                                "explanation": "字面意為在重點文字下方畫上一條線以示關鍵。"
                            }
                        ]
                    }
                }
            )
        )
    ]

    return examples