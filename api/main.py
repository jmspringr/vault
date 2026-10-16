from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import models  # noqa: F401  (registers tables with SQLModel)
from api.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Vault API", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}
