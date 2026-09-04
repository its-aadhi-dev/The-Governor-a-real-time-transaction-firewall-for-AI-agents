from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.api.routes.events import router as events_router
from backend.api.routes.transactions import router as transactions_router
from backend.database.session import get_db

from backend.events import session_hooks  # noqa: F401


app = FastAPI(
    title="The Governor",
    description=(
        "Merchant-side transaction governance infrastructure "
        "for agentic commerce."
    ),
    version="0.1.0",
)

app.include_router(transactions_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "the-governor",
    }


@app.get("/health/database")
def database_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "online",
    }
