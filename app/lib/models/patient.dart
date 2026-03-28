// lib/models/patient.dart
import 'package:hive/hive.dart';

part 'patient.g.dart';

// ─── Enums ────────────────────────────────────────────────────────────────────

@HiveType(typeId: 0)
enum TriageCategory {
  @HiveField(0) immediate,
  @HiveField(1) delayed,
  @HiveField(2) minor,
  @HiveField(3) morgue,
}

// ─── Sub-models ───────────────────────────────────────────────────────────────

@HiveType(typeId: 1)
class TriageAnswers extends HiveObject {
  @HiveField(0) bool? canWalk;
  @HiveField(1) bool? breathing;
  @HiveField(2) bool? airwayReposition;
  @HiveField(3) bool? rrOver30;
  @HiveField(4) bool? perfusionAbnormal;
  @HiveField(5) String? mentalStatus;

  TriageAnswers({
    this.canWalk,
    this.breathing,
    this.airwayReposition,
    this.rrOver30,
    this.perfusionAbnormal,
    this.mentalStatus,
  });
}

@HiveType(typeId: 2)
class ExposureData extends HiveObject {
  @HiveField(0) List<String> types;
  @HiveField(1) bool decon;
  @HiveField(2) bool secondaryDecon;

  ExposureData({
    List<String>? types,
    this.decon = false,
    this.secondaryDecon = false,
  }) : types = types ?? [];
}

@HiveType(typeId: 3)
class AutoInjectorData extends HiveObject {
  @HiveField(0) bool used;
  @HiveField(1) int dose;

  AutoInjectorData({this.used = false, this.dose = 1});
}

@HiveType(typeId: 4)
class PatientInfo extends HiveObject {
  @HiveField(0) String? age;
  @HiveField(1) String? agePreset; // child / adult / elderly
  @HiveField(2) String? sex;

  PatientInfo({this.age, this.agePreset, this.sex});
}

@HiveType(typeId: 5)
class VitalEntry extends HiveObject {
  @HiveField(0) DateTime timestamp;
  @HiveField(1) String? pulse;
  @HiveField(2) String? rr;
  @HiveField(3) String? bp;

  VitalEntry({
    required this.timestamp,
    this.pulse,
    this.rr,
    this.bp,
  });
}

@HiveType(typeId: 6)
class TreatmentEntry extends HiveObject {
  @HiveField(0) DateTime timestamp;
  @HiveField(1) String drug;
  @HiveField(2) String? dose;

  TreatmentEntry({
    required this.timestamp,
    required this.drug,
    this.dose,
  });
}

@HiveType(typeId: 7)
class BodyZoneEntry extends HiveObject {
  @HiveField(0) String zoneId;
  @HiveField(1) String zoneLabel;
  @HiveField(2) String primaryInjury;
  @HiveField(3) List<String> findings;
  @HiveField(4) String severity; // Minor / Moderate / Severe
  @HiveField(5) String? notes;
  @HiveField(6) DateTime timestamp;

  BodyZoneEntry({
    required this.zoneId,
    required this.zoneLabel,
    required this.primaryInjury,
    List<String>? findings,
    required this.severity,
    this.notes,
    required this.timestamp,
  }) : findings = findings ?? [];
}

// ─── Root Patient Model ───────────────────────────────────────────────────────

@HiveType(typeId: 8)
class Patient extends HiveObject {
  @HiveField(0) String id;
  @HiveField(1) DateTime timestamp;
  @HiveField(2) TriageCategory? triage;
  @HiveField(3) DateTime? triageTime;
  @HiveField(4) TriageAnswers? triageAnswers;
  @HiveField(5) ExposureData exposure;
  @HiveField(6) List<String> sludge;
  @HiveField(7) List<String> injuryTypes;
  @HiveField(8) AutoInjectorData autoInjector;
  @HiveField(9) PatientInfo info;
  @HiveField(10) List<VitalEntry> vitals;
  @HiveField(11) List<TreatmentEntry> treatments;
  @HiveField(12) List<BodyZoneEntry> bodyZones;

  Patient({
    required this.id,
    required this.timestamp,
    this.triage,
    this.triageTime,
    this.triageAnswers,
    ExposureData? exposure,
    List<String>? sludge,
    List<String>? injuryTypes,
    AutoInjectorData? autoInjector,
    PatientInfo? info,
    List<VitalEntry>? vitals,
    List<TreatmentEntry>? treatments,
    List<BodyZoneEntry>? bodyZones,
  })  : exposure = exposure ?? ExposureData(),
        sludge = sludge ?? [],
        injuryTypes = injuryTypes ?? [],
        autoInjector = autoInjector ?? AutoInjectorData(),
        info = info ?? PatientInfo(),
        vitals = vitals ?? [],
        treatments = treatments ?? [],
        bodyZones = bodyZones ?? [];
}
