"""
EmoFusion — Live Webcam Emotion Detection
==========================================
Standalone script to test the EfficientViT-M5 model on your webcam.

Usage:
    python webcam_live.py
    python webcam_live.py --camera 1          # if default camera index is not 0
    python webcam_live.py --model path/to.pth # custom model path
    python webcam_live.py --no-fp16           # force FP32 (slower, for debugging)

Press Q to quit.
"""

import sys
import os
import argparse
import time
import subprocess
import logging

logging.basicConfig(
    format="[webcam_live] %(levelname)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("webcam_live")

# ── Auto-install missing packages ──────────────────────────────────────────────
REQUIRED = [
    ("torch",           "torch"),
    ("torchvision",     "torchvision"),
    ("timm",            "timm"),
    ("Pillow",          "PIL"),
    ("opencv-python",   "cv2"),
    ("numpy",           "numpy"),
    ("ultralytics",     "ultralytics"),
]

def ensure_deps():
    missing = []
    for pkg, imp in REQUIRED:
        try:
            __import__(imp)
        except ImportError:
            missing.append(pkg)

    if missing:
        log.warning("Installing missing packages: %s", missing)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + missing + ["-q"]
        )
        log.info("All packages installed.")

ensure_deps()

# ── Imports (after deps guaranteed) ───────────────────────────────────────────
import cv2
import numpy as np
import torch
from PIL import Image
from collections import deque, Counter

# ── Add backend to path so we can import FaceEmotionService ───────────────────
_BACKEND = os.path.join(os.path.dirname(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from services.face_emotion import FaceEmotionService, EMOTIONS_ALL, EMOTION_EMOJIS


# ── CLI args ───────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="EmoFusion Live Webcam")
    p.add_argument("--camera",    type=int,   default=0,
                   help="Camera index (default: 0)")
    p.add_argument("--model",     type=str,   default="best_rafdb_v2_live_model.pth",
                   help="Path to model .pth file")
    p.add_argument("--threshold", type=float, default=0.60,
                   help="Confidence threshold below which 'Uncertain' is shown (default: 0.60)")
    p.add_argument("--smooth",    type=int,   default=5,
                   help="Temporal smoothing window size (default: 5)")
    p.add_argument("--no-fp16",   action="store_true",
                   help="Disable FP16 (use FP32 — slower but useful for debugging)")
    p.add_argument("--debug",     action="store_true",
                   help="Enable DEBUG logging (verbose inference timing)")
    return p.parse_args()


# ── Colours ────────────────────────────────────────────────────────────────────
PALETTE = {
    "happy":     (0,  200,  80),   # green
    "neutral":   (180, 180, 180),  # grey
    "surprise":  (0,  200, 255),   # yellow-ish
    "sad":       (200, 100,  40),  # blue-ish
    "angry":     (40,  40, 220),   # red
    "fear":      (180,  60, 200),  # purple
    "disgust":   ( 40, 160, 160),  # teal
    "uncertain": ( 40, 180, 255),  # amber
}
WHITE = (255, 255, 255)
DARK  = (15,  15,  15)
GREY  = (90,  90,  90)
FONT  = cv2.FONT_HERSHEY_DUPLEX


def draw_rounded_rect(img, x1, y1, x2, y2, r, color, thickness=-1):
    """Draw a rectangle with slightly rounded corners."""
    cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, thickness)
    cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, thickness)
    for cx, cy in [(x1+r, y1+r), (x2-r, y1+r), (x1+r, y2-r), (x2-r, y2-r)]:
        cv2.circle(img, (cx, cy), r, color, thickness)


def draw_hud(frame, fps, face_count, device, detector, infer_ms):
    """Top-left HUD with session stats."""
    h, w = frame.shape[:2]
    lines = [
        f"EmoFusion  EfficientViT-M5",
        f"FPS: {fps:5.1f}   Faces: {face_count}",
        f"Device: {str(device).upper()}   Det: {detector.upper()}",
        f"Infer: {infer_ms:.1f}ms" if infer_ms > 0 else "Infer: --",
    ]
    pad = 8
    line_h = 20
    box_h = len(lines) * line_h + pad * 2
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (280, box_h), DARK, -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    for i, line in enumerate(lines):
        col = (0, 220, 180) if i == 0 else WHITE
        cv2.putText(frame, line, (pad, pad + (i+1)*line_h - 3),
                    FONT, 0.45, col, 1, cv2.LINE_AA)


def draw_breakdown(frame, breakdown: dict, active_emotion: str):
    """Right-side mini bar chart of all 7 emotion probabilities."""
    h, w = frame.shape[:2]
    bx = w - 160
    by = 10
    bar_max = 130
    row_h = 20

    overlay = frame.copy()
    cv2.rectangle(overlay, (bx - 55, by - 5),
                  (bx + bar_max + 5, by + len(EMOTIONS_ALL) * row_h + 5), DARK, -1)
    cv2.addWeighted(overlay, 0.60, frame, 0.40, 0, frame)

    for i, emo in enumerate(EMOTIONS_ALL):
        val   = breakdown.get(emo, 0.0)
        fill  = int(val / 100.0 * bar_max)
        col   = PALETTE.get(emo, WHITE)
        alpha = 1.0 if emo == active_emotion else 0.45
        bc    = tuple(int(c * alpha) for c in col)

        row_y = by + i * row_h
        cv2.rectangle(frame, (bx, row_y + 2), (bx + fill, row_y + 14), bc, -1)
        label = f"{emo[:3].upper()} {val:4.1f}%"
        cv2.putText(frame, label, (bx - 52, row_y + 13),
                    FONT, 0.36, WHITE if emo == active_emotion else GREY,
                    1, cv2.LINE_AA)


def draw_face_result(frame, box, emotion, conf_pct, threshold_pct):
    """Bounding box + emotion label + confidence bar for one detected face."""
    x1, y1, x2, y2, _ = box
    col = PALETTE.get(emotion, WHITE)

    # Bounding box
    cv2.rectangle(frame, (x1, y1), (x2, y2), col, 2)

    # Label chip
    label = f"{emotion.upper()}  {conf_pct:.1f}%"
    (tw, th), _ = cv2.getTextSize(label, FONT, 0.68, 1)
    chip_y1 = max(0, y1 - th - 12)
    chip_y2 = y1
    draw_rounded_rect(frame, x1, chip_y1, x1 + tw + 12, chip_y2, 4, DARK, -1)
    cv2.putText(frame, label, (x1 + 6, chip_y2 - 3),
                FONT, 0.68, col, 1, cv2.LINE_AA)

    # Confidence bar below box
    bar_w = x2 - x1
    fill  = int(bar_w * min(conf_pct / 100.0, 1.0))
    cv2.rectangle(frame, (x1, y2 + 3), (x2,        y2 + 9), DARK, -1)
    cv2.rectangle(frame, (x1, y2 + 3), (x1 + fill, y2 + 9), col,  -1)

    # Threshold line
    thresh_x = x1 + int(bar_w * threshold_pct)
    cv2.line(frame, (thresh_x, y2 + 1), (thresh_x, y2 + 11), WHITE, 1)


# ── Main loop ──────────────────────────────────────────────────────────────────
def main():
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("FaceEmotion").setLevel(logging.DEBUG)

    # Locate model file
    model_path = args.model
    if not os.path.exists(model_path):
        # Try common locations
        candidates = [
            os.path.join(os.path.dirname(__file__), args.model),
            os.path.join(r"d:\emo model\Model", "best_rafdb_v2_live_model.pth"),
        ]
        for c in candidates:
            if os.path.exists(c):
                model_path = c
                break

    log.info("Model path: %s", os.path.abspath(model_path))

    # Load service
    try:
        service = FaceEmotionService(
            model_path=model_path,
            confidence_threshold=args.threshold,
            smoothing_window=args.smooth,
            use_fp16=not args.no_fp16,
        )
    except Exception as e:
        log.error("Failed to load model: %s", e)
        sys.exit(1)

    # Open camera
    log.info("Opening camera index=%d", args.camera)
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        log.error("Cannot open camera %d", args.camera)
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS,          30)

    fps_buf  = deque(maxlen=30)
    infer_ms = 0.0

    log.info("Press Q to quit")
    cv2.namedWindow("EmoFusion — Live", cv2.WINDOW_NORMAL)

    while True:
        t0 = time.perf_counter()
        ret, frame = cap.read()
        if not ret:
            log.warning("Frame read failed")
            continue

        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        # Detect faces
        try:
            face_crops, raw_boxes, face_count = service._detect_faces(pil_img)
        except Exception as exc:
            log.debug("Detection error: %s", exc)
            face_crops, raw_boxes, face_count = [], [], 0

        # Infer + smooth
        active_emotion = "neutral"
        conf_pct       = 0.0
        breakdown      = {e: 0.0 for e in EMOTIONS_ALL}

        if face_count > 0:
            try:
                raw = service._infer(face_crops[0])
                infer_ms  = raw["infer_ms"]
                raw_emo   = raw["emotion"]
                conf_pct  = raw["confidence"]
                breakdown = raw["breakdown"]
                display   = "uncertain" if conf_pct < args.threshold * 100 else raw_emo
                active_emotion = service._smooth(display)
            except Exception as exc:
                log.debug("Infer error: %s", exc)

        # Draw
        for i, box in enumerate(raw_boxes):
            draw_face_result(frame, box, active_emotion, conf_pct,
                             args.threshold)

        draw_breakdown(frame, breakdown, active_emotion)

        elapsed = time.perf_counter() - t0
        fps_buf.append(1.0 / max(elapsed, 1e-6))
        fps = sum(fps_buf) / len(fps_buf)

        draw_hud(frame, fps, face_count,
                 service.device, service.detector_type, infer_ms)

        # Bottom quality hint
        if face_count > 0 and conf_pct < args.threshold * 100:
            hint = "Low confidence — check lighting, angle, or distance"
            cv2.putText(frame, hint, (10, frame.shape[0] - 12),
                        FONT, 0.42, (0, 180, 255), 1, cv2.LINE_AA)
        elif face_count > 0:
            hint = "Pipeline healthy"
            cv2.putText(frame, hint, (10, frame.shape[0] - 12),
                        FONT, 0.42, (0, 220, 80), 1, cv2.LINE_AA)

        cv2.imshow("EmoFusion — Live", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    log.info(
        "Session ended | Frames=%d | Avg infer=%.1fms",
        service._frame_count,
        service._total_inference_ms / max(service._frame_count, 1),
    )


if __name__ == "__main__":
    main()
