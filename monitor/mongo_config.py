from pymongo import MongoClient

def get_mongo_collection(collection_name):
    client = MongoClient("mongodb://localhost:27017/")
    db = client["safeweb_db"]  # ✅ This should match the name of your MongoDB database
    return db[collection_name]
