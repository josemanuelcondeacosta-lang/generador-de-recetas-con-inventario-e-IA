import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import make_engine
from app.models import Base
from app.routers import auth, ingredients, recipes

load_dotenv()
engine = make_engine(os.environ["DATABASE_URL"])
static = Path(__file__).resolve().parents[1] / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if len(os.environ.get("JWT_SECRET", "")) < 32:
        raise RuntimeError("JWT_SECRET debe tener al menos 32 caracteres")
    Base.metadata.create_all(engine)
    yield
    engine.dispose()


app = FastAPI(title="Generador de recetas", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(ingredients.router)
app.include_router(recipes.router)
app.mount("/static", StaticFiles(directory=static), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(static / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(static / "favicon.ico", media_type="image/x-icon")
