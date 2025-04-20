from urllib.parse import parse_qs, urlparse

import nacos
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ===== 1. 从 Nacos 加载配置 =====


def load_nacos_config(data_id, group, server="127.0.0.1:8848", namespace="public"):
    client = nacos.NacosClient(server, namespace=namespace)
    config_str = client.get_config(data_id, group)
    return yaml.safe_load(config_str)


# ===== 2. 解析 JDBC URL 到 SQLAlchemy 可用格式 =====


def parse_jdbc_url(jdbc_url):
    if jdbc_url.startswith("jdbc:"):
        jdbc_url = jdbc_url[len("jdbc:") :]
    parsed = urlparse(jdbc_url)
    query = parse_qs(parsed.query)

    return {
        "username": parsed.username,
        "password": parsed.password,
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "database": parsed.path.lstrip("/"),
        "query": query,
    }


# ===== 3. 构建 SQLAlchemy Engine 和 Session =====


def build_sqlalchemy_engine(ds_config):
    jdbc_url = ds_config.get("url")
    username = ds_config.get("username")
    password = ds_config.get("password")

    url_info = parse_jdbc_url(jdbc_url)

    user = username or url_info["username"]
    pwd = password or url_info["password"]
    host = url_info["host"]
    port = url_info["port"]
    db = url_info["database"]

    # charset 处理（从 query 里提取）
    charset = url_info["query"].get("characterEncoding", ["utf8mb4"])[0]

    # SQLAlchemy 连接 URL 构建
    sqlalchemy_url = (
        f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}?charset={charset}"
    )

    engine = create_engine(
        sqlalchemy_url,
        pool_size=10,
        max_overflow=20,
        pool_recycle=1800,  # hikari.max-lifetime 对应
        pool_timeout=30,
    )
    return engine


# ===== 4. 全局 Engine 和 Session =====

# 建议在你程序启动时初始化
engine = None
SessionLocal = None


def init_db_from_nacos(data_id, group, server="127.0.0.1:8848", namespace="public"):
    global engine, SessionLocal
    config = load_nacos_config(data_id, group, server, namespace)
    ds_config = config.get("spring", {}).get("datasource", {})
    engine = build_sqlalchemy_engine(ds_config)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db_session():
    if SessionLocal is None:
        raise Exception("Database is not initialized. Call init_db_from_nacos first.")
    return SessionLocal()


def get_db():
    if SessionLocal is None:
        raise Exception("DB not initialized")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_sync_db():
    if SessionLocal is None:
        raise Exception("DB not initialized")
    return SessionLocal()
