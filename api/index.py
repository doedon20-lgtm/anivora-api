
import os
import hmac
import hashlib
import secrets

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="AniVora API", version="0.8.0")

API_SECRET = os.getenv("ANIVORA_API_SECRET", "")
ADMIN_SECRET = os.getenv("ANIVORA_ADMIN_SECRET", "")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "").rstrip("/")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    max_new_tokens: int = Field(default=256, ge=1, le=512)
    temperature: float = Field(default=0.7, ge=0, le=2)


def verify_admin_secret(candidate: str) -> bool:
    return bool(
        ADMIN_SECRET
        and candidate
        and hmac.compare_digest(candidate, ADMIN_SECRET)
    )


def create_api_key() -> str:
    if not API_SECRET:
        raise RuntimeError("API key signing is not configured")

    random_part = secrets.token_urlsafe(32)
    signature = hmac.new(
        API_SECRET.encode(),
        random_part.encode(),
        hashlib.sha256,
    ).hexdigest()

    return f"av_{random_part}_{signature}"


def verify_api_key(api_key: str) -> bool:
    if not API_SECRET or not api_key.startswith("av_"):
        return False

    try:
        random_part, signature = api_key[3:].rsplit("_", 1)
        expected = hmac.new(
            API_SECRET.encode(),
            random_part.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(signature, expected)
    except (ValueError, TypeError):
        return False


@app.get("/")
def root():
    return {
        "name": "AniVora API",
        "status": "online",
        "version": "0.8.0",
    }


@app.get("/v1/status")
def status():
    configured = bool(QWEN_BASE_URL and QWEN_API_KEY)

    return {
        "success": True,
        "api": "AniVora API",
        "version": "0.8.0",
        "provider": "local",
        "inference_runtime_installed": configured,
        "model_loaded": False,
        "generation_available": configured,
        "connection_configured": configured,
        "note": (
            "Qwen connection settings are configured. "
            "A successful generation request is still required "
            "to verify live inference."
            if configured
            else "Qwen connection settings are missing."
        ),
    }


@app.get("/v1/models")
def models():
    configured = bool(QWEN_BASE_URL and QWEN_API_KEY)

    return {
        "success": True,
        "models": [
            {
                "id": "anivora-text",
                "provider": "local",
                "status": (
                    "configured" if configured else "unavailable"
                ),
            }
        ],
    }


@app.post("/v1/keys")
def create_key(
    x_admin_secret: str = Header(
        default="",
        alias="X-Admin-Secret",
    ),
):
    if not verify_admin_secret(x_admin_secret):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        api_key = create_api_key()
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="API key signing is not configured.",
        )

    return {
        "success": True,
        "api_key": api_key,
        "warning": "Save this key securely. It will not be shown again.",
    }


@app.post("/v1/generate")
def generate(
    data: GenerateRequest,
    authorization: str = Header(
        default="",
        alias="Authorization",
    ),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing API key",
        )

    api_key = authorization[7:].strip()

    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    if not data.prompt.strip():
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty",
        )

    if not QWEN_BASE_URL or not QWEN_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Local Qwen connection is not configured.",
        )

    try:
        response = httpx.post(
            f"{QWEN_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {QWEN_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": data.prompt,
                    }
                ],
                "max_tokens": data.max_new_tokens,
                "temperature": data.temperature,
                "stream": False,
            },
            timeout=90.0,
        )
        response.raise_for_status()
        result = response.json()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Local Qwen inference timed out.",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Local Qwen returned HTTP "
                f"{exc.response.status_code}."
            ),
        )
    except (httpx.RequestError, ValueError):
        raise HTTPException(
            status_code=502,
            detail="Could not connect to local Qwen or read its response.",
        )

    choices = result.get("choices", [])
    if not choices:
        raise HTTPException(
            status_code=502,
            detail="Local Qwen returned no generated text.",
        )

    output = choices[0].get("message", {}).get("content", "")
    if not isinstance(output, str) or not output.strip():
        raise HTTPException(
            status_code=502,
            detail="Local Qwen returned empty text.",
        )

    return {
        "success": True,
        "model": "anivora-text",
        "provider": "local",
        "output": output,
}
