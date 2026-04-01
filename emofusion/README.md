# 🧠 EmoFusion — AI-Powered Emotion Detection

A full-stack web application that detects emotions from **Text**, **Audio**, and **Camera** using AI/ML.

---

## 📁 Project Structure

```
emofusion/
├── backend/                        ← Flask Python API
│   ├── app.py                      ← Main Flask app (all routes)
│   ├── requirements.txt            ← Python dependencies
│   ├── .env.example                ← Environment variables template
│   ├── train_text_model.py         ← Train TF-IDF text model
│   ├── train_audio_model.py        ← Train CNN audio model
│   ├── models/
│   │   ├── user_model.py           ← MongoDB users collection
│   │   └── emotion_model.py        ← MongoDB emotions collection
│   ├── services/
│   │   ├── text_emotion.py         ← NLP emotion service
│   │   ├── audio_emotion.py        ← Mel Spectrogram + CNN service
│   │   └── face_emotion.py         ← DeepFace / FER service
│   └── ml_models/                  ← (auto-created) Saved model files
│       ├── text_model.pkl
│       ├── tfidf_vectorizer.pkl
│       └── audio_cnn_model.h5
│
└── frontend/                       ← React + Tailwind CSS
    ├── package.json
    ├── tailwind.config.js
    ├── public/index.html
    └── src/
        ├── App.jsx                  ← Router & protected routes
        ├── index.js
        ├── index.css               ← Tailwind + custom styles
        ├── context/
        │   └── AuthContext.jsx     ← JWT auth context
        ├── utils/
        │   ├── api.js              ← Axios instance
        │   └── emotions.js         ← Emotion constants & helpers
        ├── components/
        │   ├── Layout.jsx          ← Sidebar navigation
        │   ├── EmotionResult.jsx   ← Result card with breakdown
        │   ├── TextDetection.jsx   ← Text input + analysis
        │   ├── AudioDetection.jsx  ← Record / upload + analysis
        │   ├── CameraDetection.jsx ← WebRTC + face capture
        │   └── Spinner.jsx         ← Loading spinner
        └── pages/
            ├── LoginPage.jsx
            ├── SignupPage.jsx
            ├── DashboardPage.jsx   ← 3-tab detection interface
            ├── HistoryPage.jsx     ← Charts + history table
            └── AdminPage.jsx       ← User & log management
```

---

## ⚡ Quick Setup (Step by Step)

### Prerequisites
- Python 3.9+ 
- Node.js 18+ and npm
- MongoDB (local or [MongoDB Atlas](https://www.mongodb.com/atlas) free tier)

---

### Step 1 — Clone / Download

```bash
# If using git:
git clone https://github.com/yourname/emofusion.git
cd emofusion

# Or unzip the downloaded folder and cd into it
```

---

### Step 2 — Backend Setup

```bash
cd backend

# Create and activate a virtual environment (recommended)
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# Install core dependencies
pip install flask flask-cors flask-bcrypt PyJWT pymongo python-dotenv \
            numpy scikit-learn librosa soundfile

# Configure environment
cp .env.example .env
# Edit .env — set MONGO_URI if using Atlas
```

#### Optional: Install AI libraries for real models

```bash
# Face detection (choose one)
pip install deepface          # Recommended — uses pre-trained models
# OR
pip install fer opencv-python  # Lighter alternative

# Audio CNN model
pip install tensorflow keras   # Heavy (~500MB) — needed for real audio model

# Better text NLP (BERT)
pip install transformers torch  # Very large — for production upgrade
```

#### Train the text model (takes ~5 seconds)

```bash
python train_text_model.py
# Creates: ml_models/text_model.pkl + ml_models/tfidf_vectorizer.pkl
```

#### Train the audio CNN model (requires dataset)

```bash
# Download TESS dataset: https://tspace.library.utoronto.ca/handle/1807/24487
# Organize it as:
#   dataset/happy/*.wav
#   dataset/sad/*.wav
#   dataset/angry/*.wav   ... etc.

python train_audio_model.py --dataset_path ./dataset --epochs 30
# Creates: ml_models/audio_cnn_model.h5
```

#### Start the backend

```bash
python app.py
# Running on http://localhost:5000
```

---

### Step 3 — Frontend Setup

```bash
# Open a new terminal
cd frontend

# Install dependencies
npm install

# Install Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Start development server
npm start
# Opens http://localhost:3000
```

---

### Step 4 — MongoDB Setup

**Option A: Local MongoDB**
```bash
# Install MongoDB Community Edition from https://www.mongodb.com/try/download/community
# Start service:
mongod --dbpath ./data/db
# Default URI: mongodb://localhost:27017/emofusion
```

**Option B: MongoDB Atlas (Free Cloud)**
1. Go to https://www.mongodb.com/atlas
2. Create a free cluster
3. Get your connection string
4. Update `.env`: `MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/emofusion`

---

## 🚀 Running the App

```bash
# Terminal 1 — Backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python app.py

# Terminal 2 — Frontend
cd frontend
npm start
```

Open **http://localhost:3000** in your browser.

1. Click **Sign Up** to create an account
2. Go to **Dashboard** and pick Text / Audio / Camera
3. Analyze your emotion!
4. View your **History** page for charts and trends

---

## 🔌 API Endpoints

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| POST | `/signup` | ❌ | Register new user |
| POST | `/login` | ❌ | Login, get JWT token |
| POST | `/predict-text` | ✅ | Detect emotion from text |
| POST | `/predict-audio` | ✅ | Detect emotion from audio file |
| POST | `/predict-face` | ✅ | Detect emotion from image |
| GET | `/history` | ✅ | Get user's emotion history |
| GET | `/profile` | ✅ | Get user profile + stats |
| GET | `/admin/users` | ✅ Admin | List all users |
| GET | `/admin/emotions` | ✅ Admin | List all emotion logs |
| GET | `/health` | ❌ | API health check |

---

## 🤖 AI/ML Models

### Text Emotion (NLP)
- **Default**: TF-IDF + Logistic Regression (keyword features)
- **Upgrade**: HuggingFace BERT — `j-hartmann/emotion-english-distilroberta-base`
- **Emotions**: Happy, Sad, Angry, Fear, Neutral, Disgust, Surprise

### Audio Emotion (CNN)
- **Pipeline**: Audio → Librosa → Mel Spectrogram (128×251) → 2D CNN
- **Architecture**: 3× Conv2D + BatchNorm + MaxPool → Dense(256) → Dense(7)
- **Datasets**: TESS (99.89%), RAVDESS+SAVEE+TESS (87%)
- Based on: *Sareen & Seeja, Procedia Computer Science 258, 2025*

### Face Emotion
- **Primary**: DeepFace (pre-trained, no training needed)
- **Fallback**: FER library with MTCNN
- **Backup**: Simulation mode (for demo without libraries)

---

## 🛠 Environment Variables

```env
MONGO_URI=mongodb://localhost:27017/emofusion
SECRET_KEY=your-super-secret-jwt-key-change-this
FLASK_ENV=development
PORT=5000
```

---

## 🔐 Making a User Admin

```bash
# Open MongoDB shell or MongoDB Compass
use emofusion
db.users.updateOne(
  { email: "your@email.com" },
  { $set: { is_admin: true } }
)
```

---

## 🚢 Deployment

### Backend (Render / Railway)
```bash
# Add to backend/: Procfile
web: gunicorn app:app

pip install gunicorn
pip freeze > requirements.txt
```

### Frontend (Vercel / Netlify)
```bash
cd frontend
npm run build
# Deploy the /build folder
# Set environment variable: REACT_APP_API_URL=https://your-backend.com
```

---

## 🔮 Upgrade Path

| Feature | How to enable |
|---------|--------------|
| BERT text model | `pip install transformers torch` + update `text_emotion.py` |
| Real CNN audio | Train with TESS dataset using `train_audio_model.py` |
| Real face detection | `pip install deepface` (auto-loads pre-trained weights) |
| Cloud DB | Set `MONGO_URI` in `.env` to MongoDB Atlas |
| Dark/Light toggle | Add a theme toggle to `Layout.jsx` |
| Email verification | Add `flask-mail` to backend |
| PWA | Add `manifest.json` + service worker to frontend |

---

## 📚 References

1. Sareen, V., & Seeja, K.R. (2025). Speech Emotion Recognition using Mel Spectrogram and CNN. *Procedia Computer Science*, 258, 3693–3702.
2. TESS Dataset — Toronto Emotional Speech Set
3. RAVDESS Dataset — Ryerson Audio-Visual Database
4. DeepFace — https://github.com/serengil/deepface

---

*EmoFusion — Built with ❤️ for AI & Mental Health Awareness*
