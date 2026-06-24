import 'package:flutter/foundation.dart';
import '../models/stock_models.dart';
import '../services/api_service.dart';

class StockProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  bool _isLoading = false;
  String? _error;
  List<StockInfo> _stocks = [];
  RiskResponse? _selectedRisk;
  QuoteData? _selectedQuote;
  List<HistoricalPrice> _history = [];
  List<NewsArticle> _news = [];
  String _selectedSymbol = 'ENGRO';

  bool get isLoading => _isLoading;
  String? get error => _error;
  List<StockInfo> get stocks => _stocks;
  RiskResponse? get selectedRisk => _selectedRisk;
  QuoteData? get selectedQuote => _selectedQuote;
  List<HistoricalPrice> get history => _history;
  List<NewsArticle> get news => _news;
  String get selectedSymbol => _selectedSymbol;

  void setSelectedSymbol(String symbol) {
    _selectedSymbol = symbol;
    notifyListeners();
  }

  Future<void> loadStocks() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _stocks = await _api.getStocks();
    } catch (e) {
      _error = e.toString();
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<void> loadStockDetail(String symbol) async {
    _isLoading = true;
    _error = null;
    _selectedSymbol = symbol;
    notifyListeners();
    try {
      final results = await Future.wait([
        _api.getQuote(symbol),
        _api.getHistorical(symbol),
        _api.getRisk(symbol),
        _api.getNews(symbol),
      ]);
      _selectedQuote = results[0] as QuoteData;
      _history = results[1] as List<HistoricalPrice>;
      _selectedRisk = results[2] as RiskResponse;
      _news = results[3] as List<NewsArticle>;
    } catch (e) {
      _error = e.toString();
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<void> refreshRisk() async {
    try {
      _selectedRisk = await _api.getRisk(_selectedSymbol);
      _selectedQuote = await _api.getQuote(_selectedSymbol);
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }
}
