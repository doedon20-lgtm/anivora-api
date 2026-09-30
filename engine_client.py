import os
import httpx


class AniVoraEngineClient:

    def __init__(self):
        self.engine_url = os.getenv(
            "ANIVORA_ENGINE_URL",
            ""
        ).rstrip("/")

    async def health(self):
        if not self.engine_url:
            raise RuntimeError(
                "ANIVORA_ENGINE_URL is not configured"
            )

        async with httpx.AsyncClient(
            timeout=30
        ) as client:

            response = await client.get(
                f"{self.engine_url}/health"
            )

        response.raise_for_status()

        return response.json()

    async def generate(
        self,
        prompt,
        max_new_tokens=128,
        temperature=0.7
    ):
        if not self.engine_url:
            raise RuntimeError(
                "ANIVORA_ENGINE_URL is not configured"
            )

        async with httpx.AsyncClient(
            timeout=300
        ) as client:

            response = await client.post(
                f"{self.engine_url}/generate",
                json={
                    "prompt": prompt,
                    "max_new_tokens": max_new_tokens,
                    "temperature": temperature
                }
            )

        response.raise_for_status()

        return response.json()


def get_engine_client():
    return AniVoraEngineClient()
