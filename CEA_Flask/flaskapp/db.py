from pymongo import MongoClient
import bunnet as bn
import logging as log

from .models import User, Document, LinkedIn


def init_db(DB_CONN_STR, DB_NAME):
    client = MongoClient(DB_CONN_STR)
    bn.init_bunnet(database=client[DB_NAME], document_models=[
                   User, Document, LinkedIn])


# Module to interact with MongoDB


class MongoAPI:
    def __init__(self, DB_CONN_STR, DB_NAME, data):
        log.basicConfig(level=log.DEBUG,
                        format='%(asctime)s %(levelname)s:\n%(message)s\n')
        self.client = MongoClient(DB_CONN_STR)

        # The right name should be edited here !!!
        database = data[DB_NAME]
        collection = data['name_of_the_collection']
        cursor = self.client[database]
        self.collection = cursor[collection]
        self.data = data

    def read(self):
        """Read all of the documents in the collection"""
        log.info("Reading All Data")
        documents = self.collection.find()
        # Reformat the output of the collection and remove the field "_id"
        output = [{item: data[item] for item in data if item != '_id'}
                  for data in documents]
        return output

    def write(self, data):
        """Add a new document to a collection"""
        log.info("writting Data")
        new_document = data['Document']
        response = self.collection.insert_one(
            new_document)  # insert one document at a time
        output = {'Status': 'Successfully inserted',
                  'Document_ID': str(response.inserted_id)}
        return output

    def update(self):
        """update a new document in a collection"""
        log.info('Updating Data')
        filt = self.data['Filter']
        updated_data = {"$set": self.data['DataToBeUpdated']}
        response = self.collection.update_one(filt, updated_data)
        output = {'Status': 'Successfully Updated' if response.modified_count >
                  0 else 'Nothing were updated'}
        return output

    def delete(self, data):
        """Delete a document in a collection"""
        log.info('Deleting Data')
        filt = data['Filter']
        response = self.collection.delete_one(filt)
        output = {'Status': 'Successfully Deleted' if response.deleted_count >
                  0 else "Document not found."}
        return output
