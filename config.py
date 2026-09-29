import os


def get_env(name, default=None):
    value = os.getenv(name)

    if value is None:
        return default

    value = value.strip()

    return value if value else default


# -------------------------------------------------
# Server
# -------------------------------------------------

HOST = get_env(
    "ANIVORA_HOST",
    "0.0.0.0"
)

PORT = int(
    get_env(
        "ANIVORA_PORT",
        "8000"
    )
)


# -------------------------------------------------
# AI Engine
# -------------------------------------------------

AI_URL = get_env(
    "ANIVORA_AI_URL",
    "http://127.0.0.1:11434"
)

AI_MODEL = get_env(
    "ANIVORA_AI_MODEL",
    "llama3.2"
)

AI_TIMEOUT = int(
    get_env(
        "ANIVORA_AI_TIMEOUT",
        "120"
    )
)


# -------------------------------------------------
# Database
# -------------------------------------------------

DATABASE_PATH = get_env(
    "ANIVORA_DATABASE",
    "anivora.db"
)


# -------------------------------------------------
# API
# -------------------------------------------------

API_VERSION = "v1"

SERVICE_NAME = "AniVora API"


def show_config():
    print("")
    print("AniVora configuration")
    print("----------------------")
    print(f"Host: {HOST}")
    print(f"Port: {PORT}")
    print(f"AI URL: {AI_URL}")
    print(f"AI Model: {AI_MODEL}")
    print(f"Database: {DATABASE_PATH}")
    print(f"API Version: {API_VERSION}")
    print("")
