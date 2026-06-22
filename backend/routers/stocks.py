from fastapi import APIRouter, HTTPException
from backend.models.schemas import (
    StockListResponse,
    StockDetailResponse,
    StockHistoricalResponse,
    StockNewsResponse,
    RiskResponse,
)
from backend.services import psx_data

router = APIRouter(prefix="/stocks", tags=["stocks"])

TOP_10_KSE100 = ["ENGRO", "LUCK", "HBL", "OGDC", "PSO", "MARI", "SYS", "FFC", "POL", "MCB"]


COMPANY_NAMES = {
    "ENGRO": "Engro Corporation", "LUCK": "Lucky Cement", "HBL": "Habib Bank Ltd",
    "OGDC": "Oil & Gas Development Co", "PSO": "Pakistan State Oil",
    "MARI": "Mari Petroleum", "SYS": "Systems Limited", "FFC": "Fauji Fertilizer Co",
    "POL": "Pakistan Oilfields Ltd", "MCB": "MCB Bank Ltd",
}

COMPANY_SECTORS = {
    "ENGRO": "Fertilizer", "LUCK": "Cement", "HBL": "Banking",
    "OGDC": "Oil & Gas", "PSO": "Oil & Gas", "MARI": "Oil & Gas",
    "SYS": "Technology", "FFC": "Fertilizer", "POL": "Oil & Gas",
    "MCB": "Banking",
}


@router.get("", response_model=StockListResponse)
def list_stocks():
    stocks_list = []
    for t in TOP_10_KSE100:
        stocks_list.append({
            "symbol": t,
            "name": COMPANY_NAMES.get(t, t),
            "sector": COMPANY_SECTORS.get(t, "N/A"),
        })
    return {"stocks": stocks_list, "count": len(stocks_list)}


@router.get("/{symbol}", response_model=StockDetailResponse)
def get_stock(symbol: str):
    symbol = symbol.upper()
    quote = psx_data.get_quote(symbol)
    if quote is None:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    return {"symbol": symbol, "quote": quote}


@router.get("/{symbol}/historical", response_model=StockHistoricalResponse)
def get_historical(symbol: str, days: int = 365):
    symbol = symbol.upper()
    df = psx_data.get_historical(symbol, days=days)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"No historical data for {symbol}")
    return {"symbol": symbol, "data": df.to_dict(orient="records")}


@router.get("/{symbol}/news", response_model=StockNewsResponse)
def get_news(symbol: str):
    symbol = symbol.upper()
    from backend.services.news_scraper import scrape_news
    articles = scrape_news(symbol)
    return {"symbol": symbol, "articles": articles, "count": len(articles)}


@router.get("/{symbol}/risk", response_model=RiskResponse)
def get_risk(symbol: str):
    symbol = symbol.upper()
    from backend.services.risk_model import calculate_risk
    result = calculate_risk(symbol)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Cannot compute risk for {symbol}")
    return result
