from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import stocks

app = FastAPI(
    title="PSX Stock Risk Monitor",
    description="Pakistan Stock Exchange risk analysis API",
    version="1.0.0",
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
