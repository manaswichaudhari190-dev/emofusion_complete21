FROM python:3.11-slim

WORKDIR /app

# System deps for librosa / opencv
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 ffmpeg libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

# Create ml_models directory
RUN mkdir -p ml_models

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
