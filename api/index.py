
import os
import hmac
import hashlib
import secrets

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="AniVora API", version="0.7.0")

API_SECRET = os.getenv("ANIVORA_API_SECRET", "")
ADMIN_SECRET = os.getenv("ANIVORA_ADMIN_SECRET", "")


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
        "version": "0.7.0",
    }


@app.get("/v1/status")
def status():
    return {
        "success": True,
        "api": "AniVora API",
        "version": "0.7.0",
        "inference_runtime_installed": False,
        "model_loaded": False,
        "generation_available": False,
        "provider": "local",
        "note": (
            "API is online. A compatible local inference runtime "
            "is not configured for this deployment yet."
        ),
    }


@app.get("/v1/models")
def models():
    return {
        "success": True,
        "models": [
            {
                "id": "anivora-text",
                "provider": "local",
                "status": "unavailable",
                "reason": "Local inference runtime is not configured.",
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

    raise HTTPException(
        status_code=503,
        detail=(
            "Local AI generation is not available yet. "
            "The API is online, but no compatible inference runtime "
            "is configured."
        ),
    )
