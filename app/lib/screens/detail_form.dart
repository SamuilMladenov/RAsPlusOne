// lib/screens/detail_form.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/app_theme.dart';
import '../models/patient.dart';
import '../services/providers.dart';
import '../widgets/shared_widgets.dart';
import '../widgets/body_diagram.dart';

// ─── Tab labels ───────────────────────────────────────────────────────────────
const _tabs = ['Exposure', 'SLUDGE', 'Injuries', 'Body', 'Vitals', 'Patient', 'Treatment'];

class DetailFormScreen extends ConsumerStatefulWidget {
  const DetailFormScreen({super.key});

  @override
  ConsumerState<DetailFormScreen> createState() => _DetailFormScreenState();
}

class _DetailFormScreenState extends ConsumerState<DetailFormScreen>
    with TickerProviderStateMixin {
  late TabController _tabCtrl;

  // ── Vitals form state ──────────────────────────────────────────────────────
  final _pulseCtrl = TextEditingController();
  final _rrCtrl    = TextEditingController();
  final _bpCtrl    = TextEditingController();

  // ── Treatment form state ───────────────────────────────────────────────────
  final _drugCtrl  = TextEditingController();
  final _doseCtrl  = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: _tabs.length, vsync: this);
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    _pulseCtrl.dispose();
    _rrCtrl.dispose();
    _bpCtrl.dispose();
    _drugCtrl.dispose();
    _doseCtrl.dispose();
    super.dispose();
  }

  // ── Save helpers ───────────────────────────────────────────────────────────

  Future<void> _save(Patient updated) async {
    await ref.read(patientListProvider.notifier).save(updated);
    ref.read(activePatientProvider.notifier).state = updated;
  }

  // ── Build ──────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final patient = ref.watch(activePatientProvider);
    if (patient == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final info = triageInfoFor(patient.triage);

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: Column(
          children: [

            // ── Sticky Header ─────────────────────────────────────────────
            Container(
              color: info?.color ?? AppColors.surface,
              padding: const EdgeInsets.fromLTRB(20, 14, 20, 14),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Patient ${patient.id}',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.white.withValues(alpha: 0.7),
                          ),
                        ),
                        Text(
                          '${info?.label ?? "—"} · ${info?.tag ?? ""}',
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w800,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                  GestureDetector(
                    onTap: () => Navigator.pushNamedAndRemoveUntil(
                        context, '/', (r) => false),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 10),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.25),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Text('Done ✓',
                          style: TextStyle(
                              color: Colors.white,
                              fontSize: 15,
                              fontWeight: FontWeight.w700)),
                    ),
                  ),
                ],
              ),
            ),

            // ── Tab Bar ───────────────────────────────────────────────────
            Container(
              color: AppColors.surface,
              child: TabBar(
                controller: _tabCtrl,
                isScrollable: true,
                tabAlignment: TabAlignment.start,
                indicatorColor: AppColors.accent,
                indicatorWeight: 2,
                labelColor: Colors.white,
                unselectedLabelColor: AppColors.textMuted,
                labelStyle: const TextStyle(
                    fontSize: 14, fontWeight: FontWeight.w700),
                unselectedLabelStyle: const TextStyle(
                    fontSize: 14, fontWeight: FontWeight.w400),
                tabs: _tabs.map((t) => Tab(text: t)).toList(),
              ),
            ),

            // ── Tab Content ───────────────────────────────────────────────
            Expanded(
              child: TabBarView(
                controller: _tabCtrl,
                children: [
                  _ExposureTab(patient: patient, onSave: _save),
                  _SludgeTab(patient: patient, onSave: _save),
                  _InjuriesTab(patient: patient, onSave: _save),
                  _BodyTab(patient: patient, onSave: _save),
                  _VitalsTab(
                    patient: patient,
                    onSave: _save,
                    pulseCtrl: _pulseCtrl,
                    rrCtrl: _rrCtrl,
                    bpCtrl: _bpCtrl,
                  ),
                  _PatientInfoTab(patient: patient, onSave: _save),
                  _TreatmentTab(
                    patient: patient,
                    onSave: _save,
                    drugCtrl: _drugCtrl,
                    doseCtrl: _doseCtrl,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Helper: scrollable tab body ─────────────────────────────────────────────
Widget _tabBody(List<Widget> children) => ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
      children: children,
    );

// ─── Exposure Tab ─────────────────────────────────────────────────────────────
class _ExposureTab extends StatelessWidget {
  final Patient patient;
  final Future<void> Function(Patient) onSave;
  const _ExposureTab({required this.patient, required this.onSave});

  @override
  Widget build(BuildContext context) {
    return _tabBody([
      const SectionHeader('Exposure Type'),
      ChipGroup(
        options: kExposureTypes,
        selected: patient.exposure.types,
        onToggle: (t) {
          final types = List<String>.from(patient.exposure.types);
          types.contains(t) ? types.remove(t) : types.add(t);
          patient.exposure.types
            ..clear()
            ..addAll(types);
          onSave(patient);
        },
      ),
      const SizedBox(height: 24),
      ToggleRow(
        label: 'Gross Decontamination Performed',
        value: patient.exposure.decon,
        onChange: (v) => onSave(patient..exposure.decon = v),
      ),
      ToggleRow(
        label: 'Secondary Decontamination Performed',
        value: patient.exposure.secondaryDecon,
        onChange: (v) => onSave(patient..exposure.secondaryDecon = v),
      ),
    ]);
  }
}

// ─── SLUDGE Tab ───────────────────────────────────────────────────────────────
class _SludgeTab extends StatelessWidget {
  final Patient patient;
  final Future<void> Function(Patient) onSave;
  const _SludgeTab({required this.patient, required this.onSave});

  @override
  Widget build(BuildContext context) {
    return _tabBody([
      const SectionHeader('SLUDGE Symptoms'),
      ChipGroup(
        options: kSludgeSymptoms,
        selected: patient.sludge,
        onToggle: (s) {
          final list = List<String>.from(patient.sludge);
          list.contains(s) ? list.remove(s) : list.add(s);
          patient.sludge
            ..clear()
            ..addAll(list);
          onSave(patient);
        },
      ),
    ]);
  }
}

// ─── Injuries Tab ─────────────────────────────────────────────────────────────
class _InjuriesTab extends StatelessWidget {
  final Patient patient;
  final Future<void> Function(Patient) onSave;
  const _InjuriesTab({required this.patient, required this.onSave});

  @override
  Widget build(BuildContext context) {
    return _tabBody([
      const SectionHeader('Mechanism / Injury Type'),
      ChipGroup(
        options: kInjuryTypes,
        selected: patient.injuryTypes,
        onToggle: (s) {
          final list = List<String>.from(patient.injuryTypes);
          list.contains(s) ? list.remove(s) : list.add(s);
          patient.injuryTypes
            ..clear()
            ..addAll(list);
          onSave(patient);
        },
      ),
      const SizedBox(height: 28),
      const SectionHeader('Auto-Injector'),
      ToggleRow(
        label: 'Auto-injector used',
        value: patient.autoInjector.used,
        onChange: (v) => onSave(patient..autoInjector.used = v),
      ),
      if (patient.autoInjector.used) ...[
        const SizedBox(height: 16),
        const Text('Doses administered',
            style: TextStyle(color: AppColors.textSecondary, fontSize: 15)),
        const SizedBox(height: 12),
        Row(
          children: List.generate(5, (i) {
            final n = i + 1;
            final sel = patient.autoInjector.dose == n;
            return Padding(
              padding: EdgeInsets.only(right: i < 4 ? 8 : 0),
              child: GestureDetector(
                onTap: () => onSave(patient..autoInjector.dose = n),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 120),
                  width: 52, height: 52,
                  decoration: BoxDecoration(
                    color: sel ? AppColors.accent : Colors.transparent,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                        color: sel ? AppColors.accent : AppColors.border,
                        width: 2),
                  ),
                  alignment: Alignment.center,
                  child: Text('$n',
                      style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w800,
                          color: sel ? Colors.white : AppColors.textSecondary)),
                ),
              ),
            );
          }),
        ),
      ],
    ]);
  }
}

// ─── Body Tab ─────────────────────────────────────────────────────────────────
class _BodyTab extends StatelessWidget {
  final Patient patient;
  final Future<void> Function(Patient) onSave;
  const _BodyTab({required this.patient, required this.onSave});

  @override
  Widget build(BuildContext context) {
    return _tabBody([
      BodyDiagram(
        entries: patient.bodyZones,
        onChange: (zones) {
          patient.bodyZones
            ..clear()
            ..addAll(zones);
          onSave(patient);
        },
      ),
    ]);
  }
}

// ─── Vitals Tab ───────────────────────────────────────────────────────────────
class _VitalsTab extends StatelessWidget {
  final Patient patient;
  final Future<void> Function(Patient) onSave;
  final TextEditingController pulseCtrl, rrCtrl, bpCtrl;

  const _VitalsTab({
    required this.patient,
    required this.onSave,
    required this.pulseCtrl,
    required this.rrCtrl,
    required this.bpCtrl,
  });

  void _addVital() {
    if (pulseCtrl.text.isEmpty && rrCtrl.text.isEmpty && bpCtrl.text.isEmpty) return;
    final entry = VitalEntry(
      timestamp: DateTime.now(),
      pulse: pulseCtrl.text.isEmpty ? null : pulseCtrl.text,
      rr:    rrCtrl.text.isEmpty    ? null : rrCtrl.text,
      bp:    bpCtrl.text.isEmpty    ? null : bpCtrl.text,
    );
    pulseCtrl.clear(); rrCtrl.clear(); bpCtrl.clear();
    onSave(patient..vitals.add(entry));
  }

  @override
  Widget build(BuildContext context) {
    return _tabBody([
      const SectionHeader('New Vital Signs'),
      AppInput(controller: pulseCtrl, placeholder: '—', label: 'Pulse (bpm)',
          keyboardType: TextInputType.number),
      const SizedBox(height: 12),
      AppInput(controller: rrCtrl, placeholder: '—', label: 'Respiratory Rate',
          keyboardType: TextInputType.number),
      const SizedBox(height: 12),
      AppInput(controller: bpCtrl, placeholder: '—', label: 'Blood Pressure'),
      const SizedBox(height: 16),
      BigButton(label: 'Record Vitals', color: AppColors.green, onTap: _addVital),
      if (patient.vitals.isNotEmpty) ...[
        const SizedBox(height: 28),
        const SectionHeader('Recorded Vitals'),
        ...patient.vitals.reversed.map((v) => _VitalCard(entry: v)),
      ],
    ]);
  }
}

class _VitalCard extends StatelessWidget {
  final VitalEntry entry;
  const _VitalCard({required this.entry});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface2,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(fmtDate(entry.timestamp),
              style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
          const SizedBox(height: 8),
          Row(
            children: [
              if (entry.pulse != null) _Stat('Pulse', entry.pulse!),
              if (entry.rr != null)    _Stat('RR', entry.rr!),
              if (entry.bp != null)    _Stat('BP', entry.bp!),
            ],
          ),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  final String label, value;
  const _Stat(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(right: 20),
      child: RichText(
        text: TextSpan(children: [
          TextSpan(text: '$label ', style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
          TextSpan(text: value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 16)),
        ]),
      ),
    );
  }
}

// ─── Patient Info Tab ─────────────────────────────────────────────────────────
class _PatientInfoTab extends StatefulWidget {
  final Patient patient;
  final Future<void> Function(Patient) onSave;
  const _PatientInfoTab({required this.patient, required this.onSave});

  @override
  State<_PatientInfoTab> createState() => _PatientInfoTabState();
}

class _PatientInfoTabState extends State<_PatientInfoTab> {
  late final TextEditingController _ageCtrl;

  @override
  void initState() {
    super.initState();
    _ageCtrl = TextEditingController(text: widget.patient.info.age ?? '');
    _ageCtrl.addListener(_onAgeChanged);
  }

  void _onAgeChanged() {
    widget.onSave(widget.patient
      ..info.age = _ageCtrl.text.isEmpty ? null : _ageCtrl.text
      ..info.agePreset = null);
  }

  @override
  void dispose() {
    _ageCtrl.removeListener(_onAgeChanged);
    _ageCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final info = widget.patient.info;
    return _tabBody([
      const SectionHeader('Age'),
      Row(
        children: ['Child', 'Adult', 'Elderly'].map((preset) {
          final sel = info.agePreset == preset;
          return Expanded(
            child: Padding(
              padding: EdgeInsets.only(right: preset == 'Elderly' ? 0 : 8),
              child: GestureDetector(
                onTap: () {
                  _ageCtrl.clear();
                  widget.onSave(widget.patient
                    ..info.agePreset = preset
                    ..info.age = null);
                },
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 120),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  decoration: BoxDecoration(
                    color: sel ? AppColors.accent.withValues(alpha: 0.15) : Colors.transparent,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: sel ? AppColors.accent : AppColors.border, width: 2),
                  ),
                  alignment: Alignment.center,
                  child: Text(preset, style: TextStyle(
                    fontSize: 16, fontWeight: FontWeight.w700,
                    color: sel ? AppColors.accent : AppColors.textSecondary,
                  )),
                ),
              ),
            ),
          );
        }).toList(),
      ),
      const SizedBox(height: 12),
      AppInput(
        controller: _ageCtrl,
        placeholder: 'Or enter exact age',
        keyboardType: TextInputType.number,
        label: 'Age (years)',
      ),
      const SizedBox(height: 28),
      const SectionHeader('Sex'),
      Row(
        children: ['Male', 'Female', 'Unknown'].map((s) {
          final sel = info.sex == s;
          return Expanded(
            child: Padding(
              padding: EdgeInsets.only(right: s == 'Unknown' ? 0 : 8),
              child: GestureDetector(
                onTap: () => widget.onSave(widget.patient..info.sex = s),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 120),
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  decoration: BoxDecoration(
                    color: sel ? AppColors.blue.withValues(alpha: 0.15) : Colors.transparent,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: sel ? AppColors.blue : AppColors.border, width: 2),
                  ),
                  alignment: Alignment.center,
                  child: Text(s, style: TextStyle(
                    fontSize: 16, fontWeight: FontWeight.w700,
                    color: sel ? AppColors.blue : AppColors.textSecondary,
                  )),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    ]);
  }
}

// ─── Treatment Tab ────────────────────────────────────────────────────────────
class _TreatmentTab extends StatelessWidget {
  final Patient patient;
  final Future<void> Function(Patient) onSave;
  final TextEditingController drugCtrl, doseCtrl;

  const _TreatmentTab({
    required this.patient,
    required this.onSave,
    required this.drugCtrl,
    required this.doseCtrl,
  });

  void _addTreatment() {
    if (drugCtrl.text.isEmpty) return;
    final entry = TreatmentEntry(
      timestamp: DateTime.now(),
      drug: drugCtrl.text,
      dose: doseCtrl.text.isEmpty ? null : doseCtrl.text,
    );
    drugCtrl.clear(); doseCtrl.clear();
    onSave(patient..treatments.add(entry));
  }

  @override
  Widget build(BuildContext context) {
    return _tabBody([
      const SectionHeader('Log Treatment'),
      AppInput(controller: drugCtrl, placeholder: 'Drug / Intervention'),
      const SizedBox(height: 12),
      AppInput(controller: doseCtrl, placeholder: 'Dose / Route'),
      const SizedBox(height: 16),
      BigButton(label: 'Log Treatment', color: AppColors.purple, onTap: _addTreatment),
      if (patient.treatments.isNotEmpty) ...[
        const SizedBox(height: 28),
        const SectionHeader('Treatment Log'),
        ...patient.treatments.reversed.map((tx) => _TxCard(entry: tx)),
      ],
    ]);
  }
}

class _TxCard extends StatelessWidget {
  final TreatmentEntry entry;
  const _TxCard({required this.entry});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface2,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(fmtDate(entry.timestamp),
              style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
          const SizedBox(height: 4),
          Text(entry.drug,
              style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.w700)),
          if (entry.dose != null) ...[
            const SizedBox(height: 2),
            Text(entry.dose!,
                style: const TextStyle(color: AppColors.textSecondary, fontSize: 14)),
          ],
        ],
      ),
    );
  }
}
