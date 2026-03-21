from pathlib import Path
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)

    from src.backend.database import Base, engine
    from src.backend.routers import articles, comparison, settings, sources
else:
    from .database import Base, engine
    from .routers import articles, comparison, settings, sources


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # Migrate existing databases: add country column if missing
    existing_columns = {col["name"] for col in inspect(engine).get_columns("articles")}
    if "country" not in existing_columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE articles ADD COLUMN country VARCHAR NOT NULL DEFAULT 'us'"))
            conn.commit()
    yield


app = FastAPI(
    title="NewsPerspective API",
    description="See the news. Not the spin.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router)
app.include_router(comparison.router)
app.include_router(settings.router)
app.include_router(sources.router)
