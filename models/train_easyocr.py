"""
Triage Card - ID Field OCR using EasyOCR
=========================================
No training required — EasyOCR reads the ID crops directly using
pretrained weights, restricted to digits only.

Evaluates on all three splits and prints per-sample results.

Usage:
    pip install easyocr

    python ocr_easyocr.py \
        --data_dir   ./dataset/id_field \
        --output_dir ./runs/ocr_easy
"""

import re
import json
import argparse
import difflib
from pathlib import Path

import easyocr
import matplotlib.pyplot as plt
import matplotlib.image as mpimg


# ── Ground truth from filename ────────────────────────────────────────────────

def extract_text_from_filename(filename):
    """
    Filenames: {task_id}__{index}__{id_text}.jpg
    Returns the id_text part.
    """
    stem  = Path(filename).stem
    parts = stem.split("__", 2)
    if len(parts) == 3:
        return parts[2].replace("_", " ").strip()
    return None


# ── Metrics ───────────────────────────────────────────────────────────────────

def character_error_rate(pred, target):
    if len(target) == 0:
        return 0.0 if len(pred) == 0 else 1.0
    matcher  = difflib.SequenceMatcher(None, pred, target)
    distance = len(pred) + len(target) - 2 * sum(
        t.size for t in matcher.get_matching_blocks()
    )
    return distance / len(target)


# ── Run EasyOCR on one split ──────────────────────────────────────────────────

def evaluate_split(split_dir, reader, split_name):
    split_dir = Path(split_dir)
    if not split_dir.exists():
        print(f"  [skip] {split_name} directory not found: {split_dir}")
        return None

    samples = []
    for img_path in sorted(split_dir.glob("*.jpg")):
        text = extract_text_from_filename(img_path.name)
        if text is None or text.lower() == "unknown" or text.strip() == "":
            continue
        samples.append((str(img_path), text))

    if not samples:
        print(f"  [skip] No labeled samples in {split_name}")
        return None

    print(f"\n  ── {split_name.upper()} ({len(samples)} samples) ──")
    print(f"  {'Ground Truth':<20} {'Raw OCR':<20} {'Predicted':<15} {'CER':>6}  ")
    print(f"  {'─'*65}")

    results     = []
    total_cer   = 0.0
    exact_match = 0

    for img_path, ground_truth in samples:
        # Run EasyOCR — allowlist restricts output to digits only
        raw_results = reader.readtext(
            img_path,
            allowlist="0123456789",
            detail=1,
            paragraph=False
        )

        # Pick the result with highest confidence if multiple detections
        if raw_results:
            raw_results_sorted = sorted(raw_results, key=lambda x: x[2], reverse=True)
            raw_text    = raw_results_sorted[0][1]
            confidence  = raw_results_sorted[0][2]
        else:
            raw_text   = ""
            confidence = 0.0

        # Strip any non-digit characters as a safety net
        predicted = re.sub(r"[^0-9]", "", raw_text).strip()

        cer    = character_error_rate(predicted, ground_truth)
        match  = "✓" if predicted == ground_truth else "✗"
        total_cer   += cer
        exact_match += int(predicted == ground_truth)

        print(f"  {ground_truth:<20} {raw_text:<20} {predicted:<15} {cer:>6.3f}  {match}  (conf: {confidence:.2f})")

        results.append({
            "image":        img_path,
            "ground_truth": ground_truth,
            "raw_ocr":      raw_text,
            "predicted":    predicted,
            "cer":          cer,
            "confidence":   confidence,
            "correct":      predicted == ground_truth,
        })

    n         = len(samples)
    mean_cer  = total_cer / n
    exact_acc = exact_match / n

    print(f"\n  Mean CER     : {mean_cer:.4f}  (lower is better, 0.0 = perfect)")
    print(f"  Exact match  : {exact_acc:.4f}  ({exact_match}/{n} correct)")

    return {
        "split":       split_name,
        "n":           n,
        "mean_cer":    mean_cer,
        "exact_match": exact_acc,
        "results":     results,
    }


# ── Visualize failures ────────────────────────────────────────────────────────

def save_failure_grid(all_results, output_dir):
    """Save a grid of images where OCR was wrong for visual inspection."""
    failures = [r for r in all_results if not r["correct"]]

    if not failures:
        print("\n  No failures to visualize — perfect score!")
        return

    n    = len(failures)
    cols = min(4, n)
    rows = (n + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 3, rows * 3))
    axes = [axes] if rows == 1 and cols == 1 else axes
    axes = [ax for row in (axes if rows > 1 else [axes]) for ax in (row if cols > 1 else [row])]

    for i, failure in enumerate(failures):
        ax  = axes[i]
        img = mpimg.imread(failure["image"])
        ax.imshow(img)
        ax.set_title(
            f"GT: {failure['ground_truth']}\n"
            f"Pred: {failure['predicted']}\n"
            f"CER: {failure['cer']:.2f}",
            fontsize=9
        )
        ax.axis("off")

    # Hide unused axes
    for j in range(i + 1, len(axes)):
        axes[j].axis("off")

    plt.suptitle("OCR Failures", fontsize=12)
    plt.tight_layout()
    path = str(Path(output_dir) / "ocr_failures.png")
    plt.savefig(path)
    plt.close()
    print(f"\n  Saved failure grid → {path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="EasyOCR evaluation for triage card IDs")
    parser.add_argument("--data_dir",   required=True, help="Path to dataset/id_field/")
    parser.add_argument("--output_dir", required=True, help="Where to save results")
    parser.add_argument("--gpu",        action="store_true", help="Use GPU if available")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*52}")
    print(f"  EasyOCR — Triage Card ID Recognition")
    print(f"  GPU: {'yes' if args.gpu else 'no (CPU mode)'}")
    print(f"{'='*52}\n")

    # Initialize EasyOCR — downloads models on first run (~100MB)
    print("  Initializing EasyOCR (downloads ~100MB on first run)...\n")
    reader = easyocr.Reader(["en"], gpu=args.gpu)

    data_dir    = Path(args.data_dir)
    all_results = []
    summaries   = []

    for split in ["train", "val", "test"]:
        result = evaluate_split(data_dir / split, reader, split)
        if result:
            all_results.extend(result["results"])
            summaries.append(result)

    # ── Overall summary ──
    if summaries:
        print(f"\n{'='*52}")
        print(f"  Overall Summary")
        print(f"{'='*52}")
        print(f"  {'Split':<10} {'Samples':>8} {'Mean CER':>10} {'Exact Match':>12}")
        print(f"  {'─'*44}")
        for s in summaries:
            print(f"  {s['split']:<10} {s['n']:>8} {s['mean_cer']:>10.4f} {s['exact_match']:>12.4f}")

        total_n     = sum(s["n"] for s in summaries)
        total_cer   = sum(s["mean_cer"] * s["n"] for s in summaries) / total_n
        total_exact = sum(s["exact_match"] * s["n"] for s in summaries) / total_n
        print(f"  {'─'*44}")
        print(f"  {'TOTAL':<10} {total_n:>8} {total_cer:>10.4f} {total_exact:>12.4f}")

    save_failure_grid(all_results, output_dir)

    # Save full results to JSON
    json_results = []
    for r in all_results:
        json_results.append({k: v for k, v in r.items() if k != "image"})

    summary_path = output_dir / "easyocr_results.json"
    with open(summary_path, "w") as f:
        json.dump({
            "summaries":   summaries,
            "per_sample":  json_results,
        }, f, indent=2, default=str)
    print(f"  Saved full results → {summary_path}")

    print(f"\n{'='*52}")
    print(f"  Done!")
    print(f"{'='*52}\n")

    print("  Next steps:")
    print("  - If exact match > 0.85: EasyOCR is good enough, use it directly")
    print("  - If exact match < 0.85: check the failure grid and consider")
    print("    preprocessing (contrast boost, upscaling) before OCR\n")


if __name__ == "__main__":
    main()