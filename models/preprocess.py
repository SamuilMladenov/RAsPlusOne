"""
Triage Card - Preprocessing, Crop Generation & Dataset Split
=============================================================
Parses Label Studio native JSON export.

Each annotated region shares an `id` field across its result entries:
  - type=rectanglelabels  → the label (e.g. PRIORITY_RED)
  - type=choices          → ticked or unticked
  - type=textarea         → ID text value

We group by that shared region id to correctly pair label + state.

Usage:
    python preprocess_and_split.py \
        --images_dir ./images \
        --json_path  ./result.json \
        --output_dir ./dataset \
        --split 0.7 0.15 0.15

Output structure:
    dataset/
    ├── checkboxes/
    │   ├── train/
    │   │   ├── ticked/
    │   │   │   ├── PRIORITY_RED/
    │   │   │   └── ...
    │   │   └── unticked/
    │   │       ├── PRIORITY_RED/
    │   │       └── ...
    │   ├── val/
    │   └── test/
    └── id_field/
        ├── train/   (filenames encode the ID text value)
        ├── val/
        └── test/
"""

import os
import json
import random
import argparse
import cv2
from pathlib import Path
from collections import defaultdict


ID_LABEL     = "ID_FIELD"
CROP_PADDING = 6


# ── Crop utility ──────────────────────────────────────────────────────────────

def crop_region(image, bbox, padding=CROP_PADDING):
    """Crop [x, y, w, h] pixel bbox from image with padding."""
    h_img, w_img = image.shape[:2]
    x, y, w, h = [int(v) for v in bbox]
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(w_img, x + w + padding)
    y2 = min(h_img, y + h + padding)
    return image[y1:y2, x1:x2]


def pct_to_pixels(value, orig_w, orig_h):
    """Convert Label Studio percentage coords to pixel bbox [x, y, w, h]."""
    x = value["x"] / 100 * orig_w
    y = value["y"] / 100 * orig_h
    w = value["width"]  / 100 * orig_w
    h = value["height"] / 100 * orig_h
    return [x, y, w, h]


# ── Parse Label Studio native JSON ────────────────────────────────────────────

def parse_label_studio(json_path, images_dir):
    """
    Parse Label Studio native JSON export.

    Regions are linked by a shared `id` across result entries within
    one annotation. We group all result items by that id, then extract:
      - label      from type=rectanglelabels
      - state      from type=choices
      - id_text    from type=textarea
    """
    with open(json_path, "r") as f:
        tasks = json.load(f)

    records = []

    for task in tasks:
        # Resolve image filename
        image_data = task.get("data", {}).get("image", "")
        base_name  = os.path.basename(image_data)
        image_path = os.path.join(images_dir, base_name)

        if not os.path.exists(image_path):
            # Try stripping Label Studio upload prefix
            base_name  = base_name.split("-", 1)[-1] if "-" in base_name else base_name
            image_path = os.path.join(images_dir, base_name)

        if not os.path.exists(image_path):
            print(f"  [warn] Image not found: {image_path}")
            continue

        annotations = task.get("annotations", [])
        if not annotations:
            continue

        # Use the first (or only) annotation
        result_items = annotations[0].get("result", [])

        # Group result items by their shared region id
        by_region = defaultdict(dict)
        for item in result_items:
            region_id   = item.get("id")
            item_type   = item.get("type")
            value       = item.get("value", {})
            orig_w      = item.get("original_width",  3060)
            orig_h      = item.get("original_height", 4080)

            if item_type == "rectanglelabels":
                labels = value.get("rectanglelabels", [])
                by_region[region_id]["label"] = labels[0] if labels else None
                by_region[region_id]["bbox"]  = pct_to_pixels(value, orig_w, orig_h)

            elif item_type == "choices":
                choices = value.get("choices", [])
                by_region[region_id]["state"] = choices[0] if choices else "unticked"

            elif item_type == "textarea":
                texts = value.get("text", [])
                by_region[region_id]["id_text"] = texts[0] if texts else ""
                if "bbox" not in by_region[region_id]:
                    by_region[region_id]["bbox"] = pct_to_pixels(value, orig_w, orig_h)

        # Build checkboxes and id_fields from grouped regions
        checkboxes = []
        id_fields  = []

        for region_id, region in by_region.items():
            label = region.get("label")
            bbox  = region.get("bbox")

            if not label or not bbox:
                continue

            if label == ID_LABEL:
                id_fields.append({
                    "text": region.get("id_text", ""),
                    "bbox": bbox
                })
            else:
                checkboxes.append({
                    "label": label,
                    "state": region.get("state", "unticked"),
                    "bbox":  bbox
                })

        records.append({
            "image_path": image_path,
            "task_id":    task.get("id", 0),
            "checkboxes": checkboxes,
            "id_fields":  id_fields
        })

    return records


# ── Dataset split ─────────────────────────────────────────────────────────────

def split_records(records, train_ratio, val_ratio, seed=42):
    random.seed(seed)
    shuffled = records[:]
    random.shuffle(shuffled)
    n       = len(shuffled)
    n_train = int(n * train_ratio)
    n_val   = int(n * val_ratio)
    return (
        shuffled[:n_train],
        shuffled[n_train:n_train + n_val],
        shuffled[n_train + n_val:]
    )


# ── Process one split ─────────────────────────────────────────────────────────

def process_split(records, split_name, output_dir):
    checkbox_base = Path(output_dir) / "checkboxes" / split_name
    id_base       = Path(output_dir) / "id_field"   / split_name

    stats = {"checkboxes": 0, "id_fields": 0, "skipped": 0}

    for record in records:
        image = cv2.imread(record["image_path"])
        if image is None:
            print(f"  [error] Could not read: {record['image_path']}")
            stats["skipped"] += 1
            continue

        task_id = record["task_id"]

        # ── Checkbox crops ──
        for i, cb in enumerate(record["checkboxes"]):
            crop = crop_region(image, cb["bbox"])
            if crop.size == 0:
                continue

            out_dir = checkbox_base / cb["state"] / cb["label"]
            out_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{task_id}__{i}__{cb['label']}.jpg"
            cv2.imwrite(str(out_dir / filename), crop)
            stats["checkboxes"] += 1

        # ── ID field crops ──
        for j, id_field in enumerate(record["id_fields"]):
            crop = crop_region(image, id_field["bbox"])
            if crop.size == 0:
                continue

            id_base.mkdir(parents=True, exist_ok=True)

            # Encode ground truth text in filename for easy OCR training
            text = id_field["text"].strip().replace("/", "_").replace(" ", "_") or "unknown"
            filename = f"{task_id}__{j}__{text}.jpg"
            cv2.imwrite(str(id_base / filename), crop)
            stats["id_fields"] += 1

    return stats


# ── Validation helper ─────────────────────────────────────────────────────────

def validate_records(records):
    print("  Validation summary:")
    ticked_total   = 0
    unticked_total = 0
    missing_state  = 0
    missing_id     = 0

    for r in records:
        for cb in r["checkboxes"]:
            if cb["state"] == "ticked":
                ticked_total += 1
            elif cb["state"] == "unticked":
                unticked_total += 1
            else:
                missing_state += 1
        if not r["id_fields"]:
            missing_id += 1

    print(f"    Ticked checkboxes   : {ticked_total}")
    print(f"    Unticked checkboxes : {unticked_total}")
    if missing_state:
        print(f"    [warn] Missing state: {missing_state}")
    if missing_id:
        print(f"    [warn] Images with no ID field: {missing_id}")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Triage card preprocessing & split")
    parser.add_argument("--images_dir", required=True, help="Folder with raw card images")
    parser.add_argument("--json_path",  required=True, help="Label Studio native JSON export")
    parser.add_argument("--output_dir", required=True, help="Where to write the dataset")
    parser.add_argument("--split", nargs=3, type=float, default=[0.7, 0.15, 0.15],
                        metavar=("TRAIN", "VAL", "TEST"))
    args = parser.parse_args()

    if abs(sum(args.split) - 1.0) > 1e-6:
        raise ValueError(f"Split ratios must sum to 1.0, got {sum(args.split)}")

    train_r, val_r, _ = args.split

    print(f"\n{'='*52}")
    print(f"  Triage Card Preprocessing Pipeline")
    print(f"{'='*52}")
    print(f"  Images : {args.images_dir}")
    print(f"  JSON   : {args.json_path}")
    print(f"  Output : {args.output_dir}")
    print(f"  Split  : {args.split[0]} / {args.split[1]} / {args.split[2]}")
    print(f"{'='*52}\n")

    print("Parsing Label Studio JSON...")
    records = parse_label_studio(args.json_path, args.images_dir)
    print(f"  Found {len(records)} annotated images\n")

    if not records:
        print("No records found. Check --json_path and --images_dir.")
        return

    validate_records(records)

    train_recs, val_recs, test_recs = split_records(records, train_r, val_r)
    print(f"Split: {len(train_recs)} train / {len(val_recs)} val / {len(test_recs)} test\n")

    total = {"checkboxes": 0, "id_fields": 0, "skipped": 0}
    for name, recs in [("train", train_recs), ("val", val_recs), ("test", test_recs)]:
        print(f"Processing [{name}]...")
        stats = process_split(recs, name, args.output_dir)
        print(f"  Checkboxes: {stats['checkboxes']}  |  ID fields: {stats['id_fields']}  |  Skipped: {stats['skipped']}")
        for k in total:
            total[k] += stats[k]

    print(f"\n{'='*52}")
    print(f"  Done!")
    print(f"  Checkbox crops : {total['checkboxes']}")
    print(f"  ID field crops : {total['id_fields']}")
    print(f"  Skipped        : {total['skipped']}")
    print(f"  Output         : {args.output_dir}")
    print(f"{'='*52}\n")


if __name__ == "__main__":
    main()