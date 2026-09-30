from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from engine import get_engine

app = FastAPI(
    title="AniVora Engine",
    version="0.1.0"
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
        "version": "0.1.0"
    }


@app.get("/health")
def health():
    return {
        "success": True,
        "engine": "AniVora Engine",
        "loaded": engine.loaded,
        "model": engine.model_name
    }


@app.post("/generate")
def generate(request: GenerateRequest):
    if not request.prompt.strip():
        raise HTTPException(
            status_code=400,
            detail="Prompt cannot be empty"
        )

    try:
        result = engine.generate(
            prompt=request.prompt,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature
        )

        return {
            "success": True,
            "engine": "AniVora Engine",
            "model": engine.model_name,
            "output": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
  )
