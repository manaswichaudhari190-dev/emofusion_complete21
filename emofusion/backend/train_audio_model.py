"""
Train Audio CNN Emotion Model
Mel Spectrogram + 2D CNN based on the research paper:
"Speech Emotion Recognition using Mel Spectrogram and CNNs" (Sareen & Seeja, 2025)

Supports: TESS, RAVDESS, SAVEE datasets
Run: python train_audio_model.py --dataset_path /path/to/audio/files

Dataset structure expected:
  dataset/
    happy/    *.wav files
    sad/      *.wav files
    angry/    *.wav files
    ...
"""

import os
import argparse
import numpy as np

# ─── Feature Extraction ────────────────────────────────────────────────────────
def extract_mel(audio_path: str) -> np.ndarray:
    """Extract Mel Spectrogram. Returns (128, 251, 1) array."""
    import librosa
    y, sr = librosa.load(audio_path, sr=44100, duration=2.5)
    target_len = int(44100 * 2.5)
    if len(y) < target_len:
        y = np.pad(y, (0, target_len - len(y)))
    else:
        y = y[:target_len]

    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
    mel_db = librosa.power_to_db(mel, ref=np.max)

    if mel_db.shape[1] < 251:
        mel_db = np.pad(mel_db, ((0, 0), (0, 251 - mel_db.shape[1])))
    else:
        mel_db = mel_db[:, :251]

    mel_db = (mel_db - mel_db.min()) / (mel_db.max() - mel_db.min() + 1e-8)
    return mel_db.reshape(128, 251, 1)


def augment(y, sr):
    """Data augmentation: pitch shift and time stretch"""
    import librosa
    augmented = [y]
    try:
        augmented.append(librosa.effects.pitch_shift(y, sr=sr, n_steps=3))
        augmented.append(librosa.effects.pitch_shift(y, sr=sr, n_steps=-3))
        augmented.append(librosa.effects.time_stretch(y, rate=0.8))
        augmented.append(librosa.effects.time_stretch(y, rate=1.3))
    except Exception:
        pass
    return augmented


# ─── Build CNN Model ──────────────────────────────────────────────────────────
def build_model(num_classes: int):
    import tensorflow as tf
    from tensorflow.keras import layers, models

    model = models.Sequential([
        # Block 1
        layers.Conv2D(32, (5, 5), padding="same", input_shape=(128, 251, 1)),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D((2, 2)),

        # Block 2
        layers.Conv2D(64, (3, 3), padding="same"),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D((2, 2)),

        # Block 3
        layers.Conv2D(128, (3, 3), padding="same"),
        layers.BatchNormalization(),
        layers.Activation("relu"),
        layers.MaxPooling2D((2, 2)),

        # Classifier
        layers.Flatten(),
        layers.Dense(256, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation="softmax"),
    ])

    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_path", default="dataset", help="Path to audio dataset folder")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch_size", type=int, default=32)
    args = parser.parse_args()

    EMOTIONS = ["happy", "sad", "angry", "fear", "neutral", "disgust", "surprise"]
    label_map = {e: i for i, e in enumerate(EMOTIONS)}

    print("📂 Loading dataset...")
    X, y = [], []

    for emotion in EMOTIONS:
        folder = os.path.join(args.dataset_path, emotion)
        if not os.path.exists(folder):
            print(f"  ⚠️  Folder not found: {folder}")
            continue

        files = [f for f in os.listdir(folder) if f.endswith((".wav", ".mp3"))]
        print(f"  {emotion}: {len(files)} files")

        for fname in files:
            path = os.path.join(folder, fname)
            try:
                feat = extract_mel(path)
                X.append(feat)
                y.append(label_map[emotion])
            except Exception as e:
                print(f"    Skipping {fname}: {e}")

    if not X:
        print("❌ No data found. Check your dataset_path.")
        return

    X = np.array(X, dtype=np.float32)
    y = np.array(y)
    print(f"\n📊 Dataset: {len(X)} samples, {len(EMOTIONS)} classes")

    # Train/val split
    from sklearn.model_selection import train_test_split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = build_model(len(EMOTIONS))
    model.summary()

    import tensorflow as tf
    callbacks = [
        tf.keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(patience=3, factor=0.5),
    ]

    print("\n🚀 Training...")
    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
    )

    os.makedirs("ml_models", exist_ok=True)
    model.save("ml_models/audio_cnn_model.h5")
    print("\n✅ Model saved to ml_models/audio_cnn_model.h5")
    print("   Place this file in the backend/ml_models/ folder.")


if __name__ == "__main__":
    main()
