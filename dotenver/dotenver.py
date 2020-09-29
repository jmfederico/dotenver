"""Generate .env files from .env.example templates."""

import io
import re
import sys
from pathlib import Path

import colorama
from faker import Faker
from jinja2 import Environment

VARIABLES = {}

VARIABLE_REGEX = r"""
    ^\s*
    (
        (?:export\s)?                   # Optional export command
        \s*
        ([^\s=#]+)                      # Variable name
    )
    (?:
        \s*=\s*?                        # Assignment
        (.*?)                           # Verbatim value, no parsing done
        {0}                             # Capture placeholder
    )?
    \s*$
"""

VALUES_REGEX = re.compile(VARIABLE_REGEX.format(""), re.VERBOSE)

TEMPLATE_REGEX = re.compile(
    VARIABLE_REGEX.format(
        r"""
        (?:
            \#\#\ +dotenver:            # Start of the dotenver comment
            (?:
                ([^\(\s#:]+)             # Faker generator to use
                (?::
                    ([^\(\s#]+)         # Value name
                )?
            )
            (?:\((
                .*                      # Arguments to pass to the generator
            )\))?
        )?                              # dotenver comment is optional
    """
    ),
    re.VERBOSE,
)
FAKE = Faker()


def get_value_key(generator, name):
    """
    Return a key for the given generator and name pair.

    If name None, no key is generated.
    """
    if name is not None:
        return f"{generator}+{name}"

    return None


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

    key = get_value_key(generator, name)

    value = str(VARIABLES.get(key, getattr(FAKE, generator)(**kwargs)))

    if key and key not in VARIABLES:
        VARIABLES[key] = value

    if quotes:
        value = value.replace(quotes, f"{escape_with}{quotes}")
        value = f"{quotes}{value}{quotes}"

    return value


def parse_stream(template_stream, current_dotenv):
    """Parse a dotenver template."""
    jinja2_template = io.StringIO()

    env = Environment(keep_trailing_newline=True)
    env.globals["dotenver"] = dotenver

    extra_variables = current_dotenv.copy()

    for line in template_stream:
        match = TEMPLATE_REGEX.match(line)
        if match:
            left_side, variable, value, generator, name, arguments = match.groups()

            if variable in current_dotenv:
                current_value = current_dotenv[variable][1]
                try:
                    del extra_variables[variable]
                except KeyError:
                    pass

                # Keep track of existing named values.
                key = get_value_key(generator, name)
                if key:
                    try:
                        VARIABLES[key]
                    except KeyError:
                        VARIABLES[key] = current_value

                line = (
                    f"{left_side}={current_value}"
                    if current_value is not None
                    else left_side
                )
            elif generator:
                dotenver_args = f"'{generator}'"
                if name:
                    dotenver_args = f"{dotenver_args}, '{name}'"
                if arguments:
                    dotenver_args = f"{dotenver_args}, {arguments}"
                line = f"{left_side}={{{{ dotenver({dotenver_args}) }}}}"
            elif value:
                line = f"{left_side}={value}"
            else:
                line = left_side

        jinja2_template.write(f"{line.strip()}\n")

    if extra_variables:
        jinja2_template.write(
            """
######################################
# Variables not in Dotenver template #
######################################

"""
        )
        for left_side, value in extra_variables.values():
            template_string = f"{left_side}={value}" if value is not None else left_side
            jinja2_template.write(f"{template_string}\n")

    template = env.from_string(jinja2_template.getvalue())

    return template


def get_dotenv_path(template_path):
    """Return the .env path for the given template path."""
    if template_path.suffix == ".example":
        return template_path.with_suffix("")

    return template_path.with_name(".env")


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
            colorama.Fore.RED,
            f"The following exception ocurred while reading '{dotenv_path}'",
            colorama.Fore.YELLOW,
            sep="",
            file=sys.stderr,
        )
        raise
    return values


def parse_files(templates_paths, override=False):
    """Parse multiple dotenver templates and generate or update a .env for each."""
    colorama.init()
    jinja2_templates = {}
    rendered_templates = {}

    # First pass will:
    # - capture all variables form templates and .env files
    # - capture existing values from .env files
    # - generate Jinja2 template
    for _template_path in templates_paths:
        template_path = Path(_template_path)
        current_env = (
            get_dotenv_dict(get_dotenv_path(template_path)) if not override else {}
        )
        try:
            with open(template_path, "r") as template_file:
                jinja2_templates[template_path] = parse_stream(
                    template_file, current_env
                )
        except Exception:
            print(
                colorama.Fore.RED,
                f"The following exception ocurred while processing template"
                f" '{template_path}'",
                colorama.Fore.YELLOW,
                sep="",
                file=sys.stderr,
            )
            raise

    # Second pass renders the templates.
    # Rendering on a second pass ensures all named values from .env files
    # were captured, and can be assigned to named dotenvers in templates.
    for template_path, jinja2_template in jinja2_templates.items():
        try:
            rendered_templates[template_path] = jinja2_template.render()
        except Exception:
            print(
                colorama.Fore.RED,
                f"The following exception ocurred while processing template"
                f" '{template_path}'",
                colorama.Fore.YELLOW,
                sep="",
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
                colorama.Fore.RED,
                f"The following exception ocurred while writing to '{dotenv_path}'",
                colorama.Fore.YELLOW,
                sep="",
                file=sys.stderr,
            )
            raise

        print(
            colorama.Fore.GREEN,
            f"'{template_path}' rendered to '{dotenv_path}'",
            sep="",
            file=sys.stderr,
        )
