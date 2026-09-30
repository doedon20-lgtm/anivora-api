from fastapi import FastAPI

app = FastAPI(
    title="AniVora API",
    version="1.0.0"
)


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
