from pydantic import BaseModel, Field
from typing import Optional


class TrainingIn(BaseModel):
    title: str
    description: str
    status: Optional[str]


class TrainingDb(BaseModel):
    id: str = Field(alias="_id")
    title: str
    description: str
    status: Optional[str]
    user_id: str


class UserIn(BaseModel):
    username: str
    email: str
    password: str


class UserDb(BaseModel):
    username: str = Field(alias="_id")
    email: str
    hashed_password: str
