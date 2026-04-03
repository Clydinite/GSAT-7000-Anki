import csv
import json
import os
from typing import List, Optional
from pydantic import BaseModel

class Example(BaseModel):
    sentence: str               # e.g., "He <accused> him *of* theft."
    translation: str            # Traditional Chinese Chinese translation
    explanation: Optional[str]  # Explanation of example sentence.

class WordResult(BaseModel):
    headword: str               # e.g. accuse
    explanation: str            # Usage/Grammar note in Traditional Chinese
    entries: List[Example]      # One word can have multiple POS entries
    related_forms: List[str]    # e.g., "accused" (verb conjugations, noun forms, etc., no change of meaning, just different forms of the same word)
    
class BatchWordResult(BaseModel):
    results: List[WordResult]

def append_to_raw_tsv(level: int, words: List[str], batch_results: BatchWordResult):
    """Appends results to the level-specific raw TSV file."""
    output_file = f"data/raw/level{level}.tsv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    file_exists = os.path.exists(output_file) and os.path.getsize(output_file) > 0
    
    with open(output_file, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        
        if not file_exists:
            writer.writerow(["headword", "raw_string", "response"])

        for idx, r in enumerate(batch_results.results):
            # Map the original word (raw_string) to the response
            raw_string = words[idx] if idx < len(words) else r.headword
            writer.writerow([
                r.headword,
                raw_string,
                r.model_dump_json()
            ])
        f.flush()
    print(f"Appended {len(batch_results.results)} words to {output_file}.")

EXAMPLE_RESPONSE = {
  "headword": "account",
  "explanation": "用法包括：(1) 名詞「帳戶」bank account；(2) 名詞「描述」eyewitness account；(3) 片語「將...考慮進去」take into account (固定用 into)；(4) 動詞片語「解釋/佔比例」account for。注意介係詞搭配。",
  "entries": [
    {
      "sentence": "The survivor provided a detailed <account> *of* the accident, helping the police understand what had happened on the highway.",
      "translation": "倖存者提供了關於事故的詳細描述，幫助警方了解高速公路上發生了什麼事。",
      "explanation": "名詞「敘述/描述」。片語 account of sth 常搭配 detailed, full, firsthand 等形容詞。"
    },
    {
      "sentence": "When planning the graduation trip, the committee *took* the students' safety *into* <account> to avoid any potential accidents.",
      "translation": "在規劃畢業旅行時，委員會將學生的安全考慮進去，以避免任何潛在的事故。",
      "explanation": "片語 take into account = consider。介係詞必須用 into，不可用 for/to。易錯：take account of (較少)。常在克漏字測驗考介係詞。"
    },
    {
      "sentence": "Heavy rain and thick fog <account> *for* the delay of more than twenty international flights at the airport this morning.",
      "translation": "大雨和濃霧解釋了今天早上機場二十多個國際航班延誤的原因。",
      "explanation": "動詞片語 account for = explain / constitute。可表「解釋原因」或「佔比例」。介係詞固定用 for。GSAT常出題：What accounts for...? (什麼原因導致...？)。"
    },
    {
      "sentence": "She opened a savings <account> at the bank to manage her scholarship money and prepare for unexpected expenses during her studies.",
      "translation": "她在銀行開了一個儲蓄帳戶，用來管理獎學金並為學習期間的意外開支做準備。",
      "explanation": "名詞「銀行帳戶」。常用搭配：open/close an account；bank account；current/checking/savings account。近義詞：financial account。"
    },
    {
      "sentence": "The environmental group <accounts> *for* nearly 40% of all volunteer activities in the community this year.",
      "translation": "環保團體佔了今年社區所有志願活動的近40%。",
      "explanation": "account for 表「佔比例/數量」。注意第三人稱單數 accounts。克漏字常見變化：What do these factors account for? (這些因素占了多少比例？)。"
    }
  ],
  "related_forms": ["accounts", "accountable"]
}

SYSTEM_PROMPT = """
Act as a Taiwan GSAT English teacher.

For each word, provide entries for ALL its common Parts of Speech (POS).

Rules:
- headword: The base form of the word.
- explanation: High-value GSAT usage note (including common mistakes) in Traditional Chinese. There's no need to mention "GSAT" or other filler words in the explanation.
- entries: List of example sentences with:
   - sentence:
        - Length: 15-25 words. 
        - Context: Use academic, social, or school-life themes common in GSAT.
        - Marking: 
             - Use <> for the headword
                 - The entire conjugated or inflected form of the headword must be inside <>. (e.g. <accused> for "accuse", not <accuse>d; <achievement> for "achieve", not <achieve>ment.)
                 - Never use <> for multiple words, only the conjugated or inflected form of the headword.
             - Use * * for the key collocations worth testing in a cloze test.
   - translation: Traditional Chinese.
   - explanation: Usage note for this specific example.
- related_forms: List[str] of relevant word family members, like verb conjugations or the noun form. The meaning should remain the same. (e.g. "market" and "marketing" are not related forms because they have different meanings, but "count" and "countable" are related forms because they are just different forms of the same word.)
- i+1 principle: Use clear context so the target word's meaning is obvious.
- each entry should have at least two example sentences, covering different meanings or usages of the word.

Here's an example: {example_json}
"""
