from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from bson.objectid import ObjectId
from pydantic import BaseModel
import bcrypt
import datetime

app = FastAPI()

client = MongoClient("mongodb://mongo:27017/")
db = client["CEA"]
user_collection = db["User"]

class User(BaseModel):
    username: str
    email: str
    password: str

class Password(BaseModel):
    password: str

class UserInDB(User):
    id: str

def get_password(a_password):
    a_password = a_password.encode("utf-8")
    sel = bcrypt.gensalt()
    hashed_pw = bcrypt.hashpw(a_password, sel)
    return hashed_pw.decode("utf-8")

@app.post("/user/")
def create_user(user: User):
    if user_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    hashed_password = get_password(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    user_dict["created"] = datetime.datetime.utcnow()
    new_user = user_collection.insert_one(user_dict)
    return {"id": str(new_user.inserted_id)}

@app.delete("/user/{user_id}")
def delete_user(user_id: str):
    user = user_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        user_collection.delete_one({"_id": ObjectId(user_id)})
        return {"detail": "User deleted"}
    else:
        raise HTTPException(status_code=404, detail="User not found")

# Same , but delete_user knowing username, not user_id
@app.delete("/user/{username}/delete_from_username")
def delete_user_from_username(username: str):
    user = user_collection.find_one({"username": username})
    if user:
        user_collection.delete_one({"username": username})
        return {"detail": "User deleted"}
    else:
        raise HTTPException(status_code=404, detail="User not found")

@app.patch("/user/{user_id}/set_admin")
def set_admin(user_id: str, is_admin: bool):
    user = user_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_admin": is_admin}})
        return {"detail": "Admin status updated"}
    else:
        raise HTTPException(status_code=404, detail="User not found")

# Same , but set_admin knowing username, not user_id
@app.patch("/user/{username}/set_admin_from_username")
def set_admin_from_username(username: str, is_admin: bool):
    user = user_collection.find_one({"username": username})
    if user:
        user_collection.update_one({"username": username}, {"$set": {"is_admin": is_admin}})
        return {"detail": "Admin status updated"}
    else:
        raise HTTPException(status_code=404, detail="User not found")


@app.patch("/user/{user_id}/change_password")
def change_password(user_id: str, password: Password):
    user = user_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        hashed_password = get_password(password.password)
        user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": hashed_password}})
        return {"detail": "Password updated"}
    else:
        raise HTTPException(status_code=404, detail="User not found")

# Same , but change_password knowing username, not user_id
@app.patch("/user/{username}/change_password_from_username")
def change_password_from_username(username: str, password: Password):
    user = user_collection.find_one({"username": username})
    if user:
        hashed_password = get_password(password.password)
        user_collection.update_one({"username": username}, {"$set": {"password": hashed_password}})
        return {"detail": "Password updated"}
    else:
        raise HTTPException(status_code=404, detail="User not found")

@app.get("/user/")
def get_all_users():
    return list(user_collection.find({}, {"_id": 0}))
