import datetime
import time
from typing import Optional, List, Any

import jwt
from flask import current_app
from flask_login import UserMixin
from pydantic import BaseModel, root_validator, Field, constr, validator
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


class Prediction(BaseModel):
    inserted = time.time()
    run_id: str
    prediction: List


class Document(bn.Document):
    author: str = None
    content: str = None
    url: Optional[str] = None
    date: Optional[str] = None
    note: Optional[int] = None
    predictions: List[Prediction] = None
    inserted = time.time()

    class Config:
        extra = "allow"

    class Settings:
        is_root = True

    def as_dict(self):
        return {"source": self.__class__.__name__, "author": self.author, "content": self.content, "note": self.note, "url": self.url, "date": self.date, "inserted": self.inserted, "predictions": self.predictions}


class LinkedIn(Document):
    pass

class Gscholar(Document):
    pass

# Permet de selectionner les champs à afficher
class DocumentShortView(BaseModel):
    id: bn.PydanticObjectId = Field(alias="_id")
    # class_id = source
    class_id: str = Field(alias="_class_id")
    author: constr(curtail_length=25) = ""
    content: constr(curtail_length=100) = ""
    url: Optional[str] = None
    note: Optional[int] = None
    date: Optional[str] = None
    DistilbertForClassification_v1: Optional[float] = None
    prediction: Optional[float] = None

    @root_validator
    def display_prediction(cls, values):
        # If no prediction, display DistilbertForClassification_v1
        if not values.get("prediction") and values.get("DistilbertForClassification_v1"):
            values["prediction"] = values["DistilbertForClassification_v1"]
        elif not values.get("prediction"):
            values["prediction"] = 0.0
        values["prediction"] = round(values["prediction"] * 100, 1)
        return values

    @validator("class_id")
    def source(cls, class_id):
        return class_id.split(".")[1]

    def as_dict(self):
        return {"id": self.id, "class_id": self.class_id, "author": self.author, "content": self.content, "url": self.url, "date": self.date, "prediction": self.prediction, "note": self.note}


class DocumentForModelsView(BaseModel):
    content: str
    note: Optional[int]
    def as_dict(self):
        return {"content": self.content, "note": self.note}

