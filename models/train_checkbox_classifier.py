"""
Triage Card - Section-Based Checkbox Classifier
================================================
Trains one small CNN per card section, exploiting the mutual exclusivity
constraint: only one checkbox per section can be ticked.

Models trained:
  Model A — Ticked vs Unticked          (2 classes, runs on every crop)
  Model B — Priority                    (RED, YELLOW, GREEN, BLACK)
  Model C — Respiration                 (NOT_BREATHING, LESS_10, 10_30, MORE_30)
  Model D — Perfusion                   (RADIAL_PRESENT, NO_RADIAL, CAPILLARY_LESS_2,
                                         CAPILLARY_MORE_2, SEVERE_BLEEDING)
  Model E — Mental Status               (ALERT, CANNOT_FOLLOW, UNRESPONSIVE)
  Model F — Destination                 (TRAUMA_CENTER, GENERAL_HOSPITAL,
                                         BURN_UNIT, OTHER)

Inference pipeline:
  1. Crop each checkbox region from the card photo
  2. Model A  →  ticked or unticked?
  3. If ticked → route crop to section model by its position on the card
  4. Section model → which specific checkbox is it?

Folder structure expected:
    dataset/checkboxes/
    ├── train/
    │   ├── ticked/
    │   │   ├── PRIORITY_RED/
    │   │   ├── RESP_MORE_30/
    │   │   └── ...
    │   └── unticked/
    │       └── ...
    ├── val/
    └── test/

Usage:
    pip install torch torchvision matplotlib scikit-learn pillow

    python train_checkbox_classifier.py \
        --data_dir   ./dataset/checkboxes \
        --output_dir ./runs/checkbox \
        --epochs 40
"""

import json
import time
import argparse
from pathlib import Path
from collections import Counter

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from torchvision import transforms
from PIL import Image
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix


BATCH_SIZE = 8

# Section definitions — maps section name to the label folder names it owns
SECTIONS = {
    "priority": [
        "PRIORITY_RED",
        "PRIORITY_YELLOW",
        "PRIORITY_GREEN",
        "PRIORITY_BLACK",
    ],
    "respiration": [
        "RESP_NOT_BREATHING",
        "RESP_LESS_10",
        "RESP_10_30",
        "RESP_MORE_30",
    ],
    "perfusion": [
        "PERF_RADIAL_PRESENT",
        "PERF_NO_RADIAL",
        "PERF_CAPILLARY_LESS_2",
        "PERF_CAPILLARY_MORE_2",
        "PERF_SEVERE_BLEEDING",
    ],
    "mental_status": [
        "MENTAL_ALERT",
        "MENTAL_CANNOT_FOLLOW",
        "MENTAL_UNRESPONSIVE",
    ],
    "destination": [
        "DEST_TRAUMA_CENTER",
        "DEST_GENERAL_HOSPITAL",
        "DEST_BURN_UNIT",
        "DEST_OTHER",
    ],
}


# ── Device ────────────────────────────────────────────────────────────────────

def get_device():
    if torch.backends.mps.is_available():
        print("  Device: Apple MPS (Metal)")
        return torch.device("mps")
    elif torch.cuda.is_available():
        print(f"  Device: CUDA ({torch.cuda.get_device_name(0)})")
        return torch.device("cuda")
    else:
        print("  Device: CPU")
        return torch.device("cpu")


# ── Tiny CNN ──────────────────────────────────────────────────────────────────

class TinyCNN(nn.Module):
    """
    Small enough to train on dozens of examples per class.
    Input: 64x64 RGB.
    """
    def __init__(self, num_classes):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),                    # → 32x32

            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),                    # → 16x16

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),                    # → 8x8
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


# ── Transforms ────────────────────────────────────────────────────────────────

def get_transforms():
    mean = [0.485, 0.456, 0.406]
    std  = [0.229, 0.224, 0.225]

    train_tf = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.RandomRotation(20),
        transforms.ColorJitter(brightness=0.5, contrast=0.5, saturation=0.3),
        transforms.RandomAffine(degrees=0, translate=(0.15, 0.15)),
        transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.5)),
        transforms.RandomPerspective(distortion_scale=0.2, p=0.4),
        transforms.RandomGrayscale(p=0.1),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
        transforms.RandomErasing(p=0.3),
    ])

    val_tf = transforms.Compose([
        transforms.Resize((64, 64)),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])

    return train_tf, val_tf


# ── Datasets ──────────────────────────────────────────────────────────────────

class StateDataset(Dataset):
    """Model A — binary ticked (1) vs unticked (0). Uses all crops."""
    def __init__(self, root, transform=None):
        self.transform = transform
        self.samples   = []
        self.classes   = ["unticked", "ticked"]

        root = Path(root)
        for state_dir in sorted(root.iterdir()):
            if not state_dir.is_dir():
                continue
            label = 1 if state_dir.name == "ticked" else 0
            for label_dir in state_dir.iterdir():
                if not label_dir.is_dir():
                    continue
                for img_path in label_dir.glob("*.jpg"):
                    self.samples.append((str(img_path), label))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label


class SectionDataset(Dataset):
    """
    Section model dataset — only loads ticked crops belonging to
    the specified section labels.
    """
    def __init__(self, root, section_labels, transform=None, class_to_idx=None):
        self.transform    = transform
        self.samples      = []
        ticked_dir        = Path(root) / "ticked"

        if class_to_idx is not None:
            self.class_to_idx = class_to_idx
            self.classes      = sorted(class_to_idx.keys())
        else:
            # Only include labels that exist as folders
            present = [l for l in section_labels
                       if (ticked_dir / l).exists()]
            self.classes      = present
            self.class_to_idx = {c: i for i, c in enumerate(self.classes)}

        for label in self.classes:
            label_dir = ticked_dir / label
            if not label_dir.exists():
                continue
            for img_path in label_dir.glob("*.jpg"):
                self.samples.append((str(img_path), self.class_to_idx[label]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label


# ── Weighted sampler ──────────────────────────────────────────────────────────

def make_weighted_sampler(samples):
    counts  = Counter(label for _, label in samples)
    weights = [1.0 / counts[label] for _, label in samples]
    return WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)


# ── Train / eval loops ────────────────────────────────────────────────────────

def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss, correct, total = 0.0, 0, 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        out  = model(images)
        loss = criterion(out, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * images.size(0)
        correct    += (out.argmax(1) == labels).sum().item()
        total      += images.size(0)
    return total_loss / total, correct / total


def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            out   = model(images)
            loss  = criterion(out, labels)
            preds = out.argmax(1)
            total_loss += loss.item() * images.size(0)
            correct    += (preds == labels).sum().item()
            total      += images.size(0)
            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(labels.cpu().tolist())
    return total_loss / total, correct / total, all_preds, all_labels


def train_model(model, train_loader, val_loader, criterion, epochs, lr, device, label):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    history      = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
    best_val_acc = 0.0
    best_state   = None

    print(f"\n  --- Training {label} ---")
    for epoch in range(1, epochs + 1):
        t0 = time.time()
        train_loss, train_acc   = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss,   val_acc, _, _ = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        marker = ""
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_state   = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            marker = "  ✓ best"

        print(f"  Epoch {epoch:03d}/{epochs} | "
              f"Train loss: {train_loss:.4f} acc: {train_acc:.3f} | "
              f"Val loss: {val_loss:.4f} acc: {val_acc:.3f} | "
              f"{time.time()-t0:.1f}s{marker}")

    model.load_state_dict(best_state)
    return model, history, best_val_acc


# ── Plots ─────────────────────────────────────────────────────────────────────

def save_training_plot(history, path, title):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(history["train_loss"], label="Train")
    ax1.plot(history["val_loss"],   label="Val")
    ax1.set_title(f"{title} — Loss"); ax1.set_xlabel("Epoch"); ax1.legend()
    ax2.plot(history["train_acc"], label="Train")
    ax2.plot(history["val_acc"],   label="Val")
    ax2.set_title(f"{title} — Accuracy"); ax2.set_xlabel("Epoch"); ax2.legend()
    plt.tight_layout()
    plt.savefig(str(path))
    plt.close()
    print(f"  Saved curves → {path}")


def save_confusion_matrix(all_labels, all_preds, classes, path, title):
    cm  = confusion_matrix(all_labels, all_preds)
    sz  = max(5, len(classes))
    fig, ax = plt.subplots(figsize=(sz, sz - 1))
    im  = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    plt.colorbar(im, ax=ax)
    ax.set(xticks=range(len(classes)), yticks=range(len(classes)),
           xticklabels=classes, yticklabels=classes,
           ylabel="True", xlabel="Predicted", title=title)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
    plt.tight_layout()
    plt.savefig(str(path))
    plt.close()
    print(f"  Saved confusion matrix → {path}")


def print_report(labels, preds, classes):
    """Print classification report using only classes present in this split."""
    present_labels = sorted(set(labels) | set(preds))
    present_names  = [classes[i] for i in present_labels]
    print(classification_report(labels, preds,
                                labels=present_labels,
                                target_names=present_names,
                                digits=3, zero_division=0))


# ── Train one section model ───────────────────────────────────────────────────

def train_section(section_name, section_labels, data_dir, output_dir,
                  train_tf, val_tf, criterion, epochs, lr, device):

    print(f"\n{'─'*52}")
    print(f"  Section Model: {section_name.upper()}")
    print(f"  Labels: {section_labels}")
    print(f"{'─'*52}")

    train_ds = SectionDataset(data_dir / "train", section_labels, transform=train_tf)
    val_ds   = SectionDataset(data_dir / "val",   section_labels, transform=val_tf,
                              class_to_idx=train_ds.class_to_idx)
    test_ds  = SectionDataset(data_dir / "test",  section_labels, transform=val_tf,
                              class_to_idx=train_ds.class_to_idx)

    if len(train_ds) == 0:
        print(f"  [skip] No training samples found for {section_name}")
        return None

    print(f"\n  Classes ({len(train_ds.classes)}):")
    for cls in train_ds.classes:
        count = sum(1 for _, l in train_ds.samples if l == train_ds.class_to_idx[cls])
        print(f"    {cls}: {count} samples")
    print(f"  Train: {len(train_ds)} | Val: {len(val_ds)} | Test: {len(test_ds)}")

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE,
                              sampler=make_weighted_sampler(train_ds.samples),
                              num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    model = TinyCNN(num_classes=len(train_ds.classes)).to(device)
    model, history, best_val = train_model(
        model, train_loader, val_loader,
        criterion, epochs, lr, device,
        label=f"Section: {section_name}"
    )

    # Test evaluation
    print(f"\n  Test Evaluation — {section_name}")
    _, test_acc, preds, labels = evaluate(model, test_loader, criterion, device)
    print(f"  Test accuracy: {test_acc:.4f}\n")
    print_report(labels, preds, train_ds.classes)

    # Save model
    model_path = output_dir / f"model_{section_name}.pth"
    torch.save({
        "model_state_dict": model.state_dict(),
        "classes":          train_ds.classes,
        "class_to_idx":     train_ds.class_to_idx,
        "num_classes":      len(train_ds.classes),
        "section":          section_name,
        "best_val_acc":     best_val,
        "test_acc":         test_acc,
    }, model_path)

    # Save class map
    with open(output_dir / f"model_{section_name}_classes.json", "w") as f:
        json.dump({"section": section_name,
                   "classes": train_ds.classes,
                   "class_to_idx": train_ds.class_to_idx}, f, indent=2)

    save_training_plot(history,
                       output_dir / f"model_{section_name}_curves.png",
                       f"Section: {section_name}")
    if len(test_ds) > 0:
        save_confusion_matrix(labels, preds, train_ds.classes,
                              output_dir / f"model_{section_name}_confusion.png",
                              f"{section_name} — Confusion Matrix")

    return {"section": section_name, "best_val": best_val, "test_acc": test_acc,
            "model_path": str(model_path)}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Section-based triage checkbox classifier")
    parser.add_argument("--data_dir",   required=True, help="Path to dataset/checkboxes/")
    parser.add_argument("--output_dir", required=True, help="Where to save models and logs")
    parser.add_argument("--epochs",     type=int,   default=40)
    parser.add_argument("--lr",         type=float, default=1e-3)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*52}")
    print(f"  Section-Based Checkbox Classifier")
    print(f"  Batch size : {BATCH_SIZE}")
    print(f"  Epochs     : {args.epochs}")
    print(f"{'='*52}")

    device    = get_device()
    train_tf, val_tf = get_transforms()
    criterion = nn.CrossEntropyLoss()
    data_dir  = Path(args.data_dir)

    results = {}

    # ══════════════════════════════════════════════
    #  MODEL A — Ticked vs Unticked
    # ══════════════════════════════════════════════

    print(f"\n{'─'*52}")
    print(f"  MODEL A: Ticked vs Unticked")
    print(f"{'─'*52}")

    a_train = StateDataset(data_dir / "train", transform=train_tf)
    a_val   = StateDataset(data_dir / "val",   transform=val_tf)
    a_test  = StateDataset(data_dir / "test",  transform=val_tf)

    ticked   = sum(1 for _, l in a_train.samples if l == 1)
    unticked = sum(1 for _, l in a_train.samples if l == 0)
    print(f"\n  Train — ticked: {ticked} | unticked: {unticked}")
    print(f"  Val: {len(a_val)} | Test: {len(a_test)}")

    a_train_loader = DataLoader(a_train, batch_size=BATCH_SIZE,
                                sampler=make_weighted_sampler(a_train.samples),
                                num_workers=0)
    a_val_loader   = DataLoader(a_val,  batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    a_test_loader  = DataLoader(a_test, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    model_a = TinyCNN(num_classes=2).to(device)
    model_a, history_a, best_val_a = train_model(
        model_a, a_train_loader, a_val_loader,
        criterion, args.epochs, args.lr, device,
        label="Model A (ticked/unticked)"
    )

    print(f"\n  Model A — Test Evaluation")
    _, test_acc_a, preds_a, labels_a = evaluate(model_a, a_test_loader, criterion, device)
    print(f"  Test accuracy: {test_acc_a:.4f}\n")
    print_report(labels_a, preds_a, a_train.classes)

    model_a_path = output_dir / "model_a_state.pth"
    torch.save({
        "model_state_dict": model_a.state_dict(),
        "classes":          a_train.classes,
        "num_classes":      2,
        "best_val_acc":     best_val_a,
        "test_acc":         test_acc_a,
    }, model_a_path)
    print(f"  Saved Model A → {model_a_path}")

    save_training_plot(history_a, output_dir / "model_a_curves.png", "Model A (ticked/unticked)")
    save_confusion_matrix(labels_a, preds_a, a_train.classes,
                          output_dir / "model_a_confusion.png", "Model A — Confusion Matrix")

    results["model_a"] = {"best_val": best_val_a, "test_acc": test_acc_a}

    # ══════════════════════════════════════════════
    #  SECTION MODELS B-F
    # ══════════════════════════════════════════════

    for section_name, section_labels in SECTIONS.items():
        result = train_section(
            section_name, section_labels, data_dir, output_dir,
            train_tf, val_tf, criterion, args.epochs, args.lr, device
        )
        if result:
            results[section_name] = result

    # ══════════════════════════════════════════════
    #  Summary
    # ══════════════════════════════════════════════

    print(f"\n{'='*52}")
    print(f"  Training Complete — Summary")
    print(f"{'='*52}")
    print(f"  {'Model':<20} {'Best Val':>10} {'Test Acc':>10}")
    print(f"  {'─'*42}")

    a = results.get("model_a", {})
    print(f"  {'Model A (state)':<20} {a.get('best_val', 0):.4f}     {a.get('test_acc', 0):.4f}")

    for section_name in SECTIONS:
        r = results.get(section_name, {})
        if r:
            print(f"  {section_name:<20} {r.get('best_val', 0):.4f}     {r.get('test_acc', 0):.4f}")

    print(f"\n  All outputs saved to: {output_dir}")
    print(f"{'='*52}\n")


if __name__ == "__main__":
    main()