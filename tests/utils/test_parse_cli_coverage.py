"""
Additional tests for parse_cli_input to improve coverage.
"""

import pytest
from pintdantic.utils import parse_cli_input


def test_parse_none_input():
    """Test that None input returns None"""
    result = parse_cli_input(None)
    assert result is None


def test_parse_tuple_invalid_length():
    """Test that tuple with wrong length raises ValueError"""
    with pytest.raises(ValueError) as exc_info:
        parse_cli_input((5.0,))  # Only one element

    assert "Invalid quantity tuple" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        parse_cli_input((5.0, "m", "extra"))  # Three elements

    assert "Invalid quantity tuple" in str(exc_info.value)


def test_parse_tuple_invalid_types():
    """Test that tuple with invalid types raises ValueError"""
    # Non-numeric first element
    with pytest.raises(ValueError) as exc_info:
        parse_cli_input(("not a number", "m"))

    assert "Invalid types in tuple" in str(exc_info.value)

    # Non-string second element
    with pytest.raises(ValueError) as exc_info:
        parse_cli_input((5.0, 123))

    assert "Invalid types in tuple" in str(exc_info.value)

    # Both wrong types
    with pytest.raises(ValueError) as exc_info:
        parse_cli_input(("string", 456))

    assert "Invalid types in tuple" in str(exc_info.value)


def test_parse_tuple_valid_passthrough():
    """Test that valid tuples pass through correctly"""
    result = parse_cli_input((5, "meter"))
    assert result == (5, "meter")

    result = parse_cli_input((3.14, "cm"))
    assert result == (3.14, "cm")
