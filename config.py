import os


def env(name, default):
    value = os.getenv(name)
    return value.strip() if value and value.strip() else default


HOST = env("ANIVORA_HOST", "0.0.0.0")
PORT = int(env("ANIVORA_PORT", "8000"))

AI_URL = env(
    "ANIVORA_AI_URL",
    "http://127.0.0.1:11434"
)

AI_MODEL = env(
    "ANIVORA_AI_MODEL",
    "llama3.2"
)

AI_TIMEOUT = int(
    env("ANIVORA_AI_TIMEOUT", "120")
)

DATABASE_PATH = env(
    "ANIVORA_DATABASE",
    "anivora.db"
)

API_VERSION = "v1"
SERVICE_NAME = "AniVora API"
