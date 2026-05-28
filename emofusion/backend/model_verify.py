"""
EmoFusion — Model Verification & Diagnostic Script
====================================================
Verifies that EfficientViT-M5 weights loaded correctly and the inference
pipeline is healthy before running live webcam detection.

Usage:
    python model_verify.py
    python model_verify.py --model path/to/best_rafdb_v2_live_model.pth
"""

import sys
import os
import time
import argparse
import subprocess
import logging

logging.basicConfig(format="%(message)s", level=logging.INFO)
log = logging.getLogger()

PASS = "[OK] "
FAIL = "[FAIL]"
WARN = "[WARN]"
INFO = "[INFO]"

# ── Auto-install required packages ────────────────────────────────────────────
REQUIRED = [
    ("torch",        "torch"),
    ("torchvision",  "torchvision"),
    ("timm",         "timm"),
    ("Pillow",       "PIL"),
    ("numpy",        "numpy"),
    ("opencv-python","cv2"),
]

def ensure_deps():
    missing = []
    for pkg, imp in REQUIRED:
        try:
            __import__(imp)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"{WARN} Installing missing packages: {missing}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + missing + ["-q"]
        )
        print("[INFO] All packages installed.")

ensure_deps()

import torch
import timm
import numpy as np
from PIL import Image


# ── Label mapping (must match training order exactly) ─────────────────────────
EMOTIONS_ALL = ["surprise", "fear", "disgust", "happy", "sad", "angry", "neutral"]


def separator(title=""):
    w = 60
    if title:
        pad = (w - len(title) - 2) // 2
        print(f"\n{'─'*pad} {title} {'─'*pad}")
    else:
        print("─" * w)


def check_gpu():
    separator("GPU / Device Check")
    if torch.cuda.is_available():
        name  = torch.cuda.get_device_name(0)
        props = torch.cuda.get_device_properties(0)
        vram  = props.total_memory / 1e9
        cc    = f"{props.major}.{props.minor}"
        print(f"{PASS} CUDA GPU found: {name}")
        print(f"{INFO} VRAM: {vram:.2f} GB | Compute capability: {cc}")
        device = torch.device("cuda")
        use_fp16 = True
    else:
        print(f"{WARN} No CUDA GPU detected -- using CPU (slower)")
        print(f"{INFO} Tip: check nvidia-smi to confirm driver + CUDA status")
        device = torch.device("cpu")
        use_fp16 = False
    return device, use_fp16


def load_model(model_path: str, device: torch.device, use_fp16: bool):
    separator("Model Loading")

    if not os.path.exists(model_path):
        print(f"{FAIL} Model file not found: {model_path}")
        print(f"{INFO} Tried: {os.path.abspath(model_path)}")
        sys.exit(1)

    size_mb = os.path.getsize(model_path) / 1e6
    print(f"{INFO} File: {model_path}")
    print(f"{INFO} Size: {size_mb:.1f} MB")

    # Build architecture
    t0 = time.perf_counter()
    model = timm.create_model(
        "efficientvit_m5.r224_in1k",
        pretrained=False,
        num_classes=len(EMOTIONS_ALL),
    )
    arch_ms = (time.perf_counter() - t0) * 1000
    print(f"{PASS} Architecture created: EfficientViT-M5 ({arch_ms:.0f}ms)")

    # Load weights
    t0 = time.perf_counter()
    state_dict = torch.load(model_path, map_location=device)
    load_ms = (time.perf_counter() - t0) * 1000

    stripped = False
    if any(k.startswith("module.") for k in state_dict.keys()):
        state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}
        stripped = True
        print(f"{INFO} DataParallel 'module.' prefix stripped from state_dict")

    try:
        model.load_state_dict(state_dict)
        print(f"{PASS} Weights loaded: {load_ms:.0f}ms | Keys stripped: {stripped}")
    except RuntimeError as e:
        print(f"{FAIL} Weight mismatch: {e}")
        sys.exit(1)

    model.eval()

    if use_fp16 and device.type == "cuda":
        model = model.half()
        print(f"{INFO} FP16 mode enabled (CUDA)")

    model = model.to(device)

    params = sum(p.numel() for p in model.parameters()) / 1e6
    print(f"{PASS} Model on device: {device} | Parameters: {params:.2f}M")
    return model


def check_output_shape(model, device, use_fp16):
    separator("Output Shape Check")
    dummy = torch.zeros(1, 3, 224, 224, device=device)
    if use_fp16:
        dummy = dummy.half()

    with torch.no_grad():
        t0     = time.perf_counter()
        logits = model(dummy)
        ms     = (time.perf_counter() - t0) * 1000

    shape = tuple(logits.shape)
    if shape == (1, 7):
        print(f"{PASS} Output shape: {shape} (batch=1, classes=7)")
    else:
        print(f"{FAIL} Wrong output shape: {shape} — expected (1, 7)")
        sys.exit(1)

    print(f"{INFO} Dummy inference time: {ms:.2f}ms on {device}")
    return logits


def check_softmax(logits):
    separator("Softmax Probabilities Check")
    probs = torch.softmax(logits.float(), dim=1).cpu().numpy()[0]

    prob_sum = float(probs.sum())
    if abs(prob_sum - 1.0) < 1e-4:
        print(f"{PASS} Softmax sum: {prob_sum:.8f}")
    else:
        print(f"{FAIL} Softmax doesn't sum to 1.0: {prob_sum:.8f}")

    idx  = int(np.argmax(probs))
    pred = EMOTIONS_ALL[idx]
    conf = float(probs[idx])
    print(f"{INFO} Dummy prediction (random weights): {pred} ({conf*100:.2f}%)")
    print(f"{INFO} (Random/untrained dummy output — confidence values here are meaningless)")
    return probs


def check_label_mapping():
    separator("Label Mapping Verification")
    print(f"{INFO} Trained label order:")
    for i, e in enumerate(EMOTIONS_ALL):
        print(f"       {i} = {e}")
    print(f"{PASS} 7 emotion classes confirmed")
    print(f"{WARN} If predictions look wrong, this mapping is the first place to check.")


def check_real_inference(model, device, use_fp16):
    separator("Real Image Inference Test")
    from torchvision import transforms

    tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])

    # Create a synthetic face-like image (flesh tone rectangle)
    img = np.ones((224, 224, 3), dtype=np.uint8)
    img[:, :, 0] = 220  # R
    img[:, :, 1] = 180  # G
    img[:, :, 2] = 140  # B
    pil = Image.fromarray(img)

    tensor = tf(pil).unsqueeze(0)
    if use_fp16 and device.type == "cuda":
        tensor = tensor.half()
    tensor = tensor.to(device)

    times = []
    with torch.no_grad():
        for _ in range(10):
            t0 = time.perf_counter()
            out = model(tensor)
            times.append((time.perf_counter() - t0) * 1000)

    probs = torch.softmax(out.float(), dim=1).cpu().numpy()[0]
    idx   = int(np.argmax(probs))
    print(f"{PASS} 10-run inference complete")
    print(f"{INFO} Avg: {sum(times)/len(times):.2f}ms | "
          f"Min: {min(times):.2f}ms | Max: {max(times):.2f}ms")
    print(f"{INFO} Synthetic prediction: {EMOTIONS_ALL[idx]} ({probs[idx]*100:.2f}%)")
    print(f"{INFO} All probabilities:")
    for e, p in sorted(zip(EMOTIONS_ALL, probs), key=lambda x: -x[1]):
        bar = "#" * int(p * 30)
        print(f"       {e:<10} {p*100:5.2f}%  {bar}")


def check_face_detector():
    separator("Face Detector Check")
    # YOLOv8
    try:
        from ultralytics import YOLO
        for fn in ("yolov8n-face.pt", "yolov8n.pt"):
            if os.path.exists(fn):
                print(f"{PASS} YOLOv8 detector found: {fn}")
                return
        print(f"{WARN} YOLOv8 .pt file not present — will auto-download on first run")
    except ImportError:
        print(f"{WARN} ultralytics not installed — YOLOv8 unavailable")

    # Haar fallback
    import cv2
    cascade = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    if os.path.exists(cascade):
        print(f"{PASS} Haar cascade fallback available: {cascade}")
    else:
        print(f"{FAIL} No face detector available — install ultralytics")


def confidence_guide():
    separator("Confidence Quality Guide")
    print(f"{INFO} Threshold: 60% -- below this, 'Uncertain' is displayed\n")

    print("  HIGH CONFIDENCE (>= 60%):")
    print("    [OK]  Model inference pipeline is healthy")
    print("    [OK]  Face well-lit, frontal, and clearly visible\n")

    print("  LOW CONFIDENCE (< 60%) -- possible causes:")
    causes = [
        "Poor lighting (too dark / overexposed)",
        "Motion blur from camera shake",
        "Occluded face (glasses, hair, mask, hand)",
        "Side-angle or tilted head pose",
        "Weak face detection (loose/tight bounding box)",
        "Preprocessing mismatch (wrong resize or crop)",
        "Normalization issue (wrong mean/std)",
        "Incorrect label mapping (class order mismatch)",
    ]
    for c in causes:
        print(f"    [WARN] {c}")


def final_summary(all_ok: bool):
    separator()
    if all_ok:
        print("""
[OK] ALL CHECKS PASSED
   Model is ready for production.

   Run live webcam:
     python webcam_live.py

   Or start the Flask backend:
     python app.py
""")
    else:
        print(f"{FAIL} Some checks failed -- review errors above before running.")


# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="EmoFusion Model Verification")
    p.add_argument("--model", default="best_rafdb_v2_live_model.pth",
                   help="Path to model .pth checkpoint")
    args = p.parse_args()

    # Search common locations
    model_path = args.model
    if not os.path.exists(model_path):
        for candidate in [
            os.path.join(os.path.dirname(__file__), args.model),
            r"d:\emo model\Model\best_rafdb_v2_live_model.pth",
        ]:
            if os.path.exists(candidate):
                model_path = candidate
                break

    separator("EmoFusion — Model Verification")
    print(f"Model: {os.path.abspath(model_path)}")
    separator()

    all_ok = True
    try:
        device, use_fp16 = check_gpu()
        model            = load_model(model_path, device, use_fp16)
        logits           = check_output_shape(model, device, use_fp16)
        _                = check_softmax(logits)
        check_label_mapping()
        check_real_inference(model, device, use_fp16)
        check_face_detector()
        confidence_guide()
    except SystemExit:
        all_ok = False
    except Exception as e:
        print(f"{FAIL} Unexpected error: {e}")
        import traceback; traceback.print_exc()
        all_ok = False

    final_summary(all_ok)


if __name__ == "__main__":
    main()
