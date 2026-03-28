// lib/screens/patient_list.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/app_theme.dart';
import '../models/patient.dart';
import '../services/providers.dart';
import '../widgets/shared_widgets.dart';

class PatientListScreen extends ConsumerStatefulWidget {
  const PatientListScreen({super.key});

  @override
  ConsumerState<PatientListScreen> createState() => _PatientListScreenState();
}

class _PatientListScreenState extends ConsumerState<PatientListScreen> {
  TriageCategory? _filter; // null = show all

  @override
  Widget build(BuildContext context) {
    final all = ref.watch(patientListProvider);
    final filtered = _filter == null
        ? all
        : all.where((p) => p.triage == _filter).toList();

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [

            // ── Header ──────────────────────────────────────────────────────
            Container(
              color: AppColors.surface,
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),
              child: Row(
                children: [
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: const Text('←',
                        style: TextStyle(color: AppColors.accent, fontSize: 24)),
                  ),
                  const SizedBox(width: 16),
                  const Text('Patient Log',
                      style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                          color: Colors.white)),
                  const Spacer(),
                  Text('${all.length} total',
                      style: const TextStyle(
                          color: AppColors.textMuted, fontSize: 14)),
                ],
              ),
            ),

            // ── Filter Pills ─────────────────────────────────────────────────
            Container(
              color: AppColors.surface,
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _FilterPill('ALL', _filter == null, AppColors.accent,
                        () => setState(() => _filter = null)),
                    ...TriageCategory.values.map((cat) {
                      final info = triageInfoFor(cat)!;
                      return _FilterPill(
                        info.label,
                        _filter == cat,
                        info.color,
                        () => setState(() => _filter = cat),
                      );
                    }),
                  ],
                ),
              ),
            ),

            // ── List ─────────────────────────────────────────────────────────
            Expanded(
              child: filtered.isEmpty
                  ? const Center(
                      child: Text('No patients in this category',
                          style: TextStyle(color: AppColors.textMuted, fontSize: 17)),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                      itemCount: filtered.length,
                      itemBuilder: (ctx, i) => _PatientCard(
                        patient: filtered[i],
                        onTap: () {
                          ref.read(activePatientProvider.notifier).state =
                              filtered[i];
                          Navigator.pushNamed(context, '/detail');
                        },
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Filter Pill ──────────────────────────────────────────────────────────────
class _FilterPill extends StatelessWidget {
  final String label;
  final bool active;
  final Color color;
  final VoidCallback onTap;

  const _FilterPill(this.label, this.active, this.color, this.onTap);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: 6),
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: active ? color : Colors.transparent,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: active ? Colors.transparent : AppColors.border),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: active ? Colors.white : AppColors.textMuted,
              fontSize: 13,
              fontWeight: active ? FontWeight.w700 : FontWeight.w400,
            ),
          ),
        ),
      ),
    );
  }
}

// ─── Patient Card ─────────────────────────────────────────────────────────────
class _PatientCard extends StatelessWidget {
  final Patient patient;
  final VoidCallback onTap;

  const _PatientCard({required this.patient, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final info = triageInfoFor(patient.triage);

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border, width: 0.5),
        ),
        child: Row(
          children: [
            // Badge
            if (info != null)
              TriageBadge(shortCode: info.shortCode, color: info.color)
            else
              Container(
                width: 56, height: 56,
                decoration: BoxDecoration(
                  color: AppColors.border,
                  borderRadius: BorderRadius.circular(14),
                ),
                alignment: Alignment.center,
                child: const Text('?',
                    style: TextStyle(fontSize: 22, color: Colors.white54)),
              ),

            const SizedBox(width: 16),

            // Details
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    patient.id,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                      letterSpacing: 1,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    fmtDate(patient.timestamp),
                    style: const TextStyle(
                        color: AppColors.textMuted, fontSize: 13),
                  ),
                  if (patient.info.sex != null ||
                      patient.info.agePreset != null ||
                      patient.info.age != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      [
                        patient.info.sex,
                        patient.info.agePreset ??
                            (patient.info.age != null
                                ? 'Age ${patient.info.age}'
                                : null),
                      ].whereType<String>().join(' · '),
                      style: const TextStyle(
                          color: AppColors.textMuted, fontSize: 12),
                    ),
                  ],
                ],
              ),
            ),

            // Right info
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  info?.label ?? 'Pending',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: info?.color ?? AppColors.textMuted,
                  ),
                ),
                if (patient.vitals.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    '${patient.vitals.length} vitals',
                    style: const TextStyle(
                        color: AppColors.textMuted, fontSize: 11),
                  ),
                ],
                if (patient.treatments.isNotEmpty) ...[
                  const SizedBox(height: 2),
                  Text(
                    '${patient.treatments.length} tx',
                    style: const TextStyle(
                        color: AppColors.textMuted, fontSize: 11),
                  ),
                ],
              ],
            ),

            const SizedBox(width: 4),
            const Icon(Icons.chevron_right, color: AppColors.textMuted, size: 20),
          ],
        ),
      ),
    );
  }
}
