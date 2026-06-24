import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/stock_models.dart';

class ApiService {
  static const String _baseUrl = 'https://psx-risk-monitor.onrender.com';
  static const Duration _timeout = Duration(seconds: 60);

  Future<List<StockInfo>> getStocks() async {
    final res = await _get('/stocks');
    return (res['stocks'] as List)
        .map((e) => StockInfo.fromJson(e))
        .toList();
  }

  Future<QuoteData> getQuote(String symbol) async {
    final res = await _get('/stocks/$symbol');
    return QuoteData.fromJson(res['quote']);
  }

  Future<List<HistoricalPrice>> getHistorical(String symbol,
      {int days = 30}) async {
    final res = await _get('/stocks/$symbol/historical?days=$days');
    return (res['data'] as List)
        .map((e) => HistoricalPrice.fromJson(e))
        .toList();
  }

  Future<List<NewsArticle>> getNews(String symbol) async {
    try {
      final res = await _get('/stocks/$symbol/news');
      return (res['articles'] as List)
          .map((e) => NewsArticle.fromJson(e))
          .toList();
    } catch (_) {
      return [];
    }
  }

  Future<RiskResponse> getRisk(String symbol) async {
    final res = await _get('/stocks/$symbol/risk');
    return RiskResponse.fromJson(res);
  }

  Future<Map<String, dynamic>> _get(String path) async {
    final url = Uri.parse('$_baseUrl$path');
    final response = await http
        .get(url, headers: {'Accept': 'application/json'})
        .timeout(_timeout);
    if (response.statusCode != 200) {
      throw Exception(
          'HTTP ${response.statusCode}: ${response.body.substring(0, response.body.length.clamp(0, 100))}');
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }
}
