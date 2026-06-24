import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../providers/stock_provider.dart';
import '../models/stock_models.dart';
import 'detail_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<StockProvider>().loadStocks();
    });
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('PSX Monitor'),
        centerTitle: true,
      ),
      body: Consumer<StockProvider>(
        builder: (context, provider, _) {
          if (provider.isLoading && provider.stocks.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }
          if (provider.error != null && provider.stocks.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.cloud_off, size: 48, color: t.colorScheme.error),
                  const SizedBox(height: 16),
                  Text(provider.error!, style: t.textTheme.bodyMedium),
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    onPressed: () => provider.loadStocks(),
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry'),
                  ),
                ],
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () => provider.loadStocks(),
            child: ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
              itemCount: provider.stocks.length,
              itemBuilder: (context, index) {
                final stock = provider.stocks[index];
                return _StockCard(stock: stock);
              },
            ),
          );
        },
      ),
    );
  }
}

class _StockCard extends StatelessWidget {
  final StockInfo stock;
  const _StockCard({required this.stock});

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final isUp = stock.change >= 0;
    final changeColor = isUp ? Colors.green.shade600 : Colors.red.shade600;

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: t.colorScheme.outlineVariant),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => DetailScreen(symbol: stock.symbol),
            ),
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: t.colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(12),
                ),
                alignment: Alignment.center,
                child: Text(
                  stock.symbol.substring(0, 2),
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: t.colorScheme.onPrimaryContainer,
                    fontSize: 16,
                  ),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Text(
                          stock.symbol,
                          style: const TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 15,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: t.colorScheme.surfaceContainerHighest,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            stock.sector,
                            style: TextStyle(
                              fontSize: 10,
                              color: t.colorScheme.onSurfaceVariant,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Text(
                      stock.name,
                      style: TextStyle(
                        fontSize: 12,
                        color: t.colorScheme.onSurfaceVariant,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    'PKR ${NumberFormat('#,##0.00').format(stock.price)}',
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 15,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: changeColor.withAlpha(25),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          isUp ? Icons.trending_up : Icons.trending_down,
                          size: 14,
                          color: changeColor,
                        ),
                        const SizedBox(width: 2),
                        Text(
                          '${isUp ? '+' : ''}${stock.changePercent.toStringAsFixed(2)}%',
                          style: TextStyle(
                            color: changeColor,
                            fontWeight: FontWeight.w600,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 4),
              Icon(Icons.chevron_right, color: t.colorScheme.onSurfaceVariant),
            ],
          ),
        ),
      ),
    );
  }
}
