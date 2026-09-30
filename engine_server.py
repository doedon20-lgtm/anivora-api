from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import torch

from engine import get_engine


app = FastAPI(
    title="AniVora Engine",
    version="0.4.0"
)

engine = get_engine()


class GenerateRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 128
    temperature: float = 0.7


@app.get("/")
def root():
    return {
        "name": "AniVora Engine",
        "status": "online",
        "version": "0.4.0"
    }


@app.get("/health")
def health():
    return {
        "success": True,
        "engine": "AniVora Engine",
        "loaded": engine.loaded,
        "model": engine.model_name,
        "device": engine.device,
        "cuda_available": torch.cuda.is_available(),
        "gpu_count": torch.cuda.device_count()
    }


@app.get("/system")
def system():
    gpu_name = None

    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)

    return {
        "success": True,
        "cpu": True,
        "cuda_available": torch.cuda.is_available(),
        "gpu_count": torch.cuda.device_count(),
        "gpu": gpu_name,
        "device": engine.device
    }


@app.post("/generate")
def generate(request: GenerateRequest):

    if not request.prompt.strip():
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty"
        )

    try:
        output = engine.generate(
            prompt=request.prompt,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature
        )

        return {
            "success": True,
            "engine": "AniVora Engine",
            "model": engine.model_name,
            "device": engine.device,
            "output": output
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
