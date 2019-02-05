"""Generate .env files from .env.example templates."""

import io
import re
import sys
from os.path import dirname

import colorama
from faker import Faker
from jinja2 import Environment

VARIABLES = {}

VARIABLE_REGEX = r"""
    ^\s*
    (
        (?:export\s)?                   # Optional export command
        \s*
        ([^\s=]+)                       # Variable name
    )
    \s*=\s*                             # Equal sign
"""

VALUES_REGEX = re.compile(
    r"""
        {0}
        (.*)                            # Verbatim value, no parsing done
        $
    """.format(
        VARIABLE_REGEX
    ),
    re.VERBOSE,
)

TEMPLATE_REGEX = re.compile(
    r"""
        {0}
        .*                              # Anything until a dotenver comment
        (?:
            \#\#\ +dotenver:            # Start of the dotenver comment
            ([^\(\s]+)                  # Faker generator to use
            (?:\((
                .*                      # Arguments to pass to the generator
            )\))?
        )
        \s*$
    """.format(
        VARIABLE_REGEX
    ),
    re.VERBOSE,
)
FAKE = Faker()


def dotenver(generator, name=None, quotes=None, escape_with="\\", **kwargs):
    r"""
    Generate fake data from the given `generator`.

    If a `name` is given, the value from the given `generator` and `name`
    will be saved and used for subsequent calls.
    In those cases only the quotes argument is honored for each call.

    The returned value will be optionally surrounded with single or
    double quotes as specified by `quotes`, and escaped with `escape_with`,
    which is a backslash `\` by default.
    """
    if quotes not in [None, "'", '"']:
        raise ValueError("quotes must be a single `'` or double `\"` quote")

    key = None
    if name is not None:
        key = f"{generator}+{name}"

    data = str(VARIABLES.get(key, getattr(FAKE, generator)(**kwargs)))

    if key and key not in VARIABLES:
        VARIABLES[key] = data

    if quotes:
        data = data.replace(quotes, f"{escape_with}{quotes}")
        data = f"{quotes}{data}{quotes}"

    return data


def parse_stream(template_stream, current_dotenv):
    """Parse a dotenver template."""
    jinja2_template = io.StringIO()

    env = Environment(keep_trailing_newline=True)
    env.globals["dotenver"] = dotenver

    missing_variables = current_dotenv.copy()

    for line in template_stream:
        match = TEMPLATE_REGEX.match(line)
        if match:
            assignment, variable, faker, arguments = match.groups()

            if variable in current_dotenv:
                del missing_variables[variable]
                line = f"{assignment}={current_dotenv[variable][1]}"
            else:
                dotenver_args = f"'{faker}'"
                if arguments:
                    dotenver_args = f"{dotenver_args}, {arguments}"
                line = f"{assignment}={{{{ dotenver({dotenver_args}) }}}}"

        jinja2_template.write(f"{line.strip()}\n")

    if missing_variables:
        jinja2_template.write(
            """
######################################
# Variables not in Dotenver template #
######################################

"""
        )
        for data in missing_variables.values():
            jinja2_template.write(f"{data[0]}={data[1]}\n")

    template = env.from_string(jinja2_template.getvalue())

    return template.render()


def get_dotenv_path(template_path):
    """Return the .env path for the given template path."""
    dotenv_dir = dirname(template_path)
    if dotenv_dir:
        dotenv_dir += "/"

    return f"{dotenv_dir}.env"


def get_dotenv_dict(dotenv_path):
    """
    Read a .env file and return a dictionary of the parsed data.

    Each item has the VARIABLE as the key, and the value is a tuple:
    (assignment, value)

    If the file does not exist, return an empty dict.
    """
    values = dict()
    try:
        with open(dotenv_path, "r") as dotenv_file:
            for line in dotenv_file:
                match = VALUES_REGEX.match(line)
                if match:
                    assignment, variable, value = match.groups()
                    values[variable] = (assignment, value)
    except FileNotFoundError:
        pass
    except Exception:
        print(
            f"{colorama.Fore.RED}\n",
            f"The following exception ocurred while reading '{dotenv_path}'",
            f"\n{colorama.Fore.YELLOW}",
            file=sys.stderr,
        )
        raise
    return values


def parse_files(templates_paths, override=False):
    """Parse multiple dotenver templates and generate or update a .env for each."""
    colorama.init()
    rendered_templates = {}

    for template_path in templates_paths:
        current_env = (
            get_dotenv_dict(get_dotenv_path(template_path)) if not override else {}
        )
        try:
            with open(template_path, "r") as template_file:
                rendered_templates[template_path] = parse_stream(
                    template_file, current_env
                )
        except Exception:
            print(
                f"{colorama.Fore.RED}\n",
                f"The following exception ocurred while processing template '{template_path}'",
                f"\n{colorama.Fore.YELLOW}",
                file=sys.stderr,
            )
            raise

    for template_path, rendered_template in rendered_templates.items():
        dotenv_path = get_dotenv_path(template_path)
        try:
            with open(dotenv_path, "w") as dotenv_file:
                dotenv_file.write(rendered_template)
        except Exception:
            print(
                f"{colorama.Fore.RED}\n",
                f"The following exception ocurred while writing to '{dotenv_path}'",
                f"\n{colorama.Fore.YELLOW}",
                file=sys.stderr,
            )
            raise

        print(
            f"{colorama.Fore.GREEN}",
            f"'{template_path}' rendered to '{dotenv_path}'",
            f"{colorama.Fore.RESET}",
            file=sys.stderr,
        )
