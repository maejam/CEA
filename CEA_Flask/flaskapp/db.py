from pymongo import MongoClient
import bunnet as bn


from .models import User, Document, LinkedIn


def init_db(DB_CONN_STR, DB_NAME):
    client = MongoClient(DB_CONN_STR)
    bn.init_bunnet(database=client[DB_NAME], document_models=[User, Document, LinkedIn])
