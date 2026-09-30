from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import secrets
import re

app = FastAPI(
    title="AniVora API",
    version="1.0.0"
)

developers = {}


@app.get("/")
def root():
    return {
        "success": True,
        "service": "AniVora API",
        "status": "online"
    }


@app.get("/v1/status")
def status():
    return {
        "success": True,
        "service": "AniVora API",
        "version": "v1",
        "status": "online"
    }


@app.get("/v1/models")
def models():
    return {
        "success": True,
        "models": [
            {
                "id": "anivora-text",
                "type": "text-generation",
                "status": "available"
            }
        ]
    }


@app.post("/v1/register")
async def register(request: Request):

    try:
        data = await request.json()

        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()

        if not name:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Name is required"
                }
            )

        if not re.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            email
        ):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Valid email is required"
                }
            )

        api_key = "av_" + secrets.token_urlsafe(32)

        developers[email] = {
            "name": name,
            "email": email,
            "api_key": api_key
        }

        return {
            "success": True,
            "developer": {
                "name": name,
                "email": email
            },
            "api_key": api_key
        }

    except Exception as error:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(error)
            }
  )
