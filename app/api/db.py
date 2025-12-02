from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import declarative_base

DATABASE_URL = "sqlite+aiosqlite:///./dev.db"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

# 🔥 VAŽNO: ovo registruje modele prije kreiranja tabela!
from app.api import models  # noqa: F401


async def init_db():
    async with engine.begin() as conn:
        print(">>> Kreiram tabele...")
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    async with async_session() as session:
        yield session
