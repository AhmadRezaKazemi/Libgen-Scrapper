#### Libgen Scrapper

this is a free source scrapper you can use to get books you like from https://libgen.is/ domain.

you enter the keywords, it scraps the website and fetches all books, then saves the query in mongodb.<br />
then it returns a zip file containing all books in the website with details.<br />
when you enter keywords that are already fetched before it gives you the option to fetch them instead or scrap again.<br />
you can also fetch already scrapped data so far and use them.

#### installation

simply download the files.
then create a "local_settings.py" like "sample_settings.py" and fill the information like the following:

DATABASE = {<br />
'name': Database Name,<br />
'host': host,<br />
'port': port,<br />
}<br />
PATH = where to save output

#### how to use:

run the main.py with the -k argument followed by search string. wait until data is processed.
then you can see the outcome in the path specified in the local_settings.py

optional commands: <br />
-d  ->  use this command to gather more information about each book and a book cover url<br />
-c  ->  change which column to search in. the columns are as follows:
title, author, series, publisher, year, identifier(isbn), language, md5, tags<br />
-m  ->  turn on mask option to return book with similar name ending too<br />
-o  ->  ignore scrapping and search mongodb for old scrapped data<br />
-of ->  output result format, default format is json. valid formats are: json, xml, csv
-db ->  download image and one book file per book and save them in the "media" folder beside result
-to ->  timeout for fetching website url, default value is 3.
