import pytest

from pathlib import Path
from pintdantic import QuantityField, QuantityModel
from pydantic import ValidationError
from pint import Quantity

# -----------------------------------
# Child models for testing
# -----------------------------------


class ChildModel(QuantityModel):
    length: QuantityField
    width: QuantityField
    id: int  # Non-quantity field


class ChildModelWithDefaults(QuantityModel):
    length: QuantityField = (10, "m")
    id: int


# -------------------------------
# Parsing / validation tests
# -------------------------------


def test_valid_quantity_parsing():
    data = {"length": Quantity(1.0, "m"), "width": Quantity(2.0, "m"), "id": 42}
    model = ChildModel(**data)
    assert isinstance(model.length, Quantity)
    assert model.length.magnitude == 1.0
    assert model.width.magnitude == 2.0
    assert model.id == 42


def test_invalid_magnitude_type_raises():
    with pytest.raises(ValidationError):
        ChildModel(length="not_a_quantity", width=Quantity(2.0, "m"), id=1)


def test_invalid_units_type_raises():
    with pytest.raises(TypeError):
        ChildModel(length=Quantity(1.0, 123), width=Quantity(2.0, "m"), id=1)


# Dict parsing
def test_parse_from_valid_dict():
    data = {
        "length": {"magnitude": 3.0, "units": "m"},
        "width": {"magnitude": 4, "units": "m"},
        "id": 99,
    }
    model = ChildModel(**data)
    assert model.length.magnitude == 3.0
    assert str(model.length.units) == "meter"


def test_parse_from_invalid_dict_keys():
    bad_data = {
        "length": {"mag": 3.0, "unit": "m"},  # wrong keys
        "width": {"magnitude": 2.0, "units": "m"},
        "id": 1,
    }
    with pytest.raises(ValidationError):
        ChildModel(**bad_data)


# Tuple parsing
def test_parse_from_valid_tuple():
    data = {"length": (5.0, "m"), "width": (6, "m"), "id": 10}
    model = ChildModel(**data)
    assert model.length.magnitude == 5.0
    assert str(model.width.units) == "meter"


def test_parse_from_invalid_tuple_length():
    bad_data = {"length": (5.0, "m", "extra"), "width": (6.0, "m"), "id": 2}
    with pytest.raises(ValidationError):
        ChildModel(**bad_data)


def test_parse_from_invalid_tuple_types():
    bad_data = {"length": ("not_a_number", "m"), "width": (2.0, "m"), "id": 3}
    with pytest.raises(ValidationError):
        ChildModel(**bad_data)


# List parsing (condensed format)
def test_parse_from_valid_list():
    """Test parsing from condensed list format [magnitude, units]"""
    data = {"length": [5.0, "m"], "width": [6, "m"], "id": 10}
    model = ChildModel(**data)
    assert model.length.magnitude == 5.0
    assert str(model.width.units) == "meter"


def test_parse_from_invalid_list_length():
    """Test that list with wrong length raises error"""
    bad_data = {"length": [5.0, "m", "extra"], "width": [6.0, "m"], "id": 2}
    with pytest.raises(ValidationError):
        ChildModel(**bad_data)


def test_parse_from_invalid_list_types():
    """Test that list with wrong types raises error"""
    bad_data = {"length": ["not_a_number", "m"], "width": [2.0, "m"], "id": 3}
    with pytest.raises(ValidationError):
        ChildModel(**bad_data)


# Bare float/int parsing
def test_parse_from_float_with_default_units():
    model = ChildModelWithDefaults(length=10.0, id=1)
    assert model.length.magnitude == 10.0
    assert str(model.length.units) == "meter"


def test_parse_from_float_without_default_units_raises():
    with pytest.raises(ValidationError):
        ChildModel(length=10.0, width=Quantity(2.0, "m"), id=1)


# -------------------------------
# Serialization tests
# -------------------------------


def test_serialize_model_returns_condensed_by_default():
    """Test that serialization uses condensed list format by default"""
    data = {"length": Quantity(1.0, "m"), "width": Quantity(2.0, "m"), "id": 42}
    model = ChildModel(**data)
    serialized = model.model_dump()
    # Default should be condensed format [magnitude, units]
    assert serialized["length"] == [1.0, "meter"]
    assert serialized["width"] == [2.0, "meter"]
    assert serialized["id"] == 42


def test_serialize_model_verbose_format():
    """Test that verbose=True uses dict format"""
    data = {"length": Quantity(1.0, "m"), "width": Quantity(2.0, "m"), "id": 42}
    model = ChildModel(**data)
    serialized = model.model_dump(context={"verbose": True})
    # Verbose format should be dict
    assert serialized["length"]["magnitude"] == 1.0
    assert serialized["length"]["units"] == "meter"
    assert serialized["width"]["magnitude"] == 2.0
    assert serialized["width"]["units"] == "meter"
    assert serialized["id"] == 42


def test_to_dict_condensed_by_default():
    """Test that to_dict() uses condensed format by default"""
    data = {"length": Quantity(5.0, "m"), "width": Quantity(6.0, "m"), "id": 7}
    model = ChildModel(**data)
    d = model.to_dict()
    assert d["length"] == [5.0, "meter"]
    assert d["width"] == [6.0, "meter"]
    assert d["id"] == 7


def test_to_dict_verbose():
    """Test that to_dict(verbose=True) uses dict format"""
    data = {"length": Quantity(5.0, "m"), "width": Quantity(6.0, "m"), "id": 7}
    model = ChildModel(**data)
    d = model.to_dict(verbose=True)
    assert d["length"]["magnitude"] == 5.0
    assert d["length"]["units"] == "meter"
    assert d["width"]["magnitude"] == 6.0
    assert d["width"]["units"] == "meter"
    assert d["id"] == 7


# -------------------------------
# Save / load tests
# -------------------------------


def test_save_and_load_condensed(tmp_path: Path):
    """Test save/load with condensed format (default)"""
    data = {"length": Quantity(1.1, "m"), "width": Quantity(2.2, "m"), "id": 123}
    model = ChildModel(**data)
    path = tmp_path / "test_condensed.json"
    saved_path = model.save(path)
    assert saved_path.exists()

    # Verify file contains condensed format
    import json

    with open(saved_path) as f:
        content = json.load(f)
    assert content["length"] == [1.1, "meter"]
    assert content["width"] == [2.2, "meter"]

    # Load and verify
    loaded_model = ChildModel.load(saved_path)
    assert loaded_model.length.magnitude == 1.1
    assert loaded_model.length.units == "meter"
    assert loaded_model.width.magnitude == 2.2
    assert loaded_model.width.units == "meter"
    assert loaded_model.id == 123


def test_save_and_load_verbose(tmp_path: Path):
    """Test save/load with verbose format"""
    data = {"length": Quantity(1.1, "m"), "width": Quantity(2.2, "m"), "id": 123}
    model = ChildModel(**data)
    path = tmp_path / "test_verbose.json"
    saved_path = model.save(path, verbose=True)
    assert saved_path.exists()

    # Verify file contains verbose format
    import json

    with open(saved_path) as f:
        content = json.load(f)
    assert content["length"]["magnitude"] == 1.1
    assert content["length"]["units"] == "meter"
    assert content["width"]["magnitude"] == 2.2
    assert content["width"]["units"] == "meter"

    # Load and verify
    loaded_model = ChildModel.load(saved_path)
    assert loaded_model.length.magnitude == 1.1
    assert loaded_model.length.units == "meter"
    assert loaded_model.width.magnitude == 2.2
    assert loaded_model.width.units == "meter"
    assert loaded_model.id == 123


def test_load_legacy_verbose_format(tmp_path: Path):
    """Test backwards compatibility: loading old verbose format files"""
    import json

    # Create a file with old verbose format
    path = tmp_path / "legacy.json"
    legacy_data = {
        "length": {"magnitude": 5.5, "units": "meter"},
        "width": {"magnitude": 3.3, "units": "meter"},
        "id": 999,
    }
    with open(path, "w") as f:
        json.dump(legacy_data, f)

    # Should load without issues
    loaded_model = ChildModel.load(path)
    assert loaded_model.length.magnitude == 5.5
    assert loaded_model.length.units == "meter"
    assert loaded_model.width.magnitude == 3.3
    assert loaded_model.width.units == "meter"
    assert loaded_model.id == 999


def test_round_trip_serialization_condensed(tmp_path: Path):
    """Test round-trip with condensed format"""
    original = ChildModel(length=Quantity(7, "m"), width=Quantity(8, "m"), id=55)
    path = tmp_path / "roundtrip_condensed.json"
    original.save(path)  # Default: condensed
    reloaded = ChildModel.load(path)
    assert reloaded.length == original.length
    assert reloaded.width == original.width
    assert reloaded.id == original.id


def test_round_trip_serialization_verbose(tmp_path: Path):
    """Test round-trip with verbose format"""
    original = ChildModel(length=Quantity(7, "m"), width=Quantity(8, "m"), id=55)
    path = tmp_path / "roundtrip_verbose.json"
    original.save(path, verbose=True)
    reloaded = ChildModel.load(path)
    assert reloaded.length == original.length
    assert reloaded.width == original.width
    assert reloaded.id == original.id
