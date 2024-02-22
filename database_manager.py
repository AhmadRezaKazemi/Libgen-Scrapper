from pymongo import MongoClient


class DatabaseManager:
    def __init__(self, database_name, host, port):
        self.database_name = database_name
        self.host = host
        self.port = port

        self.db = self.connect_to_database()

    def connect_to_database(self):
        try:
            client = MongoClient(
                host=self.host,
                port=self.port
            )
            mongodb_database = client[self.database_name]
            return mongodb_database
        except Exception as error:
            print('Error', error)
            return None

    def get_collection(self, collection_name):
        collections = self.db.list_collection_names()
        if collection_name in collections:
            return self.db.get_collection(collection_name)
        else:
            return self.db[collection_name]

    def insert(self, data, collection_name):
        try:
            collection = self.get_collection(collection_name)

            if type(data) == list:
                if len(data) == 1:
                    return collection.insert_one(data).inserted_id
                else:
                    return collection.insert_many(data).inserted_ids
            if type(data) == dict:
                return collection.insert_one(data).inserted_id
        except Exception as error:
            print('Error', error)
            return None
