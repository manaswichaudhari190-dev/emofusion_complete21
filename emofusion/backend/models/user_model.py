"""
User Model — MongoDB operations for user accounts
"""

import os
import datetime
from bson import ObjectId
from pymongo import MongoClient


class UserModel:
    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/emofusion")
        client = MongoClient(mongo_uri)
        db = client.get_default_database()
        self.col = db["users"]
        # Ensure unique index on email
        self.col.create_index("email", unique=True)

    def create(self, name: str, email: str, hashed_password: str) -> str:
        doc = {
            "name": name,
            "email": email,
            "password": hashed_password,
            "is_admin": False,
            "created_at": datetime.datetime.utcnow(),
        }
        result = self.col.insert_one(doc)
        return str(result.inserted_id)

    def find_by_email(self, email: str):
        return self.col.find_one({"email": email})

    def find_by_id(self, user_id: str):
        try:
            return self.col.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None

    def get_all(self) -> list:
        users = []
        for u in self.col.find({}, {"password": 0}):
            u["_id"] = str(u["_id"])
            if "created_at" in u:
                u["created_at"] = u["created_at"].isoformat()
            users.append(u)
        return users
