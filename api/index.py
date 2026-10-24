
import os
import hmac
import hashlib
import secrets
import httpx

from typing import Literal
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


APP_VERSION = "1.0.0"
QWEN_TIMEOUT = 90

app = FastAPI(
    title="AniVora API",
    version=APP_VERSION,
    description="AniVora API and initial generation orchestrator."
)

ANIVORA_API_SECRET = os.getenv("ANIVORA_API_SECRET", "")
ANIVORA_ADMIN_SECRET = os.getenv("ANIVORA_ADMIN_SECRET", "")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "").rstrip("/")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    max_new_tokens: int = Field(default=256, ge=1, le=512)
    temperature: float = Field(default=0.7, ge=0, le=2)


class OrchestrateRequest(BaseModel):
    task: Literal["text", "story", "image", "video", "voice", "3d"]
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

    return hmac.compare_digest(supplied_signature, expected_signature)


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
        with httpx.Client(timeout=8, trust_env=False) as client:
            response = client.get(f"{QWEN_BASE_URL}/health")
            response.raise_for_status()

        return True, None

    except httpx.TimeoutException:
        return False, "Qwen health check timed out."

    except httpx.HTTPStatusError as exc:
        return False, f"Qwen health returned HTTP {exc.response.status_code}."

    except httpx.RequestError as exc:
        return False, f"Qwen connection error: {type(exc).__name__}."

    except Exception as exc:
        return False, f"Health check failed: {type(exc).__name__}."


def generate_text(request: GenerateRequest):
    if not qwen_configured():
        raise HTTPException(
            status_code=503,
            detail="Qwen connection settings are missing."
        )

    payload = {
        "model": "qwen",
        "messages": [
            {"role": "user", "content": request.prompt}
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

    if not isinstance(data, dict):
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

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise HTTPException(
            status_code=502,
            detail="Qwen returned an invalid generation result."
        )

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise HTTPException(
            status_code=502,
            detail="Qwen returned an invalid message."
        )

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


@app.get("/")
def root():
    return {
        "name": "AniVora API",
        "status": "online",
        "version": APP_VERSION
    }


@app.get("/v1/status")
def status():
    reachable, error = qwen_health()

    return {
        "success": True,
        "api": "AniVora API",
        "version": APP_VERSION,
        "provider": "local",
        "connection_configured": qwen_configured(),
        "runtime_reachable": reachable,
        "model_loaded": None,
        "generation_available": reachable,
        "connection_error": error,
        "note": (
            "Qwen health endpoint is reachable; generation has not "
            "been verified by this health check."
            if reachable
            else "Qwen connection failed. See connection_error."
        )
    }


@app.get("/v1/capabilities")
def capabilities():
    return {
        "success": True,
        "orchestrator_version": "1.0.0",
        "available_tasks": ["text", "story"],
        "planned_tasks": ["image", "video", "voice", "3d"],
        "text_provider_configured": qwen_configured(),
        "note": (
            "Image, video, voice, and 3D require separate generation "
            "adapters before they can run."
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
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.get(
                f"{QWEN_BASE_URL}/v1/models",
                headers={"Authorization": f"Bearer {QWEN_API_KEY}"}
            )
            response.raise_for_status()
            data = response.json()

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

    if not isinstance(data, dict) or not isinstance(data.get("data"), list):
        raise HTTPException(
            status_code=502,
            detail="Qwen returned an invalid models response."
        )

    return {"object": "list", "data": data["data"]}


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
    return generate_text(request)


@app.post("/v1/orchestrate")
def orchestrate(
    request: OrchestrateRequest,
    authorization: str | None = Header(default=None)
):
    require_customer_key(authorization)

    if request.task in ("image", "video", "voice", "3d"):
        raise HTTPException(
            status_code=501,
            detail={
                "success": False,
                "task": request.task,
                "message": (
                    f"The {request.task} generation adapter is not "
                    "implemented yet."
                )
            }
        )

    prompt = request.prompt

    if request.task == "story":
        prompt = (
            "You are AniVora Story Studio. Create a coherent, "
            "well-structured story based on this request. "
            "Respect the user's requested genre, characters, tone, "
            "and length.\n\n"
            f"Story request:\n{request.prompt}"
        )

    result = generate_text(
        GenerateRequest(
            prompt=prompt,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature
        )
    )

    return {
        "success": True,
        "task": request.task,
        "orchestrator_version": "1.0.0",
        "result": result
    }
