# config.py
import os

# Formato de URL para arXiv (se deben incluir todos los parámetros)
ARXIV_API_URL = ('http://export.arxiv.org/api/query?search_query={type_query}:{query}'
                 "&start={start}&max_results={max_results}"
                 "&sortBy={sortby}&sortOrder={sortorder}")

# Parámetros por defecto para la consulta
QUERY_TOPIC = "RAG"
TYPE_QUERY = "all"
START = 0
MAX_RES = 10
#SORTBY = "submittedDate"
SORTBY = "relevance"
SORTORDER = "descending"

# Configuración para GitHub
GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Configuración para el LLM (modifica según tu entorno)
LLM_BASE_URL = "http://localhost:1234/v1"
LLM_API_KEY = "lm-studio"
LLM_MODEL = "deepseek-r1-distill-qwen-14b"
