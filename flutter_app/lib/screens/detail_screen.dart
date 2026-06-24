import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';
import '../providers/stock_provider.dart';
import '../models/stock_models.dart';

class DetailScreen extends StatefulWidget {
  final String symbol;
  const DetailScreen({super.key, required this.symbol});

  @override
  State<DetailScreen> createState() => _DetailScreenState();
}

class _DetailScreenState extends State<DetailScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<StockProvider>().loadStockDetail(widget.symbol);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.symbol)),
      body: Consumer<StockProvider>(
        builder: (context, provider, _) {
          if (provider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (provider.error != null) {
            return _errorView(context, provider);
          }

          final risk = provider.selectedRisk;
          final quote = provider.selectedQuote;
          final history = provider.history;
          final news = provider.news;

          return RefreshIndicator(
            onRefresh: () => provider.loadStockDetail(widget.symbol),
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _Header(symbol: widget.symbol, quote: quote, risk: risk),
                  const SizedBox(height: 16),
                  if (risk != null) _RiskGaugeCard(risk: risk),
                  const SizedBox(height: 12),
                  if (risk != null) _IndicatorChips(indicators: risk.indicators),
                  const SizedBox(height: 12),
                  if (history.isNotEmpty) _ChartCard(history: history),
                  const SizedBox(height: 12),
                  if (quote != null) _QuoteCard(quote: quote),
                  const SizedBox(height: 12),
                  if (risk != null) _AnalysisCard(risk: risk),
                  const SizedBox(height: 12),
                  if (news.isNotEmpty) _NewsSection(news: news),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _errorView(BuildContext context, StockProvider provider) {
    final t = Theme.of(context);
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.cloud_off, size: 48, color: t.colorScheme.error),
          const SizedBox(height: 16),
          Text(provider.error!, style: t.textTheme.bodyMedium),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: () => provider.loadStockDetail(widget.symbol),
            icon: const Icon(Icons.refresh),
            label: const Text('Retry'),
          ),
        ],
      ),
    );
  }
}

// ────────────────── Header ──────────────────

class _Header extends StatelessWidget {
  final String symbol;
  final QuoteData? quote;
  final RiskResponse? risk;
  const _Header({required this.symbol, this.quote, this.risk});

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final companyName = _companyName(symbol);
    final isUp = quote != null && quote!.change >= 0;
    final changeColor = isUp ? Colors.green.shade600 : Colors.red.shade600;

    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: t.colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 52,
                  height: 52,
                  decoration: BoxDecoration(
                    color: t.colorScheme.primaryContainer,
                    borderRadius: BorderRadius.circular(14),
                  ),
                  alignment: Alignment.center,
                  child: Text(
                    symbol.substring(0, 2),
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: t.colorScheme.onPrimaryContainer,
                      fontSize: 18,
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(symbol,
                          style: const TextStyle(
                              fontSize: 22, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 2),
                      Text(companyName,
                          style: TextStyle(
                              fontSize: 13,
                              color: t.colorScheme.onSurfaceVariant)),
                    ],
                  ),
                ),
                if (risk != null) _RiskLabel(level: risk!.riskLevel),
              ],
            ),
            if (quote != null) ...[
              const SizedBox(height: 16),
              Row(
                children: [
                  Text(
                    'PKR ${NumberFormat('#,##0.00').format(quote!.price)}',
                    style: const TextStyle(
                        fontSize: 26, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(width: 12),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: changeColor.withAlpha(25),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          isUp ? Icons.arrow_upward : Icons.arrow_downward,
                          size: 16,
                          color: changeColor,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${isUp ? '+' : ''}${quote!.changePercent.toStringAsFixed(2)}%',
                          style: TextStyle(
                            color: changeColor,
                            fontWeight: FontWeight.w600,
                            fontSize: 15,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _companyName(String symbol) {
    const names = {
      'ENGRO': 'Engro Corporation', 'LUCK': 'Lucky Cement', 'HBL': 'Habib Bank Ltd',
      'OGDC': 'Oil & Gas Dev. Co', 'PSO': 'Pakistan State Oil',
      'MARI': 'Mari Petroleum', 'SYS': 'Systems Limited', 'FFC': 'Fauji Fertilizer',
      'POL': 'Pakistan Oilfields', 'MCB': 'MCB Bank Ltd',
    };
    return names[symbol] ?? symbol;
  }
}

class _RiskLabel extends StatelessWidget {
  final String level;
  const _RiskLabel({required this.level});

  @override
  Widget build(BuildContext context) {
    final color = switch (level) {
      'LOW' => Colors.green.shade700,
      'MEDIUM' => Colors.orange.shade700,
      'HIGH' => Colors.red.shade700,
      _ => Colors.grey,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withAlpha(20),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withAlpha(80)),
      ),
      child: Text(level, style: TextStyle(
        color: color, fontWeight: FontWeight.w600, fontSize: 13,
      )),
    );
  }
}

// ────────────────── Risk Gauge ──────────────────

class _RiskGaugeCard extends StatelessWidget {
  final RiskResponse risk;
  const _RiskGaugeCard({required this.risk});

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final score = risk.riskScore;
    final level = risk.riskLevel;
    final color = switch (level) {
      'LOW' => Colors.green,
      'MEDIUM' => Colors.orange,
      'HIGH' => Colors.red,
      _ => Colors.grey,
    };

    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: t.colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            SizedBox(
              height: 120,
              child: CustomPaint(
                size: const Size(double.infinity, 120),
                painter: _ArcGaugePainter(score: score, color: color),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '${score.toStringAsFixed(0)} / 100',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            Text(
              '${level == 'LOW' ? 'Low Risk — Favorable' : level == 'MEDIUM' ? 'Medium Risk — Caution' : 'High Risk — Avoid'}',
              style: TextStyle(
                fontSize: 13,
                color: t.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 12),
            if (risk.mlPrediction != null) _MLPrediction(risk: risk),
          ],
        ),
      ),
    );
  }
}

class _MLPrediction extends StatelessWidget {
  final RiskResponse risk;
  const _MLPrediction({required this.risk});

  @override
  Widget build(BuildContext context) {
    final pred = risk.mlPrediction!;
    final isUp = pred['next_day_direction'] == 'up';
    final confidence = (pred['confidence'] as num).toDouble();

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: (isUp ? Colors.green : Colors.red).withAlpha(15),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            isUp ? Icons.trending_up : Icons.trending_down,
            color: isUp ? Colors.green.shade600 : Colors.red.shade600,
            size: 20,
          ),
          const SizedBox(width: 8),
          Text(
            'ML predicts ${isUp ? 'UP' : 'DOWN'} tomorrow',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              color: isUp ? Colors.green.shade700 : Colors.red.shade700,
            ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: Colors.grey.withAlpha(30),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              '${(confidence * 100).toStringAsFixed(0)}% conf.',
              style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
            ),
          ),
        ],
      ),
    );
  }
}

class _ArcGaugePainter extends CustomPainter {
  final double score;
  final Color color;

  _ArcGaugePainter({required this.score, required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height * 0.85);
    final radius = size.width * 0.35;
    const startAngle = math.pi;
    const sweepAngle = math.pi;
    final fillSweep = (score / 100) * math.pi;

    final bgPaint = Paint()
      ..color = Colors.grey.withAlpha(40)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 14
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      sweepAngle,
      false,
      bgPaint,
    );

    final fgPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 14
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      fillSweep,
      false,
      fgPaint,
    );
  }

  @override
  bool shouldRepaint(covariant _ArcGaugePainter old) => old.score != score;
}

// ────────────────── Indicator Chips ──────────────────

class _IndicatorChips extends StatelessWidget {
  final RiskIndicatorBreakdown indicators;
  const _IndicatorChips({required this.indicators});

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final chips = <Widget>[];

    if (indicators.rsi != null) {
      final rsiColor = indicators.rsi! > 70
          ? Colors.red
          : indicators.rsi! < 30
              ? Colors.green
              : Colors.orange;
      chips.add(_Chip(
        label: 'RSI ${indicators.rsi!.toStringAsFixed(0)}',
        color: rsiColor,
      ));
    }
    if (indicators.macd != null) {
      final macdColor =
          indicators.macd == 'bullish' ? Colors.green : Colors.red;
      chips.add(_Chip(
        label: indicators.macd!.toUpperCase(),
        color: macdColor,
        icon: indicators.macd == 'bullish'
            ? Icons.arrow_upward
            : Icons.arrow_downward,
      ));
    }
    if (indicators.atrPercent != null) {
      chips.add(_Chip(
        label: 'ATR ${indicators.atrPercent!.toStringAsFixed(1)}%',
        color: Colors.blue,
      ));
    }
    if (indicators.volumeChange != null) {
      final volUp = indicators.volumeChange! >= 0;
      chips.add(_Chip(
        label: 'Vol ${volUp ? '+' : ''}${indicators.volumeChange!.toStringAsFixed(0)}%',
        color: volUp ? Colors.teal : Colors.blueGrey,
        icon: volUp ? Icons.trending_up : Icons.trending_down,
      ));
    }

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: chips,
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final Color color;
  final IconData? icon;
  const _Chip(
      {required this.label, required this.color, this.icon});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withAlpha(15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withAlpha(60)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 14, color: color),
            const SizedBox(width: 4),
          ],
          Text(label,
              style: TextStyle(
                  color: color, fontSize: 12, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

// ────────────────── Chart ──────────────────

class _ChartCard extends StatelessWidget {
  final List<HistoricalPrice> history;
  const _ChartCard({required this.history});

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: t.colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Price History', style: TextStyle(
              fontSize: 15, fontWeight: FontWeight.w600,
              color: t.colorScheme.onSurface,
            )),
            const SizedBox(height: 4),
            Text('Last ${history.length} days',
                style: TextStyle(fontSize: 12, color: t.colorScheme.onSurfaceVariant)),
            const SizedBox(height: 16),
            SizedBox(
              height: 200,
              child: history.length < 2
                  ? const Center(child: Text('Not enough data'))
                  : _lineChart(history, t),
            ),
          ],
        ),
      ),
    );
  }

  Widget _lineChart(List<HistoricalPrice> history, ThemeData t) {
    final spots = <FlSpot>[];
    double minY = double.infinity;
    double maxY = double.negativeInfinity;
    for (int i = 0; i < history.length; i++) {
      final c = history[i].close;
      spots.add(FlSpot(i.toDouble(), c));
      if (c < minY) minY = c;
      if (c > maxY) maxY = c;
    }
    final padding = (maxY - minY) * 0.08;
    final step = (history.length / 5).ceil().clamp(1, 100);

    return LineChart(
      LineChartData(
        gridData: FlGridData(
          show: true,
          horizontalInterval: (maxY - minY) / 4,
          getDrawingHorizontalLine: (value) => FlLine(
            color: t.colorScheme.outlineVariant.withAlpha(80),
            strokeWidth: 0.5,
          ),
          drawVerticalLine: false,
        ),
        titlesData: FlTitlesData(
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 48,
              getTitlesWidget: (value, meta) {
                return Text(
                  value.toStringAsFixed(0),
                  style: TextStyle(fontSize: 10, color: t.colorScheme.onSurfaceVariant),
                );
              },
            ),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 24,
              interval: step.toDouble(),
              getTitlesWidget: (value, meta) {
                final idx = value.toInt();
                if (idx < 0 || idx >= history.length) return const SizedBox();
                return Text(
                  history[idx].date.substring(5),
                  style: TextStyle(fontSize: 9, color: t.colorScheme.onSurfaceVariant),
                );
              },
            ),
          ),
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        borderData: FlBorderData(show: false),
        minY: minY - padding,
        maxY: maxY + padding,
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: t.colorScheme.primary,
            barWidth: 2,
            dotData: const FlDotData(show: false),
            belowBarData: BarAreaData(
              show: true,
              color: t.colorScheme.primary.withAlpha(25),
            ),
          ),
        ],
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            getTooltipItems: (spots) => spots.map((s) {
              return LineTooltipItem(
                '${s.y.toStringAsFixed(2)}',
                TextStyle(color: t.colorScheme.onPrimary, fontWeight: FontWeight.w600),
              );
            }).toList(),
          ),
        ),
      ),
    );
  }
}

// ────────────────── Quote Details ──────────────────

class _QuoteCard extends StatelessWidget {
  final QuoteData quote;
  const _QuoteCard({required this.quote});

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final items = <Widget>[];

    void addRow(String label1, String val1, String label2, String val2) {
      items.add(Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Row(
          children: [
            Expanded(child: _InfoTile(label: label1, value: val1)),
            const SizedBox(width: 12),
            Expanded(child: _InfoTile(label: label2, value: val2)),
          ],
        ),
      ));
    }

    if (quote.open != 0 && quote.high != 0) {
      addRow('Open', quote.open.toStringAsFixed(2), 'High', quote.high.toStringAsFixed(2));
    }
    if (quote.volume > 0) {
      addRow('Volume', NumberFormat('#,##0').format(quote.volume), 'Low', quote.low.toStringAsFixed(2));
    }

    if (quote.marketCap != null && quote.marketCap != 0) {
      final mc = '${NumberFormat('#,##0.0').format(quote.marketCap! / 1e9)}B';
      if (quote.peRatio != null && quote.peRatio != 0) {
        addRow('Market Cap', mc, 'P/E Ratio', quote.peRatio!.toStringAsFixed(2));
      } else {
        items.add(_InfoTile(label: 'Market Cap', value: mc));
      }
    } else if (quote.peRatio != null && quote.peRatio != 0) {
      items.add(_InfoTile(label: 'P/E Ratio', value: quote.peRatio!.toStringAsFixed(2)));
    }

    if (items.isEmpty) return const SizedBox();

    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: t.colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Quote Details', style: TextStyle(
              fontSize: 15, fontWeight: FontWeight.w600,
              color: t.colorScheme.onSurface,
            )),
            const SizedBox(height: 16),
            ...items,
          ],
        ),
      ),
    );
  }
}

class _InfoTile extends StatelessWidget {
  final String label;
  final String value;
  const _InfoTile({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: t.colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(fontSize: 11, color: t.colorScheme.onSurfaceVariant)),
          const SizedBox(height: 4),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
        ],
      ),
    );
  }
}

// ────────────────── Analysis / Explanation ──────────────────

class _AnalysisCard extends StatelessWidget {
  final RiskResponse risk;
  const _AnalysisCard({required this.risk});

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final ind = risk.indicators;

    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: t.colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Technical Analysis', style: TextStyle(
              fontSize: 15, fontWeight: FontWeight.w600,
              color: t.colorScheme.onSurface,
            )),
            const SizedBox(height: 16),
            if (ind.rsi != null) _analysisRow(
              'RSI', '${ind.rsi!.toStringAsFixed(1)}',
              ind.rsi! > 70 ? 'Overbought' : ind.rsi! < 30 ? 'Oversold' : 'Neutral',
              ind.rsi! > 70 ? Colors.red : ind.rsi! < 30 ? Colors.green : Colors.orange,
              t,
            ),
            if (ind.macd != null) _analysisRow(
              'MACD', ind.macd!.toUpperCase(),
              ind.macd == 'bullish' ? 'Bullish signal' : 'Bearish signal',
              ind.macd == 'bullish' ? Colors.green : Colors.red,
              t,
            ),
            if (ind.bbPosition != null) _analysisRow(
              'Bollinger', ind.bbPosition!.toUpperCase(),
              ind.bbPosition == 'above' ? 'Price above upper band' : ind.bbPosition == 'below' ? 'Price below lower band' : 'Price in middle band',
              ind.bbPosition == 'above' ? Colors.red : ind.bbPosition == 'below' ? Colors.green : Colors.blue,
              t,
            ),
            if (ind.sma20 != null && ind.sma50 != null) _analysisRow(
              'SMA', '20: ${ind.sma20!.toStringAsFixed(0)} / 50: ${ind.sma50!.toStringAsFixed(0)}',
              ind.sma20! > ind.sma50! ? 'Short-term above long-term' : 'Short-term below long-term',
              ind.sma20! > ind.sma50! ? Colors.green : Colors.red,
              t,
            ),
            if (ind.atrPercent != null) _analysisRow(
              'Volatility', 'ATR ${ind.atrPercent!.toStringAsFixed(1)}%',
              ind.atrPercent! > 5 ? 'High volatility' : ind.atrPercent! > 2 ? 'Moderate volatility' : 'Low volatility',
              ind.atrPercent! > 5 ? Colors.red : ind.atrPercent! > 2 ? Colors.orange : Colors.green,
              t,
            ),
          ],
        ),
      ),
    );
  }

  Widget _analysisRow(String label, String value, String subtitle, Color color, ThemeData t) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Container(
            width: 4,
            height: 32,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(width: 12),
          SizedBox(
            width: 72,
            child: Text(label, style: TextStyle(
              fontWeight: FontWeight.w600, fontSize: 13,
              color: t.colorScheme.onSurface,
            )),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(value, style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13)),
                Text(subtitle, style: TextStyle(fontSize: 11, color: t.colorScheme.onSurfaceVariant)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ────────────────── News ──────────────────

class _NewsSection extends StatelessWidget {
  final List<NewsArticle> news;
  const _NewsSection({required this.news});

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: t.colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text('News & Sentiment', style: TextStyle(
                  fontSize: 15, fontWeight: FontWeight.w600,
                  color: t.colorScheme.onSurface,
                )),
                const Spacer(),
                Text('${news.length} articles',
                    style: TextStyle(fontSize: 12, color: t.colorScheme.onSurfaceVariant)),
              ],
            ),
            const SizedBox(height: 12),
            ...news.take(5).map((article) => _newsItem(article, t)),
          ],
        ),
      ),
    );
  }

  Widget _newsItem(NewsArticle article, ThemeData t) {
    final sentimentColor = switch (article.sentiment) {
      'positive' => Colors.green,
      'negative' => Colors.red,
      _ => Colors.grey,
    };

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            margin: const EdgeInsets.only(top: 4),
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: sentimentColor,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(article.title,
                    style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13)),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Text(article.source,
                        style: TextStyle(fontSize: 11, color: t.colorScheme.onSurfaceVariant)),
                    const SizedBox(width: 8),
                    Text(article.date,
                        style: TextStyle(fontSize: 11, color: t.colorScheme.onSurfaceVariant.withAlpha(150))),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
