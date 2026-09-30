import os
import hashlib
import hmac
import secrets

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

from engine_client import get_engine_client


app = FastAPI(
    title="AniVora API",
    version="0.4.0"
)

API_SECRET = os.getenv("ANIVORA_API_SECRET", "")

engine_client = get_engine_client()


# -----------------------------
# API KEY SYSTEM
# -----------------------------

def create_api_key():
    if not API_SECRET:
        raise RuntimeError(
            "ANIVORA_API_SECRET is not configured"
        )

    random_part = secrets.token_urlsafe(32)

    signature = hmac.new(
        API_SECRET.encode(),
        random_part.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"av_{random_part}_{signature}"


def verify_api_key(api_key: str):
    if not API_SECRET:
        return False

    if not api_key.startswith("av_"):
        return False

    try:
        value = api_key[3:]

        random_part, signature = value.rsplit(
            "_",
            1
        )

        expected = hmac.new(
            API_SECRET.encode(),
            random_part.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(
            signature,
            expected
        )

    except Exception:
        return False


# -----------------------------
# REQUEST MODEL
# -----------------------------

class GenerateRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 128
    temperature: float = 0.7


# -----------------------------
# ROOT
# -----------------------------

@app.get("/")
def root():
    return {
        "name": "AniVora API",
        "status": "online",
        "version": "0.4.0",
        "engine": "AniVora Engine"
    }


# -----------------------------
# API STATUS
# -----------------------------

@app.get("/v1/status")
async def status():

    engine_status = None

    try:
        engine_status = await engine_client.health()
    except Exception:
        engine_status = {
            "connected": False
        }

    return {
        "success": True,
        "api": "AniVora API",
        "engine": "AniVora Engine",
        "engine_status": engine_status
    }


# -----------------------------
# MODELS
# -----------------------------

@app.get("/v1/models")
def models():

    return {
        "success": True,
        "models": [
            {
                "id": "anivora-text",
                "type": "text",
                "engine": "AniVora Engine",
                "status": "available"
            }
        ]
    }


# -----------------------------
# CREATE API KEY
# -----------------------------

@app.post("/v1/keys")
def create_key():

    key = create_api_key()

    return {
        "success": True,
        "api_key": key,
        "warning": "Save this key now. It will not be shown again."
    }


# -----------------------------
# GENERATE
# -----------------------------

@app.post("/v1/generate")
async def generate(
    request: Request,
    data: GenerateRequest
):

    authorization = request.headers.get(
        "Authorization",
        ""
    )

    if not authorization.startswith(
        "Bearer "
    ):
        raise HTTPException(
            status_code=401,
            detail="Missing API key"
        )

    api_key = authorization[
        7:
    ].strip()

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
            prompt=data.prompt,
            max_new_tokens=data.max_new_tokens,
            temperature=data.temperature
        )

        return {
            "success": True,
            "api": "AniVora API",
            "engine": "AniVora Engine",
            "result": result
        }

    except Exception as e:

        raise HTTPException(
            status_code=503,
            detail=f"AniVora Engine error: {str(e)}"
)
