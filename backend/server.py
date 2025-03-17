from fastapi import FastAPI

app = FastAPI()

from heartbeat.api import router as heartbeat_router

app.include_router(heartbeat_router)
