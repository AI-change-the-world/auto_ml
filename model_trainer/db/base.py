from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

engine = None
SessionLocal = None


def init_db(database_url: str):
    """初始化数据库连接"""
    global engine, SessionLocal
    engine = create_engine(
        database_url,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
        pool_timeout=30,
    )
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """获取数据库会话"""
    if SessionLocal is None:
        raise Exception("DB not initialized")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_sync_db():
    """获取同步数据库会话"""
    if SessionLocal is None:
        raise Exception("DB not initialized")
    return SessionLocal()
