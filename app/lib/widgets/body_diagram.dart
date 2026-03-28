// lib/widgets/body_diagram.dart
import 'package:flutter/material.dart';
import '../models/app_theme.dart';
import '../models/patient.dart';
import 'shared_widgets.dart';

// ─── Custom Painter for the silhouette + zones ─────────────────────────────

class _BodyPainter extends CustomPainter {
  final List<BodyZone> zones;
  final List<BodyZoneEntry> entries;
  final String? hoveredId;

  _BodyPainter({
    required this.zones,
    required this.entries,
    this.hoveredId,
  });

  Color _fillFor(String zoneId) {
    final entry = entries.where((e) => e.zoneId == zoneId).firstOrNull;
    if (entry == null) return Colors.white.withValues(alpha: 0.04);
    return SeverityColors.forSeverity(entry.severity).withValues(alpha: 0.5);
  }

  Color _strokeFor(String zoneId) {
    final entry = entries.where((e) => e.zoneId == zoneId).firstOrNull;
    if (entry == null) return Colors.white.withValues(alpha: hoveredId == zoneId ? 0.4 : 0.15);
    return SeverityColors.forSeverity(entry.severity);
  }

  void _drawSilhouette(Canvas canvas, Size size) {
    final bodyPaint = Paint()..color = const Color(0xFF2A2A3E);

    // Draw head as ellipse
    canvas.drawOval(
      Rect.fromCenter(
        center: Offset(size.width * 0.5, size.height * 0.11),
        width: size.width * 0.225,
        height: size.height * 0.15,
      ),
      bodyPaint,
    );

    // Draw all body part rects
    final rects = [
      _rect(size, 0.4425, 0.1887, 0.115, 0.0566), // neck
      _rect(size, 0.325,  0.2453, 0.35,  0.1509),  // chest
      _rect(size, 0.35,   0.3962, 0.3,   0.1132),  // abdomen
      _rect(size, 0.3625, 0.5094, 0.275, 0.0943),  // pelvis
      _rect(size, 0.2,    0.2453, 0.1375,0.1698),  // l upper arm
      _rect(size, 0.675,  0.2453, 0.1375,0.1698),  // r upper arm
      _rect(size, 0.15,   0.4151, 0.1125,0.1509),  // l forearm
      _rect(size, 0.7375, 0.4151, 0.1125,0.1509),  // r forearm
      _rect(size, 0.345,  0.6038, 0.1375,0.1698),  // l thigh
      _rect(size, 0.5175, 0.6038, 0.1375,0.1698),  // r thigh
      _rect(size, 0.325,  0.7736, 0.1375,0.1887),  // l lower leg
      _rect(size, 0.5375, 0.7736, 0.1375,0.1887),  // r lower leg
    ];

    for (final r in rects) {
      canvas.drawRRect(
        RRect.fromRectAndRadius(r, const Radius.circular(8)),
        bodyPaint,
      );
    }
  }

  Rect _rect(Size s, double lf, double tf, double wf, double hf) =>
      Rect.fromLTWH(s.width * lf, s.height * tf, s.width * wf, s.height * hf);

  @override
  void paint(Canvas canvas, Size size) {
    _drawSilhouette(canvas, size);

    for (final zone in zones) {
      final rect = Rect.fromLTWH(
        size.width * zone.rect.left,
        size.height * zone.rect.top,
        size.width * zone.rect.width,
        size.height * zone.rect.height,
      );
      final rRect = RRect.fromRectAndRadius(rect, const Radius.circular(8));
      final hasEntry = entries.any((e) => e.zoneId == zone.id);

      // Fill
      canvas.drawRRect(rRect, Paint()..color = _fillFor(zone.id));

      // Stroke
      canvas.drawRRect(
        rRect,
        Paint()
          ..color = _strokeFor(zone.id)
          ..style = PaintingStyle.stroke
          ..strokeWidth = hasEntry ? 2.5 : 1,
      );

      // Label
      final tp = TextPainter(
        text: TextSpan(
          text: zone.label,
          style: TextStyle(
            fontSize: hasEntry ? 10 : 8,
            fontWeight: hasEntry ? FontWeight.w700 : FontWeight.w400,
            color: hasEntry ? Colors.white : Colors.white38,
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout(maxWidth: rect.width);
      tp.paint(
        canvas,
        Offset(rect.left + (rect.width - tp.width) / 2,
            rect.top + (rect.height - tp.height) / 2),
      );
    }
  }

  @override
  bool shouldRepaint(_BodyPainter old) =>
      old.entries != entries || old.hoveredId != hoveredId;
}



// ─── Body Diagram Widget ───────────────────────────────────────────────────

class BodyDiagram extends StatefulWidget {
  final List<BodyZoneEntry> entries;
  final void Function(List<BodyZoneEntry>) onChange;

  const BodyDiagram({super.key, required this.entries, required this.onChange});

  @override
  State<BodyDiagram> createState() => _BodyDiagramState();
}

class _BodyDiagramState extends State<BodyDiagram> {
  bool _isFront = true;
  String? _hoveredId;

  List<BodyZone> get _zones => _isFront ? frontZones : backZones;

  void _onTap(BuildContext context, Offset localPos, Size size) {
    for (final zone in _zones.reversed) {
      final rect = Rect.fromLTWH(
        size.width * zone.rect.left,
        size.height * zone.rect.top,
        size.width * zone.rect.width,
        size.height * zone.rect.height,
      );
      if (rect.contains(localPos)) {
        _openZoneSheet(context, zone);
        return;
      }
    }
  }

  void _openZoneSheet(BuildContext context, BodyZone zone) {
    final existing =
        widget.entries.where((e) => e.zoneId == zone.id).firstOrNull;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _ZoneSheet(
        zone: zone,
        existing: existing,
        onSave: (entry) {
          final updated = [
            ...widget.entries.where((e) => e.zoneId != zone.id),
            entry,
          ];
          widget.onChange(updated);
        },
        onClear: () {
          widget.onChange(
              widget.entries.where((e) => e.zoneId != zone.id).toList());
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // View toggle
        Row(
          children: [
            _ViewTab('Front View', _isFront, () => setState(() => _isFront = true)),
            const SizedBox(width: 8),
            _ViewTab('Back View', !_isFront, () => setState(() => _isFront = false)),
          ],
        ),
        const SizedBox(height: 16),

        // Diagram
        Center(
          child: LayoutBuilder(builder: (ctx, constraints) {
            final w = constraints.maxWidth.clamp(0.0, 360.0);
            final h = w * (530 / 400);
            return GestureDetector(
              onTapUp: (d) => _onTap(ctx, d.localPosition, Size(w, h)),
              child: SizedBox(
                width: w,
                height: h,
                child: CustomPaint(
                  painter: _BodyPainter(
                    zones: _zones,
                    entries: widget.entries,
                    hoveredId: _hoveredId,
                  ),
                ),
              ),
            );
          }),
        ),

        // Marked zones summary
        if (widget.entries.isNotEmpty) ...[
          const SizedBox(height: 16),
          const SectionHeader('Marked Zones'),
          ...widget.entries.map((e) => _ZoneSummaryRow(entry: e)),
        ],
      ],
    );
  }
}

// ─── View Tab ─────────────────────────────────────────────────────────────────

class _ViewTab extends StatelessWidget {
  final String label;
  final bool active;
  final VoidCallback onTap;
  const _ViewTab(this.label, this.active, this.onTap);

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.symmetric(vertical: 14),
          decoration: BoxDecoration(
            color: active ? AppColors.accent : Colors.transparent,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: active ? AppColors.accent : AppColors.border,
              width: 2,
            ),
          ),
          alignment: Alignment.center,
          child: Text(
            label,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              color: active ? Colors.white : AppColors.textSecondary,
            ),
          ),
        ),
      ),
    );
  }
}

// ─── Zone Summary Row ─────────────────────────────────────────────────────────

class _ZoneSummaryRow extends StatelessWidget {
  final BodyZoneEntry entry;
  const _ZoneSummaryRow({required this.entry});

  @override
  Widget build(BuildContext context) {
    final color = SeverityColors.forSeverity(entry.severity);
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.border, width: 0.5)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(entry.zoneLabel,
                style: const TextStyle(color: AppColors.textSecondary, fontSize: 15)),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(entry.severity,
                style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w700)),
          ),
          const SizedBox(width: 8),
          Text(entry.primaryInjury,
              style: const TextStyle(color: AppColors.textMuted, fontSize: 13)),
        ],
      ),
    );
  }
}

// ─── Zone Bottom Sheet ────────────────────────────────────────────────────────

class _ZoneSheet extends StatefulWidget {
  final BodyZone zone;
  final BodyZoneEntry? existing;
  final void Function(BodyZoneEntry) onSave;
  final VoidCallback onClear;

  const _ZoneSheet({
    required this.zone,
    this.existing,
    required this.onSave,
    required this.onClear,
  });

  @override
  State<_ZoneSheet> createState() => _ZoneSheetState();
}

class _ZoneSheetState extends State<_ZoneSheet> {
  String _primary = '';
  List<String> _findings = [];
  String _severity = 'Minor';
  final _notesCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    if (widget.existing != null) {
      _primary = widget.existing!.primaryInjury;
      _findings = List.from(widget.existing!.findings);
      _severity = widget.existing!.severity;
      _notesCtrl.text = widget.existing!.notes ?? '';
    }
  }

  @override
  void dispose() {
    _notesCtrl.dispose();
    super.dispose();
  }

  void _save() {
    if (_primary.isEmpty) { Navigator.pop(context); return; }
    widget.onSave(BodyZoneEntry(
      zoneId: widget.zone.id,
      zoneLabel: widget.zone.label,
      primaryInjury: _primary,
      findings: _findings,
      severity: _severity,
      notes: _notesCtrl.text.isEmpty ? null : _notesCtrl.text,
      timestamp: DateTime.now(),
    ));
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.75,
      maxChildSize: 0.95,
      minChildSize: 0.5,
      builder: (_, ctrl) => Container(
        decoration: const BoxDecoration(
          color: Color(0xFF111111),
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: ListView(
          controller: ctrl,
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 36),
          children: [
            // Handle
            Center(
              child: Container(
                width: 40, height: 4,
                margin: const EdgeInsets.symmetric(vertical: 12),
                decoration: BoxDecoration(
                  color: AppColors.border,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),

            Text(widget.zone.label,
                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: Colors.white)),
            const SizedBox(height: 20),

            const SectionHeader('Primary Injury'),
            Wrap(
              spacing: 8, runSpacing: 8,
              children: kInjuryPrimary.map((p) {
                final sel = _primary == p;
                return GestureDetector(
                  onTap: () => setState(() => _primary = p),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 120),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    decoration: BoxDecoration(
                      color: sel ? AppColors.accent.withValues(alpha: 0.15) : Colors.transparent,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: sel ? AppColors.accent : AppColors.border, width: 2),
                    ),
                    child: Text(p, style: TextStyle(
                      fontSize: 14, fontWeight: FontWeight.w600,
                      color: sel ? AppColors.accent : AppColors.textSecondary,
                    )),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 20),

            const SectionHeader('Additional Findings'),
            Wrap(
              spacing: 8, runSpacing: 8,
              children: kInjuryFindings.map((f) {
                final sel = _findings.contains(f);
                return GestureDetector(
                  onTap: () => setState(() =>
                      sel ? _findings.remove(f) : _findings.add(f)),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 120),
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: sel ? const Color(0xFFF39C12).withValues(alpha: 0.15) : Colors.transparent,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: sel ? const Color(0xFFF39C12) : AppColors.border, width: 2),
                    ),
                    child: Text(f, style: TextStyle(
                      fontSize: 14, fontWeight: FontWeight.w600,
                      color: sel ? const Color(0xFFF39C12) : AppColors.textSecondary,
                    )),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 20),

            const SectionHeader('Severity'),
            Row(
              children: ['Minor', 'Moderate', 'Severe'].map((s) {
                final sel = _severity == s;
                final c = SeverityColors.forSeverity(s);
                return Expanded(
                  child: Padding(
                    padding: EdgeInsets.only(right: s == 'Severe' ? 0 : 8),
                    child: GestureDetector(
                      onTap: () => setState(() => _severity = s),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 120),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        decoration: BoxDecoration(
                          color: sel ? c.withValues(alpha: 0.15) : Colors.transparent,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: sel ? c : AppColors.border, width: 2),
                        ),
                        alignment: Alignment.center,
                        child: Text(s, style: TextStyle(
                          fontSize: 15, fontWeight: FontWeight.w700,
                          color: sel ? c : AppColors.textSecondary,
                        )),
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 24),

            Row(
              children: [
                Expanded(
                  child: GestureDetector(
                    onTap: () { widget.onClear(); Navigator.pop(context); },
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      decoration: BoxDecoration(
                        border: Border.all(color: AppColors.border),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      alignment: Alignment.center,
                      child: const Text('Clear',
                          style: TextStyle(color: AppColors.textMuted, fontSize: 16)),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  flex: 2,
                  child: GestureDetector(
                    onTap: _save,
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      decoration: BoxDecoration(
                        color: AppColors.accent,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      alignment: Alignment.center,
                      child: const Text('Save Zone',
                          style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w700)),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
