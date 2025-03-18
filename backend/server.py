from fastapi import FastAPI

app = FastAPI()

from heartbeat.api import router as heartbeat_router
from utils.api import router as utils_router

app.include_router(heartbeat_router)
app.include_router(utils_router)
