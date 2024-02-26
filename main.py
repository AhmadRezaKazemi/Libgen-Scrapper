import argparse
from scraper import generate_url
import json
from database_manager import DatabaseManager
import local_settings
from datetime import date


# database_manager = DatabaseManager(
#     database_name=local_settings.DATABASE['name'],
#     host=local_settings.DATABASE['host'],
#     port=local_settings.DATABASE['port'],
# )


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
    parser.add_argument("-to", "--timeout", help="webpage request timeout, default: 3", default=3, type=int)

    return parser.parse_args()


if __name__ == "__main__":
    cli_args = arg_parser()
    try:
        # output = cli_args.keywords.replace(" ", "-") + '_' + str(date.today())

        for book in generate_url(cli_args):
            print(json.dumps(book, indent=4))

        # Todo: save data in database
        print('done!')
    except Exception as error:
        print('Error:', error)
