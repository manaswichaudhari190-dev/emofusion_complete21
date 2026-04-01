"""
Emotion Model — MongoDB operations for emotion detection logs
"""

import os
import datetime
from bson import ObjectId
from pymongo import MongoClient


class EmotionModel:
    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/emofusion")
        client = MongoClient(mongo_uri)
        db = client.get_default_database()
        self.col = db["emotions"]

    def log(self, user_id: str, emotion: str, confidence: float, input_type: str):
        doc = {
            "user_id": user_id,
            "emotion": emotion,
            "confidence": round(confidence, 2),
            "input_type": input_type,
            "timestamp": datetime.datetime.utcnow(),
        }
        self.col.insert_one(doc)

    def get_by_user(self, user_id: str, limit: int = 50) -> list:
        records = []
        for r in self.col.find({"user_id": user_id}).sort("timestamp", -1).limit(limit):
            r["_id"] = str(r["_id"])
            r["timestamp"] = r["timestamp"].isoformat()
            records.append(r)
        return records

    def get_stats(self, user_id: str) -> dict:
        records = self.get_by_user(user_id, limit=1000)
        if not records:
            return {"total": 0, "dominant_emotion": None, "by_type": {}}

        emotion_counts = {}
        type_counts = {}
        for r in records:
            emotion_counts[r["emotion"]] = emotion_counts.get(r["emotion"], 0) + 1
            type_counts[r["input_type"]] = type_counts.get(r["input_type"], 0) + 1

        dominant = max(emotion_counts, key=emotion_counts.get)
        return {
            "total": len(records),
            "dominant_emotion": dominant,
            "emotion_distribution": emotion_counts,
            "by_type": type_counts,
        }

    def get_all(self, limit: int = 200) -> list:
        records = []
        for r in self.col.find({}).sort("timestamp", -1).limit(limit):
            r["_id"] = str(r["_id"])
            r["timestamp"] = r["timestamp"].isoformat()
            records.append(r)
        return records
