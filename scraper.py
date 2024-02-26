import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import validators
import threading
import time

BASE_URL = "https://libgen.is/search.php?req={keyword}&open=0" \
           "&view={view_style}&res=100&phrase={mask_option}" \
           "&column={column}&page={page_number}"
WEBSITE_PREFIX = "https://libgen.is/"


def get_webpage_data(url):
    try:
        url_response = requests.get(url, timeout=5)
        url_response.raise_for_status()
        return url_response
    except Exception as e:
        print(f'could not fetch {url}. error: {e}')
        return None


def urls_from_library_lol(url):
    response = get_webpage_data(url)

    if response is None:
        return None

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f'could not parse {response.url} with error: {e}')
        return None

    try:
        all_urls = [item.find('a')['href'] for item in soup.find_all('h2')]

        all_urls.extend([item.find('a')['href'] for item in soup.find_all('li')])

        return all_urls
    except Exception as e:
        print(f'could not get fetch urls from {url} with error {e}')
        return None


def urls_from_libgen_li(url):
    response = get_webpage_data(url)

    if response is None:
        return None

    try:
        soup = BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f'could not parse {response.url} with error: {e}')
        return None

    try:
        return [soup.find('table').find_all('td')[1].find('a')['href'].strip()]
    except Exception as e:
        print(f'could not get fetch urls from {url} with error {e}')
        return None


def fetch_book_download_urls(urls):
    download_urls = []

    for url in urls:
        url_list = None
        domain = urlparse(url).netloc
        if domain == "library.lol":
            url_list = urls_from_library_lol(url)
        elif domain == 'libgen.li':
            url_list = urls_from_libgen_li(url)

        if url_list is not None:
            download_urls.extend(url_list)

    # remove duplicates
    download_urls = sorted(set(download_urls))

    for url in download_urls:
        if not validators.url(url):
            download_urls.remove(url)

    return download_urls


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

    all_urls = soup.find_all('table')[4].find_all('td')

    urls = [item.find('a')['href'] for item in all_urls[0:2]]

    return fetch_book_download_urls(urls)


def simpler_parser_thread(book, books):
    books.append(
        {
            "ID": book[0].text.strip(),
            "Author": book[1].text.strip(),
            "Title": book_title(book[2]),
            "Publisher": book[3].text.strip(),
            "Year": book[4].text.strip(),
            "Pages": book[5].text.strip(),
            "Language": book[6].text.strip(),
            "Size": book[7].text.strip(),
            "Extension": book[8].text.strip(),
            "Link": fetch_book_download_urls([item.find('a')['href'] for item in book[9:-1]]),
        }
    )


def detailed_parser_thread(book_table, books):
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
        "Image": WEBSITE_PREFIX + first_row[0].find('img')['src'],
        "Title": first_row[2].text.strip(),
        "Volume": first_row[3].text.split(':', 1)[-1].strip(),
        "Author": second_row[1].text.strip(),
        "Series": third_row[1].text.split(':', 1)[-1].strip(),
        "Publisher": forth_row[1].text.strip(),
        "year": fifth_row[1].text.strip(),
        "Edition": fifth_row[3].text.strip(),
        "Language": sixth_row[1].text.strip(),
        "Pages": sixth_row[3].text.strip(),
        "ISBN": [item.strip() for item in seventh_row[1].text.strip().split(',')],
        "Time Added": eighth_row[1].text.strip(),
        "Time Modified": eighth_row[3].text.strip(),
        "Size": ninth_row[1].text.strip(),
        "Extension": ninth_row[3].text.strip(),
        "Link": parse_detailed_url(WEBSITE_PREFIX + first_row[2].find('a')['href']),
    })


def parser_initializer(all_books, parser):
    threads = []
    books = []

    for book in all_books:
        thread = threading.Thread(target=parser, args=(book, books))
        thread.start()
        threads.append(thread)
        time.sleep(1)

    for thread in threads:
        thread.join()

    return books


def parse_simple(soup):
    table_rows = soup.find_all('table')[2].find_all('tr')

    book_rows = table_rows[1:]

    if len(book_rows) == 0:
        return None

    all_books = [row.find_all('td') for row in book_rows]

    return parser_initializer(all_books, simpler_parser_thread)


def parse_detailed(soup):
    all_books_tables = soup.find_all('table')[3:-1:2]

    if len(all_books_tables) == 0:
        return None

    return parser_initializer(all_books_tables, detailed_parser_thread)


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


def generate_url(cli_args):
    global args
    args = cli_args
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

        yield results

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
