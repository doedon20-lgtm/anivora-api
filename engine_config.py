import os


class EngineConfig:
    MODEL_NAME = os.getenv(
        "ANIVORA_MODEL",
        "Qwen/Qwen3-0.6B"
    )

    HOST = os.getenv(
        "ANIVORA_ENGINE_HOST",
        "0.0.0.0"
    )

    PORT = int(
        os.getenv(
            "ANIVORA_ENGINE_PORT",
            "8000"
        )
    )

    MAX_NEW_TOKENS = int(
        os.getenv(
            "ANIVORA_MAX_NEW_TOKENS",
            "128"
        )
    )

    TEMPERATURE = float(
        os.getenv(
            "ANIVORA_TEMPERATURE",
            "0.7"
        )
    )

    DEVICE = os.getenv(
        "ANIVORA_DEVICE",
        "auto"
  )
