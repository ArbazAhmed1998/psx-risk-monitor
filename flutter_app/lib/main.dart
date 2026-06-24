import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/stock_provider.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => StockProvider(),
      child: MaterialApp(
        title: 'PSX Monitor',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorSchemeSeed: const Color(0xFF1A237E),
          useMaterial3: true,
          brightness: Brightness.light,
          appBarTheme: const AppBarTheme(centerTitle: true),
          cardTheme: const CardThemeData(elevation: 0),
        ),
        darkTheme: ThemeData(
          colorSchemeSeed: const Color(0xFF1A237E),
          useMaterial3: true,
          brightness: Brightness.dark,
          appBarTheme: const AppBarTheme(centerTitle: true),
          cardTheme: const CardThemeData(elevation: 0),
        ),
        home: const HomeScreen(),
      ),
    );
  }
}
