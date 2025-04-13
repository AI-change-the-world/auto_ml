from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from db import DB
from heartbeat.api import router as heartbeat_router
from utils.api import router as utils_router
from yolo.api import router as yolo_router
from label.api import router as label_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    DB.init()
    yield
    DB.close()


app = FastAPI(lifespan=lifespan)


app.include_router(heartbeat_router)
app.include_router(utils_router)
app.include_router(yolo_router)
app.include_router(label_router)


if __name__ == "__main__":
    import uvicorn

    debug = os.environ.get("IS_DEBUG", None)
    uvicorn.run(
        "server:app", host="0.0.0.0", port=8000, reload=debug == "true" or debug is None
    )
