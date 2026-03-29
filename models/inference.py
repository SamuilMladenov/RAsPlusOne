"""
Triage Card - Inference Pipeline
==================================
Takes a raw card photo and outputs a structured triage result
by running all trained models in sequence.

Pipeline:
  1. Load raw card photo
  2. For each checkbox region (positions learned from training data):
       a. Crop the region
       b. Model A  → ticked or unticked?
       c. If ticked → route to section model → which label?
  3. Run EasyOCR on the ID field region
  4. Output structured JSON result

Usage:
    pip install torch torchvision easyocr pillow

    # Single image
    python inference.py \
        --image      ./input_photos/photo.jpg \
        --models_dir ./runs/run3breakdown \
        --output_dir ./results

    # Batch — all images in a folder
    python inference.py \
        --image_dir  ./new_cards \
        --models_dir ./runs/run3breakdown \
        --output_dir ./results
"""

import re
import json
import argparse
import time
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import easyocr


# ── Average bbox positions per label (% of image, from training data) ─────────
# Format: (x, y, width, height) all as percentages of image dimensions

REGION_MAP = {
    "ID_FIELD":             (12.86, 15.71, 15.43,  4.82),

    "PRIORITY_RED":         (17.61, 26.33,  3.87,  2.86),
    "PRIORITY_YELLOW":      (38.00, 26.04,  3.99,  2.87),
    "PRIORITY_GREEN":       (58.57, 26.19,  3.95,  2.89),
    "PRIORITY_BLACK":       (79.15, 26.14,  3.99,  2.80),

    "RESP_NOT_BREATHING":   (13.39, 38.71,  3.32,  2.41),
    "RESP_LESS_10":         (51.28, 38.70,  3.35,  2.51),
    "RESP_10_30":           (10.33, 42.99,  3.31,  2.38),
    "RESP_MORE_30":         (50.35, 42.91,  3.21,  2.24),

    "PERF_RADIAL_PRESENT":  (13.57, 52.15,  3.20,  2.29),
    "PERF_NO_RADIAL":       (51.16, 52.16,  3.40,  2.45),
    "PERF_CAPILLARY_LESS_2":(12.58, 56.07,  3.33,  2.37),
    "PERF_CAPILLARY_MORE_2":(51.43, 56.00,  3.31,  2.42),
    "PERF_SEVERE_BLEEDING": (10.46, 60.19,  3.24,  2.31),

    "MENTAL_ALERT":         (11.69, 69.07,  3.25,  2.36),
    "MENTAL_UNRESPONSIVE":  (50.22, 69.47,  3.27,  2.37),
    "MENTAL_CANNOT_FOLLOW": (11.60, 73.14,  3.28,  2.33),

    "DEST_TRAUMA_CENTER":   (10.87, 82.01,  3.08,  2.24),
    "DEST_GENERAL_HOSPITAL":(50.42, 82.72,  3.31,  2.39),
    "DEST_BURN_UNIT":       (11.76, 86.24,  3.39,  2.28),
    "DEST_OTHER":           (49.43, 86.68,  3.27,  2.27),
}

# Section routing — maps each label to its section model
SECTIONS = {
    "priority":     ["PRIORITY_RED", "PRIORITY_YELLOW", "PRIORITY_GREEN", "PRIORITY_BLACK"],
    "respiration":  ["RESP_NOT_BREATHING", "RESP_LESS_10", "RESP_10_30", "RESP_MORE_30"],
    "perfusion":    ["PERF_RADIAL_PRESENT", "PERF_NO_RADIAL", "PERF_CAPILLARY_LESS_2",
                     "PERF_CAPILLARY_MORE_2", "PERF_SEVERE_BLEEDING"],
    "mental_status":["MENTAL_ALERT", "MENTAL_UNRESPONSIVE", "MENTAL_CANNOT_FOLLOW"],
    "destination":  ["DEST_TRAUMA_CENTER", "DEST_GENERAL_HOSPITAL",
                     "DEST_BURN_UNIT", "DEST_OTHER"],
}

# Reverse map: label → section name
LABEL_TO_SECTION = {
    label: section
    for section, labels in SECTIONS.items()
    for label in labels
}

CROP_PADDING = 6


# ── TinyCNN (must match training architecture) ────────────────────────────────

class TinyCNN(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16), nn.ReLU(inplace=True), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32), nn.ReLU(inplace=True), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64), nn.ReLU(inplace=True), nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.5),
            nn.Linear(64 * 8 * 8, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        return self.classifier(self.features(x))


# ── Device ────────────────────────────────────────────────────────────────────

def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


# ── Transform (must match val_tf from training) ───────────────────────────────

val_transform = transforms.Compose([
    transforms.Resize((64, 64)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])


# ── Load models ───────────────────────────────────────────────────────────────

def load_model(path, device):
    checkpoint  = torch.load(path, map_location=device)
    num_classes = checkpoint["num_classes"]
    model       = TinyCNN(num_classes=num_classes).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, checkpoint["classes"]


def load_all_models(models_dir, device):
    models_dir = Path(models_dir)
    loaded = {}

    # Model A — ticked/unticked
    path_a = models_dir / "model_a_state.pth"
    if not path_a.exists():
        raise FileNotFoundError(f"Model A not found: {path_a}")
    loaded["model_a"], loaded["classes_a"] = load_model(path_a, device)
    print(f"  ✓ Model A (ticked/unticked)  → {path_a}")

    # Section models
    for section in SECTIONS:
        path = models_dir / f"model_{section}.pth"
        if path.exists():
            model, classes = load_model(path, device)
            loaded[f"model_{section}"]   = model
            loaded[f"classes_{section}"] = classes
            print(f"  ✓ Section model: {section:<16} → {path}")
        else:
            print(f"  [warn] Section model not found: {path}")

    return loaded


# ── Crop utility ──────────────────────────────────────────────────────────────

def crop_region(image, x_pct, y_pct, w_pct, h_pct, padding=CROP_PADDING):
    """Crop a region defined in percentage coordinates."""
    img_w, img_h = image.size
    x  = int(x_pct / 100 * img_w)
    y  = int(y_pct / 100 * img_h)
    w  = int(w_pct / 100 * img_w)
    h  = int(h_pct / 100 * img_h)
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(img_w, x + w + padding)
    y2 = min(img_h, y + h + padding)
    return image.crop((x1, y1, x2, y2))


# ── Inference ─────────────────────────────────────────────────────────────────

def predict_checkbox(crop, model, classes, device):
    """Run a TinyCNN on a crop and return (class_name, confidence)."""
    tensor  = val_transform(crop).unsqueeze(0).to(device)
    with torch.no_grad():
        logits = model(tensor)
        probs  = torch.softmax(logits, dim=1)[0]
        idx    = probs.argmax().item()
    return classes[idx], probs[idx].item()


def run_inference(image_path, models, ocr_reader, device):
    """
    Run the full inference pipeline on one card image.
    Returns a dict with the parsed triage result.
    """
    t0    = time.time()
    image = Image.open(image_path).convert("RGB")

    result = {
        "image":        str(image_path),
        "id":           None,
        "priority":     None,
        "respiration":  None,
        "perfusion":    None,
        "mental_status":None,
        "destination":  None,
        "raw_detections": {},
        "processing_time_ms": None,
    }

    # ── Step 1: Read ID field with EasyOCR ──
    x, y, w, h     = REGION_MAP["ID_FIELD"]
    id_crop        = crop_region(image, x, y, w, h, padding=8)
    ocr_results    = ocr_reader.readtext(
        np.array(id_crop), allowlist="0123456789", detail=1, paragraph=False
    )
    if ocr_results:
        best        = max(ocr_results, key=lambda r: r[2])
        raw_id      = re.sub(r"[^0-9]", "", best[1])
        result["id"] = raw_id if raw_id else None
    result["raw_detections"]["ID_FIELD"] = result["id"]

    # ── Step 2: Run checkbox models ──
    # Track ticked labels per section for mutual exclusivity
    section_ticked = {s: [] for s in SECTIONS}

    for label, (x, y, w, h) in REGION_MAP.items():
        if label == "ID_FIELD":
            continue

        crop = crop_region(image, x, y, w, h)

        # Model A — is it ticked?
        state, state_conf = predict_checkbox(
            crop, models["model_a"], models["classes_a"], device
        )

        if state == "ticked":
            section = LABEL_TO_SECTION.get(label)
            if section and f"model_{section}" in models:
                # Section model — which specific label?
                pred_label, label_conf = predict_checkbox(
                    crop,
                    models[f"model_{section}"],
                    models[f"classes_{section}"],
                    device
                )
                section_ticked[section].append({
                    "label":      pred_label,
                    "confidence": label_conf,
                    "state_conf": state_conf,
                })
            else:
                # No section model — use the region label directly
                section_ticked[section].append({
                    "label":      label,
                    "confidence": state_conf,
                    "state_conf": state_conf,
                })

        result["raw_detections"][label] = {
            "state":      state,
            "state_conf": round(state_conf, 3),
        }

    # ── Step 3: Pick winner per section (highest confidence ticked) ──
    section_to_result_key = {
        "priority":     "priority",
        "respiration":  "respiration",
        "perfusion":    "perfusion",
        "mental_status":"mental_status",
        "destination":  "destination",
    }

    for section, ticked_list in section_ticked.items():
        if ticked_list:
            # Pick the one with highest label confidence
            winner = max(ticked_list, key=lambda x: x["confidence"])
            result[section_to_result_key[section]] = winner["label"]

    result["processing_time_ms"] = round((time.time() - t0) * 1000)
    return result


# ── Visualization ─────────────────────────────────────────────────────────────

def visualize_result(image_path, result, output_path):
    """Draw bounding boxes and predictions on the card image."""
    image = Image.open(image_path).convert("RGB")
    draw  = ImageDraw.Draw(image)
    img_w, img_h = image.size

    # Color per state
    state_colors = {"ticked": "#00CC44", "unticked": "#888888"}

    for label, (x_pct, y_pct, w_pct, h_pct) in REGION_MAP.items():
        x  = int(x_pct / 100 * img_w)
        y  = int(y_pct / 100 * img_h)
        w  = int(w_pct / 100 * img_w)
        h  = int(h_pct / 100 * img_h)

        if label == "ID_FIELD":
            draw.rectangle([x, y, x+w, y+h], outline="#0088FF", width=3)
            if result["id"]:
                draw.text((x, y - 18), f"ID: {result['id']}", fill="#0088FF")
            continue

        detection = result["raw_detections"].get(label, {})
        state     = detection.get("state", "unticked") if isinstance(detection, dict) else "unticked"
        color     = state_colors.get(state, "#888888")
        width     = 3 if state == "ticked" else 1

        draw.rectangle([x, y, x+w, y+h], outline=color, width=width)

    # Draw final result summary in top-left corner
    summary_lines = [
        f"ID: {result['id'] or '?'}",
        f"Priority: {result['priority'] or '?'}",
        f"Respiration: {result['respiration'] or '?'}",
        f"Perfusion: {result['perfusion'] or '?'}",
        f"Mental: {result['mental_status'] or '?'}",
        f"Destination: {result['destination'] or '?'}",
    ]
    bg_h = len(summary_lines) * 22 + 10
    draw.rectangle([5, 5, 320, bg_h], fill="white", outline="black")
    for i, line in enumerate(summary_lines):
        draw.text((10, 10 + i * 22), line, fill="black")

    image.save(str(output_path))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Triage card inference pipeline")
    parser.add_argument("--image",      help="Path to a single card image")
    parser.add_argument("--image_dir",  help="Path to folder of card images")
    parser.add_argument("--models_dir", required=True,
                        help="Path to ./runs/checkbox (contains model_a_state.pth etc.)")
    parser.add_argument("--output_dir", required=True, help="Where to save results")
    parser.add_argument("--visualize",  action="store_true",
                        help="Save annotated card images")
    parser.add_argument("--gpu",        action="store_true",
                        help="Use GPU for EasyOCR")
    args = parser.parse_args()

    if not args.image and not args.image_dir:
        parser.error("Provide either --image or --image_dir")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    device = get_device()
    print(f"\n{'='*52}")
    print(f"  Triage Card Inference Pipeline")
    print(f"  Device: {device}")
    print(f"{'='*52}\n")

    # Load models
    print("  Loading checkpoint models...")
    models = load_all_models(args.models_dir, device)

    # Load EasyOCR
    print("\n  Loading EasyOCR...")
    ocr_reader = easyocr.Reader(["en"], gpu=args.gpu)

    # Collect images
    if args.image:
        image_paths = [Path(args.image)]
    else:
        exts = ["*.jpg", "*.JPG", "*.jpeg", "*.JPEG", "*.png", "*.PNG"]
        image_paths = sorted(
            p for ext in exts for p in Path(args.image_dir).glob(ext)
        )

    print(f"\n  Processing {len(image_paths)} image(s)...\n")

    all_results = []

    for image_path in image_paths:
        print(f"  {image_path.name}")
        try:
            result = run_inference(image_path, models, ocr_reader, device)
            all_results.append(result)

            # Print result
            print(f"    ID           : {result['id'] or '(not read)'}")
            print(f"    Priority     : {result['priority'] or '(none ticked)'}")
            print(f"    Respiration  : {result['respiration'] or '(none ticked)'}")
            print(f"    Perfusion    : {result['perfusion'] or '(none ticked)'}")
            print(f"    Mental status: {result['mental_status'] or '(none ticked)'}")
            print(f"    Destination  : {result['destination'] or '(none ticked)'}")
            print(f"    Time         : {result['processing_time_ms']}ms\n")

            # Save individual JSON
            json_path = output_dir / f"{image_path.stem}_result.json"
            with open(json_path, "w") as f:
                json.dump(result, f, indent=2)

            # Visualize
            if args.visualize:
                vis_path = output_dir / f"{image_path.stem}_annotated.jpg"
                visualize_result(image_path, result, vis_path)
                print(f"    Saved annotated image → {vis_path}")

        except Exception as e:
            print(f"    [error] {e}\n")

    # Save combined results
    if len(all_results) > 1:
        combined_path = output_dir / "all_results.json"
        with open(combined_path, "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"  Saved combined results → {combined_path}")

    print(f"\n{'='*52}")
    print(f"  Done! Processed {len(all_results)} card(s)")
    print(f"  Results saved to: {output_dir}")
    print(f"{'='*52}\n")


if __name__ == "__main__":
    main()