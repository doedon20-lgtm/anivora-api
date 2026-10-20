import os
import hashlib
import hmac
import secrets

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from engine_client import get_engine_client

app = FastAPI(title="AniVora API", version="0.5.0")

API_SECRET = os.getenv("ANIVORA_API_SECRET", "")
ADMIN_SECRET = os.getenv("ANIVORA_ADMIN_SECRET", "")

engine_client = get_engine_client()


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    max_new_tokens: int = Field(default=512, ge=1, le=2048)
    temperature: float = Field(default=0.7, gt=0, le=2)


def create_api_key():
    if not API_SECRET:
        raise RuntimeError("API signing secret is not configured")

    random_part = secrets.token_urlsafe(32)
    signature = hmac.new(
        API_SECRET.encode(),
        random_part.encode(),
        hashlib.sha256
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
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected)

    except (ValueError, TypeError):
        return False


def verify_admin_secret(candidate: str) -> bool:
    if not ADMIN_SECRET or not candidate:
        return False

    return hmac.compare_digest(candidate, ADMIN_SECRET)


@app.get("/")
def root():
    return {
        "name": "AniVora API",
        "status": "online",
        "version": "0.5.0"
    }


@app.get("/v1/status")
async def status():
    try:
        engine_status = await engine_client.health()
        connected = True
    except Exception:
        engine_status = {"connected": False}
        connected = False

    return {
        "success": True,
        "api": "AniVora API",
        "generation_available": connected,
        "engine_status": engine_status
    }


@app.get("/v1/models")
def models():
    return {
        "success": True,
        "models": [
            {
                "id": "anivora-text",
                "type": "text",
                "status": "available"
            }
        ]
    }


@app.post("/v1/keys")
def create_key(
    x_admin_secret: str = Header(default="", alias="X-Admin-Secret")
):
    if not verify_admin_secret(x_admin_secret):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )

    try:
        key = create_api_key()
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="API key provisioning is not configured"
        )

    return {
        "success": True,
        "api_key": key,
        "warning": "Save this key securely. It will not be shown again."
    }


@app.post("/v1/generate")
async def generate(
    data: GenerateRequest,
    authorization: str = Header(default="", alias="Authorization")
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing API key"
        )

    api_key = authorization[7:].strip()

    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    if not data.prompt.strip():
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty"
        )

    try:
        result = await engine_client.generate(
            prompt=data.prompt.strip(),
            max_new_tokens=data.max_new_tokens,
            temperature=data.temperature
        )

        output = result.get("output") if isinstance(result, dict) else None

        if not isinstance(output, str) or not output.strip():
            raise HTTPException(
                status_code=502,
                detail="The generation service returned no text"
            )

        return {
            "success": True,
            "api": "AniVora API",
            "model": "anivora-text",
            "result": {
                "output": output
            }
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="AniVora generation service is unavailable"
  )
