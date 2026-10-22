
import os
import hmac
import hashlib
import secrets

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

APP_VERSION = "0.9.0"

app = FastAPI(title="AniVora API", version=APP_VERSION)

API_SECRET = os.getenv("ANIVORA_API_SECRET", "")
ADMIN_SECRET = os.getenv("ANIVORA_ADMIN_SECRET", "")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "").rstrip("/")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")

QWEN_TIMEOUT = 90.0
HEALTH_TIMEOUT = 3.0

SYSTEM_PROMPT = (
    "You are AniVora, a helpful AI assistant. "
    "Answer the user's actual request clearly and directly. "
    "Do not invent facts, product features, sources, or claims. "
    "If you do not know something, say so instead of guessing. "
    "Follow the requested format and keep answers relevant. "
    "For coding requests, provide practical, valid code and "
    "explain important assumptions briefly."
)


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
        API_SECRET.encode("utf-8"),
        random_part.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"av_{random_part}_{signature}"


def verify_api_key(api_key: str) -> bool:
    if not API_SECRET or not api_key.startswith("av_"):
        return False

    try:
        body = api_key[3:]

        # SHA-256 hexadecimal signatures are exactly 64 characters.
        # Parse from the end because the random part can contain "_".
        if len(body) <= 65 or body[-65] != "_":
            return False

        random_part = body[:-65]
        signature = body[-64:]

        if not random_part:
            return False

        expected = hmac.new(
            API_SECRET.encode("utf-8"),
            random_part.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(signature, expected)

    except (ValueError, TypeError):
        return False


def qwen_is_healthy() -> bool:
    """Check whether the configured Qwen server responds to /health."""
    if not QWEN_BASE_URL or not QWEN_API_KEY:
        return False

    try:
        response = httpx.get(
            f"{QWEN_BASE_URL}/health",
            timeout=HEALTH_TIMEOUT,
        )
        return response.status_code == 200
    except httpx.HTTPError:
        return False


@app.get("/")
def root():
    return {
        "name": "AniVora API",
        "status": "online",
        "version": APP_VERSION,
    }


@app.get("/v1/status")
def status():
    configured = bool(QWEN_BASE_URL and QWEN_API_KEY)
    healthy = qwen_is_healthy()

    if not configured:
        note = "Qwen connection settings are missing."
    elif healthy:
        note = "The configured Qwen server is responding to health checks."
    else:
        note = (
            "Qwen settings exist, but the server did not pass its "
            "health check. Check the model server and tunnel."
        )

    return {
        "success": True,
        "api": "AniVora API",
        "version": APP_VERSION,
        "provider": "local",
        "connection_configured": configured,
        "inference_runtime_installed": healthy,
        "runtime_reachable": healthy,
        "model_loaded": healthy,
        "generation_available": configured and healthy,
        "note": note,
    }


@app.get("/v1/models")
def models():
    configured = bool(QWEN_BASE_URL and QWEN_API_KEY)
    healthy = qwen_is_healthy()

    if configured and healthy:
        model_status = "ready"
    elif configured:
        model_status = "configured"
    else:
        model_status = "unavailable"

    return {
        "success": True,
        "models": [
            {
                "id": "anivora-text",
                "provider": "local",
                "status": model_status,
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
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )

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
    scheme, separator, credential = authorization.partition(" ")

    if (
        not separator
        or scheme.lower() != "bearer"
        or not credential.strip()
    ):
        raise HTTPException(
            status_code=401,
            detail="Missing API key",
        )

    api_key = credential.strip()

    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    prompt = data.prompt.strip()

    if not prompt:
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty",
        )

    if not QWEN_BASE_URL or not QWEN_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Local Qwen connection is not configured.",
        )

    payload = {
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "max_tokens": data.max_new_tokens,
        "temperature": data.temperature,
        "stream": False,
    }

    try:
        response = httpx.post(
            f"{QWEN_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {QWEN_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=QWEN_TIMEOUT,
        )

        response.raise_for_status()
        result = response.json()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Local Qwen inference timed out.",
        )
    except httpx.HTTPStatusError as exc:
        # Never expose upstream response bodies or credentials.
        raise HTTPException(
            status_code=502,
            detail=(
                "Local Qwen returned HTTP "
                f"{exc.response.status_code}."
            ),
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to local Qwen.",
        )
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Local Qwen returned invalid JSON.",
        )

    if not isinstance(result, dict):
        raise HTTPException(
            status_code=502,
            detail="Local Qwen returned an unexpected response.",
        )

    choices = result.get("choices")

    if not isinstance(choices, list) or not choices:
        raise HTTPException(
            status_code=502,
            detail="Local Qwen returned no generated text.",
        )

    first_choice = choices[0]

    if not isinstance(first_choice, dict):
        raise HTTPException(
            status_code=502,
            detail="Local Qwen returned an unexpected response.",
        )

    message = first_choice.get("message")

    if not isinstance(message, dict):
        raise HTTPException(
            status_code=502,
            detail="Local Qwen returned an unexpected response.",
        )

    output = message.get("content")

    if not isinstance(output, str) or not output.strip():
        raise HTTPException(
            status_code=502,
            detail="Local Qwen returned empty text.",
        )

    return {
        "success": True,
        "model": "anivora-text",
        "provider": "local",
        "output": output.strip(),
    }
