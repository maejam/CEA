import datetime
from typing import Optional

import jwt
from flask import current_app
from flask_login import UserMixin
from pydantic import BaseModel, Field, constr

import bunnet as bn


class User(bn.Document, UserMixin):
    username: bn.Indexed(str, unique=True)
    email: bn.Indexed(str, unique=True)
    password: str
    created: datetime.datetime = datetime.datetime.utcnow()
    is_admin: bool = False

    def get_reset_token(self, expires_seconds=1800):
        token = jwt.encode(
            {
                "user_id": str(self.id),
                "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_seconds),
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
        # TODO avec quelle exception?
        except Exception as e:
            return False
        return User.get(data.get("user_id")).run()


class Author(BaseModel):
    first_name: str
    last_name: str


class Document(bn.Document):
    author: str = ""
    content: str = ""
    url: Optional[str] = None
    # Ajouter la date en optionnel
    date: Optional[str] = None
    note: Optional[int] = None
    inserted: datetime.datetime = datetime.datetime.utcnow()

    class Settings:
        is_root = True

    def as_dict(self):
        return {"source": self.__class__.__name__, "author": self.author, "content": self.content, "url": self.url, "date": self.date, "inserted": self.inserted}


class LinkedIn(Document):
    pass


# Permet de selectionner les champs à afficher
class DocumentShortView(BaseModel):
    id: bn.PydanticObjectId = Field(alias="_id")
    # class_id = source
    class_id: str = Field(alias="_class_id")
    author: constr(curtail_length=25) = ""
    content: constr(curtail_length=100) = ""
    url: Optional[str] = None
    date: Optional[str] = None
    note: Optional[int] = None
