// lib/models/app_theme.dart
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

// ─── Triage Colors ─────────────────────────────────────────────────────────────
class TriageColors {
  static const immediate = Color(0xFFC0392B);
  static const delayed   = Color(0xFFD4AC0D);
  static const minor     = Color(0xFF1E8449);
  static const morgue    = Color(0xFF1C2833);
}

// ─── App Palette ───────────────────────────────────────────────────────────────
class AppColors {
  static const bg       = Color(0xFF0D0D1A);
  static const surface  = Color(0xFF111111);
  static const surface2 = Color(0xFF1A1A2E);
  static const border   = Color(0xFF2A2A3A);
  static const accent   = Color(0xFFE74C3C);
  static const textPrimary   = Color(0xFFFFFFFF);
  static const textSecondary = Color(0xFFAAAAAA);
  static const textMuted     = Color(0xFF666666);
  static const green  = Color(0xFF27AE60);
  static const purple = Color(0xFF8E44AD);
  static const blue   = Color(0xFF3498DB);
}

// ─── Severity Colors ───────────────────────────────────────────────────────────
class SeverityColors {
  static const minor    = Color(0xFF1E8449);
  static const moderate = Color(0xFFD4AC0D);
  static const severe   = Color(0xFFC0392B);

  static Color forSeverity(String s) {
    switch (s) {
      case 'Moderate': return moderate;
      case 'Severe':   return severe;
      default:         return minor;
    }
  }
}

// ─── Theme ─────────────────────────────────────────────────────────────────────
class AppTheme {
  static ThemeData get dark {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AppColors.bg,
      colorScheme: const ColorScheme.dark(
        primary: AppColors.accent,
        surface: AppColors.surface,
      ),
      textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme),
      useMaterial3: true,
    );
  }
}

// ─── Triage Info ──────────────────────────────────────────────────────────────
class TriageInfo {
  final String label;
  final String tag;
  final String shortCode;
  final Color color;

  const TriageInfo({
    required this.label,
    required this.tag,
    required this.shortCode,
    required this.color,
  });
}

const Map<String, TriageInfo> triageInfoMap = {
  'immediate': TriageInfo(label: 'IMMEDIATE', tag: 'Red Tag',    shortCode: 'I', color: TriageColors.immediate),
  'delayed':   TriageInfo(label: 'DELAYED',   tag: 'Yellow Tag', shortCode: 'D', color: TriageColors.delayed),
  'minor':     TriageInfo(label: 'MINOR',     tag: 'Green Tag',  shortCode: 'M', color: TriageColors.minor),
  'morgue':    TriageInfo(label: 'MORGUE',    tag: 'Black Tag',  shortCode: 'X', color: TriageColors.morgue),
};

TriageInfo? triageInfoFor(dynamic category) {
  if (category == null) return null;
  // Accept both enum and string
  final key = category.toString().split('.').last.toLowerCase();
  return triageInfoMap[key];
}

// ─── Body Zone Model ──────────────────────────────────────────────────────────
class BodyZone {
  final String id;
  final String label;
  final Rect rect; // normalized 0–1 coordinates

  const BodyZone({required this.id, required this.label, required this.rect});
}

// Zones defined in a 400×530 viewport, normalized
const List<BodyZone> frontZones = [
  BodyZone(id: 'head',         label: 'Head',       rect: Rect.fromLTWH(0.3875, 0.0377, 0.225,  0.1509)),
  BodyZone(id: 'neck',         label: 'Neck',       rect: Rect.fromLTWH(0.4425, 0.1887, 0.115,  0.0566)),
  BodyZone(id: 'chest',        label: 'Chest',      rect: Rect.fromLTWH(0.325,  0.2453, 0.35,   0.1509)),
  BodyZone(id: 'abdomen',      label: 'Abdomen',    rect: Rect.fromLTWH(0.35,   0.3962, 0.3,    0.1132)),
  BodyZone(id: 'pelvis',       label: 'Pelvis',     rect: Rect.fromLTWH(0.3625, 0.5094, 0.275,  0.0943)),
  BodyZone(id: 'l_upper_arm',  label: 'L Arm',      rect: Rect.fromLTWH(0.2,    0.2453, 0.1375, 0.1698)),
  BodyZone(id: 'r_upper_arm',  label: 'R Arm',      rect: Rect.fromLTWH(0.675,  0.2453, 0.1375, 0.1698)),
  BodyZone(id: 'l_forearm',    label: 'L Forearm',  rect: Rect.fromLTWH(0.15,   0.4151, 0.1125, 0.1509)),
  BodyZone(id: 'r_forearm',    label: 'R Forearm',  rect: Rect.fromLTWH(0.7375, 0.4151, 0.1125, 0.1509)),
  BodyZone(id: 'l_thigh',      label: 'L Thigh',    rect: Rect.fromLTWH(0.345,  0.6038, 0.1375, 0.1698)),
  BodyZone(id: 'r_thigh',      label: 'R Thigh',    rect: Rect.fromLTWH(0.5175, 0.6038, 0.1375, 0.1698)),
  BodyZone(id: 'l_lower_leg',  label: 'L Leg',      rect: Rect.fromLTWH(0.325,  0.7736, 0.1375, 0.1887)),
  BodyZone(id: 'r_lower_leg',  label: 'R Leg',      rect: Rect.fromLTWH(0.5375, 0.7736, 0.1375, 0.1887)),
];

const List<BodyZone> backZones = [
  BodyZone(id: 'head_b',         label: 'Head',       rect: Rect.fromLTWH(0.3875, 0.0377, 0.225,  0.1509)),
  BodyZone(id: 'upper_back',     label: 'Upper Back', rect: Rect.fromLTWH(0.3125, 0.2453, 0.375,  0.1509)),
  BodyZone(id: 'lower_back',     label: 'Lower Back', rect: Rect.fromLTWH(0.3375, 0.3962, 0.325,  0.1321)),
  BodyZone(id: 'l_upper_arm_b',  label: 'L Arm',      rect: Rect.fromLTWH(0.2,    0.2453, 0.1375, 0.1698)),
  BodyZone(id: 'r_upper_arm_b',  label: 'R Arm',      rect: Rect.fromLTWH(0.675,  0.2453, 0.1375, 0.1698)),
  BodyZone(id: 'l_thigh_b',      label: 'L Thigh',    rect: Rect.fromLTWH(0.345,  0.6038, 0.1375, 0.1698)),
  BodyZone(id: 'r_thigh_b',      label: 'R Thigh',    rect: Rect.fromLTWH(0.5175, 0.6038, 0.1375, 0.1698)),
  BodyZone(id: 'l_lower_leg_b',  label: 'L Leg',      rect: Rect.fromLTWH(0.325,  0.7736, 0.1375, 0.1887)),
  BodyZone(id: 'r_lower_leg_b',  label: 'R Leg',      rect: Rect.fromLTWH(0.5375, 0.7736, 0.1375, 0.1887)),
];

// ─── Constants ────────────────────────────────────────────────────────────────
const kInjuryPrimary = [
  'Laceration', 'Burn', 'Fracture suspected',
  'Penetrating injury', 'Bruise', 'Crush injury',
];

const kInjuryFindings = [
  'Bleeding', 'Swelling', 'Deformity', 'Tenderness', 'Contamination',
];

const kSludgeSymptoms = [
  'Salivation', 'Lacrimation', 'Urination',
  'Defecation', 'GI Distress', 'Emesis',
];

const kInjuryTypes = [
  'Blunt trauma', 'Burn', 'C-spine', 'Cardiac',
  'Crushing', 'Fracture', 'Laceration', 'Penetrating',
];

const kExposureTypes = ['Radiological', 'Biological', 'Chemical'];
