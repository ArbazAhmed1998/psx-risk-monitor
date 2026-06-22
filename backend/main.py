import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import stocks

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from backend.services.risk_model import train_ml_model
    model_path = os.path.join("backend", "models", "risk_classifier.pkl")
    if not os.path.exists(model_path):
        logger.info("ML model not found, training on startup...")
        try:
            train_ml_model()
        except Exception as e:
            logger.warning(f"Could not train ML model on startup: {e}")
    yield


app = FastAPI(
    title="PSX Stock Risk Monitor",
    description="Pakistan Stock Exchange risk analysis API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router)


@app.get("/")
def root():
    return {"message": "PSX Stock Risk Monitor API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
