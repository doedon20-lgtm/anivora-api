
import os
import hashlib
import hmac
import secrets
import threading
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="AniVora API", version="0.6.0")

API_SECRET = os.getenv("ANIVORA_API_SECRET", "")
ADMIN_SECRET = os.getenv("ANIVORA_ADMIN_SECRET", "")

MODEL_REPO = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
MODEL_FILE = "qwen2.5-0.5b-instruct-q4_k_m.gguf"

_model = None
_model_lock = threading.Lock()


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    max_new_tokens: int = Field(default=512, ge=1, le=1024)
    temperature: float = Field(default=0.7, gt=0, le=2)


def verify_admin_secret(candidate: str) -> bool:
    return bool(
        ADMIN_SECRET
        and candidate
        and hmac.compare_digest(candidate, ADMIN_SECRET)
    )


def create_api_key() -> str:
    if not API_SECRET:
        raise RuntimeError("API signing secret is not configured")

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


def load_model():
    global _model

    if _model is not None:
        return _model

    with _model_lock:
        if _model is not None:
            return _model

        try:
            from huggingface_hub import hf_hub_download
            from llama_cpp import Llama

            model_path = hf_hub_download(
                repo_id=MODEL_REPO,
                filename=MODEL_FILE,
                cache_dir="/tmp/anivora-model-cache",
            )

            _model = Llama(
                model_path=model_path,
                n_ctx=4096,
                n_threads=1,
                n_batch=128,
                n_gpu_layers=0,
                verbose=False,
            )

            return _model

        except Exception:
            # Do not expose internal paths, credentials, or stack traces.
            raise HTTPException(
                status_code=503,
                detail="The local model could not be loaded.",
            )


@app.get("/")
def root():
    return {
        "name": "AniVora API",
        "status": "online",
        "version": "0.6.0",
    }


@app.get("/v1/status")
def status():
    try:
        import huggingface_hub
        import llama_cpp

        runtime_installed = True
    except ImportError:
        runtime_installed = False

    return {
        "success": True,
        "api": "AniVora API",
        "inference_runtime_installed": runtime_installed,
        "model_loaded": _model is not None,
        "generation_available": runtime_installed,
        "model": MODEL_REPO,
        "note": (
            "The model loads on the first generation request."
            if runtime_installed and _model is None
            else "Check runtime installation before generating."
            if not runtime_installed
            else "The model is loaded in this process."
        ),
    }


@app.get("/v1/models")
def models():
    return {
        "success": True,
        "models": [
            {
                "id": "anivora-text",
                "type": "text",
                "provider": "local",
                "model": MODEL_REPO,
                "status": (
                    "loaded"
                    if _model is not None
                    else "not_loaded"
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
        key = create_api_key()
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="API key provisioning is not configured.",
        )

    return {
        "success": True,
        "api_key": key,
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
        raise HTTPException(status_code=401, detail="Missing API key")

    api_key = authorization[7:].strip()

    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    prompt = data.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    model = load_model()

    try:
        result = model.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are AniVora's local text model. "
                        "Follow the user's instructions accurately."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=data.max_new_tokens,
            temperature=data.temperature,
        )

        output = result["choices"][0]["message"]["content"]

        if not isinstance(output, str) or not output.strip():
            raise HTTPException(
                status_code=502,
                detail="The local model returned no text.",
            )

        return {
            "success": True,
            "api": "AniVora API",
            "model": "anivora-text",
            "result": {"output": output.strip()},
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Local text generation failed.",
        )
