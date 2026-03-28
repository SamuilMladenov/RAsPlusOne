// lib/screens/home_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/app_theme.dart';
import '../models/patient.dart';
import '../services/providers.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final patients = ref.watch(patientListProvider);
    final counts   = ref.watch(categoryCountsProvider);

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 28),
              const Text(
                'MASS CASUALTY',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 11, fontWeight: FontWeight.w700,
                  letterSpacing: 4, color: AppColors.accent,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'Triage System',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: 32, fontWeight: FontWeight.w800,
                  color: Colors.white, letterSpacing: -0.8,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'START Protocol · Offline First',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 13, color: AppColors.textMuted),
              ),
              if (patients.isNotEmpty) ...[
                const SizedBox(height: 24),
                Row(
                  children: [
                    _CountCard('IMMED',   counts[TriageCategory.immediate] ?? 0, TriageColors.immediate),
                    const SizedBox(width: 8),
                    _CountCard('DELAYED', counts[TriageCategory.delayed]   ?? 0, TriageColors.delayed),
                    const SizedBox(width: 8),
                    _CountCard('MINOR',   counts[TriageCategory.minor]     ?? 0, TriageColors.minor),
                    const SizedBox(width: 8),
                    _CountCard('MORGUE',  counts[TriageCategory.morgue]    ?? 0, TriageColors.morgue),
                  ],
                ),
              ],
              const SizedBox(height: 28),
              Expanded(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Expanded(
                      child: _SquareButton(
                        label: '+ New\nPatient',
                        sublabel: 'START Triage',
                        color: AppColors.accent,
                        onTap: () async {
                          final patient = await ref.read(patientListProvider.notifier).createNew();
                          if (context.mounted) {
                            ref.read(activePatientProvider.notifier).state = patient;
                            Navigator.pushNamed(context, '/triage');
                          }
                        },
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: _SquareButton(
                        label: 'Patient\nList',
                        sublabel: '${patients.length} recorded',
                        color: AppColors.surface2,
                        onTap: () => Navigator.pushNamed(context, '/list'),
                      ),
                    ),
                  ],
                ),
              ),
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 20),
                child: Text(
                  'All data stored locally · No internet required',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: AppColors.textMuted, fontSize: 12),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SquareButton extends StatefulWidget {
  final String label;
  final String sublabel;
  final Color color;
  final VoidCallback onTap;
  const _SquareButton({required this.label, required this.sublabel, required this.color, required this.onTap});

  @override
  State<_SquareButton> createState() => _SquareButtonState();
}

class _SquareButtonState extends State<_SquareButton> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 80));
    _scale = Tween(begin: 1.0, end: 0.95).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOut));
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _ctrl.forward(),
      onTapUp: (_) { _ctrl.reverse(); widget.onTap(); },
      onTapCancel: () => _ctrl.reverse(),
      child: AnimatedBuilder(
        animation: _scale,
        builder: (_, child) => Transform.scale(scale: _scale.value, child: child),
        child: Container(
          decoration: BoxDecoration(
            color: widget.color,
            borderRadius: BorderRadius.circular(20),
            boxShadow: [BoxShadow(color: widget.color.withValues(alpha: 0.35), blurRadius: 20, offset: const Offset(0, 6))],
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(widget.label, textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w900, color: Colors.white, height: 1.15, letterSpacing: -0.5)),
              const SizedBox(height: 10),
              Text(widget.sublabel, textAlign: TextAlign.center,
                style: TextStyle(fontSize: 14, color: Colors.white.withValues(alpha: 0.7), fontWeight: FontWeight.w500)),
            ],
          ),
        ),
      ),
    );
  }
}

class _CountCard extends StatelessWidget {
  final String label;
  final int count;
  final Color color;
  const _CountCard(this.label, this.count, this.color);

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(12)),
        child: Column(
          children: [
            Text('$count', style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w900, color: Colors.white)),
            Text(label, style: const TextStyle(fontSize: 8, fontWeight: FontWeight.w700, color: Colors.white70, letterSpacing: 0.5)),
          ],
        ),
      ),
    );
  }
}
