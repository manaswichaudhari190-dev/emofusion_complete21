"""
Train Text Emotion Model
TF-IDF + Logistic Regression on a small seed dataset.
For production, replace with a BERT fine-tuned model or use:
  pip install transformers
  model = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")

Run: python train_text_model.py
"""

import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# ─── Seed Training Data ────────────────────────────────────────────────────────
# Expand this dataset for better accuracy. Use ISEAR or GoEmotions dataset.
TRAINING_DATA = [
    # happy
    ("I am so happy today!", "happy"),
    ("This is wonderful news, I'm thrilled!", "happy"),
    ("I love spending time with my friends", "happy"),
    ("Best day of my life, feeling amazing!", "happy"),
    ("I just got promoted, feeling great!", "happy"),
    ("Everything is going so well for me", "happy"),
    ("I'm so excited about this opportunity", "happy"),
    ("This makes me smile so much", "happy"),
    # sad
    ("I feel so sad and alone", "sad"),
    ("I can't stop crying, everything hurts", "sad"),
    ("I miss my family so much", "sad"),
    ("Nothing seems to be going right", "sad"),
    ("I'm feeling really down and hopeless", "sad"),
    ("My heart is broken and I don't know what to do", "sad"),
    ("I feel like nobody cares about me", "sad"),
    # angry
    ("I am so angry right now!", "angry"),
    ("This is completely unacceptable behavior", "angry"),
    ("I hate when people do that, it's infuriating", "angry"),
    ("Stop doing this, it makes me furious", "angry"),
    ("I'm fed up with all of this", "angry"),
    ("Why does this keep happening, I'm so mad", "angry"),
    # fear
    ("I'm really scared about what might happen", "fear"),
    ("I feel so anxious and nervous", "fear"),
    ("What if something terrible happens?", "fear"),
    ("I'm terrified of the future", "fear"),
    ("I keep worrying about everything", "fear"),
    ("I'm so afraid of making mistakes", "fear"),
    # neutral
    ("I went to the store and bought groceries", "neutral"),
    ("The meeting is scheduled for Monday", "neutral"),
    ("I read a book this afternoon", "neutral"),
    ("The weather is cloudy today", "neutral"),
    ("I completed my tasks for the day", "neutral"),
    # disgust
    ("That is absolutely disgusting", "disgust"),
    ("I can't believe how gross that is", "disgust"),
    ("This situation is revolting", "disgust"),
    ("I feel sick looking at this", "disgust"),
    # surprise
    ("Wow, I did not expect that at all!", "surprise"),
    ("Oh my goodness, this is shocking!", "surprise"),
    ("I can't believe what just happened", "surprise"),
    ("That was completely unexpected!", "surprise"),
    ("What?! How is that even possible?", "surprise"),
]

texts, labels = zip(*TRAINING_DATA)

# ─── Train ────────────────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    texts, labels, test_size=0.2, random_state=42, stratify=labels
)

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
    ("clf", LogisticRegression(max_iter=500, C=1.0)),
])

pipeline.fit(X_train, y_train)

print("=== Training Complete ===")
y_pred = pipeline.predict(X_test)
print(classification_report(y_test, y_pred))

# ─── Save Model ───────────────────────────────────────────────────────────────
os.makedirs("ml_models", exist_ok=True)

# Save as separate components for the service to load
vectorizer = pipeline.named_steps["tfidf"]
clf = pipeline.named_steps["clf"]

with open("ml_models/tfidf_vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

with open("ml_models/text_model.pkl", "wb") as f:
    pickle.dump(clf, f)

print("\n✅ Model saved to ml_models/")
print("  - ml_models/tfidf_vectorizer.pkl")
print("  - ml_models/text_model.pkl")
print("\nFor better accuracy, use the GoEmotions dataset:")
print("  https://github.com/google-research/google-research/tree/master/goemotions")
