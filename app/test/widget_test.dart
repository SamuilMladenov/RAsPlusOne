// test/widget_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:rasplusone/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const TriageApp());
    expect(find.text('Triage System'), findsOneWidget);
  });
}
