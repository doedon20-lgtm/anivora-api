
import os
import hmac
import hashlib
import secrets
import httpx

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="AniVora API", version="0.9.1")

ANIVORA_API_SECRET = os.getenv("ANIVORA_API_SECRET", "")
ANIVORA_ADMIN_SECRET = os.getenv("ANIVORA_ADMIN_SECRET", "")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "").rstrip("/")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")

QWEN_TIMEOUT = 90


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    max_new_tokens: int = Field(default=256, ge=1, le=512)
    temperature: float = Field(default=0.7, ge=0, le=2)


def qwen_configured():
    return bool(QWEN_BASE_URL and QWEN_API_KEY)


def make_customer_key():
    if not ANIVORA_API_SECRET:
        raise HTTPException(
            status_code=503,
            detail="API key signing is not configured."
        )

    random_part = secrets.token_urlsafe(32)
    signature = hmac.new(
        ANIVORA_API_SECRET.encode(),
        random_part.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"av_{random_part}_{signature}"


def verify_api_key(api_key: str) -> bool:
    if not ANIVORA_API_SECRET or not api_key.startswith("av_"):
        return False

    body = api_key[3:]

    if len(body) <= 65 or body[-65] != "_":
        return False

    random_part = body[:-65]
    supplied_signature = body[-64:]

    expected_signature = hmac.new(
        ANIVORA_API_SECRET.encode(),
        random_part.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        supplied_signature,
        expected_signature
    )


def require_customer_key(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="A valid AniVora API key is required."
        )

    api_key = authorization[7:].strip()

    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid AniVora API key."
        )


def require_admin_key(authorization: str | None):
    if not ANIVORA_ADMIN_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Admin access is not configured."
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Admin authorization is required."
        )

    supplied = authorization[7:].strip()

    if not hmac.compare_digest(supplied, ANIVORA_ADMIN_SECRET):
        raise HTTPException(
            status_code=403,
            detail="Admin authorization failed."
        )


def qwen_health():
    if not qwen_configured():
        return False, "Qwen connection settings are missing."

    try:
        with httpx.Client(
            timeout=8,
            trust_env=False
        ) as client:
            response = client.get(f"{QWEN_BASE_URL}/health")
            response.raise_for_status()

        return True, None

    except httpx.TimeoutException:
        return False, "Qwen health check timed out."

    except httpx.RequestError as exc:
        return False, f"Connection error: {type(exc).__name__}."

    except httpx.HTTPStatusError as exc:
        return False, f"Qwen health returned HTTP {exc.response.status_code}."

    except Exception as exc:
        return False, f"Health check failed: {type(exc).__name__}."


@app.get("/")
def root():
    return {
        "name": "AniVora API",
        "status": "online",
        "version": "0.9.1"
    }


@app.get("/v1/status")
def status():
    reachable, error = qwen_health()

    return {
        "success": True,
        "api": "AniVora API",
        "version": "0.9.1",
        "provider": "local",
        "connection_configured": qwen_configured(),
        "inference_runtime_installed": False,
        "runtime_reachable": reachable,
        "model_loaded": reachable,
        "generation_available": reachable,
        "connection_error": error,
        "note": (
            "Qwen is reachable."
            if reachable
            else "Qwen connection failed. See connection_error."
        )
    }


@app.get("/v1/models")
def models(authorization: str | None = Header(default=None)):
    require_customer_key(authorization)

    if not qwen_configured():
        raise HTTPException(
            status_code=503,
            detail="Qwen connection settings are missing."
        )

    try:
        with httpx.Client(
            timeout=15,
            trust_env=False
        ) as client:
            response = client.get(
                f"{QWEN_BASE_URL}/v1/models",
                headers={"Authorization": f"Bearer {QWEN_API_KEY}"}
            )
            response.raise_for_status()
            data = response.json()

        return {
            "object": "list",
            "data": data.get("data", [])
        }

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Qwen models request timed out."
        )

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Qwen returned HTTP {exc.response.status_code}."
        )

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Qwen connection error: {type(exc).__name__}."
        )

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=502,
            detail="Qwen returned an invalid response."
        )


@app.post("/v1/keys")
def create_key(authorization: str | None = Header(default=None)):
    require_admin_key(authorization)

    return {
        "success": True,
        "api_key": make_customer_key(),
        "warning": "Store this key securely. It will not be shown again."
    }


@app.post("/v1/generate")
def generate(
    request: GenerateRequest,
    authorization: str | None = Header(default=None)
):
    require_customer_key(authorization)

    if not qwen_configured():
        raise HTTPException(
            status_code=503,
            detail="Qwen connection settings are missing."
        )

    payload = {
        "model": "qwen",
        "messages": [
            {
                "role": "user",
                "content": request.prompt
            }
        ],
        "max_tokens": request.max_new_tokens,
        "temperature": request.temperature,
        "stream": False
    }

    try:
        with httpx.Client(
            timeout=QWEN_TIMEOUT,
            trust_env=False
        ) as client:
            response = client.post(
                f"{QWEN_BASE_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {QWEN_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            response.raise_for_status()
            data = response.json()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Qwen generation timed out."
        )

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Qwen returned HTTP {exc.response.status_code}."
        )

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Qwen connection error: {type(exc).__name__}."
        )

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=502,
            detail="Qwen returned an invalid response."
        )

    choices = data.get("choices")

    if not isinstance(choices, list) or not choices:
        raise HTTPException(
            status_code=502,
            detail="Qwen returned no generation results."
        )

    message = choices[0].get("message", {})
    content = message.get("content", "")

    if not isinstance(content, str) or not content.strip():
        raise HTTPException(
            status_code=502,
            detail="Qwen returned empty text."
        )

    return {
        "success": True,
        "model": data.get("model", "qwen"),
        "output": content,
        "usage": data.get("usage")
    }
