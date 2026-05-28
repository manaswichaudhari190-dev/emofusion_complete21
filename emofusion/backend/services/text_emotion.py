"""
Text Emotion Service
Uses TF-IDF + Logistic Regression for emotion detection.
Can be upgraded to a HuggingFace BERT model for better accuracy.
"""

import re
import random
from typing import Dict, Any

EMOTION_SUGGESTIONS = {
    "happy": "You're radiating positivity! Keep nurturing what's bringing you joy—share it with others.",
    "sad": "It's okay to feel sad. Try journaling your thoughts or talking to someone you trust.",
    "angry": "Take a few deep breaths. A short walk or some music can help channel that energy.",
    "fear": "Fear is a signal, not a stop sign. Break the worry into small, manageable steps.",
    "neutral": "You seem balanced. A short mindfulness check-in can sustain this calm state.",
    "disgust": "Something feels off—trust that feeling. Stepping away and getting fresh air often helps.",
    "surprise": "Embrace the unexpected! Curiosity is a superpower—explore what surprised you.",
}

EMOTION_EMOJIS = {
    "happy": "😊",
    "sad": "😢",
    "angry": "😠",
    "fear": "😨",
    "neutral": "😐",
    "disgust": "🤢",
    "surprise": "😲",
}

# Single source of truth for all 7 emotions (BUG 2 FIX: neutral was missing)
EMOTIONS_ALL = ["happy", "sad", "angry", "fear", "neutral", "disgust", "surprise"]

# Keyword-based heuristics for demo; the real model uses sklearn below
EMOTION_KEYWORDS = {
    "happy": ["happy", "joy", "excited", "love", "great", "wonderful", "amazing", "fantastic", "smile", "laugh", "good", "best", "delighted", "thrilled", "cheerful"],
    "sad": ["sad", "cry", "unhappy", "depressed", "miserable", "heartbroken", "lonely", "grief", "sorrow", "down", "hopeless", "pain"],
    "angry": ["angry", "furious", "mad", "hate", "rage", "annoyed", "irritated", "frustrated", "outraged", "livid"],
    "fear": ["scared", "afraid", "fear", "terrified", "anxious", "nervous", "worried", "panic", "dread", "terror"],
    # BUG 2 FIX: "neutral" is now explicitly defined so breakdown always has 7 keys
    "neutral": ["okay", "fine", "alright", "normal", "meh", "so-so", "calm", "indifferent"],
    "disgust": ["disgusting", "gross", "nasty", "revolting", "sickening", "repulsive", "awful"],
    "surprise": ["surprised", "shocked", "astonished", "unexpected", "wow", "unbelievable", "incredible"],
}


class TextEmotionService:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self._load_model()

    def _load_model(self):
        """
        Try to load a pre-trained sklearn model from disk.
        Falls back to keyword heuristics if not found.
        To train: run `python train_text_model.py`
        """
        try:
            import pickle
            import os
            model_path = os.path.join(os.path.dirname(__file__), "..", "ml_models", "text_model.pkl")
            vec_path = os.path.join(os.path.dirname(__file__), "..", "ml_models", "tfidf_vectorizer.pkl")
            if os.path.exists(model_path) and os.path.exists(vec_path):
                with open(model_path, "rb") as f:
                    self.model = pickle.load(f)
                with open(vec_path, "rb") as f:
                    self.vectorizer = pickle.load(f)
                print("[TextEmotionService] Loaded sklearn model successfully.")
            else:
                print("[TextEmotionService] No trained model found. Using keyword heuristics.")
        except Exception as e:
            print(f"[TextEmotionService] Could not load model: {e}")

    def _clean_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _keyword_predict(self, text: str) -> Dict[str, Any]:
        """Simple keyword-based fallback predictor"""
        text_lower = text.lower()
        # BUG 2 FIX: iterate all 7 emotions including neutral
        scores = {emotion: 0 for emotion in EMOTIONS_ALL}

        for emotion, keywords in EMOTION_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    scores[emotion] += 1

        if all(v == 0 for v in scores.values()):
            emotion = "neutral"
            confidence = float(62 + random.randint(0, 20))
        else:
            emotion = max(scores, key=scores.get)
            total = sum(scores.values())
            confidence = round((scores[emotion] / total) * 100, 1)
            confidence = max(55.0, min(confidence, 96.0))

        # Build breakdown using EMOTIONS_ALL (always 7 keys, neutral included)
        remaining = 100.0 - confidence
        breakdown = {e: 0.0 for e in EMOTIONS_ALL}
        breakdown[emotion] = confidence
        others = [e for e in EMOTIONS_ALL if e != emotion]
        for i, e in enumerate(others):
            if i == len(others) - 1:
                breakdown[e] = round(remaining, 1)
            else:
                val = round(remaining / len(others), 1)
                breakdown[e] = val
                remaining -= val

        # BUG 7 FIX: normalize so breakdown sums exactly to 100 (eliminates rounding drift)
        total = sum(breakdown.values())
        if total > 0:
            breakdown = {e: round(v / total * 100, 1) for e, v in breakdown.items()}

        return {
            "emotion": emotion,
            "confidence": confidence,
            "emoji": EMOTION_EMOJIS.get(emotion, "😐"),
            "breakdown": breakdown,
            "suggestion": EMOTION_SUGGESTIONS.get(emotion, "Take care of yourself."),
            "input_type": "text",
        }

    def predict(self, text: str) -> Dict[str, Any]:
        """Predict emotion from text"""
        cleaned = self._clean_text(text)

        if self.model and self.vectorizer:
            try:
                vec = self.vectorizer.transform([cleaned])
                proba = self.model.predict_proba(vec)[0]
                classes = self.model.classes_
                idx = proba.argmax()
                emotion = classes[idx]
                confidence = round(float(proba[idx]) * 100, 1)
                breakdown = {c: round(float(p) * 100, 1) for c, p in zip(classes, proba)}
                return {
                    "emotion": emotion,
                    "confidence": confidence,
                    "emoji": EMOTION_EMOJIS.get(emotion, "😐"),
                    "breakdown": breakdown,
                    "suggestion": EMOTION_SUGGESTIONS.get(emotion, "Take care of yourself."),
                    "input_type": "text",
                }
            except Exception as e:
                print(f"[TextEmotionService] Prediction failed: {e}, falling back.")

        return self._keyword_predict(text)
