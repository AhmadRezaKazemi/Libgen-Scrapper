from urllib.request import urlopen
import urllib.parse
from shutil import copyfileobj
import local_settings
import cgi
import os
import random
import string

BOOK_DEFAULT_NAME_SIZE = 10


def generate_random_string(length):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def save_file(url, output_name):
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