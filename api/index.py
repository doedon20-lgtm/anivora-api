import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from database import create_tables
from routes import (
    handle_register,
    handle_health,
    handle_models,
    handle_generate,
)


app = FastAPI(
    title="AniVora API",
    version="1.0.0"
)


# Initialize database tables when the function starts.
create_tables()


@app.get("/")
async def root():
    return {
        "success": True,
        "service": "AniVora API",
        "version": "v1",
        "status": "online"
    }


@app.get("/v1/status")
async def status():
    result = handle_health()

    return JSONResponse(
        status_code=result["status"],
        content=result["body"]
    )


@app.get("/v1/models")
async def models():
    result = handle_models()

    return JSONResponse(
        status_code=result["status"],
        content=result["body"]
    )


@app.post("/v1/register")
async def register(request: Request):

    try:
        body = await request.body()

        result = handle_register(
            body.decode(
                "utf-8",
                errors="replace"
            )
        )

        return JSONResponse(
            status_code=result["status"],
            content=result["body"]
        )

    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal AniVora API error"
            }
        )


@app.post("/v1/generate")
async def generate(request: Request):

    try:
        body = await request.body()

        result = handle_generate(
            body.decode(
                "utf-8",
                errors="replace"
            ),
            request.headers
        )

        return JSONResponse(
            status_code=result["status"],
            content=result["body"]
        )

    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal AniVora API error"
            }
)
