import security
import database
import models
from security import get_current_user, SECRET_KEY
from fastapi import FastAPI, Depends, HTTPException, Form, Path, Body, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from typing import List
from models import TrainingDb, TrainingIn, UserDb
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@app.on_event("startup")
async def startup_db_client():
    await database.init_db()


### API: Auth & Users ###

@app.get("/users/me")
async def get_me(current_user: dict = Depends(security.get_current_user)):
    return current_user


@app.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    return await security.login(form.username, form.password)


@app.post("/register/user", response_model=models.UserDb)
async def register_user(user: models.UserIn):
    if not security.is_valid_email(user.email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    hashed_password = security.hash_password(user.password)
    user_db = models.UserDb(
        _id=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )

    new_user = await database.db["users"].insert_one(jsonable_encoder(user_db))
    created_user = await database.db["users"].find_one({"_id": new_user.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)


### API: Training ###

@app.post("/trainings", response_model=TrainingDb)
async def create_training(
    training_in: TrainingIn,
    current_user: UserDb = Depends(get_current_user),  # Ensure this line is present
):
    created_training = await database.save_training(training_in)
    return created_training


@app.get("/trainings", response_model=List[TrainingDb])
async def list_trainings(current_user: UserDb = Depends(get_current_user)):  # Use the custom dependency here
    trainings = await database.list_trainings()
    return trainings


@app.put("/trainings/{training_id}/status")
async def update_training_status_endpoint(
        training_id: str,
        new_status: str,
        current_user: UserDb = Depends(security.get_current_user)
):
    updated_training = await database.perform_update_training_status(training_id, new_status)
    if updated_training is None:
        raise HTTPException(status_code=404, detail="Training not found")
    return updated_training


@app.delete("/trainings/{training_id}")
async def delete_training(training_id: str, current_user: UserDb = Depends(security.get_current_user)):
    deleted_training = await database.delete_training(training_id)
    if deleted_training is None:
        raise HTTPException(status_code=404, detail="Training not found")
    return deleted_training
