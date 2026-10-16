from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import Session

from api import models  # noqa: F401  (registers tables with SQLModel)
from api.auth import router as auth_router
from api.database import create_db_and_tables, engine
from api.routers.summary import router as summary_router
from api.routers.transactions import router as transactions_router
from scripts.seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    # Free-tier hosting resets the SQLite file on redeploy; re-seed demo data if missing
    with Session(engine) as session:
        seed(session)
    yield


app = FastAPI(title="Vault API", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(transactions_router)
app.include_router(summary_router)


@app.get("/health")
def health():
    return {"status": "ok"}
