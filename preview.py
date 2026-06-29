from utils import Flashcard
from to_anki import generate_html
from templates.preview_utils import generate_preview_html
import os

sample_card = Flashcard.model_validate(
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
        {
          "word": "item",
          "pos": "noun",
          "translation": "物件；項目",
          "explanation": "指個別的物品實體"
        },
        {
          "word": "article",
          "pos": "noun",
          "translation": "物品；一件商品",
          "explanation": "常用於特定類別的物品"
        }
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
        {
          "word": "purpose",
          "pos": "noun",
          "translation": "目的；意圖",
          "explanation": "指做某事的初衷或意圖"
        },
        {
          "word": "aim",
          "pos": "noun",
          "translation": "目標；宗旨",
          "explanation": "指努力想要達到的終點"
        },
        {
          "word": "goal",
          "pos": "noun",
          "translation": "目標",
          "explanation": "指長期的理想或目的地"
        }
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
              "translation": "儘管市長聲稱加稅是必要的，但憤怒的市民提出異議認為，這將會不公平地傷害那些已經在苦苦掙扎的貧困家庭。"
            }
          ]
        }
      ],
      "synonyms": [
        {
          "word": "oppose",
          "pos": "verb",
          "translation": "反對；對抗",
          "explanation": "及物動詞，直接接名詞受詞，不加 to"
        },
        {
          "word": "protest",
          "pos": "verb",
          "translation": "抗議；反對",
          "explanation": "強調公開表達不滿與抗議"
        }
      ],
      "antonyms": [
        {
          "word": "approve",
          "pos": "verb",
          "translation": "贊成；批准",
          "explanation": "指官方或口頭上的認可"
        },
        {
          "word": "consent",
          "pos": "verb",
          "translation": "同意；答應",
          "explanation": "常搭配介系詞 consent to"
        }
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
        "word": "objective",
        "pos": "noun",
        "translation": "目標；目的",
        "explanation": "等同於名詞 object 的抽象意圖語意。"
      },
      {
        "word": "reject",
        "pos": "verb",
        "translation": "拒絕；排斥",
        "explanation": "字根組合：re- (向後) + ject (投擲)，意為往回扔、不要。"
      },
      {
        "word": "project",
        "pos": "verb",
        "translation": "投射；預測",
        "explanation": "字根組合：pro- (向前) + ject (投擲)，意為往前扔出光線或想法。"
      }
    ]
  }
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
