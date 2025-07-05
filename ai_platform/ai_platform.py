import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from Aether.api import router as aether_router
from base.nacos_config import init_db_from_nacos
from gan.api import router as gan_router
from heartbeat.api import router as heartbeat_router
from label.api import router as label_router
from process.api import router as process_router
from utils.api import router as utils_router
from yolo.api import router as yolo_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🔧 Initializing DB from Nacos...")
    init_db_from_nacos(
        "DB",
        "AUTO_ML",
        server=os.getenv("NACOS_ADDR") or "127.0.0.1:8848",
        namespace="public",
    )
    print("✅ DB Ready")
    yield
    print("🧹 Lifespan exit — you could clean up here if needed.")


app = FastAPI(lifespan=lifespan)


app.include_router(heartbeat_router)
app.include_router(utils_router)
app.include_router(yolo_router)
app.include_router(label_router)
app.include_router(process_router)
app.include_router(aether_router)
app.include_router(gan_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许访问的前端地址列表
    allow_credentials=True,  # 是否允许携带 cookie
    allow_methods=["*"],  # 允许的请求方法
    allow_headers=["*"],  # 允许的请求头
)


if __name__ == "__main__":
    import uvicorn

    debug = os.environ.get("IS_DEBUG", None)
    uvicorn.run(
        "ai_platform:app",
        host="0.0.0.0",
        port=8000,
        reload=debug == "true" or debug is None,
    )
