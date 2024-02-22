import requests
import argparse
import json
from bs4 import BeautifulSoup
from database_manager import DatabaseManager
import local_settings


BASE_URL = "https://libgen.is/search.php?req={keyword}&open=0" \
           "&view={view_style}&res=100&phrase={mask_option}" \
           "&column={column}&page={page_number}"
WEBSITE_PREFIX = "https://libgen.is/"

# database_manager = DatabaseManager(
#     database_name=local_settings.DATABASE['name'],
#     host=local_settings.DATABASE['host'],
#     port=local_settings.DATABASE['port'],
# )


def get_webpage_data(url):
    try:
        url_response = requests.get(url)
        url_response.raise_for_status()
        return url_response
    except Exception as e:
        print(f'could not fetch {url}. error: {e}')
        return None


def download_book(urls):
    raise NotImplementedError("downloading books not implemented")
    # Todo: implement downloading book
    return urls


def book_urls(urls):
    if args.download_book:
        return download_book(urls)
    else:
        return urls


def download_image(url):
    raise NotImplementedError("downloading image not implemented")
    # Todo: implement downloading book


def book_image(url):
    if args.download_book:
        return download_image(url)
    else:
        return url


def book_title(element):
    all_names = element.find_all('a')

    if len(all_names) > 1:
        name = all_names[1]
    else:
        name = all_names[0]

    if hasattr(name, 'contents'):
        return name.contents[0].strip()
    else:
        return name.text.strip()


def parse_detailed_url(url):
    response = get_webpage_data(url)

    if response is None:
        print(f"could not load {url} for download links")
        return ""

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f'could not parse {response.url} with error: {e}')
        return ""

    all_urls = soup.find_all('table')[4]

    urls = ""
    if args.download_book:
        return download_book(urls)
    else:
        return urls


def parse_simple(soup):
    table_rows = soup.find_all('table')[2].find_all('tr')

    book_rows = table_rows[1:]

    if len(book_rows) == 0:
        return None

    all_books = [row.find_all('td') for row in book_rows]

    return [
        {
            "ID": columns[0].text.strip(),
            "Author": columns[1].text.strip(),
            "Title": book_title(columns[2]),
            "Publisher": columns[3].text.strip(),
            "Year": columns[4].text.strip(),
            "Pages": columns[5].text.strip(),
            "Language": columns[6].text.strip(),
            "Size": columns[7].text.strip(),
            "Extension": columns[8].text.strip(),
            "Link": book_urls([item.find('a')['href'] for item in columns[9:-1]]),
        } for columns in all_books
    ]


def parse_detailed(soup):
    all_books_tables = soup.find_all('table')[3:-1:2]

    if len(all_books_tables) == 0:
        return None

    books = []

    for book_table in all_books_tables:
        all_rows = book_table.find('tbody').find_all('tr')[:-1]
        first_row = all_rows[1].find_all('td')
        second_row = all_rows[2].find_all('td')
        third_row = all_rows[3].find_all('td')
        forth_row = all_rows[4].find_all('td')
        fifth_row = all_rows[5].find_all('td')
        sixth_row = all_rows[6].find_all('td')
        seventh_row = all_rows[7].find_all('td')
        eighth_row = all_rows[8].find_all('td')
        ninth_row = all_rows[9].find_all('td')

        books.append({
            "ID": seventh_row[3].text.strip(),
            "Image": book_image(WEBSITE_PREFIX + first_row[0].find('img')['src']),
            "Title": first_row[2].text.strip(),
            "Volume": first_row[3].text.split(':', 1)[-1].strip(),
            "Author": second_row[1].text.strip(),
            "Series": third_row[1].text.split(':', 1)[-1].strip(),
            "Publisher": forth_row[1].text.strip(),
            "year": fifth_row[1].text.strip(),
            "Edition": fifth_row[3].text.strip(),
            "Language": sixth_row[1].text.strip(),
            "Pages": sixth_row[3].text.strip(),
            "ISBN": seventh_row[1].text.strip(),
            "Time Added": eighth_row[1].text.strip(),
            "Time Modified": eighth_row[3].text.strip(),
            "Size": ninth_row[1].text.strip(),
            "Extension": ninth_row[3].text.strip(),
            "Link": parse_detailed_url(WEBSITE_PREFIX + first_row[2].find('a')['href']),
        })

    return books


def parse_url(response):
    try:
        soup = BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f'could not parse {response.url} with error: {e}')
        return None

    if args.detailed:
        return parse_detailed(soup)
    else:
        return parse_simple(soup)


def generate_url():
    page_index = 1

    request_url = BASE_URL.format(
        keyword=args.keywords.replace(" ", "+"),
        view_style="detailed" if args.detailed else "simple",
        mask_option="0" if args.mask_option else "1",
        column=args.column,
        page_number=page_index,
    )

    response = get_webpage_data(request_url)

    if response is None:
        print(f"Error! could not load {request_url}")
        return

    while response is not None:
        results = parse_url(response)

        # webpage would not raise 404, instead there is no content
        if results is None:
            break

        # Todo: save data in database
        for book in results:
            print(json.dumps(book, indent=4))

        page_index += 1

        request_url = BASE_URL.format(
            keyword=args.keywords.replace(" ", "+"),
            view_style="detailed" if args.detailed else "simple",
            mask_option="0" if args.mask_option else "1",
            column=args.column,
            page_number=page_index,
        )

        response = get_webpage_data(request_url)

    print(f'reached end of pages. last page was {page_index-1}')


def arg_parser():
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="libgen scrapper",
        epilog="Thanks for using"
    )

    parser.add_argument("-k", "--keywords", help="Search keywords", type=str, required=True)
    parser.add_argument("-d", "--detailed", help="Detailed scrap results", action="store_true")
    parser.add_argument(
        "-c",
        "--column",
        help="Search column. options: title, author, series, "
             "publisher, year, identifier(isbn), language, md5, tags",
        type=str,
        default="def")
    parser.add_argument("-m", "--mask_option", help="search for close words too", action="store_true")
    parser.add_argument("-db", "--download_book", help="download book instead of saving url", action="store_true")

    return parser.parse_args()


if __name__ == "__main__":
    args = arg_parser()
    try:
        generate_url()
        print('done!')
    except Exception as error:
        print('Error:', error)
