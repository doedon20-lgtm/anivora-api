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
            "http://127.0.0.1:11434"
        ).rstrip("/")

        self.model = os.getenv(
            "ANIVORA_AI_MODEL",
            "llama3.2"
        )

        self.timeout = int(
            os.getenv(
                "ANIVORA_AI_TIMEOUT",
                "120"
            )
        )

    def generate(self, prompt):
        if not prompt or not prompt.strip():
            raise AIEngineError(
                "Prompt cannot be empty."
            )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
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
                    "AI server returned an error."
                )
            except json.JSONDecodeError:
                message = raw or "AI server returned an error."

            raise AIEngineError(message)

        except urllib.error.URLError as error:
            raise AIEngineError(
                "Could not connect to the AI engine. "
                f"Make sure the AI server is running at {self.base_url}."
            ) from error

        except TimeoutError:
            raise AIEngineError(
                "The AI request timed out."
            )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as error:
            raise AIEngineError(
                "AI engine returned malformed JSON."
            ) from error

        result = data.get("response")

        if not isinstance(result, str):
            raise AIEngineError(
                "AI engine returned no valid response."
            )

        result = result.strip()

        if not result:
            raise AIEngineError(
                "AI engine returned an empty response."
            )

        return result


_engine = AIEngine()


def generate_text(prompt):
    return _engine.generate(prompt)
