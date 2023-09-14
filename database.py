import pymongo
from fastapi.encoders import jsonable_encoder
import models
import security
import uuid
import os
import motor.motor_asyncio
from dotenv import load_dotenv


load_dotenv()

mongo_uri = os.getenv("MONGODB_URI")
mongodb_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
db = mongodb_client["trainings_db"]
trainings_collection = db["trainings"]


async def init_db():
    print("Connecting to the MongoDB database...")
    client = mongodb_client
    db = client["trainings_db"]
    trainings_collection = db.get_collection("trainings")
    await trainings_collection.create_index([("_id", pymongo.ASCENDING)])

    print("Connected to the MongoDB database!")


### User ###

async def create_user(user_in: models.UserIn):
    user_id = str(uuid.uuid4())
    hashed_password = security.hash_password(user_in.password)
    user_db = models.UserDb(
        _id=user_id,
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
    )
    new_user = await db["users"].insert_one(jsonable_encoder(user_db))
    created_user = await db["users"].find_one({"_id": new_user.inserted_id})
    created_user["_id"] = str(created_user["_id"])
    return created_user


async def get_user_by_username_or_email(username: str, email: str):
    user = await db["users"].find_one({"$or": [{"username": username}, {"email": email}]})
    return user


async def get_user(username: str, password: str = None):
    document = await db["users"].find_one({"_id": username})
    print(f'database.get_user({username}, {password}): {document}')
    if document:
        user = models.UserDb(**document)
        if password:
            if security.verify_password(password, user.hashed_password):
                return user
        else:
            return user


### Training ###

async def save_training(training_in: models.TrainingIn):
    training_id = str(uuid.uuid4())
    training_db = models.TrainingDb(
        _id=training_id,
        title=training_in.title,
        description=training_in.description,  
        status=training_in.status,
        user_id=training_id,
    )
    new_training = await db["trainings"].insert_one(jsonable_encoder(training_db))
    created_training = await db["trainings"].find_one({"_id": new_training.inserted_id})

    created_training["_id"] = str(created_training["_id"])
    return created_training


async def perform_update_training_status(training_id: str, new_status: str):
    updated_training = await update_training_status(training_id, new_status)
    return updated_training


async def update_training_status(training_id: str, new_status: str):
    updated_training = await db["trainings"].find_one_and_update(
        {"_id": training_id},
        {"$set": {"status": new_status}},
        return_document=True
    )
    return updated_training


async def delete_training(training_id: str):
    deleted_training = await db["trainings"].find_one_and_delete({"_id": training_id})
    return deleted_training


async def list_trainings():
    trainings = []
    async for training in db["trainings"].find():
        training["_id"] = str(training["_id"])
        trainings.append(training)
    return trainings
