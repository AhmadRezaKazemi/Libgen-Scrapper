import argparse
from scraper import generate_url
import json
from database_manager import DatabaseManager
import local_settings
from datetime import date


database_manager = DatabaseManager(
    database_name=local_settings.DATABASE['name'],
    host=local_settings.DATABASE['host'],
    port=local_settings.DATABASE['port'],
)


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
        default="def"
    )
    parser.add_argument("-m", "--mask_option", help="search for close words too", action="store_true")
    parser.add_argument("-o", "--output", help="give report from scrapped files", action="store_true")
    parser.add_argument(
        "-of",
        "--output_format",
        help="choose output format, default is json",
        default='json',
    )
    parser.add_argument("-db", "--download_book", help="download book instead of saving url", action="store_true")
    parser.add_argument("-to", "--timeout", help="webpage request timeout, default: 3", default=3, type=int)

    return parser.parse_args()


def remove_duplicate_books(books):
    unique_combinations = {}

    unique_books = []

    for book in books:
        name_genre_combination = (
            book.get('Title', ''),
            book.get('Author', ''),
            book.get('Publisher', ''),
            book.get('Edition', ''),
        )

        # If the combination is not encountered before, add it to the dictionary
        if name_genre_combination not in unique_combinations:
            unique_combinations[name_genre_combination] = True
            unique_books.append(book)

    return unique_books


def generate_output(books):
    # output = cli_args.keywords.replace(" ", "-") + '_' + str(date.today())
    print('we need an output')
    return


def data_already_scraped(old_query):
    print('this query is already scraped in the following dates:')
    for i in range(len(old_query)):
        print(f'{i+1}- {old_query[i]["scrapingDate"]}')
    print('enter desired index to get the query result')
    user_input = input('or enter -1 to scrap again: ')

    try:
        entered_index = int(user_input)

        if entered_index != -1 and 1 <= entered_index <= len(old_query):
            generate_output(
                database_manager.get_books(
                    old_query[entered_index - 1]['books'],
                    cli_args.detailed
                )
            )
        elif entered_index == -1:
            scrap_data()
        else:
            print('wrong input')

    except Exception as e:
        print('Error', e)
        return


def scrap_data():
    try:
        books = generate_url(cli_args)

        if len(books) == 0:
            print('an error has occurred!')
            return

        print('scraped data!')

        # for book in books:
        #     print(json.dumps(book, indent=4))

        if cli_args.detailed:
            ids = database_manager.insert_detailed_books(cli_args.keywords, remove_duplicate_books(books))
        else:
            ids = database_manager.insert_simple_books(cli_args.keywords, remove_duplicate_books(books))

        if ids is None:
            print('no new books added to database')
        else:
            generate_output(
                database_manager.get_books(
                    ids,
                    cli_args.detailed
                )
            )

    except Exception as error:
        print('Error:', error)


def check_scrap_data():
    try:
        old_query = database_manager.check_old_queries(cli_args.keywords, cli_args.detailed)

        if old_query is not None:
            data_already_scraped(list(old_query))
            return

        scrap_data()

    except Exception as error:
        print('Error:', error)


if __name__ == "__main__":
    cli_args = arg_parser()
    if cli_args.output:
        generate_output()
    else:
        check_scrap_data()
