import os

### ARXIV ###

# Formato de URL para arXiv (se deben incluir todos los parámetros)
ARXIV_API_URL = ("http://export.arxiv.org/api/query?search_query={type_query}:{query}"
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

### Towards Data Science ###
TDS_URL = "https://towardsdatascience.com/?s={query}"

# Parámetros
QUERY_TOPIC_TDS = "RAG"
