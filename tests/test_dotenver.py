"""Tests for dotenver."""

import tempfile

from dotenver import __version__, dotenver

TEMPLATE_FILE = tempfile.NamedTemporaryFile()
TEMPLATE_FILE.write(
    b"""
export FALSE_VARIABLE= ## ## dotenver:boolean(chance_of_getting_true=0)
TRUE_VARIABLE= ## dotenver:boolean(name='true', chance_of_getting_true=100)
"""
)
TEMPLATE_FILE.flush()

NAMED_TEMPLATE_FILE = tempfile.NamedTemporaryFile()
NAMED_TEMPLATE_FILE.write(
    b"""
NAMED_VARIABLE= ## dotenver:boolean(name='true', chance_of_getting_true=0)
"""
)
NAMED_TEMPLATE_FILE.flush()

DOTENV_FILE = open(dotenver.get_dotenv_path(TEMPLATE_FILE.name), "r+")


def test_version():
    """Test that version has correctly set."""
    assert __version__ == "0.2.0.dev0"


def test_dotenv_path():
    """Test that the dotenv file path is generated correctly."""
    assert dotenver.get_dotenv_path("/path/to/file") == "/path/to/.env"


def test_parse():
    """Test that a .env file is created correctly."""
    DOTENV_FILE.truncate(0)
    dotenver.parse_files([TEMPLATE_FILE.name])
    expected = """
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
export FALSE_VARIABLE=True
TRUE_VARIABLE=False
"""
    )
    DOTENV_FILE.flush()

    dotenver.parse_files([TEMPLATE_FILE.name])

    expected = """
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
export FALSE_VARIABLE=True
TRUE_VARIABLE=False
"""
    )
    DOTENV_FILE.flush()

    dotenver.parse_files([TEMPLATE_FILE.name], override=True)

    expected = """
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
export FALSE_VARIABLE=False
TRUE_VARIABLE=True
"""
    DOTENV_FILE.seek(0)
    assert DOTENV_FILE.read() == expected


def test_named_values_are_equal():
    """Test that named variables have the same value."""
    DOTENV_FILE.truncate(0)

    dotenver.parse_files([TEMPLATE_FILE.name, NAMED_TEMPLATE_FILE.name], override=True)

    expected = """
NAMED_VARIABLE=True
"""
    DOTENV_FILE.seek(0)
    assert DOTENV_FILE.read() == expected
