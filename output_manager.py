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
import zipfile
import shutil

BOOK_DEFAULT_NAME_SIZE = 10


class MongoEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


def save_file(url, output_name, default_file_name):
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
        filename = default_file_name

    os.makedirs(output_name, exist_ok=True)

    try:
        file_path = os.path.join(output_name, filename)
        with open(file_path, 'wb') as f:
            copyfileobj(remote_file, f)
        return filename
    except Exception as e:
        return None


def download_media(books, path):
    # Todo: make percentage progress per each book
    for book in books:
        if "Image URL" in book:
            image_name = save_file(book["Image URL"], path + '\\media\\image\\', book["Title"])
            if image_name is not None:
                book["Image Path"] = '.\\media\\image\\' + image_name
            else:
                book["Image Path"] = None

        book_name = None
        for download_url in book["Download Links"]:
            book_name = save_file(download_url, path + '\\media\\file\\', book["Title"])

            if book_name is not None:
                book["Book File"] = '.\\media\\file\\' + book_name
                break

        # if no file found for this book, set None as value
        if book_name is None:
            book["Book File"] = None


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


def compress_output(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))


def generate_output(books, keywords, output_format, should_download_media):
    file_output = local_settings.PATH + keywords.replace(" ", "-") + '_' + str(date.today())

    book_list = []
    try:
        for inner_cursor in books:
            for book in inner_cursor:
                book_list.append(book)
    except Exception as e:
        print('could not turn books into a list. error:', e)

    try:
        if should_download_media:
            download_media(book_list, file_output)
    except Exception as e:
        print('could not download media. error:', e)

    try:
        os.makedirs(file_output, exist_ok=True)

        if output_format == 'json':
            json_output(book_list, file_output + '\\report.json')
        elif output_format == 'xml':
            xml_output(book_list, file_output + '\\report.xml')
        elif output_format == 'csv':
            csv_output(book_list, file_output + '\\report.csv')
        else:
            print('output not supported!')
    except Exception as e:
        print('could not create output. error:', e)
        return

    try:
        compress_output(file_output, file_output + '.zip')
        shutil.rmtree(file_output)
        print('data ready at:')
        print(file_output + '.zip')
    except Exception as e:
        print('could not compress folder. error:', e)
