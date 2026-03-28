// lib/models/patient.g.dart
// GENERATED CODE - DO NOT MODIFY BY HAND
// Run: flutter pub run build_runner build

part of 'patient.dart';

// ─── TriageCategory Adapter ───────────────────────────────────────────────────
class TriageCategoryAdapter extends TypeAdapter<TriageCategory> {
  @override
  final int typeId = 0;

  @override
  TriageCategory read(BinaryReader reader) {
    switch (reader.readByte()) {
      case 0: return TriageCategory.immediate;
      case 1: return TriageCategory.delayed;
      case 2: return TriageCategory.minor;
      case 3: return TriageCategory.morgue;
      default: return TriageCategory.immediate;
    }
  }

  @override
  void write(BinaryWriter writer, TriageCategory obj) {
    writer.writeByte(obj.index);
  }
}

// ─── TriageAnswers Adapter ────────────────────────────────────────────────────
class TriageAnswersAdapter extends TypeAdapter<TriageAnswers> {
  @override
  final int typeId = 1;

  @override
  TriageAnswers read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read()};
    return TriageAnswers(
      canWalk: fields[0] as bool?,
      breathing: fields[1] as bool?,
      airwayReposition: fields[2] as bool?,
      rrOver30: fields[3] as bool?,
      perfusionAbnormal: fields[4] as bool?,
      mentalStatus: fields[5] as String?,
    );
  }

  @override
  void write(BinaryWriter writer, TriageAnswers obj) {
    writer
      ..writeByte(6)
      ..writeByte(0)..write(obj.canWalk)
      ..writeByte(1)..write(obj.breathing)
      ..writeByte(2)..write(obj.airwayReposition)
      ..writeByte(3)..write(obj.rrOver30)
      ..writeByte(4)..write(obj.perfusionAbnormal)
      ..writeByte(5)..write(obj.mentalStatus);
  }
}

// ─── ExposureData Adapter ─────────────────────────────────────────────────────
class ExposureDataAdapter extends TypeAdapter<ExposureData> {
  @override
  final int typeId = 2;

  @override
  ExposureData read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read()};
    return ExposureData(
      types: (fields[0] as List).cast<String>(),
      decon: fields[1] as bool,
      secondaryDecon: fields[2] as bool,
    );
  }

  @override
  void write(BinaryWriter writer, ExposureData obj) {
    writer
      ..writeByte(3)
      ..writeByte(0)..write(obj.types)
      ..writeByte(1)..write(obj.decon)
      ..writeByte(2)..write(obj.secondaryDecon);
  }
}

// ─── AutoInjectorData Adapter ─────────────────────────────────────────────────
class AutoInjectorDataAdapter extends TypeAdapter<AutoInjectorData> {
  @override
  final int typeId = 3;

  @override
  AutoInjectorData read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read()};
    return AutoInjectorData(used: fields[0] as bool, dose: fields[1] as int);
  }

  @override
  void write(BinaryWriter writer, AutoInjectorData obj) {
    writer
      ..writeByte(2)
      ..writeByte(0)..write(obj.used)
      ..writeByte(1)..write(obj.dose);
  }
}

// ─── PatientInfo Adapter ──────────────────────────────────────────────────────
class PatientInfoAdapter extends TypeAdapter<PatientInfo> {
  @override
  final int typeId = 4;

  @override
  PatientInfo read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read()};
    return PatientInfo(age: fields[0] as String?, agePreset: fields[1] as String?, sex: fields[2] as String?);
  }

  @override
  void write(BinaryWriter writer, PatientInfo obj) {
    writer
      ..writeByte(3)
      ..writeByte(0)..write(obj.age)
      ..writeByte(1)..write(obj.agePreset)
      ..writeByte(2)..write(obj.sex);
  }
}

// ─── VitalEntry Adapter ───────────────────────────────────────────────────────
class VitalEntryAdapter extends TypeAdapter<VitalEntry> {
  @override
  final int typeId = 5;

  @override
  VitalEntry read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read()};
    return VitalEntry(
      timestamp: fields[0] as DateTime,
      pulse: fields[1] as String?,
      rr: fields[2] as String?,
      bp: fields[3] as String?,
    );
  }

  @override
  void write(BinaryWriter writer, VitalEntry obj) {
    writer
      ..writeByte(4)
      ..writeByte(0)..write(obj.timestamp)
      ..writeByte(1)..write(obj.pulse)
      ..writeByte(2)..write(obj.rr)
      ..writeByte(3)..write(obj.bp);
  }
}

// ─── TreatmentEntry Adapter ───────────────────────────────────────────────────
class TreatmentEntryAdapter extends TypeAdapter<TreatmentEntry> {
  @override
  final int typeId = 6;

  @override
  TreatmentEntry read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read()};
    return TreatmentEntry(
      timestamp: fields[0] as DateTime,
      drug: fields[1] as String,
      dose: fields[2] as String?,
    );
  }

  @override
  void write(BinaryWriter writer, TreatmentEntry obj) {
    writer
      ..writeByte(3)
      ..writeByte(0)..write(obj.timestamp)
      ..writeByte(1)..write(obj.drug)
      ..writeByte(2)..write(obj.dose);
  }
}

// ─── BodyZoneEntry Adapter ────────────────────────────────────────────────────
class BodyZoneEntryAdapter extends TypeAdapter<BodyZoneEntry> {
  @override
  final int typeId = 7;

  @override
  BodyZoneEntry read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read()};
    return BodyZoneEntry(
      zoneId: fields[0] as String,
      zoneLabel: fields[1] as String,
      primaryInjury: fields[2] as String,
      findings: (fields[3] as List).cast<String>(),
      severity: fields[4] as String,
      notes: fields[5] as String?,
      timestamp: fields[6] as DateTime,
    );
  }

  @override
  void write(BinaryWriter writer, BodyZoneEntry obj) {
    writer
      ..writeByte(7)
      ..writeByte(0)..write(obj.zoneId)
      ..writeByte(1)..write(obj.zoneLabel)
      ..writeByte(2)..write(obj.primaryInjury)
      ..writeByte(3)..write(obj.findings)
      ..writeByte(4)..write(obj.severity)
      ..writeByte(5)..write(obj.notes)
      ..writeByte(6)..write(obj.timestamp);
  }
}

// ─── Patient Adapter ──────────────────────────────────────────────────────────
class PatientAdapter extends TypeAdapter<Patient> {
  @override
  final int typeId = 8;

  @override
  Patient read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read()};
    return Patient(
      id: fields[0] as String,
      timestamp: fields[1] as DateTime,
      triage: fields[2] as TriageCategory?,
      triageTime: fields[3] as DateTime?,
      triageAnswers: fields[4] as TriageAnswers?,
      exposure: fields[5] as ExposureData?,
      sludge: (fields[6] as List?)?.cast<String>(),
      injuryTypes: (fields[7] as List?)?.cast<String>(),
      autoInjector: fields[8] as AutoInjectorData?,
      info: fields[9] as PatientInfo?,
      vitals: (fields[10] as List?)?.cast<VitalEntry>(),
      treatments: (fields[11] as List?)?.cast<TreatmentEntry>(),
      bodyZones: (fields[12] as List?)?.cast<BodyZoneEntry>(),
    );
  }

  @override
  void write(BinaryWriter writer, Patient obj) {
    writer
      ..writeByte(13)
      ..writeByte(0)..write(obj.id)
      ..writeByte(1)..write(obj.timestamp)
      ..writeByte(2)..write(obj.triage)
      ..writeByte(3)..write(obj.triageTime)
      ..writeByte(4)..write(obj.triageAnswers)
      ..writeByte(5)..write(obj.exposure)
      ..writeByte(6)..write(obj.sludge)
      ..writeByte(7)..write(obj.injuryTypes)
      ..writeByte(8)..write(obj.autoInjector)
      ..writeByte(9)..write(obj.info)
      ..writeByte(10)..write(obj.vitals)
      ..writeByte(11)..write(obj.treatments)
      ..writeByte(12)..write(obj.bodyZones);
  }
}
