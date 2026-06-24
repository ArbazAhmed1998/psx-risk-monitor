import 'package:flutter/material.dart';

class RiskBadge extends StatelessWidget {
  final String riskLevel;
  final double riskScore;
  final double size;

  const RiskBadge({
    super.key,
    required this.riskLevel,
    required this.riskScore,
    this.size = 16,
  });

  Color get _color {
    switch (riskLevel) {
      case 'LOW':
        return Colors.green;
      case 'MEDIUM':
        return Colors.orange;
      case 'HIGH':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  IconData get _icon {
    switch (riskLevel) {
      case 'LOW':
        return Icons.check_circle;
      case 'MEDIUM':
        return Icons.warning_amber_rounded;
      case 'HIGH':
        return Icons.cancel;
      default:
        return Icons.help;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: 'Risk Score: ${riskScore.toStringAsFixed(0)}/100',
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(_icon, color: _color, size: size),
          const SizedBox(width: 4),
          Text(
            riskLevel,
            style: TextStyle(
              color: _color,
              fontWeight: FontWeight.bold,
              fontSize: size * 0.9,
            ),
          ),
        ],
      ),
    );
  }
}
