class StockInfo {
  final String symbol;
  final String name;
  final String sector;
  final double price;
  final double change;
  final double changePercent;

  StockInfo({
    required this.symbol,
    required this.name,
    required this.sector,
    this.price = 0,
    this.change = 0,
    this.changePercent = 0,
  });

  factory StockInfo.fromJson(Map<String, dynamic> json) {
    return StockInfo(
      symbol: json['symbol'] ?? '',
      name: json['name'] ?? '',
      sector: json['sector'] ?? '',
      price: (json['price'] ?? 0).toDouble(),
      change: (json['change'] ?? 0).toDouble(),
      changePercent: (json['change_percent'] ?? 0).toDouble(),
    );
  }
}

class QuoteData {
  final double price;
  final double change;
  final double changePercent;
  final double open;
  final double high;
  final double low;
  final int volume;
  final double? marketCap;
  final double? peRatio;

  QuoteData({
    required this.price,
    required this.change,
    required this.changePercent,
    required this.open,
    required this.high,
    required this.low,
    required this.volume,
    this.marketCap,
    this.peRatio,
  });

  factory QuoteData.fromJson(Map<String, dynamic> json) {
    return QuoteData(
      price: (json['price'] ?? 0).toDouble(),
      change: (json['change'] ?? 0).toDouble(),
      changePercent: (json['change_percent'] ?? 0).toDouble(),
      open: (json['open'] ?? 0).toDouble(),
      high: (json['high'] ?? 0).toDouble(),
      low: (json['low'] ?? 0).toDouble(),
      volume: (json['volume'] ?? 0).toInt(),
      marketCap: json['market_cap']?.toDouble(),
      peRatio: json['pe_ratio']?.toDouble(),
    );
  }
}

class HistoricalPrice {
  final String date;
  final double open;
  final double high;
  final double low;
  final double close;
  final int volume;

  HistoricalPrice({
    required this.date,
    required this.open,
    required this.high,
    required this.low,
    required this.close,
    required this.volume,
  });

  factory HistoricalPrice.fromJson(Map<String, dynamic> json) {
    return HistoricalPrice(
      date: json['date'] ?? '',
      open: (json['open'] ?? 0).toDouble(),
      high: (json['high'] ?? 0).toDouble(),
      low: (json['low'] ?? 0).toDouble(),
      close: (json['close'] ?? 0).toDouble(),
      volume: (json['volume'] ?? 0).toInt(),
    );
  }
}

class NewsArticle {
  final String title;
  final String source;
  final String url;
  final String date;
  final String snippet;
  final String sentiment;
  final double sentimentScore;

  NewsArticle({
    required this.title,
    required this.source,
    required this.url,
    required this.date,
    required this.snippet,
    required this.sentiment,
    required this.sentimentScore,
  });

  factory NewsArticle.fromJson(Map<String, dynamic> json) {
    return NewsArticle(
      title: json['title'] ?? '',
      source: json['source'] ?? '',
      url: json['url'] ?? '',
      date: json['date'] ?? '',
      snippet: json['snippet'] ?? '',
      sentiment: json['sentiment'] ?? 'neutral',
      sentimentScore: (json['sentiment_score'] ?? 0).toDouble(),
    );
  }
}

class RiskIndicatorBreakdown {
  final double? rsi;
  final String? macd;
  final double? sma20;
  final double? sma50;
  final String? bbPosition;
  final double? atrPercent;
  final double? volumeChange;

  RiskIndicatorBreakdown({
    this.rsi,
    this.macd,
    this.sma20,
    this.sma50,
    this.bbPosition,
    this.atrPercent,
    this.volumeChange,
  });

  factory RiskIndicatorBreakdown.fromJson(Map<String, dynamic> json) {
    return RiskIndicatorBreakdown(
      rsi: json['rsi']?.toDouble(),
      macd: json['macd'],
      sma20: json['sma_20']?.toDouble(),
      sma50: json['sma_50']?.toDouble(),
      bbPosition: json['bb_position'],
      atrPercent: json['atr_percent']?.toDouble(),
      volumeChange: json['volume_change']?.toDouble(),
    );
  }
}

class RiskResponse {
  final String symbol;
  final String date;
  final double riskScore;
  final String riskLevel;
  final Map<String, dynamic> components;
  final RiskIndicatorBreakdown indicators;
  final Map<String, dynamic>? mlPrediction;
  final List<String> explanation;

  RiskResponse({
    required this.symbol,
    required this.date,
    required this.riskScore,
    required this.riskLevel,
    required this.components,
    required this.indicators,
    this.mlPrediction,
    required this.explanation,
  });

  factory RiskResponse.fromJson(Map<String, dynamic> json) {
    return RiskResponse(
      symbol: json['symbol'] ?? '',
      date: json['date'] ?? '',
      riskScore: (json['risk_score'] ?? 0).toDouble(),
      riskLevel: json['risk_level'] ?? 'MEDIUM',
      components: Map<String, dynamic>.from(json['components'] ?? {}),
      indicators: RiskIndicatorBreakdown.fromJson(
          json['indicators'] ?? {}),
      mlPrediction: json['ml_prediction'] != null
          ? Map<String, dynamic>.from(json['ml_prediction'])
          : null,
      explanation: List<String>.from(json['explanation'] ?? []),
    );
  }
}
