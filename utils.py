import csv
import json
import os
from typing import List, Optional, Literal
from pydantic import BaseModel

# --- State Management ---
VerificationState = Literal["none", "ai_pass", "ai_fail", "human"]

class Example(BaseModel):
    sentence: str               # e.g., "He <target>accused</target> him <pattern>of</pattern> theft."
    translation: str            # Traditional Chinese translation
    explanation: Optional[str]  # Explanation of example sentence.

class WordResult(BaseModel):
    headword: str               # e.g. accuse
    explanation: str            # Usage/Grammar note in Traditional Chinese
    entries: List[Example]      # One word can have multiple POS entries
    related_forms: List[str]    # e.g., "accused" (verb conjugations, noun forms, etc., no change of meaning, just different forms of the same word)
    
class BatchWordResult(BaseModel):
    results: List[WordResult]

class VerificationResult(BaseModel):
    status: Literal["pass", "fail"]
    comment: str  # Natural language description of the problem

class BatchVerificationResult(BaseModel):
    results: List[VerificationResult]

def get_random_human_examples(count: int = 10) -> List[dict]:
    """Fetches random human-verified examples to use as a few-shot seed."""
    examples: List[dict] = []
    all_human_rows: List[dict] = []
    for level in range(1, 7):
        file_path: str = f"data/raw/level{level}.tsv"
        if not os.path.exists(file_path): continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                human_rows: List[dict] = [row for row in reader if row.get("verification") == "human"]
                all_human_rows.extend(human_rows)
        except: continue
    if not all_human_rows: return []
    import random
    selected: List[dict] = random.sample(all_human_rows, min(len(all_human_rows), count))
    for row in selected:
        try:
            examples.append({"headword": row["headword"], "response": json.loads(row["response"])})
        except: continue
    return examples

def append_to_raw_tsv(level: int, words: List[str], batch_results: BatchWordResult, verification: VerificationState = "none", comment: str = "", attempts: int = 0) -> None:
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

EXAMPLE_RESPONSE = {
  "headword": "account",
  "explanation": "用法包括：(1) 名詞「帳戶」bank account；(2) 名詞「描述」eyewitness account；(3) 片語「將...考慮進去」take into account (固定用 into)；(4) 動詞片語「解釋/佔比例」account for。注意介係詞搭配。",
  "entries": [
    {
      "sentence": "The survivor provided a detailed <target>account</target> <pattern>of</pattern> the accident, helping the police understand what had happened on the highway.",
      "translation": "倖存者提供了關於事故的詳細描述，幫助警方了解高速公路上發生了什麼事。",
      "explanation": "名詞「敘述/描述」。片語 account of sth 常搭配 detailed, full, firsthand 等形容詞。"
    },
    {
      "sentence": "When planning the graduation trip, the committee <pattern>took</pattern> the students' safety <pattern>into</pattern> <target>account</target> to avoid any potential accidents.",
      "translation": "在規劃畢業旅行時，委員會將學生的安全考慮進去，以避免任何潛在的事故。",
      "explanation": "片語 take into account = consider。介係詞必須用 into，不可用 for/to。易錯：take account of (較少)。常在克漏字測驗考介係詞。"
    },
    {
      "sentence": "Heavy rain and thick fog <target>account</target> <pattern>for</pattern> the delay of more than twenty international flights at the airport this morning.",
      "translation": "大雨和濃霧解釋了今天早上機場二十多個國際航班延誤的原因。",
      "explanation": "動詞片語 account for = explain / constitute。可表「解釋原因」或「佔比例」。介係詞固定用 for。GSAT常出題：What accounts for...? (什麼原因導致...？)。"
    },
    {
      "sentence": "She opened a <pattern>savings</pattern> <target>account</target> at the bank to manage her scholarship money and prepare for unexpected expenses during her studies.",
      "translation": "她在銀行開了一個儲蓄帳戶，用來管理獎學金並為學習期間的意外開支做準備。",
      "explanation": "名詞「銀行帳戶」。常用搭配：open/close an account；bank account；current/checking/savings account。近義詞：financial account。"
    },
    {
      "sentence": "The environmental group <target>accounts</target> <pattern>for</pattern> nearly 40% of all volunteer activities in the community this year.",
      "translation": "環保團體佔了今年社區所有志願活動的近40%。",
      "explanation": "account for 表「佔比例/數量」。注意第三人稱單數 accounts。克漏字常見變化：What do these factors account for? (這些因素占了多少比例？)。"
    }
  ],
  "related_forms": ["accounts", "accountable"]
}

SYSTEM_PROMPT = """
Act as a Taiwan GSAT English teacher, providing Anki flashcard content for the given words. Follow the instructions and format strictly.

Rules:
- For each word, provide entries for ALL its common parts of speech as included in the parentheses. More could be provided.
- i+1 principle: Use clear context so the target word's meaning is obvious. It should be that the target word is guessable from the context. Additionally, the example sentences should be at a slightly lower difficulty level than the target word to ensure comprehensibility for GSAT students. For instance, if the target word is a Level 4 word, the example sentences should primarily use Level 2 and Level 3 words, with minimal use of Level 4 words. The example sentence should not contain any words that are significantly more difficult than the target word.
- Dynamic Sentence Scaling: The number of example sentences must reflect the word's complexity.
    - For simple or technical words with only one primary meaning (e.g., "aspirin," "photosynthesis"), provide 3–4 high-quality sentences.
    - For polysemous words (words with multiple meanings, e.g., "strike," "account," "leave"), you must provide 4–6 sentences to ensure every distinct GSAT-relevant definition and major collocation is covered.
    - Goal: The more versatile the word, the more sentences you must provide. Do not use a fixed number for every word; prioritize coverage of meaning over a standard count. The number of sentences should be an accurate reflection of the word's complexity and polysemy, not an arbitrary quota.

Fields:
- headword: The base form of the word. The headword field should not include any POS tags or parentheses, just the base form of the word. (e.g "achieve", not "achieve (n.)", "achieve (v.)", or "achieve(ment) (n./v.)" etc.)
- explanation: High-value GSAT usage note in Traditional Chinese. Common mistakes should be explained. There's no need to mention "GSAT" or other filler words in the explanation.
- entries: List of example sentences with:
   - sentence:
        - Length: 15-35 words.
        - Context: Use academic, social, or school-life themes common in GSAT.
        - Marking:
             - Use <target>...</target> for the headword
                 - The entire conjugated or inflected form of the headword must be inside <target>...</target>. (e.g. <target>accused</target> for "accuse", not <target>accuse</target>d; <target>achievement</target> for "achieve", not <target>achieve</target>ment.)
                 - Never use <target>...</target> for multiple words, only the conjugated or inflected form of the headword.
             - Use <pattern>...</pattern> for the key collocations of the headword. Never use <pattern>...</pattern> for the headword itself, or other parts of the sentence. (e.g. "When planning the graduation trip, the committee <pattern>took</pattern> the students' safety <pattern>into</pattern> <target>account</target> to avoid any potential accidents." In this sentence, "safety", "accident", etc., should NOT be marked as it's not a collocation of the headword "account". Only "take" and "into" should be marked as collocations of "account". Another example: "Students should <pattern>take</pattern> <target>advantage</target> <pattern>of</pattern> the school's career counseling services to explore their future options.") Additionally, it's also reasonable to mark anything other than prepositions if it's a frequent collocation of the headword (e.g. "Many companies <pattern>place</pattern> <target>advertisements</target> <pattern>in</pattern> newspapers and magazines to inform potential customers about their latest products and services.") It's possible for the collocation to not be adjacent to the headword, provided that it's indeed a collocation.
   - translation: Traditional Chinese translation of the sentence.
   - explanation: Usage note for this specific example. Should not contain any Markdown tags like `* ... *` or `** ... **` or any XML tags (`<pattern> ... </pattern>` and `<target> ... </target>`)
- related_forms: List[str] of relevant word family members, like verb conjugations or the noun form. The meaning should remain the same. (e.g. "market" and "marketing" are not related forms because they have different meanings, but "count" and "countable" are related forms because they are just different forms of the same word.)
"""
