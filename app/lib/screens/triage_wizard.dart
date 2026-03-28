// lib/screens/triage_wizard.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/app_theme.dart';
import '../models/patient.dart';
import '../services/providers.dart';
import '../widgets/shared_widgets.dart';

// ─── Step Definition ──────────────────────────────────────────────────────────

class _TriageStep {
  final String question;
  final String subtext;
  final String yesLabel;
  final String noLabel;

  const _TriageStep({
    required this.question,
    required this.subtext,
    this.yesLabel = 'YES',
    this.noLabel  = 'NO',
  });
}

const _steps = [
  _TriageStep(
    question: 'Can the patient walk?',
    subtext:  'Ask them to take a few steps',
  ),
  _TriageStep(
    question: 'Is the patient breathing?',
    subtext:  'Look, listen, feel for breathing',
    yesLabel: 'Breathing',
    noLabel:  'Not breathing',
  ),
  _TriageStep(
    question: 'After airway reposition — is the patient breathing?',
    subtext:  'Jaw thrust / head-tilt performed',
    yesLabel: 'Now breathing',
    noLabel:  'Still not breathing',
  ),
  _TriageStep(
    question: 'Respiratory rate > 30?',
    subtext:  'Count breaths for 15 sec × 4',
  ),
  _TriageStep(
    question: 'Capillary refill > 2 sec OR no radial pulse?',
    subtext:  'Press nail bed 2 sec, check wrist pulse',
  ),
  _TriageStep(
    question: 'Can the patient follow simple commands?',
    subtext:  'Ask to squeeze hand or open eyes',
    yesLabel: 'Can follow',
    noLabel:  'Cannot follow',
  ),
];

// ─── Wizard State ─────────────────────────────────────────────────────────────

class _WizardState {
  final int stepIndex;           // index into _steps
  final TriageAnswers answers;

  const _WizardState({
    this.stepIndex = 0,
    required this.answers,
  });

  _WizardState copyWith({int? stepIndex, TriageAnswers? answers}) =>
      _WizardState(
        stepIndex: stepIndex ?? this.stepIndex,
        answers: answers ?? this.answers,
      );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

class TriageWizardScreen extends ConsumerStatefulWidget {
  const TriageWizardScreen({super.key});

  @override
  ConsumerState<TriageWizardScreen> createState() => _TriageWizardScreenState();
}

class _TriageWizardScreenState extends ConsumerState<TriageWizardScreen> {
  late _WizardState _state;

  @override
  void initState() {
    super.initState();
    _state = _WizardState(answers: TriageAnswers());
  }

  // ── Logic Handlers ──────────────────────────────────────────────────────────

  void _onYes() {
    switch (_state.stepIndex) {
      case 0: // Can walk → MINOR
        _state.answers.canWalk = true;
        _assign(TriageCategory.minor);
        break;
      case 1: // Breathing → continue to step 3 (RR)
        _state.answers.breathing = true;
        _state.answers.airwayReposition = false;
        setState(() => _state = _state.copyWith(stepIndex: 3));
        break;
      case 2: // After reposition, now breathing → IMMEDIATE
        _state.answers.breathing = true;
        _state.answers.airwayReposition = true;
        _assign(TriageCategory.immediate);
        break;
      case 3: // RR > 30 → IMMEDIATE
        _state.answers.rrOver30 = true;
        _assign(TriageCategory.immediate);
        break;
      case 4: // Perfusion abnormal → IMMEDIATE
        _state.answers.perfusionAbnormal = true;
        _assign(TriageCategory.immediate);
        break;
      case 5: // Follows commands → DELAYED
        _state.answers.mentalStatus = 'obeys';
        _assign(TriageCategory.delayed);
        break;
    }
  }

  void _onNo() {
    switch (_state.stepIndex) {
      case 0: // Cannot walk → step 1 (breathing)
        _state.answers.canWalk = false;
        setState(() => _state = _state.copyWith(stepIndex: 1));
        break;
      case 1: // Not breathing → step 2 (reposition)
        _state.answers.breathing = false;
        setState(() => _state = _state.copyWith(stepIndex: 2));
        break;
      case 2: // After reposition still not breathing → MORGUE
        _state.answers.airwayReposition = true;
        _assign(TriageCategory.morgue);
        break;
      case 3: // RR normal → step 4 (perfusion)
        _state.answers.rrOver30 = false;
        setState(() => _state = _state.copyWith(stepIndex: 4));
        break;
      case 4: // Perfusion normal → step 5 (mental)
        _state.answers.perfusionAbnormal = false;
        setState(() => _state = _state.copyWith(stepIndex: 5));
        break;
      case 5: // Cannot follow commands → IMMEDIATE
        _state.answers.mentalStatus = 'no_obey';
        _assign(TriageCategory.immediate);
        break;
    }
  }

  void _goBack() {
    // Map back step transitions
    final backMap = {2: 1, 3: 1, 4: 3, 5: 4};
    final prev = backMap[_state.stepIndex] ?? _state.stepIndex - 1;
    setState(() => _state = _state.copyWith(stepIndex: prev < 0 ? 0 : prev));
  }

  Future<void> _assign(TriageCategory category) async {
    final patient = ref.read(activePatientProvider);
    if (patient == null) return;

    final updated = Patient(
      id: patient.id,
      timestamp: patient.timestamp,
      triage: category,
      triageTime: DateTime.now(),
      triageAnswers: _state.answers,
      exposure: patient.exposure,
      sludge: patient.sludge,
      injuryTypes: patient.injuryTypes,
      autoInjector: patient.autoInjector,
      info: patient.info,
      vitals: patient.vitals,
      treatments: patient.treatments,
      bodyZones: patient.bodyZones,
    );
    await ref.read(patientListProvider.notifier).save(updated);
    ref.read(activePatientProvider.notifier).state = updated;

    if (mounted) Navigator.pushReplacementNamed(context, '/result');
  }

  // ── Visual progress bar ─────────────────────────────────────────────────────

  // Logical steps for display: 0,1,2,3,4 → map internal 2 as still step 1
  double get _progressFraction {
    const progressMap = {0: 0.1, 1: 0.3, 2: 0.3, 3: 0.5, 4: 0.7, 5: 0.9};
    return progressMap[_state.stepIndex] ?? 0.1;
  }

  // ── Build ───────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final patient = ref.watch(activePatientProvider);
    final step = _steps[_state.stepIndex];

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [

            // ── Progress Header ────────────────────────────────────────────
            Container(
              color: AppColors.surface,
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'START TRIAGE',
                        style: TextStyle(
                          color: AppColors.accent,
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.5,
                        ),
                      ),
                      Text(
                        patient != null ? '${patient.id} · ${fmtTime(patient.timestamp)}' : '',
                        style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: TweenAnimationBuilder<double>(
                      tween: Tween(end: _progressFraction),
                      duration: const Duration(milliseconds: 300),
                      builder: (ctx, val, __) => LinearProgressIndicator(
                        value: val,
                        minHeight: 6,
                        backgroundColor: AppColors.border,
                        valueColor:
                            const AlwaysStoppedAnimation<Color>(AppColors.accent),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // ── Question ───────────────────────────────────────────────────
            Expanded(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 36, 20, 0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      step.question,
                      style: const TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.w800,
                        color: Colors.white,
                        height: 1.2,
                        letterSpacing: -0.3,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      step.subtext,
                      style: const TextStyle(
                        fontSize: 17,
                        color: AppColors.textSecondary,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 48),
                    BigButton(
                      label: step.yesLabel,
                      color: AppColors.green,
                      onTap: _onYes,
                    ),
                    const SizedBox(height: 16),
                    BigButton(
                      label: step.noLabel,
                      color: AppColors.accent,
                      onTap: _onNo,
                    ),
                  ],
                ),
              ),
            ),

            // ── Back button ────────────────────────────────────────────────
            if (_state.stepIndex > 0)
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
                child: GestureDetector(
                  onTap: _goBack,
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    decoration: BoxDecoration(
                      border: Border.all(color: AppColors.border),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    alignment: Alignment.center,
                    child: const Text(
                      '← Back',
                      style: TextStyle(color: AppColors.textMuted, fontSize: 16),
                    ),
                  ),
                ),
              )
            else
              const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}
