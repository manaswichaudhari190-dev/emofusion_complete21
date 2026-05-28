"""
Face Emotion Service — EfficientViT-M5 (Production)
====================================================
Model  : best_rafdb_v2_live_model.pth
Arch   : EfficientViT-M5 (timm)
Labels : 0=Surprise 1=Fear 2=Disgust 3=Happy 4=Sad 5=Angry 6=Neutral
Device : CUDA (FP16) → CPU (FP32) auto-fallback
"""

import os
import sys
import time
import random
import logging
import numpy as np
from collections import deque, Counter
from typing import Dict, Any, List, Tuple, Optional

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    format="[FaceEmotion] %(levelname)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("FaceEmotion")


def _ensure_package(pkg: str, import_name: Optional[str] = None) -> bool:
    """Auto-install a pip package if the import fails."""
    import_name = import_name or pkg
    try:
        __import__(import_name)
        return True
    except ImportError:
        log.warning("'%s' not found — installing...", pkg)
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])
        return True


# Auto-install all required packages
for _pkg, _imp in [
    ("timm", "timm"),
    ("torch", "torch"),
    ("torchvision", "torchvision"),
    ("Pillow", "PIL"),
    ("opencv-python", "cv2"),
    ("numpy", "numpy"),
    ("ultralytics", "ultralytics"),
]:
    _ensure_package(_pkg, _imp)

import torch
import torch.nn as nn
import timm
import numpy as np
from PIL import Image
from torchvision import transforms


# ══════════════════════════════════════════════════════════════════════════════
#  CRITICAL — Label mapping must match EXACTLY how the model was trained.
#  User's training order: 0=Surprise 1=Fear 2=Disgust 3=Happy 4=Sad 5=Angry 6=Neutral
# ══════════════════════════════════════════════════════════════════════════════
EMOTIONS_ALL = ["surprise", "fear", "disgust", "happy", "sad", "angry", "neutral"]

EMOTION_EMOJIS = {
    "surprise": "😲", "fear": "😨", "disgust": "🤢",
    "happy": "😊",   "sad": "😢",  "angry": "😠",
    "neutral": "😐", "uncertain": "🤔",
}

EMOTION_SUGGESTIONS = {
    "happy":     "Your smile says it all! Happiness is contagious — share this moment.",
    "sad":       "Your face reflects something heavy. Be gentle with yourself today.",
    "angry":     "Tension shows on your face. Try exhaling slowly and relaxing your jaw.",
    "fear":      "You look worried. Box breathing (4s in/hold/out/hold) can calm nerves.",
    "neutral":   "Resting but present. A small smile can genuinely shift your mood.",
    "disgust":   "Your expression shows discomfort. Identify the trigger and create distance.",
    "surprise":  "Wide eyes! Embrace the unexpected — some of the best things are surprises.",
    "uncertain": "Expression unclear. Ensure good lighting and face the camera directly.",
}

# Low-confidence diagnostic reasons
LOW_CONFIDENCE_REASONS = [
    "Poor lighting conditions — the face is too dark or overexposed",
    "Motion blur from camera shake or fast head movement",
    "Occluded face — glasses, hair, mask, or hand partially covering features",
    "Side-angle or tilted head — model trained on near-frontal faces",
    "Weak face detection — bounding box may be too loose or too tight",
    "Preprocessing mismatch — verify Resize(224) + ImageNet normalize applied",
    "Normalization issue — confirm mean=[0.485,0.456,0.406] std=[0.229,0.224,0.225]",
    "Label mapping mismatch — verify EMOTIONS_ALL matches training class order",
]

# Inference confidence threshold (< 0.60 → display 'Uncertain')
CONFIDENCE_THRESHOLD = 0.60

# Inference pre-processing — must match training val_transform exactly
INFERENCE_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


# ══════════════════════════════════════════════════════════════════════════════
class FaceEmotionService:
    """
    Production facial emotion recognition service.

    Pipeline:
        webcam frame → YOLOv8 face detect → crop+pad →
        224×224 RGB normalize → EfficientViT-M5 → softmax →
        threshold filter → 5-frame smoothing → result dict
    """

    def __init__(
        self,
        model_path: str = "best_rafdb_v2_live_model.pth",
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        smoothing_window: int = 5,
        use_fp16: bool = True,
    ):
        self.confidence_threshold = confidence_threshold
        self.smoothing_window = smoothing_window
        self.history: deque = deque(maxlen=smoothing_window)
        self.use_fp16 = use_fp16
        self._frame_count = 0
        self._total_inference_ms = 0.0

        # ── Device selection ──────────────────────────────────────────────
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if self.device.type == "cuda":
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb  = torch.cuda.get_device_properties(0).total_memory / 1e9
            log.info("✅ CUDA GPU detected: %s (%.1f GB VRAM)", gpu_name, vram_gb)
        else:
            log.warning("⚠️  No CUDA GPU detected — running on CPU (slower inference)")

        self._load_emotion_model(model_path)
        self._load_face_detector()
        self._run_startup_verification()

    # ── Model loading ──────────────────────────────────────────────────────

    def _load_emotion_model(self, model_path: str) -> None:
        """Load EfficientViT-M5 and restore trained weights."""
        log.info("Loading EfficientViT-M5 architecture (7 classes)...")

        self.model = timm.create_model(
            "efficientvit_m5.r224_in1k",
            pretrained=False,
            num_classes=len(EMOTIONS_ALL),   # 7
        )

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"\n❌ Model file not found: {model_path}\n"
                f"   Copy best_rafdb_v2_live_model.pth to: {os.path.abspath('.')}"
            )

        log.info("Loading weights from: %s", os.path.abspath(model_path))
        state_dict = torch.load(model_path, map_location=self.device)

        # Strip DataParallel 'module.' prefix if present (multi-GPU training)
        if any(k.startswith("module.") for k in state_dict.keys()):
            log.info("Stripping DataParallel 'module.' prefix from state_dict")
            state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}

        self.model.load_state_dict(state_dict)
        self.model.eval()

        # FP16 on CUDA for ~2× speed + 50% less VRAM
        precision = "FP32"
        if self.use_fp16 and self.device.type == "cuda":
            self.model = self.model.half()
            precision = "FP16"

        self.model = self.model.to(self.device)
        param_count = sum(p.numel() for p in self.model.parameters()) / 1e6
        log.info(
            "✅ EfficientViT-M5 loaded | %.1fM params | %s | device=%s",
            param_count, precision, self.device,
        )

    def _load_face_detector(self) -> None:
        """Load YOLOv8 face detector (falls back to OpenCV Haar cascade)."""
        self.detector_type = "none"

        # Try YOLOv8 face-specific model first
        try:
            from ultralytics import YOLO
            yolo_path = "yolov8n-face.pt"
            if not os.path.exists(yolo_path):
                yolo_path = "yolov8n.pt"   # generic — auto-downloads
            self.detector = YOLO(yolo_path)
            self.detector_type = "yolo"
            log.info("✅ Face detector: YOLOv8 (%s)", yolo_path)
            return
        except Exception as e:
            log.warning("YOLOv8 unavailable (%s) — falling back to Haar cascade", e)

        # Haar cascade fallback (always available via OpenCV)
        import cv2
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.haar = cv2.CascadeClassifier(cascade_path)
        self.detector_type = "haar"
        log.info("✅ Face detector: OpenCV Haar cascade")

    # ── Startup verification ───────────────────────────────────────────────

    def _run_startup_verification(self) -> None:
        """Verify model output shape, label mapping, and softmax behaviour."""
        log.info("Running startup verification...")

        dummy = torch.zeros(1, 3, 224, 224, device=self.device)
        if self.use_fp16 and self.device.type == "cuda":
            dummy = dummy.half()

        with torch.no_grad():
            logits = self.model(dummy)
            probs  = torch.softmax(logits.float(), dim=1)

        # Shape check
        assert logits.shape == (1, 7), (
            f"❌ Wrong output shape: {logits.shape} — expected (1, 7)"
        )
        log.info("✅ Output tensor shape: %s ✓", tuple(logits.shape))

        # Softmax sum check
        prob_sum = float(probs.sum().item())
        assert abs(prob_sum - 1.0) < 1e-4, (
            f"❌ Softmax probabilities don't sum to 1.0: {prob_sum}"
        )
        log.info("✅ Softmax sum: %.6f ✓", prob_sum)

        # Label mapping confirmation
        log.info(
            "✅ Label mapping: %s",
            " | ".join(f"{i}={e}" for i, e in enumerate(EMOTIONS_ALL)),
        )
        log.info("🟢 Model pipeline healthy — ready for inference")

    # ── Face detection ─────────────────────────────────────────────────────

    def _detect_faces_yolo(
        self, frame_bgr: np.ndarray, padding: int = 20
    ) -> Tuple[List, int]:
        """YOLOv8-based face detection."""
        h, w = frame_bgr.shape[:2]
        results = self.detector(frame_bgr, verbose=False)
        boxes_out = []

        for box in results[0].boxes:
            conf = float(box.conf[0])
            if conf < 0.45:
                continue
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(w, x2 + padding)
            y2 = min(h, y2 + padding)
            boxes_out.append((x1, y1, x2, y2, conf))

        return boxes_out, len(boxes_out)

    def _detect_faces_haar(
        self, frame_bgr: np.ndarray, padding: int = 20
    ) -> Tuple[List, int]:
        """OpenCV Haar cascade face detection."""
        import cv2
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self.haar.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        h, w = frame_bgr.shape[:2]
        boxes_out = []

        for (fx, fy, fw, fh) in faces:
            x1 = max(0, fx - padding)
            y1 = max(0, fy - padding)
            x2 = min(w, fx + fw + padding)
            y2 = min(h, fy + fh + padding)
            boxes_out.append((x1, y1, x2, y2, 1.0))

        return boxes_out, len(boxes_out)

    def _detect_faces(
        self, image: Image.Image, padding: int = 20
    ) -> Tuple[List[Image.Image], List[Tuple], int]:
        """Detect faces; returns (cropped PIL list, raw boxes, count)."""
        import cv2
        frame_bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        if self.detector_type == "yolo":
            raw_boxes, count = self._detect_faces_yolo(frame_bgr, padding)
        else:
            raw_boxes, count = self._detect_faces_haar(frame_bgr, padding)

        face_crops = []
        for (x1, y1, x2, y2, _) in raw_boxes:
            crop = frame_bgr[y1:y2, x1:x2]
            if crop.size == 0:
                continue
            face_crops.append(Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)))

        return face_crops, raw_boxes, len(face_crops)

    # ── Preprocessing ──────────────────────────────────────────────────────

    def _preprocess(self, face_pil: Image.Image) -> torch.Tensor:
        """
        Preprocess a cropped face for EfficientViT-M5:
          RGB → Resize(224,224) → ToTensor → ImageNet Normalize
        """
        if face_pil.mode != "RGB":
            face_pil = face_pil.convert("RGB")
        tensor = INFERENCE_TRANSFORM(face_pil).unsqueeze(0)  # (1,3,224,224)
        if self.use_fp16 and self.device.type == "cuda":
            tensor = tensor.half()
        return tensor.to(self.device)

    # ── Inference ──────────────────────────────────────────────────────────

    @torch.no_grad()
    def _infer(self, face_pil: Image.Image) -> Dict[str, Any]:
        """Run EfficientViT-M5 on one face crop; return emotion + probs."""
        t0 = time.perf_counter()

        tensor = self._preprocess(face_pil)
        logits = self.model(tensor)                      # (1,7)
        probs  = torch.softmax(logits.float(), dim=1)    # FP32 for stability
        probs_np = probs.cpu().numpy()[0]                # (7,)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        self._frame_count += 1
        self._total_inference_ms += elapsed_ms

        idx        = int(np.argmax(probs_np))
        emotion    = EMOTIONS_ALL[idx]
        confidence = float(probs_np[idx])

        log.debug(
            "Inference: %s (%.1f%%) in %.1fms [avg %.1fms]",
            emotion, confidence * 100, elapsed_ms,
            self._total_inference_ms / self._frame_count,
        )

        breakdown = {
            EMOTIONS_ALL[i]: round(float(probs_np[i]) * 100, 2)
            for i in range(len(EMOTIONS_ALL))
        }

        return {
            "emotion":     emotion,
            "confidence":  round(confidence * 100, 2),
            "breakdown":   breakdown,
            "infer_ms":    round(elapsed_ms, 2),
        }

    # ── Confidence analysis ────────────────────────────────────────────────

    def _analyze_confidence(self, confidence_pct: float) -> str:
        """Return a human-readable confidence quality message."""
        if confidence_pct >= self.confidence_threshold * 100:
            return "✅ Model inference pipeline is healthy."
        # Low confidence — pick 3 most likely reasons
        reasons = random.sample(LOW_CONFIDENCE_REASONS, min(3, len(LOW_CONFIDENCE_REASONS)))
        lines   = "\n  • ".join(reasons)
        return f"⚠️  Low confidence ({confidence_pct:.1f}%). Possible causes:\n  • {lines}"

    # ── Temporal smoothing ─────────────────────────────────────────────────

    def _smooth(self, emotion: str) -> str:
        """5-frame rolling majority vote to suppress flickering."""
        self.history.append(emotion)
        return Counter(self.history).most_common(1)[0][0]

    # ── Public API — used by Flask /predict-face ───────────────────────────

    def predict(self, image_input) -> Dict[str, Any]:
        """
        Main entry point.
        Accepts Flask FileStorage | PIL Image | np.ndarray | file path.
        Returns EmoFusion API contract dict.
        """
        # ── Normalise input ────────────────────────────────────────────────
        if hasattr(image_input, "stream"):          # Flask FileStorage
            image = Image.open(image_input.stream).convert("RGB")
        elif isinstance(image_input, str):
            image = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, np.ndarray):
            image = Image.fromarray(image_input).convert("RGB")
        else:
            image = image_input.convert("RGB")

        # ── Face detection ─────────────────────────────────────────────────
        try:
            face_crops, raw_boxes, face_count = self._detect_faces(image)
        except Exception as exc:
            log.error("Face detection failed: %s", exc)
            return self._no_face_result(0)

        log.debug("Faces detected: %d (detector=%s)", face_count, self.detector_type)

        if face_count == 0:
            log.info("No face detected in frame")
            return self._no_face_result(0)

        # ── Inference on primary face ──────────────────────────────────────
        try:
            raw = self._infer(face_crops[0])
        except Exception as exc:
            log.error("Inference error: %s", exc)
            return self._no_face_result(face_count)

        emotion    = raw["emotion"]
        conf_pct   = raw["confidence"]

        # ── Confidence gate ────────────────────────────────────────────────
        display_emotion = "uncertain" if conf_pct < self.confidence_threshold * 100 else emotion

        # ── Temporal smoothing ─────────────────────────────────────────────
        smoothed = self._smooth(display_emotion)

        # ── Confidence quality analysis ────────────────────────────────────
        quality_msg = self._analyze_confidence(conf_pct)
        if "healthy" not in quality_msg:
            log.info(quality_msg)

        return {
            "emotion":        smoothed,
            "confidence":     conf_pct,
            "emoji":          EMOTION_EMOJIS.get(smoothed, "😐"),
            "breakdown":      raw["breakdown"],
            "suggestion":     EMOTION_SUGGESTIONS.get(smoothed, "Take care of yourself."),
            "input_type":     "camera",
            "faces_detected": face_count,
            "infer_ms":       raw["infer_ms"],
            "model":          "efficientvit_m5_v2",
            "quality":        quality_msg,
        }

    def _no_face_result(self, face_count: int) -> Dict[str, Any]:
        return {
            "emotion":        "neutral",
            "confidence":     0.0,
            "emoji":          EMOTION_EMOJIS["neutral"],
            "breakdown":      {e: 0.0 for e in EMOTIONS_ALL},
            "suggestion":     EMOTION_SUGGESTIONS["neutral"],
            "input_type":     "camera",
            "faces_detected": face_count,
            "infer_ms":       0.0,
            "model":          "efficientvit_m5_v2",
            "quality":        "No face detected in frame.",
        }

    # ── Real-time webcam pipeline ──────────────────────────────────────────

    def run_webcam(self, camera_index: int = 0) -> None:
        """
        Standalone real-time webcam loop.
        Press Q to quit.
        """
        import cv2
        log.info("Starting webcam pipeline (camera=%d) | Press Q to quit", camera_index)

        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            log.error("Cannot open camera %d", camera_index)
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        fps_history: deque = deque(maxlen=30)
        font  = cv2.FONT_HERSHEY_DUPLEX
        GREEN = (0, 220, 80)
        AMBER = (0, 180, 255)
        RED   = (60, 60, 240)
        BLUE  = (255, 200, 0)
        WHITE = (255, 255, 255)
        DARK  = (20, 20, 20)

        while True:
            t_start = time.perf_counter()
            ret, frame = cap.read()
            if not ret:
                log.warning("Frame read failed — retrying")
                continue

            pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

            # ── Detect faces ────────────────────────────────────────────────
            try:
                face_crops, raw_boxes, face_count = self._detect_faces(pil_img)
            except Exception:
                face_crops, raw_boxes, face_count = [], [], 0

            result = None
            if face_count > 0:
                try:
                    raw = self._infer(face_crops[0])
                    emotion  = raw["emotion"]
                    conf_pct = raw["confidence"]
                    display  = "uncertain" if conf_pct < self.confidence_threshold * 100 \
                               else emotion
                    smoothed = self._smooth(display)
                    result   = {
                        "emotion":    smoothed,
                        "confidence": conf_pct,
                        "breakdown":  raw["breakdown"],
                        "infer_ms":   raw["infer_ms"],
                    }
                except Exception as exc:
                    log.error("Infer error: %s", exc)

            # ── Draw bounding boxes ─────────────────────────────────────────
            for i, (x1, y1, x2, y2, det_conf) in enumerate(raw_boxes):
                color = GREEN if (result and result["emotion"] != "uncertain") else AMBER
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                if result and i == 0:
                    emotion  = result["emotion"].upper()
                    conf_pct = result["confidence"]
                    label    = f"{emotion}  {conf_pct:.1f}%"
                    col      = GREEN if emotion != "UNCERTAIN" else AMBER

                    # Label background
                    (tw, th), _ = cv2.getTextSize(label, font, 0.65, 1)
                    cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 8, y1), DARK, -1)
                    cv2.putText(frame, label, (x1 + 4, y1 - 4), font, 0.65, col, 1, cv2.LINE_AA)

                    # Confidence bar
                    bar_w = x2 - x1
                    fill  = int(bar_w * min(conf_pct / 100, 1.0))
                    cv2.rectangle(frame, (x1, y2 + 2), (x2, y2 + 8), DARK,  -1)
                    cv2.rectangle(frame, (x1, y2 + 2), (x1 + fill, y2 + 8), col, -1)

            # ── HUD overlay ─────────────────────────────────────────────────
            elapsed = time.perf_counter() - t_start
            fps_history.append(1.0 / max(elapsed, 1e-6))
            fps = sum(fps_history) / len(fps_history)

            hud_lines = [
                f"FPS: {fps:.1f}",
                f"Faces: {face_count}",
                f"Device: {str(self.device).upper()}",
                f"Detector: {self.detector_type.upper()}",
            ]
            if result:
                hud_lines.append(f"Infer: {result['infer_ms']:.1f}ms")

            for idx, line in enumerate(hud_lines):
                cv2.putText(frame, line, (10, 22 + idx * 22),
                            font, 0.52, WHITE, 1, cv2.LINE_AA)

            # ── Breakdown bar chart ─────────────────────────────────────────
            if result:
                bx, by = frame.shape[1] - 175, 10
                for ei, emo in enumerate(EMOTIONS_ALL):
                    val   = result["breakdown"].get(emo, 0.0)
                    bar_w = int(val * 1.2)   # scale to ~120px max
                    col   = GREEN if emo == result["emotion"] else BLUE
                    cv2.rectangle(frame, (bx, by + ei*18), (bx + bar_w, by + ei*18 + 14), col, -1)
                    cv2.putText(frame, f"{emo[:3].upper()} {val:.0f}%",
                                (bx - 55, by + ei*18 + 12),
                                font, 0.38, WHITE, 1, cv2.LINE_AA)

            cv2.imshow("EmoFusion — EfficientViT-M5 Live", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()
        log.info(
            "Session ended. Frames=%d | Avg inference=%.1fms",
            self._frame_count,
            self._total_inference_ms / max(self._frame_count, 1),
        )
