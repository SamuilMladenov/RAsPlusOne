// lib/screens/home_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/app_theme.dart';
import '../models/patient.dart';
import '../services/providers.dart';
import '../widgets/shared_widgets.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final patients = ref.watch(patientListProvider);
    final counts   = ref.watch(categoryCountsProvider);

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── Header ──────────────────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 28, 20, 0),
              child: Column(
                children: [
                  Text(
                    'MASS CASUALTY',
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 4,
                      color: AppColors.accent,
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Triage System',
                    style: TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                      letterSpacing: -0.8,
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'START Protocol · Offline First',
                    style: TextStyle(fontSize: 13, color: AppColors.textMuted),
                  ),
                ],
              ),
            ),

            // ── Category Counters ────────────────────────────────────────────
            if (patients.isNotEmpty)
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
                child: Row(
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
              ),

            // ── Buttons ──────────────────────────────────────────────────────
            Expanded(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 28, 20, 0),
                child: Column(
                  children: [
                    BigButton(
                      label: '+ New Patient',
                      sublabel: 'START Rapid Triage',
                      color: AppColors.accent,
                      onTap: () async {
                        final patient =
                            await ref.read(patientListProvider.notifier).createNew();
                        if (context.mounted) {
                          ref.read(activePatientProvider.notifier).state = patient;
                          Navigator.pushNamed(context, '/triage');
                        }
                      },
                    ),
                    const SizedBox(height: 14),
                    BigButton(
                      label: 'Patient List',
                      sublabel: '${patients.length} patient${patients.length != 1 ? "s" : ""} recorded',
                      color: AppColors.surface2,
                      onTap: () => Navigator.pushNamed(context, '/list'),
                    ),
                  ],
                ),
              ),
            ),

            // ── Footer ───────────────────────────────────────────────────────
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 24),
              child: Text(
                'All data stored locally · No internet required',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.textMuted, fontSize: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Count Card ───────────────────────────────────────────────────────────────

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
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            Text(
              '$count',
              style: const TextStyle(
                fontSize: 26,
                fontWeight: FontWeight.w900,
                color: Colors.white,
              ),
            ),
            Text(
              label,
              style: const TextStyle(
                fontSize: 8,
                fontWeight: FontWeight.w700,
                color: Colors.white70,
                letterSpacing: 0.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
