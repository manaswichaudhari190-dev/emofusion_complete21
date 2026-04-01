"""
EmoFusion Backend - Flask API
AI-powered emotion detection from Text, Audio, and Camera
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import jwt
import datetime
import os
from functools import wraps
from dotenv import load_dotenv

# Local imports
from models.user_model import UserModel
from models.emotion_model import EmotionModel
from services.text_emotion import TextEmotionService
from services.audio_emotion import AudioEmotionService
from services.face_emotion import FaceEmotionService

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"], supports_credentials=True)
bcrypt = Bcrypt(app)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "emofusion-secret-key-2024")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

# Initialize services
user_model = UserModel()
emotion_model = EmotionModel()
text_service = TextEmotionService()
audio_service = AudioEmotionService()
face_service = FaceEmotionService()


# ─── JWT Auth Decorator ────────────────────────────────────────────────────────
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = user_model.find_by_id(data["user_id"])
            if not current_user:
                return jsonify({"error": "Invalid token"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(current_user, *args, **kwargs)
    return decorated


# ─── Auth Routes ───────────────────────────────────────────────────────────────
@app.route("/signup", methods=["POST"])
def signup():
    """Register a new user"""
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    if not all([name, email, password]):
        return jsonify({"error": "All fields are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if user_model.find_by_email(email):
        return jsonify({"error": "Email already registered"}), 409

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    user_id = user_model.create(name, email, hashed_pw)

    token = jwt.encode(
        {
            "user_id": user_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
        },
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )

    return jsonify({
        "message": "Account created successfully",
        "token": token,
        "user": {"id": user_id, "name": name, "email": email},
    }), 201


@app.route("/login", methods=["POST"])
def login():
    """Log in an existing user"""
    data = request.get_json()
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    if not all([email, password]):
        return jsonify({"error": "Email and password required"}), 400

    user = user_model.find_by_email(email)
    if not user or not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = jwt.encode(
        {
            "user_id": str(user["_id"]),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
        },
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
        },
    })


# ─── Emotion Detection Routes ──────────────────────────────────────────────────
@app.route("/predict-text", methods=["POST"])
@token_required
def predict_text(current_user):
    """Detect emotion from text input"""
    data = request.get_json()
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "Text input required"}), 400

    if len(text) > 1000:
        return jsonify({"error": "Text too long (max 1000 characters)"}), 400

    result = text_service.predict(text)
    emotion_model.log(
        user_id=str(current_user["_id"]),
        emotion=result["emotion"],
        confidence=result["confidence"],
        input_type="text",
    )

    return jsonify(result)


@app.route("/predict-audio", methods=["POST"])
@token_required
def predict_audio(current_user):
    """Detect emotion from audio file"""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    if audio_file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    allowed = {"wav", "mp3", "ogg", "webm"}
    ext = audio_file.filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed:
        return jsonify({"error": "Unsupported audio format"}), 400

    result = audio_service.predict(audio_file)
    emotion_model.log(
        user_id=str(current_user["_id"]),
        emotion=result["emotion"],
        confidence=result["confidence"],
        input_type="audio",
    )

    return jsonify(result)


@app.route("/predict-face", methods=["POST"])
@token_required
def predict_face(current_user):
    """Detect emotion from camera image"""
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image_file = request.files["image"]
    result = face_service.predict(image_file)

    emotion_model.log(
        user_id=str(current_user["_id"]),
        emotion=result["emotion"],
        confidence=result["confidence"],
        input_type="camera",
    )

    return jsonify(result)


# ─── History & Profile Routes ──────────────────────────────────────────────────
@app.route("/history", methods=["GET"])
@token_required
def get_history(current_user):
    """Get user's emotion history"""
    limit = min(int(request.args.get("limit", 50)), 100)
    history = emotion_model.get_by_user(str(current_user["_id"]), limit=limit)
    return jsonify({"history": history})


@app.route("/profile", methods=["GET"])
@token_required
def get_profile(current_user):
    """Get user profile and stats"""
    stats = emotion_model.get_stats(str(current_user["_id"]))
    return jsonify({
        "user": {
            "id": str(current_user["_id"]),
            "name": current_user["name"],
            "email": current_user["email"],
            "created_at": str(current_user.get("created_at", "")),
        },
        "stats": stats,
    })


# ─── Admin Routes ──────────────────────────────────────────────────────────────
@app.route("/admin/users", methods=["GET"])
@token_required
def admin_users(current_user):
    """Admin: list all users"""
    if not current_user.get("is_admin"):
        return jsonify({"error": "Admin access required"}), 403
    users = user_model.get_all()
    return jsonify({"users": users})


@app.route("/admin/emotions", methods=["GET"])
@token_required
def admin_emotions(current_user):
    """Admin: list all emotion logs"""
    if not current_user.get("is_admin"):
        return jsonify({"error": "Admin access required"}), 403
    logs = emotion_model.get_all(limit=200)
    return jsonify({"logs": logs})


# ─── Health Check ──────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "app": "EmoFusion API v1.0"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
