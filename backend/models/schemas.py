from pydantic import BaseModel
from typing import Optional


class StockInfo(BaseModel):
    symbol: str
    name: str
    sector: str


class StockListResponse(BaseModel):
    stocks: list[StockInfo]
    count: int


class QuoteData(BaseModel):
    price: float
    change: float
    change_percent: float
    open: float
    high: float
    low: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None


class StockDetailResponse(BaseModel):
    symbol: str
    quote: QuoteData


class HistoricalPrice(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockHistoricalResponse(BaseModel):
    symbol: str
    data: list[HistoricalPrice]


class NewsArticle(BaseModel):
    title: str
    source: str
    url: str
    date: str
    snippet: str
    sentiment: str
    sentiment_score: float


class StockNewsResponse(BaseModel):
    symbol: str
    articles: list[NewsArticle]
    count: int


class IndicatorBreakdown(BaseModel):
    rsi: Optional[float] = None
    macd: Optional[str] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    bb_position: Optional[str] = None
    atr_percent: Optional[float] = None
    volume_change: Optional[float] = None


class MLPrediction(BaseModel):
    next_day_direction: str
    confidence: float


class RiskComponent(BaseModel):
    technical: float
    news_sentiment: float
    volatility: float


class RiskResponse(BaseModel):
    symbol: str
    date: str
    risk_score: float
    risk_level: str
    components: RiskComponent
    indicators: IndicatorBreakdown
    ml_prediction: Optional[MLPrediction] = None
    explanation: list[str]
