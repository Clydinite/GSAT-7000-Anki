import json
import time
import os
import csv
from google import genai
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
genai.api_key = os.getenv("GENAI_API_KEY")
