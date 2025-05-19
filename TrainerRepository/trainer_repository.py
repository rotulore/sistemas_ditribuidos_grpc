from bson import ObjectId
from datetime import datetime

class TrainerRepository:
    def __init__(self, collection):
        self.collection = collection

    def get_by_id(self, id_str):
        doc = self.collection.find_one({"_id": ObjectId(id_str)})
        return doc

    def create(self, data):
        # añade timestamp de creación
        data["created_at"] = datetime.utcnow()
        result = self.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return data
