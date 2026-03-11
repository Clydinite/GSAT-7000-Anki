# %%
# Setup

import json
import time
import os
import csv
import re
from typing import List, Literal, Optional
from google import genai
from google.api_core import exceptions
from pydantic import BaseModel
from dotenv import load_dotenv

class Example(BaseModel):
    sentence: str               # e.g., "He <accused> him *of* theft."
    translation: str            # Traditional Chinese translation
    explanation: Optional[str]  # Explanation of example sentence.

class WordResult(BaseModel):
    headword: str               # e.g. accuse
    explanation: str            # Usage/Grammar note in Traditional Chinese
    entries: List[Example]      # One word can have multiple POS entries
    related_forms: List[str]    # e.g., "accused" (verb conjugations, noun forms, etc., no change of meaning, just different forms of the same word)
    
class BatchWordResult(BaseModel):
    results: List[WordResult]
    
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable.")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# %%
# Testing

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="Explain how AI works in a few words"
)
print(response.text)

# %%
example_response = {
  "headword": "account",
  "explanation": "常考用法包括：(1) 名詞「帳戶」bank account；(2) 名詞「描述」eyewitness account；(3) 片語「將...考慮進去」take into account (固定用 into)；(4) 動詞片語「解釋/佔比例」account for。注意介係詞搭配。",
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

result = WordResult.model_validate(example_response)
result


# %%
def generate_data(batch_words: list[str]) -> BatchWordResult:
    prompt = f"""
    Act as a Taiwan GSAT English teacher.
    
    For each word, provide entries for ALL its common Parts of Speech (POS).
    
    Rules:

    - headword: The base form of the word.
    - explanation: High-value GSAT usage note (including common mistakes) in Traditional Chinese.
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
    
    Here's an example: {example_response}
    
    Here are the words: {batch_words}
    """
    
    # Using the latest 2026 SDK 'generate' method
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": BatchWordResult,
            "temperature": 0.3, # Low temperature for more deterministic output
        }
    )
    
    return response.parsed

# %%
# Loading word list

origin = "data/vocabulary"

# start from level 3
level = 3
word_list = []

with open(f"{origin}/level{level}.txt", "r", encoding="utf-8") as f:
    word_list = [line.strip() for line in f.readlines()]

print(f"Loaded {len(word_list)} words from level {level}.")
print(word_list[:5])

# %%
# # Test run with first 5 words

# words = word_list[:5]
# batch_results = generate_data(words)
# print(batch_results)

# %%
words = word_list

existing_words = set()
if os.path.exists("raw_gsat_data.tsv"):
    with open("raw_gsat_data.tsv", "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader, None)  # Skip header
        for row in reader:
            if row: existing_words.add(row[1]) # the raw_string is in the second column

# filter out words already processed
words_to_process = [w for w in words if w not in existing_words]

print(existing_words)
print(words_to_process[:5])
print(f"Resuming: {len(existing_words)} already done. {len(words_to_process)} remaining.")

# %%
def is_quota_error(e):
    err_str = str(e).lower()
    return "429" in err_str or "resource_exhausted" in err_str

# %%
# Processing loop

words = word_list

existing_words = set()
if os.path.exists("raw_gsat_data.tsv"):
    with open("raw_gsat_data.tsv", "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader, None)  # Skip header
        for row in reader:
            if row: existing_words.add(row[1]) # the raw_string is in the second column

# filter out words already processed
words_to_process = [w for w in words if w not in existing_words]

print(existing_words)
print(words_to_process[:5])
print(f"Resuming: {len(existing_words)} already done. {len(words_to_process)} remaining.")

with open("raw_gsat_data.tsv", "a", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    
    if os.path.getsize("raw_gsat_data.tsv") == 0:
        writer.writerow(["headword", "raw_string", "response"])

    chunk_size = 10
    total_chunks = (len(words_to_process) + chunk_size - 1) // chunk_size
    
    for start_idx in range(0, len(words_to_process), chunk_size):
        chunk = words_to_process[start_idx : start_idx + chunk_size]
        print(f"Processing chunk {start_idx//chunk_size + 1} of {total_chunks}...")
        
        success = False
        
        # retry if quota error occurs, but break on permanent error
        while not success:
            try:
                batch_results = generate_data(chunk)
                results = batch_results.results
                
                for idx, r in enumerate(results):
                    writer.writerow([
                        r.headword,
                        chunk[idx],
                        r.model_dump_json()
                    ])
                
                f.flush()
                success = True # This breaks the 'while not success' loop
                
                # Optional small breath to keep the API happy
                time.sleep(5)
                
            except Exception as e:
                err_msg = str(e)
                if is_quota_error(err_msg):
                    retry_match = re.search(r"'retryDelay':\s*'(\d+)s'", err_msg)
                
                    if retry_match:
                        delay = int(retry_match.group(1)) + 2 # Adding safety buffer
                        print(f"    Quota hit. Waiting {delay}s per API request...")
                        time.sleep(delay)
                    else:
                        print("    Quota hit. No delay found, waiting 30s...")
                        time.sleep(30)
                else:
                    # 'success' remains False, so the 'while' loop tries the same chunk again
                    print(f"    Permanent error at {chunk}: {e}")
                    print("    Waiting 10s before retrying current chunk...")
                    time.sleep(10)
                    
                    # break out of the "while" loop on permanent error (to avoid infinite loop)
                    break


