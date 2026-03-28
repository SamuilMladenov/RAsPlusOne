// lib/main.dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'models/app_theme.dart';
import 'services/db_service.dart';
import 'screens/home_screen.dart';
import 'screens/triage_wizard.dart';
import 'screens/triage_result.dart';
import 'screens/detail_form.dart';
import 'screens/patient_list.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Keep screen on during triage — critical for emergency use
  SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
  ));

  // Initialise Hive storage
  await DbService.init();

  runApp(
    const ProviderScope(child: TriageApp()),
  );
}

class TriageApp extends StatelessWidget {
  const TriageApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MCI Triage',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark,

      // ── Named Routes ──────────────────────────────────────────────────────
      initialRoute: '/',
      routes: {
        '/':       (_) => const HomeScreen(),
        '/triage': (_) => const TriageWizardScreen(),
        '/result': (_) => const TriageResultScreen(),
        '/detail': (_) => const DetailFormScreen(),
        '/list':   (_) => const PatientListScreen(),
      },
    );
  }
}
