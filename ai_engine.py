
import json
import os
import urllib.error
import urllib.request


class AIEngineError(Exception):
    pass


class AIEngine:
    def __init__(self):
        self.base_url = os.getenv(
            "ANIVORA_AI_URL",
            "https://andy-lat-magazines-deposits.trycloudflare.com"
        ).rstrip("/")

        self.model = os.getenv(
            "ANIVORA_AI_MODEL",
            "/data/data/com.termux/files/home/models/qwen/qwen2.5-0.5b-instruct-q4_k_m.gguf"
        )

        self.timeout = int(
            os.getenv("ANIVORA_AI_TIMEOUT", "120")
        )

    def generate(self, prompt):
        if not isinstance(prompt, str) or not prompt.strip():
            raise AIEngineError("Prompt cannot be empty.")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are AniVora AI, a helpful assistant. "
                        "Follow the user's instructions carefully."
                    )
                },
                {
                    "role": "user",
                    "content": prompt.strip()
                }
            ],
            "max_tokens": 512,
            "temperature": 0.7,
            "stream": False
        }

        request = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout
            ) as response:
                raw = response.read().decode(
                    "utf-8",
                    errors="replace"
                )

        except urllib.error.HTTPError as error:
            raw = error.read().decode(
                "utf-8",
                errors="replace"
            )

            try:
                data = json.loads(raw)
                message = data.get(
                    "error",
                    "Qwen returned an HTTP error."
                )

                if isinstance(message, dict):
                    message = message.get(
                        "message",
                        "Qwen returned an HTTP error."
                    )
            except json.JSONDecodeError:
                message = raw or "Qwen returned an HTTP error."

            raise AIEngineError(
                f"Qwen HTTP {error.code}: {message}"
            ) from error

        except (urllib.error.URLError, TimeoutError) as error:
            raise AIEngineError(
                "Could not connect to Qwen at "
                f"{self.base_url}. Check that llama-server and "
                "the Cloudflare tunnel are running and that "
                "ANIVORA_AI_URL is correct."
            ) from error

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as error:
            raise AIEngineError(
                "Qwen returned malformed JSON."
            ) from error

        choices = data.get("choices")
        result = None

        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            if isinstance(message, dict):
                result = message.get("content")

        if not isinstance(result, str) or not result.strip():
            raise AIEngineError(
                "Qwen returned no valid generated text."
            )

        return result.strip()


_engine = AIEngine()


def generate_text(prompt):
    return _engine.generate(prompt)
