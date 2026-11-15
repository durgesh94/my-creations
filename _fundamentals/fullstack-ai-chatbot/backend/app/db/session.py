
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

# SQLAlchemy engine and session configuration
engine = create_engine(
    get_settings().database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)

# Dependency to get a database session
def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db
