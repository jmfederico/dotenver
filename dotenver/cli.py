"""Define CLI interface for Dotenver."""

import argparse
import glob
import sys
from pathlib import Path

import colorama

from . import __version__, dotenver


def check_file_path(file_path):
    """Validate that the given file_path exists and can read."""
    file_path = Path(file_path)
    dotenv_path = dotenver.get_dotenv_path(file_path)

    if dotenv_path.name == file_path.name:
        print(colorama.Fore.RED, file=sys.stderr, end="")
        raise argparse.ArgumentTypeError(
            "'%s'. Template file can not be named '%s'" % (file_path, file_path.name)
        )

    try:
        open(file_path, "r")
    except FileNotFoundError:
        print(colorama.Fore.RED, file=sys.stderr, end="")
        raise argparse.ArgumentTypeError("'%s' could not be found" % file_path)
    except PermissionError:
        print(colorama.Fore.RED, file=sys.stderr, end="")
        raise argparse.ArgumentTypeError("'%s' is not readable" % file_path)

    try:
        open(dotenv_path, "a")
    except PermissionError:
        print(colorama.Fore.RED, file=sys.stderr, end="")
        raise argparse.ArgumentTypeError("'%s' is not writable" % dotenv_path)

    try:
        open(dotenv_path, "r")
    except FileNotFoundError:
        pass
    except PermissionError:
        print(colorama.Fore.RED, file=sys.stderr, end="")
        raise argparse.ArgumentTypeError("'%s' is not readable" % dotenv_path)

    return file_path


def cli():
    """Parse DotEnver templates and save to .env files."""
    colorama.init()

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
        help="process all template files recursively",
    )
    parser.add_argument(
        "--pattern",
        help=(
            "glob pattern used to search for templates. Only used with --recursive."
            " Default: '**/.env.example'"
        ),
        default="**/.env.example",
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
        files = glob.glob(args.pattern, recursive=True)

        if not files:

            print(
                colorama.Fore.RED,
                "No template files found",
                file=sys.stderr,
                sep="",
            )
            return

        print(
            colorama.Fore.BLUE,
            "The following files will be parsed:",
            file=sys.stderr,
            sep="",
        )

        for file_ in files:
            print(colorama.Fore.BLUE, f" - {file_}", file=sys.stderr, sep="")

        print("", file=sys.stderr)
        confirmation = input(f'{colorama.Fore.YELLOW}Type "y" to confirm: ')
        print("", file=sys.stderr)

        if confirmation != "y":
            print(
                colorama.Fore.RED,
                "Will not proceed without your confirmation.",
                file=sys.stderr,
                sep="",
            )
            return

    dotenver.parse_files(files, override=args.override)
    return


if __name__ == "__main__":
    cli()
