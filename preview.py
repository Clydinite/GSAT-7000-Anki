from utils import Flashcard
from to_anki import generate_html
from templates.preview_utils import generate_preview_html
import os

sample_card = Flashcard.model_validate(
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
                            },
                            {
                                "sentence": "The museum display features a collection of everyday <target>objects</target> from the ancient Roman era.",
                                "translation": "博物館的展覽展示了一系列來自古羅馬時期的日常物品。",
                            },
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
)

with open("templates/card.css", "r", encoding="utf-8") as f:
    css = f.read()

with open("templates/back.html", "r", encoding="utf-8") as f:
    back_html = f.read()

# Replace Anki mustache placeholders for preview
# Note: The back_html uses {{Front}} and {{Back}}. 
# For preview we should inject the card HTML into the 'Back' part
card_html = generate_html(sample_card)
final_back_html = back_html.replace("{{Back}}", card_html).replace("{{Front}}", sample_card.headword)

# Directly use final_back_html as it already contains the full card structure
html_content = generate_preview_html(css, final_back_html)

with open("templates/preview.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Preview generated: open templates/preview.html in your browser.")
