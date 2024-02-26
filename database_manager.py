from pymongo import MongoClient
from datetime import date


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
            return collection.insert_one(data).inserted_id
        except Exception as error:
            print('Error', error)
            return None

    def insert_unique_books(self, books, collection_name):
        try:
            collection = self.get_collection(collection_name)

            inserted_id = []

            for book in books:

                query = {}

                for field in ['Title', 'Author', 'Publisher', 'Edition']:
                    # Check if the field exists in the book dictionary
                    if field in book:
                        query[field] = book[field]

                existing_books_count = collection.count_documents(query)

                # If no duplicate book found, insert the new book
                if existing_books_count == 0:
                    inserted_id.append(collection.insert_one(book).inserted_id)
                else:
                    # Todo: update old book in database / add new book but with creation date? not sure
                    inserted_id.extend(
                        [book['_id']
                         for book in
                         collection.find(
                            query
                        )]
                    )

            return inserted_id
        except Exception as error:
            print('Error', error)
            return None

    def insert_books(self, keywords, unique_books, book_collection_name, query_collection_name):
        inserted_books_id = self.insert_unique_books(unique_books, book_collection_name)

        #  no books were added
        if inserted_books_id is None or len(inserted_books_id) == 0:
            return None

        inserted_query_id = self.insert(
            {
                'keywords': keywords,
                'books': inserted_books_id,
                'scrapingDate': str(date.today())
            },
            query_collection_name
        )

        return inserted_books_id, inserted_query_id

    def insert_simple_books(self, keywords, unique_books):
        return self.insert_books(keywords, unique_books, 'SimpleBooks', 'SimpleQuery')

    def insert_detailed_books(self, keywords, unique_books):
        return self.insert_books(keywords, unique_books, 'DetailedBooks', 'DetailedQuery')

    def check_old_queries(self, keywords, is_detailed):
        try:
            collection = self.get_collection('DetailedQuery' if is_detailed else 'SimpleQuery')

            if collection.count_documents({'keywords': keywords}) != 0:
                return collection.find({'keywords': keywords})

            return None
        except Exception as error:
            print('Error', error)
            return None

    def get_books(self, book_ids, is_detailed):
        try:
            collection = self.get_collection('DetailedBooks' if is_detailed else 'SimpleBooks')

            books = []

            for book_id in book_ids:
                books.append(collection.find({'_id': book_id}))

            return books
        except Exception as error:
            print('Error', error)
            return None
