// lib/screens/triage_wizard.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/app_theme.dart';
import '../models/patient.dart';
import '../services/providers.dart';
import '../widgets/shared_widgets.dart';

class _TriageStep {
  final String question;
  final String subtext;
  final String yesLabel;
  final String noLabel;
  const _TriageStep({required this.question, required this.subtext, this.yesLabel = 'YES', this.noLabel = 'NO'});
}

const _steps = [
  _TriageStep(question: 'Can the patient walk?',                             subtext: 'Ask them to take a few steps'),
  _TriageStep(question: 'Is the patient breathing?',                         subtext: 'Look, listen, feel for breathing',               yesLabel: 'Breathing',      noLabel: 'Not breathing'),
  _TriageStep(question: 'After airway reposition — is the patient breathing?',subtext: 'Jaw thrust / head-tilt performed',               yesLabel: 'Now breathing',  noLabel: 'Still not breathing'),
  _TriageStep(question: 'Respiratory rate > 30?',                            subtext: 'Count breaths for 15 sec × 4'),
  _TriageStep(question: 'Capillary refill > 2 sec OR no radial pulse?',      subtext: 'Press nail bed 2 sec, check wrist pulse'),
  _TriageStep(question: 'Can the patient follow simple commands?',            subtext: 'Ask to squeeze hand or open eyes',               yesLabel: 'Can follow',     noLabel: 'Cannot follow'),
];

class _WizardState {
  final int stepIndex;
  final TriageAnswers answers;
  const _WizardState({this.stepIndex = 0, required this.answers});
  _WizardState copyWith({int? stepIndex, TriageAnswers? answers}) =>
      _WizardState(stepIndex: stepIndex ?? this.stepIndex, answers: answers ?? this.answers);
}

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

  void _onYes() {
    switch (_state.stepIndex) {
      case 0: _state.answers.canWalk = true;               _assign(TriageCategory.minor);     break;
      case 1: _state.answers.breathing = true; _state.answers.airwayReposition = false; setState(() => _state = _state.copyWith(stepIndex: 3)); break;
      case 2: _state.answers.breathing = true; _state.answers.airwayReposition = true;  _assign(TriageCategory.immediate); break;
      case 3: _state.answers.rrOver30 = true;              _assign(TriageCategory.immediate); break;
      case 4: _state.answers.perfusionAbnormal = true;     _assign(TriageCategory.immediate); break;
      case 5: _state.answers.mentalStatus = 'obeys';       _assign(TriageCategory.delayed);   break;
    }
  }

  void _onNo() {
    switch (_state.stepIndex) {
      case 0: _state.answers.canWalk = false;              setState(() => _state = _state.copyWith(stepIndex: 1)); break;
      case 1: _state.answers.breathing = false;            setState(() => _state = _state.copyWith(stepIndex: 2)); break;
      case 2: _state.answers.airwayReposition = true;      _assign(TriageCategory.morgue);    break;
      case 3: _state.answers.rrOver30 = false;             setState(() => _state = _state.copyWith(stepIndex: 4)); break;
      case 4: _state.answers.perfusionAbnormal = false;    setState(() => _state = _state.copyWith(stepIndex: 5)); break;
      case 5: _state.answers.mentalStatus = 'no_obey';     _assign(TriageCategory.immediate); break;
    }
  }

  void _goBack() {
    final backMap = {2: 1, 3: 1, 4: 3, 5: 4};
    final prev = backMap[_state.stepIndex] ?? _state.stepIndex - 1;
    setState(() => _state = _state.copyWith(stepIndex: prev < 0 ? 0 : prev));
  }

  Future<void> _assign(TriageCategory category) async {
    final patient = ref.read(activePatientProvider);
    if (patient == null) return;
    final updated = Patient(
      id: patient.id, timestamp: patient.timestamp,
      triage: category, triageTime: DateTime.now(), triageAnswers: _state.answers,
      exposure: patient.exposure, sludge: patient.sludge, injuryTypes: patient.injuryTypes,
      autoInjector: patient.autoInjector, info: patient.info,
      vitals: patient.vitals, treatments: patient.treatments, bodyZones: patient.bodyZones,
    );
    await ref.read(patientListProvider.notifier).save(updated);
    ref.read(activePatientProvider.notifier).state = updated;
    if (mounted) Navigator.pushReplacementNamed(context, '/result');
  }

  double get _progressFraction {
    const progressMap = {0: 0.1, 1: 0.3, 2: 0.3, 3: 0.5, 4: 0.7, 5: 0.9};
    return progressMap[_state.stepIndex] ?? 0.1;
  }

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
                      const Text('START TRIAGE',
                        style: TextStyle(color: AppColors.accent, fontSize: 12, fontWeight: FontWeight.w700, letterSpacing: 1.5)),
                      Text(patient != null ? '${patient.id} · ${fmtTime(patient.timestamp)}' : '',
                        style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                    ],
                  ),
                  const SizedBox(height: 10),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: TweenAnimationBuilder<double>(
                      tween: Tween(end: _progressFraction),
                      duration: const Duration(milliseconds: 300),
                      builder: (ctx, val, __) => LinearProgressIndicator(
                        value: val, minHeight: 6,
                        backgroundColor: AppColors.border,
                        valueColor: const AlwaysStoppedAnimation<Color>(AppColors.accent),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // ── Question ───────────────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 32, 20, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(step.question,
                    style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800,
                        color: Colors.white, height: 1.2, letterSpacing: -0.3)),
                  const SizedBox(height: 10),
                  Text(step.subtext,
                    style: const TextStyle(fontSize: 17, color: AppColors.textSecondary, height: 1.4)),
                ],
              ),
            ),

            // ── YES / NO — big square buttons side by side ─────────────────
            Expanded(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 0),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Expanded(child: _AnswerButton(label: step.yesLabel, color: AppColors.green,  onTap: _onYes)),
                    const SizedBox(width: 16),
                    Expanded(child: _AnswerButton(label: step.noLabel,  color: AppColors.accent, onTap: _onNo)),
                  ],
                ),
              ),
            ),

            // ── Back ───────────────────────────────────────────────────────
            if (_state.stepIndex > 0)
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
                child: GestureDetector(
                  onTap: _goBack,
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    decoration: BoxDecoration(border: Border.all(color: AppColors.border), borderRadius: BorderRadius.circular(12)),
                    alignment: Alignment.center,
                    child: const Text('← Back', style: TextStyle(color: AppColors.textMuted, fontSize: 16)),
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

// ─── Large square answer button ────────────────────────────────────────────────
class _AnswerButton extends StatefulWidget {
  final String label;
  final Color color;
  final VoidCallback onTap;
  const _AnswerButton({required this.label, required this.color, required this.onTap});

  @override
  State<_AnswerButton> createState() => _AnswerButtonState();
}

class _AnswerButtonState extends State<_AnswerButton> with SingleTickerProviderStateMixin {
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
            boxShadow: [BoxShadow(color: widget.color.withValues(alpha: 0.4), blurRadius: 20, offset: const Offset(0, 6))],
          ),
          alignment: Alignment.center,
          child: Text(widget.label,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: -0.3)),
        ),
      ),
    );
  }
}
