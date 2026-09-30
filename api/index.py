from fastapi import FastAPI

app = FastAPI()


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
