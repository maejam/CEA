import datetime
from typing import Optional, Dict


import pymongo
from pydantic import BaseModel, Field, validator, constr
from bson.objectid import ObjectId
import bunnet as bn
import jwt
from flask import current_app
from flask_login import UserMixin


class User(bn.Document, UserMixin):
    username: bn.Indexed(str, unique=True)#, index_type=pymongo.TEXT)
    email: bn.Indexed(str, unique=True)#, index_type=pymongo.TEXT)
    password: str
    created: datetime.datetime = datetime.datetime.utcnow()

    def get_reset_token(self, expires_seconds=1800):
        token = jwt.encode(
                {
                    "user_id": str(self.id),
                    "exp": datetime.datetime.utcnow()+datetime.timedelta(seconds=expires_seconds),
                },
                current_app.config["SECRET_KEY"],
                algorithm="HS256"
                )
        return token

    @staticmethod
    def check_reset_token(token):
        try:
            data = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                leeway=datetime.timedelta(seconds=10),
                algorithms=["HS256"]
                )
        except:
            return False
        return User.get(data.get("user_id")).run()


class Author(BaseModel):
    first_name: str
    last_name: str


class Document(bn.Document):
    # title: str
    author: str
    content: str
    # inserted: datetime.datetime = datetime.datetime.utcnow()
    # grades: Optional[Dict[User, int]]

    class Settings:
        is_root = True


class LinkedIn(Document):
    pass


class DocumentShortView(BaseModel):
    id: bn.PydanticObjectId = Field(alias="_id")
    class_id: str =Field(alias="_class_id")
    author: constr(curtail_length=25)
    content: constr(curtail_length=100)
