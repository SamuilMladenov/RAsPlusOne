// lib/screens/detail_form.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/app_theme.dart';
import '../models/patient.dart';
import '../services/providers.dart';
import '../widgets/shared_widgets.dart';
import '../widgets/body_diagram.dart';

const _tabs = ['Exposure', 'SLUDGE', 'Injuries', 'Body', 'Vitals', 'Patient', 'Treatment'];

// ─── Root screen — owns TabController and text controllers ────────────────────
class DetailFormScreen extends ConsumerStatefulWidget {
  const DetailFormScreen({super.key});
  @override
  ConsumerState<DetailFormScreen> createState() => _DetailFormScreenState();
}

class _DetailFormScreenState extends ConsumerState<DetailFormScreen>
    with TickerProviderStateMixin {
  late TabController _tabCtrl;
  final _pulseCtrl = TextEditingController();
  final _rrCtrl    = TextEditingController();
  final _bpCtrl    = TextEditingController();
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
    _pulseCtrl.dispose(); _rrCtrl.dispose(); _bpCtrl.dispose();
    _drugCtrl.dispose();  _doseCtrl.dispose();
    super.dispose();
  }

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
            // ── Header ────────────────────────────────────────────────────
            Container(
              color: info?.color ?? AppColors.surface,
              padding: const EdgeInsets.fromLTRB(20, 14, 20, 14),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Patient ${patient.id}',
                          style: TextStyle(fontSize: 12, color: Colors.white.withValues(alpha: 0.7))),
                        Text('${info?.label ?? "—"} · ${info?.tag ?? ""}',
                          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: Colors.white)),
                      ],
                    ),
                  ),
                  GestureDetector(
                    onTap: () => Navigator.pushNamedAndRemoveUntil(context, '/', (r) => false),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.25),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Text('Done ✓',
                        style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w700)),
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
                labelStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                unselectedLabelStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w400),
                tabs: _tabs.map((t) => Tab(text: t)).toList(),
              ),
            ),
            // ── Tab Content ───────────────────────────────────────────────
            Expanded(
              child: TabBarView(
                controller: _tabCtrl,
                children: [
                  const _ExposureTab(),
                  const _SludgeTab(),
                  const _InjuriesTab(),
                  const _BodyTab(),
                  _VitalsTab(pulseCtrl: _pulseCtrl, rrCtrl: _rrCtrl, bpCtrl: _bpCtrl),
                  const _PatientInfoTab(),
                  _TreatmentTab(drugCtrl: _drugCtrl, doseCtrl: _doseCtrl),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Shared save helper used by all tabs ──────────────────────────────────────
extension _SaveExt on WidgetRef {
  Future<void> savePatient(Patient p) async {
    await read(patientListProvider.notifier).save(p);
    read(activePatientProvider.notifier).state = p;
  }
}

// ─── EXPOSURE TAB ─────────────────────────────────────────────────────────────
// Exposure types: large vertical buttons (glove-friendly)
// Decon: large YES/NO button pairs instead of tiny switches
class _ExposureTab extends ConsumerWidget {
  const _ExposureTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final patient = ref.watch(activePatientProvider)!;

    Future<void> save(Patient p) => ref.savePatient(p);

    void toggleType(String t) {
      final types = List<String>.from(patient.exposure.types);
      types.contains(t) ? types.remove(t) : types.add(t);
      patient.exposure.types..clear()..addAll(types);
      save(patient);
    }

    void setDecon(bool v)          { patient.exposure.decon = v;          save(patient); }
    void setSecondaryDecon(bool v) { patient.exposure.secondaryDecon = v; save(patient); }

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
      children: [
        const SectionHeader('Exposure Type'),
        ...kExposureTypes.map((opt) {
          final active = patient.exposure.types.contains(opt);
          return _VerticalToggleButton(
            label: opt,
            active: active,
            activeColor: AppColors.accent,
            onTap: () => toggleType(opt),
          );
        }),

        const SizedBox(height: 28),
        const SectionHeader('Gross Decontamination'),
        _YesNoRow(
          value: patient.exposure.decon,
          onYes: () => setDecon(true),
          onNo:  () => setDecon(false),
        ),

        const SizedBox(height: 20),
        const SectionHeader('Secondary Decontamination'),
        _YesNoRow(
          value: patient.exposure.secondaryDecon,
          onYes: () => setSecondaryDecon(true),
          onNo:  () => setSecondaryDecon(false),
        ),
      ],
    );
  }
}

// ─── SLUDGE TAB ───────────────────────────────────────────────────────────────
class _SludgeTab extends ConsumerWidget {
  const _SludgeTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final patient = ref.watch(activePatientProvider)!;

    void toggle(String s) {
      final list = List<String>.from(patient.sludge);
      list.contains(s) ? list.remove(s) : list.add(s);
      patient.sludge..clear()..addAll(list);
      ref.savePatient(patient);
    }

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
      children: [
        const SectionHeader('SLUDGE Symptoms'),
        ...kSludgeSymptoms.map((opt) => _VerticalToggleButton(
          label: opt,
          active: patient.sludge.contains(opt),
          activeColor: AppColors.accent,
          onTap: () => toggle(opt),
        )),
      ],
    );
  }
}

// ─── INJURIES TAB ─────────────────────────────────────────────────────────────
class _InjuriesTab extends ConsumerWidget {
  const _InjuriesTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final patient = ref.watch(activePatientProvider)!;

    void toggleType(String s) {
      final list = List<String>.from(patient.injuryTypes);
      list.contains(s) ? list.remove(s) : list.add(s);
      patient.injuryTypes..clear()..addAll(list);
      ref.savePatient(patient);
    }

    void setInjectorUsed(bool v) { patient.autoInjector.used = v; ref.savePatient(patient); }
    void setDose(int d)          { patient.autoInjector.dose = d; ref.savePatient(patient); }

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
      children: [
        const SectionHeader('Mechanism / Injury Type'),
        ...kInjuryTypes.map((opt) => _VerticalToggleButton(
          label: opt,
          active: patient.injuryTypes.contains(opt),
          activeColor: AppColors.accent,
          onTap: () => toggleType(opt),
        )),

        const SizedBox(height: 28),
        const SectionHeader('Auto-Injector Used'),
        _YesNoRow(
          value: patient.autoInjector.used,
          onYes: () => setInjectorUsed(true),
          onNo:  () => setInjectorUsed(false),
        ),

        if (patient.autoInjector.used) ...[
          const SizedBox(height: 20),
          const SectionHeader('Doses Administered'),
          Row(
            children: List.generate(5, (i) {
              final n = i + 1;
              final sel = patient.autoInjector.dose == n;
              return Expanded(
                child: Padding(
                  padding: EdgeInsets.only(right: i < 4 ? 8 : 0),
                  child: GestureDetector(
                    onTap: () => setDose(n),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 120),
                      height: 64,
                      decoration: BoxDecoration(
                        color: sel ? AppColors.accent : Colors.transparent,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: sel ? AppColors.accent : AppColors.border, width: 2),
                      ),
                      alignment: Alignment.center,
                      child: Text('$n', style: TextStyle(
                        fontSize: 24, fontWeight: FontWeight.w800,
                        color: sel ? Colors.white : AppColors.textSecondary)),
                    ),
                  ),
                ),
              );
            }),
          ),
        ],
      ],
    );
  }
}

// ─── BODY TAB ─────────────────────────────────────────────────────────────────
class _BodyTab extends ConsumerWidget {
  const _BodyTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final patient = ref.watch(activePatientProvider)!;

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
      children: [
        BodyDiagram(
          entries: patient.bodyZones,
          onChange: (zones) {
            patient.bodyZones..clear()..addAll(zones);
            ref.savePatient(patient);
          },
        ),
      ],
    );
  }
}

// ─── VITALS TAB ───────────────────────────────────────────────────────────────
class _VitalsTab extends ConsumerWidget {
  final TextEditingController pulseCtrl, rrCtrl, bpCtrl;
  const _VitalsTab({required this.pulseCtrl, required this.rrCtrl, required this.bpCtrl});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final patient = ref.watch(activePatientProvider)!;

    void addVital() {
      if (pulseCtrl.text.isEmpty && rrCtrl.text.isEmpty && bpCtrl.text.isEmpty) return;
      patient.vitals.add(VitalEntry(
        timestamp: DateTime.now(),
        pulse: pulseCtrl.text.isEmpty ? null : pulseCtrl.text,
        rr:    rrCtrl.text.isEmpty    ? null : rrCtrl.text,
        bp:    bpCtrl.text.isEmpty    ? null : bpCtrl.text,
      ));
      pulseCtrl.clear(); rrCtrl.clear(); bpCtrl.clear();
      ref.savePatient(patient);
    }

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
      children: [
        const SectionHeader('New Vital Signs'),
        AppInput(controller: pulseCtrl, placeholder: '—', label: 'Pulse (bpm)', keyboardType: TextInputType.number),
        const SizedBox(height: 12),
        AppInput(controller: rrCtrl,    placeholder: '—', label: 'Respiratory Rate', keyboardType: TextInputType.number),
        const SizedBox(height: 12),
        AppInput(controller: bpCtrl,    placeholder: '—', label: 'Blood Pressure'),
        const SizedBox(height: 16),
        BigButton(label: 'Record Vitals', color: AppColors.green, onTap: addVital),
        if (patient.vitals.isNotEmpty) ...[
          const SizedBox(height: 28),
          const SectionHeader('Recorded Vitals'),
          ...patient.vitals.reversed.map((v) => _VitalCard(entry: v)),
        ],
      ],
    );
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
      decoration: BoxDecoration(color: AppColors.surface2, borderRadius: BorderRadius.circular(12)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(fmtDate(entry.timestamp), style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
          const SizedBox(height: 8),
          Row(children: [
            if (entry.pulse != null) _Stat('Pulse', entry.pulse!),
            if (entry.rr    != null) _Stat('RR',    entry.rr!),
            if (entry.bp    != null) _Stat('BP',    entry.bp!),
          ]),
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
      child: RichText(text: TextSpan(children: [
        TextSpan(text: '$label ', style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
        TextSpan(text: value,     style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 16)),
      ])),
    );
  }
}

// ─── PATIENT INFO TAB ─────────────────────────────────────────────────────────
// All buttons now call savePatient immediately — no StatefulWidget needed.
class _PatientInfoTab extends ConsumerStatefulWidget {
  const _PatientInfoTab();
  @override
  ConsumerState<_PatientInfoTab> createState() => _PatientInfoTabState();
}

class _PatientInfoTabState extends ConsumerState<_PatientInfoTab> {
  late final TextEditingController _ageCtrl;

  @override
  void initState() {
    super.initState();
    final patient = ref.read(activePatientProvider);
    _ageCtrl = TextEditingController(text: patient?.info.age ?? '');
    _ageCtrl.addListener(_onAgeChanged);
  }

  void _onAgeChanged() {
    final patient = ref.read(activePatientProvider);
    if (patient == null) return;
    patient.info.age       = _ageCtrl.text.isEmpty ? null : _ageCtrl.text;
    patient.info.agePreset = null;
    ref.savePatient(patient);
  }

  @override
  void dispose() {
    _ageCtrl.removeListener(_onAgeChanged);
    _ageCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final patient = ref.watch(activePatientProvider)!;
    final info    = patient.info;

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
      children: [
        const SectionHeader('Age'),
        Row(
          children: ['Child', 'Adult', 'Elderly'].map((preset) {
            final sel = info.agePreset == preset;
            return Expanded(
              child: Padding(
                padding: EdgeInsets.only(right: preset == 'Elderly' ? 0 : 8),
                child: GestureDetector(
                  onTap: () {
                    _ageCtrl.removeListener(_onAgeChanged);
                    _ageCtrl.clear();
                    _ageCtrl.addListener(_onAgeChanged);
                    patient.info.agePreset = preset;
                    patient.info.age       = null;
                    ref.savePatient(patient);
                  },
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 120),
                    height: 64,
                    decoration: BoxDecoration(
                      color: sel ? AppColors.accent.withValues(alpha: 0.15) : Colors.transparent,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: sel ? AppColors.accent : AppColors.border, width: 2),
                    ),
                    alignment: Alignment.center,
                    child: Text(preset, style: TextStyle(
                      fontSize: 18, fontWeight: FontWeight.w700,
                      color: sel ? AppColors.accent : AppColors.textSecondary)),
                  ),
                ),
              ),
            );
          }).toList(),
        ),
        const SizedBox(height: 12),
        AppInput(controller: _ageCtrl, placeholder: 'Or enter exact age',
            keyboardType: TextInputType.number, label: 'Age (years)'),

        const SizedBox(height: 28),
        const SectionHeader('Sex'),
        Row(
          children: ['Male', 'Female'].map((s) {
            final sel = info.sex == s;
            return Expanded(
              child: Padding(
                padding: EdgeInsets.only(right: s == 'Female' ? 0 : 8),
                child: GestureDetector(
                  onTap: () {
                    patient.info.sex = s;
                    ref.savePatient(patient);
                  },
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 120),
                    height: 64,
                    decoration: BoxDecoration(
                      color: sel ? AppColors.blue.withValues(alpha: 0.15) : Colors.transparent,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: sel ? AppColors.blue : AppColors.border, width: 2),
                    ),
                    alignment: Alignment.center,
                    child: Text(s, style: TextStyle(
                      fontSize: 18, fontWeight: FontWeight.w700,
                      color: sel ? AppColors.blue : AppColors.textSecondary)),
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }
}

// ─── TREATMENT TAB ────────────────────────────────────────────────────────────
class _TreatmentTab extends ConsumerWidget {
  final TextEditingController drugCtrl, doseCtrl;
  const _TreatmentTab({required this.drugCtrl, required this.doseCtrl});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final patient = ref.watch(activePatientProvider)!;

    void addTreatment() {
      if (drugCtrl.text.isEmpty) return;
      patient.treatments.add(TreatmentEntry(
        timestamp: DateTime.now(),
        drug: drugCtrl.text,
        dose: doseCtrl.text.isEmpty ? null : doseCtrl.text,
      ));
      drugCtrl.clear(); doseCtrl.clear();
      ref.savePatient(patient);
    }

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
      children: [
        const SectionHeader('Log Treatment'),
        AppInput(controller: drugCtrl, placeholder: 'Drug / Intervention'),
        const SizedBox(height: 12),
        AppInput(controller: doseCtrl, placeholder: 'Dose / Route'),
        const SizedBox(height: 16),
        BigButton(label: 'Log Treatment', color: AppColors.purple, onTap: addTreatment),
        if (patient.treatments.isNotEmpty) ...[
          const SizedBox(height: 28),
          const SectionHeader('Treatment Log'),
          ...patient.treatments.reversed.map((tx) => _TxCard(entry: tx)),
        ],
      ],
    );
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
      decoration: BoxDecoration(color: AppColors.surface2, borderRadius: BorderRadius.circular(12)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(fmtDate(entry.timestamp), style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
          const SizedBox(height: 4),
          Text(entry.drug, style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.w700)),
          if (entry.dose != null) ...[
            const SizedBox(height: 2),
            Text(entry.dose!, style: const TextStyle(color: AppColors.textSecondary, fontSize: 14)),
          ],
        ],
      ),
    );
  }
}

// ─── Shared UI components ─────────────────────────────────────────────────────

/// Full-width vertical toggle button — large enough for gloved fingers
class _VerticalToggleButton extends StatelessWidget {
  final String label;
  final bool active;
  final Color activeColor;
  final VoidCallback onTap;

  const _VerticalToggleButton({
    required this.label,
    required this.active,
    required this.activeColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        width: double.infinity,
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 20),
        decoration: BoxDecoration(
          color: active ? activeColor.withValues(alpha: 0.18) : AppColors.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: active ? activeColor : AppColors.border,
            width: active ? 2.5 : 1.5,
          ),
        ),
        child: Row(
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              width: 26, height: 26,
              decoration: BoxDecoration(
                color: active ? activeColor : Colors.transparent,
                shape: BoxShape.circle,
                border: Border.all(color: active ? activeColor : AppColors.textMuted, width: 2),
              ),
              alignment: Alignment.center,
              child: active
                  ? const Icon(Icons.check, color: Colors.white, size: 16)
                  : null,
            ),
            const SizedBox(width: 16),
            Text(label, style: TextStyle(
              fontSize: 19, fontWeight: FontWeight.w700,
              color: active ? activeColor : AppColors.textPrimary,
            )),
          ],
        ),
      ),
    );
  }
}

/// Large YES / NO button pair — replaces tiny toggle switches
class _YesNoRow extends StatelessWidget {
  final bool? value; // null = neither selected
  final VoidCallback onYes;
  final VoidCallback onNo;

  const _YesNoRow({required this.value, required this.onYes, required this.onNo});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(child: _YesNoBtn(label: 'YES', active: value == true,  color: AppColors.green,  onTap: onYes)),
        const SizedBox(width: 10),
        Expanded(child: _YesNoBtn(label: 'NO',  active: value == false, color: AppColors.accent, onTap: onNo)),
      ],
    );
  }
}

class _YesNoBtn extends StatelessWidget {
  final String label;
  final bool active;
  final Color color;
  final VoidCallback onTap;

  const _YesNoBtn({required this.label, required this.active, required this.color, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        height: 64,
        decoration: BoxDecoration(
          color: active ? color : Colors.transparent,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: active ? color : AppColors.border, width: 2),
        ),
        alignment: Alignment.center,
        child: Text(label, style: TextStyle(
          fontSize: 20, fontWeight: FontWeight.w800,
          color: active ? Colors.white : AppColors.textSecondary,
        )),
      ),
    );
  }
}
