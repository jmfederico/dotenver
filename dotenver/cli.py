"""Define CLI interface for Dotenver."""

import argparse
import glob
import sys
from os.path import basename

import colorama

from . import __version__, dotenver


def check_file_path(file_path):
    """Validate that the given file_path exists and can read."""
    colorama.init()

    dotenv_path = dotenver.get_dotenv_path(file_path)

    if basename(dotenv_path) == basename(file_path):
        print(colorama.Fore.RED, file=sys.stderr)
        raise argparse.ArgumentTypeError(
            "'%s'. Template file can not be named .env" % file_path
        )

    try:
        open(file_path, "r")
    except FileNotFoundError:
        print(colorama.Fore.RED, file=sys.stderr)
        raise argparse.ArgumentTypeError("'%s' could not be found" % file_path)
    except PermissionError:
        print(colorama.Fore.RED, file=sys.stderr)
        raise argparse.ArgumentTypeError("'%s' is not readable" % file_path)

    try:
        open(dotenv_path, "a")
    except PermissionError:
        print(colorama.Fore.RED, file=sys.stderr)
        raise argparse.ArgumentTypeError("'%s' is not writable" % dotenv_path)

    try:
        open(dotenv_path, "r")
    except FileNotFoundError:
        pass
    except PermissionError:
        print(colorama.Fore.RED, file=sys.stderr)
        raise argparse.ArgumentTypeError("'%s' is not readable" % dotenv_path)

    return file_path


def cli():
    """Parse DotEnver templates and save to .env files."""
    parser = argparse.ArgumentParser(
        description="""Render DotEnver templates as .env files.
By default values in existing in .env files are respected, and missing variables are added.
"""
    )

    parser.add_argument(
        "-o", "--override", action="store_true", help="override current .env files."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="process all .env.example files recursively",
    )
    group.add_argument(
        "--version", action="store_true", help="print current DotEnver version"
    )
    group.add_argument(
        "files",
        metavar="file",
        type=check_file_path,
        nargs="*",
        default=False,
        help="path to file to process",
    )

    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    files = args.files
    if args.recursive:
        files = glob.glob("**/.env.example", recursive=True)

        if not files:
            print(colorama.Fore.RED, file=sys.stderr)
            print('No ".env.example" files found', file=sys.stderr)

    dotenver.parse_files(files, override=args.override)
    return


if __name__ == "__main__":
    cli()
