import os
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    print("GEMINI_API_KEY found.")
    print("Key length:", len(api_key))
else:
    print("GEMINI_API_KEY NOT found.")