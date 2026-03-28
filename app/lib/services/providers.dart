// lib/services/providers.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../models/patient.dart';
import 'db_service.dart';

// ─── Patient List Provider ────────────────────────────────────────────────────

class PatientListNotifier extends Notifier<List<Patient>> {
  @override
  List<Patient> build() => DbService.getAll();

  Future<void> refresh() async {
    state = DbService.getAll();
  }

  Future<Patient> createNew() async {
    const uuid = Uuid();
    final patient = Patient(
      id: uuid.v4().substring(0, 8).toUpperCase(),
      timestamp: DateTime.now(),
    );
    await DbService.upsert(patient);
    state = DbService.getAll();
    return patient;
  }

  Future<void> save(Patient patient) async {
    await DbService.upsert(patient);
    state = DbService.getAll();
  }

  Future<void> delete(String id) async {
    await DbService.delete(id);
    state = DbService.getAll();
  }
}

final patientListProvider =
    NotifierProvider<PatientListNotifier, List<Patient>>(PatientListNotifier.new);

// ─── Active Patient Provider ──────────────────────────────────────────────────

final activePatientProvider = StateProvider<Patient?>((ref) => null);

// ─── Category Counts Provider ─────────────────────────────────────────────────

final categoryCountsProvider = Provider<Map<TriageCategory, int>>((ref) {
  ref.watch(patientListProvider); // rebuild when list changes
  return DbService.categoryCounts();
});
