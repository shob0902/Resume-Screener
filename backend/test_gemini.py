import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("gemini api key"))

# List all available models
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(model.name)
