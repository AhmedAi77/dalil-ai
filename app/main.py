"""FastAPI application entry point."""

import logging

from fastapi import FastAPI

from app.api.documents import router as documents_router
from app.api.query import router as query_router
from app.api.speech import router as speech_router
from app.api.auth import router as auth_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(
    title="Contexta",
    version="1.0.0",
    description="A private document knowledge workspace with source-grounded answers.",
)
app.include_router(documents_router)
app.include_router(query_router)
app.include_router(speech_router)
app.include_router(auth_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
