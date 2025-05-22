"""
Configuration settings for the application
"""

# API URLs
ARXIV_API_URL = "https://export.arxiv.org/api/query"
TDS_URL = "https://towardsdatascience.com"
GITHUB_API_URL = "https://api.github.com"

# Default settings
MAX_RESULTS = 10
TIMEOUT = 10  # seconds

# Error messages
ERROR_MSG_TIMEOUT = "Request timed out"
ERROR_MSG_CONNECTION = "Connection error"
ERROR_MSG_SERVER = "Server error"
ERROR_MSG_NOT_FOUND = "Resource not found"

# WebSocket settings
WS_URL = "ws://localhost:8100/ws/search"
WS_PING_INTERVAL = 30  # seconds
WS_MAX_RETRIES = 3

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

LLM_BASE_URL = "http://localhost:1234/v1"
LLM_API_KEY = "lm-studio"
LLM_MODEL = "deepseek-r1-distill-qwen-14b"
