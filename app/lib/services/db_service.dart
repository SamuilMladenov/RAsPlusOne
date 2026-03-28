// lib/services/db_service.dart
import 'package:hive_flutter/hive_flutter.dart';
import '../models/patient.dart';

class DbService {
  static const _boxName = 'patients';
  static late Box<Patient> _box;

  /// Call once in main() before runApp
  static Future<void> init() async {
    await Hive.initFlutter();

    // Register all adapters
    Hive.registerAdapter(TriageCategoryAdapter());
    Hive.registerAdapter(TriageAnswersAdapter());
    Hive.registerAdapter(ExposureDataAdapter());
    Hive.registerAdapter(AutoInjectorDataAdapter());
    Hive.registerAdapter(PatientInfoAdapter());
    Hive.registerAdapter(VitalEntryAdapter());
    Hive.registerAdapter(TreatmentEntryAdapter());
    Hive.registerAdapter(BodyZoneEntryAdapter());
    Hive.registerAdapter(PatientAdapter());

    _box = await Hive.openBox<Patient>(_boxName);
  }

  // ─── CRUD ──────────────────────────────────────────────────────────────────

  static List<Patient> getAll() {
    final list = _box.values.toList();
    list.sort((a, b) => b.timestamp.compareTo(a.timestamp));
    return list;
  }

  static Patient? get(String id) {
    return _box.values.cast<Patient?>().firstWhere(
      (p) => p?.id == id,
      orElse: () => null,
    );
  }

  static Future<void> upsert(Patient patient) async {
    // Use patient.id as the Hive key
    await _box.put(patient.id, patient);
  }

  static Future<void> delete(String id) async {
    await _box.delete(id);
  }

  static Future<void> clear() async {
    await _box.clear();
  }

  // ─── Stats ─────────────────────────────────────────────────────────────────

  static Map<TriageCategory, int> categoryCounts() {
    final counts = <TriageCategory, int>{};
    for (final cat in TriageCategory.values) {
      counts[cat] = 0;
    }
    for (final p in _box.values) {
      if (p.triage != null) {
        counts[p.triage!] = (counts[p.triage!] ?? 0) + 1;
      }
    }
    return counts;
  }

  // ─── Listen ────────────────────────────────────────────────────────────────

  /// Stream of box events — use with StreamBuilder or Riverpod
  static Stream<BoxEvent> get stream => _box.watch();
}
