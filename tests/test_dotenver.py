"""Tests for dotenver."""

import tempfile

from dotenver import __version__, dotenver

DIRECTORY = tempfile.TemporaryDirectory()

TEMPLATE_FILE = tempfile.NamedTemporaryFile(mode="w+", dir=DIRECTORY.name, delete=False)
TEMPLATE_FILE.write(
    """
STATIC_VARIABLE=static
export FALSE_VARIABLE= ## ## dotenver:boolean(chance_of_getting_true=0)
TRUE_VARIABLE= ## dotenver:boolean(name='true', chance_of_getting_true=100)
"""
)
TEMPLATE_FILE.flush()

DOTENV_FILE = open(dotenver.get_dotenv_path(TEMPLATE_FILE.name), "w+")


def set_dotenv(content):
    """Replace content of .env with the value passed."""
    DOTENV_FILE.truncate(0)
    DOTENV_FILE.seek(0)
    DOTENV_FILE.write(content)
    DOTENV_FILE.flush()
    DOTENV_FILE.seek(0)


def get_tempfile(content):
    """Create and return a new temporary file with the given content."""
    temp_file = tempfile.NamedTemporaryFile(mode="w+", dir=DIRECTORY.name)
    temp_file.write(content)
    temp_file.flush()
    temp_file.seek(0)
    return temp_file


def test_version():
    """Test that version has correctly set."""
    assert __version__ == "0.5.0.dev0"


def test_dotenv_path():
    """Test that the dotenv file path is generated correctly."""
    assert dotenver.get_dotenv_path("/path/to/file") == "/path/to/.env"


def test_parse():
    """Test that a .env file is created correctly."""
    set_dotenv("")

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
    set_dotenv(
        """
EXISTING_VARIABLE=existing
"""
    )

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
    assert DOTENV_FILE.read() == expected


def test_existing_are_respected():
    """Test that existing known values are respected."""
    set_dotenv(
        """
STATIC_VARIABLE=dynamic
export FALSE_VARIABLE=True
TRUE_VARIABLE=False
"""
    )

    dotenver.parse_files([TEMPLATE_FILE.name])

    expected = """
STATIC_VARIABLE=dynamic
export FALSE_VARIABLE=True
TRUE_VARIABLE=False
"""
    assert DOTENV_FILE.read() == expected


def test_existing_are_overridden():
    """Test that existing known values are overridden."""
    set_dotenv(
        """
STATIC_VARIABLE=dynamic
export FALSE_VARIABLE=True
TRUE_VARIABLE=False
"""
    )

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
    set_dotenv(
        """
EXISTING_VARIABLE=existing
"""
    )

    dotenver.parse_files([TEMPLATE_FILE.name], override=True)

    expected = """
STATIC_VARIABLE=static
export FALSE_VARIABLE=False
TRUE_VARIABLE=True
"""
    assert DOTENV_FILE.read() == expected


def test_named_values_are_equal():
    """Test that named variables have the same value."""
    set_dotenv("")

    tamplate_with_name = get_tempfile(
        "NAMED_VARIABLE= ## dotenver:boolean(name='true', chance_of_getting_true=0)"
    )

    dotenver.parse_files([TEMPLATE_FILE.name, tamplate_with_name.name], override=True)

    expected = "NAMED_VARIABLE=True\n"
    assert DOTENV_FILE.read() == expected


def test_dotenver_triumphs_value():
    """Test that dotenver is prefferred over value in template."""
    set_dotenv("")

    tamplate_with_name = get_tempfile(
        "VARIABLE=False ## dotenver:boolean(chance_of_getting_true=100)"
    )

    dotenver.parse_files([tamplate_with_name.name])

    expected = "VARIABLE=True\n"
    assert DOTENV_FILE.read() == expected


def test_can_handle_duplicate_existing_variable():
    """Test that dotenver does not break on duplicate existing variables."""
    set_dotenv(
        """
DUPLICATE_VARIABLE=duplicate
"""
    )

    tamplate_with_duplicate = get_tempfile(
        """
DUPLICATE_VARIABLE= ## dotenver:boolean(chance_of_getting_true=100)
DUPLICATE_VARIABLE= ## dotenver:boolean(chance_of_getting_true=0)
"""
    )

    dotenver.parse_files([tamplate_with_duplicate.name])

    expected = """
DUPLICATE_VARIABLE=duplicate
DUPLICATE_VARIABLE=duplicate
"""
    assert DOTENV_FILE.read() == expected


def test_existing_unassigned_variables_are_respected():
    """Test that existing values for unassigned variables are respected."""
    set_dotenv("UNASSIGNED_EXTSTING=assigned")

    tamplate_with_unassigned = get_tempfile("UNASSIGNED_EXTSTING")

    dotenver.parse_files([tamplate_with_unassigned.name])

    expected = "UNASSIGNED_EXTSTING=assigned\n"
    assert DOTENV_FILE.read() == expected


def test_unassigned_variables():
    """Test that unassigned variables are left untouched."""
    set_dotenv("")

    tamplate_with_unassigned = get_tempfile("UNASSIGNED")

    dotenver.parse_files([tamplate_with_unassigned.name])

    expected = "UNASSIGNED\n"
    assert DOTENV_FILE.read() == expected
