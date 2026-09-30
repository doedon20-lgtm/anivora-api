import uvicorn

from engine_config import EngineConfig


if __name__ == "__main__":
    uvicorn.run(
        "engine_server:app",
        host=EngineConfig.HOST,
        port=EngineConfig.PORT,
        reload=False
    )
