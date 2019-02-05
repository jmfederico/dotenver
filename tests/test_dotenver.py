"""Tests for dotenver."""

import tempfile

from dotenver import __version__, dotenver

DIRECTORY = tempfile.TemporaryDirectory()

TEMPLATE_FILE = tempfile.NamedTemporaryFile(dir=DIRECTORY.name, delete=False)
TEMPLATE_FILE.write(
    b"""
STATIC_VARIABLE=static
export FALSE_VARIABLE= ## ## dotenver:boolean(chance_of_getting_true=0)
TRUE_VARIABLE= ## dotenver:boolean(name='true', chance_of_getting_true=100)
"""
)
TEMPLATE_FILE.flush()

DOTENV_FILE = open(dotenver.get_dotenv_path(TEMPLATE_FILE.name), "w+")


def test_version():
    """Test that version has correctly set."""
    assert __version__ == "0.3.0"


def test_dotenv_path():
    """Test that the dotenv file path is generated correctly."""
    assert dotenver.get_dotenv_path("/path/to/file") == "/path/to/.env"


def test_parse():
    """Test that a .env file is created correctly."""
    DOTENV_FILE.truncate(0)
    dotenver.parse_files([TEMPLATE_FILE.name])
    expected = """
STATIC_VARIABLE=static
export FALSE_VARIABLE=False
TRUE_VARIABLE=True
"""
    DOTENV_FILE.seek(0)
    assert DOTENV_FILE.read() == expected


def test_unknowns_are_kept():
    """Test that existing unknown variables are kept."""
    DOTENV_FILE.truncate(0)
    DOTENV_FILE.write(
        """
# A comment
EXISTING_VARIABLE=existing
"""
    )
    DOTENV_FILE.flush()

    dotenver.parse_files([TEMPLATE_FILE.name], override=False)

    expected = """
STATIC_VARIABLE=static
export FALSE_VARIABLE=False
TRUE_VARIABLE=True

######################################
# Variables not in Dotenver template #
######################################

EXISTING_VARIABLE=existing
"""
    DOTENV_FILE.seek(0)
    assert DOTENV_FILE.read() == expected


def test_existing_are_respected():
    """Test that existing known values are respected."""
    DOTENV_FILE.truncate(0)
    DOTENV_FILE.write(
        """
STATIC_VARIABLE=dynamic
export FALSE_VARIABLE=True
TRUE_VARIABLE=False
"""
    )
    DOTENV_FILE.flush()

    dotenver.parse_files([TEMPLATE_FILE.name])

    expected = """
STATIC_VARIABLE=dynamic
export FALSE_VARIABLE=True
TRUE_VARIABLE=False
"""
    DOTENV_FILE.seek(0)
    assert DOTENV_FILE.read() == expected


def test_existing_are_overridden():
    """Test that existing known values are overridden."""
    DOTENV_FILE.truncate(0)
    DOTENV_FILE.write(
        """
# A comment
STATIC_VARIABLE=dynamic
export FALSE_VARIABLE=True
TRUE_VARIABLE=False
"""
    )
    DOTENV_FILE.flush()

    dotenver.parse_files([TEMPLATE_FILE.name], override=True)

    expected = """
STATIC_VARIABLE=static
export FALSE_VARIABLE=False
TRUE_VARIABLE=True
"""
    DOTENV_FILE.seek(0)
    assert DOTENV_FILE.read() == expected


def test_unknowns_are_discarded():
    """Test that existing unknown values are discarded."""
    DOTENV_FILE.truncate(0)
    DOTENV_FILE.write(
        """
# A comment
EXISTING_VARIABLE=existing
"""
    )
    DOTENV_FILE.flush()

    dotenver.parse_files([TEMPLATE_FILE.name], override=True)

    expected = """
STATIC_VARIABLE=static
export FALSE_VARIABLE=False
TRUE_VARIABLE=True
"""
    DOTENV_FILE.seek(0)
    assert DOTENV_FILE.read() == expected


def test_named_values_are_equal():
    """Test that named variables have the same value."""
    DOTENV_FILE.truncate(0)

    tamplate_with_name = tempfile.NamedTemporaryFile(dir=DIRECTORY.name)
    tamplate_with_name.write(
        b"""
NAMED_VARIABLE= ## dotenver:boolean(name='true', chance_of_getting_true=0)
"""
    )
    tamplate_with_name.flush()

    dotenver.parse_files([TEMPLATE_FILE.name, tamplate_with_name.name], override=True)

    expected = """
NAMED_VARIABLE=True
"""
    DOTENV_FILE.seek(0)
    assert DOTENV_FILE.read() == expected


def test_dotenver_triumphs_value():
    """Test that dotenver is prefferred over value in template."""
    DOTENV_FILE.truncate(0)

    tamplate_with_name = tempfile.NamedTemporaryFile(dir=DIRECTORY.name)
    tamplate_with_name.write(
        b"""
VARIABLE=value ## dotenver:boolean(chance_of_getting_true=100)
"""
    )
    tamplate_with_name.flush()

    dotenver.parse_files([tamplate_with_name.name])

    expected = """
VARIABLE=True
"""
    DOTENV_FILE.seek(0)
    assert DOTENV_FILE.read() == expected
