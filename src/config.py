# config.py
from dotenv import load_dotenv
import os

load_dotenv("../.env")
# Configuración para el LLM (modifica según tu entorno)
LLM_BASE_URL = "http://localhost:1234"
LLM_API_KEY = "lm-studio"
LLM_MODEL = "deepseek-r1-distill-qwen-14b"

LLM_BASE_URL_OPENAI = "https://api.openai.com"
LLM_API_KEY_OPENAI = os.getenv("OPENAI_API_KEY")
LLM_MODEL_OPENAI = "gpt-4o"