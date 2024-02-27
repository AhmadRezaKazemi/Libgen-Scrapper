from urllib.request import urlopen
import urllib.parse
from shutil import copyfileobj
from bson import ObjectId
from datetime import date
import local_settings
import cgi
import os
import random
import string
import json
import xml.etree.ElementTree as eT
import csv

BOOK_DEFAULT_NAME_SIZE = 10


def generate_random_string(length):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def save_file(url, output_name):
    # Todo: add command to download books
    try:
        remote_file = urlopen(url)
        content_disposition = remote_file.info()['Content-Disposition']
    except Exception as e:
        return None

    try:
        if content_disposition is not None:
            _, params = cgi.parse_header(content_disposition)
            filename = params["filename"]
        else:
            filename = os.path.basename(urllib.parse.unquote(url))
    except Exception as e:
        filename = generate_random_string(BOOK_DEFAULT_NAME_SIZE)

    os.makedirs(local_settings.PATH + output_name, exist_ok=True)

    try:
        file_path = os.path.join(local_settings.PATH + output_name, filename)
        with open(file_path, 'wb') as f:
            copyfileobj(remote_file, f)
        return file_path
    except Exception as e:
        return None


def download_media(books):
    return


class MongoEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


def json_output(books, path):
    with open(path, "w") as json_file:
        json.dump(books, json_file, indent=4, cls=MongoEncoder)


def xml_output(books, path):
    root = eT.Element("books")

    for book_dict in books:
        book_elem = eT.SubElement(root, "book")

        for key, value in book_dict.items():
            if isinstance(value, ObjectId):
                value = str(value)

            key = key.replace(" ", "_")

            if isinstance(value, list):
                for item in value:
                    sub_elem = eT.SubElement(book_elem, key)
                    sub_elem.text = item
            else:
                sub_elem = eT.SubElement(book_elem, key)
                sub_elem.text = value

    tree = eT.ElementTree(root)

    with open(path, "wb") as xml_file:
        tree.write(xml_file, encoding="utf-8", xml_declaration=True)


def csv_output(books, path):
    headers = list(books[0].keys())

    # Write the list of dictionaries to the CSV file
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(books)


def compress_output(path):
    return


def generate_output(books, keywords, output_format):
    output = keywords.replace(" ", "-") + '_' + str(date.today())

    book_list = []
    for inner_cursor in books:
        for book in inner_cursor:
            book_list.append(book)

    if output_format == 'json':
        json_output(book_list, local_settings.PATH + output + '.json')
    elif output_format == 'xml':
        xml_output(book_list, local_settings.PATH + output + '.xml')
    elif output_format == 'csv':
        csv_output(book_list, local_settings.PATH + output + '.csv')
    else:
        print('output not supported!')
