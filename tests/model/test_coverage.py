"""
Tests to improve code coverage for edge cases and error handling.
"""

import pytest
from pathlib import Path
from pint import Quantity
from pydantic import ValidationError
from pintdantic import QuantityModel, QuantityField


class ModelWithDefaults(QuantityModel):
    """Model with tuple defaults for testing default handling"""

    length: QuantityField = (10.0, "m")
    width: QuantityField = (5.0, "m")
    name: str = "default"


class ModelWithDict(QuantityModel):
    """Model that can contain dict fields"""

    metadata: dict
    length: QuantityField


def test_dict_to_quantity_method():
    """Test the _dict_to_quantity static method"""
    quantity_dict = {"magnitude": 42.0, "units": "meter"}
    quantity = QuantityModel._dict_to_quantity(quantity_dict)
    assert isinstance(quantity, Quantity)
    assert quantity.magnitude == 42.0
    assert str(quantity.units) == "meter"


def test_serialize_dict_values():
    """Test serialization of dict values containing Quantities (condensed by default)"""
    model = ModelWithDict(
        metadata={"key1": "value1", "key2": 123},
        length=Quantity(10.0, "m"),
    )

    serialized = model.to_dict()
    assert serialized["metadata"]["key1"] == "value1"
    assert serialized["metadata"]["key2"] == 123
    assert serialized["length"] == [10.0, "meter"]


def test_serialize_nested_dict_with_quantities():
    """Test serialization of dicts containing Quantity objects (condensed by default)"""

    class ModelWithQuantityDict(QuantityModel):
        data: dict

    # Create a model with a dict containing Quantity objects
    model = ModelWithQuantityDict(
        data={"measurement": Quantity(25.0, "cm"), "count": 5}
    )

    serialized = model.to_dict()
    assert serialized["data"]["measurement"] == [25.0, "centimeter"]
    assert serialized["data"]["count"] == 5

    # Test verbose format
    serialized_verbose = model.to_dict(verbose=True)
    assert serialized_verbose["data"]["measurement"]["magnitude"] == 25.0
    assert serialized_verbose["data"]["measurement"]["units"] == "centimeter"
    assert serialized_verbose["data"]["count"] == 5


def test_default_tuple_handling_when_field_not_provided():
    """Test that tuple defaults are converted to Quantity when field not provided"""
    # Create model without providing the quantity fields
    model = ModelWithDefaults(name="test")

    assert isinstance(model.length, Quantity)
    assert model.length.magnitude == 10.0
    assert str(model.length.units) == "meter"

    assert isinstance(model.width, Quantity)
    assert model.width.magnitude == 5.0
    assert str(model.width.units) == "meter"


def test_default_non_tuple_handling():
    """Test that non-tuple defaults are handled correctly"""

    class ModelWithNonTupleDefaults(QuantityModel):
        length: QuantityField = Quantity(15.0, "m")
        name: str = "default"

    model = ModelWithNonTupleDefaults()
    assert isinstance(model.length, Quantity)
    assert model.length.magnitude == 15.0
    assert model.name == "default"


def test_invalid_tuple_units_type():
    """Test error when tuple has non-string units"""

    class TestModel(QuantityModel):
        length: QuantityField

    with pytest.raises(ValidationError) as exc_info:
        TestModel(length=(10.0, 123))  # Units should be string, not int

    assert "Units must be str" in str(exc_info.value)


def test_invalid_dict_magnitude_type():
    """Test error when dict has non-numeric magnitude"""

    class TestModel(QuantityModel):
        length: QuantityField

    with pytest.raises(ValidationError) as exc_info:
        TestModel(length={"magnitude": "not a number", "units": "m"})

    assert "magnitude must be float or int" in str(exc_info.value)


def test_invalid_dict_units_type():
    """Test error when dict has non-string units"""

    class TestModel(QuantityModel):
        length: QuantityField

    with pytest.raises(ValidationError) as exc_info:
        TestModel(length={"magnitude": 10.0, "units": 123})

    assert "units must be str" in str(exc_info.value)


def test_load_non_dict_json_raises_error(tmp_path: Path):
    """Test that loading a JSON array (non-dict) raises ValueError"""

    class TestModel(QuantityModel):
        length: QuantityField

    # Write a JSON array instead of object
    test_file = tmp_path / "invalid.json"
    test_file.write_text('[{"magnitude": 10.0, "units": "m"}]')

    with pytest.raises(ValueError) as exc_info:
        TestModel.load(test_file)

    assert "Unexpected JSON structure" in str(exc_info.value)
    assert "expected dict" in str(exc_info.value)


def test_serialize_empty_dict():
    """Test serialization of empty dict"""

    class TestModel(QuantityModel):
        data: dict
        length: QuantityField

    model = TestModel(data={}, length=Quantity(5.0, "m"))
    serialized = model.to_dict()
    assert serialized["data"] == {}


def test_serialize_nested_dict_with_nested_model():
    """Test serialization of dict containing nested models (condensed by default)"""

    class Inner(QuantityModel):
        size: QuantityField

    class Outer(QuantityModel):
        data: dict

    inner = Inner(size=Quantity(10.0, "m"))
    outer = Outer(data={"nested": inner, "value": 42})

    serialized = outer.to_dict()
    assert serialized["data"]["nested"]["size"] == [10.0, "meter"]
    assert serialized["data"]["value"] == 42

    # Test verbose format
    serialized_verbose = outer.to_dict(verbose=True)
    assert serialized_verbose["data"]["nested"]["size"]["magnitude"] == 10.0
    assert serialized_verbose["data"]["value"] == 42


def test_serialize_list_with_mixed_types():
    """Test serialization of lists containing mixed types (condensed by default)"""

    class TestModel(QuantityModel):
        items: list

    model = TestModel(
        items=[1, "string", Quantity(5.0, "m"), {"key": "value"}, [1, 2, 3]]
    )

    serialized = model.to_dict()
    assert serialized["items"][0] == 1
    assert serialized["items"][1] == "string"
    assert serialized["items"][2] == [5.0, "meter"]
    assert serialized["items"][3] == {"key": "value"}
    assert serialized["items"][4] == [1, 2, 3]

    # Test verbose format
    serialized_verbose = model.to_dict(verbose=True)
    assert serialized_verbose["items"][2]["magnitude"] == 5.0
    assert serialized_verbose["items"][2]["units"] == "meter"


def test_invalid_list_units_type():
    """Test error when list format has non-string units"""

    class TestModel(QuantityModel):
        length: QuantityField

    with pytest.raises(ValidationError) as exc_info:
        TestModel(length=[10.0, 123])  # Units should be string, not int

    assert "Units must be str" in str(exc_info.value)


def test_invalid_list_magnitude_type():
    """Test error when list format has non-numeric magnitude"""

    class TestModel(QuantityModel):
        length: QuantityField

    with pytest.raises(ValidationError) as exc_info:
        TestModel(length=["not a number", "m"])

    assert "Magnitude must be float or int" in str(exc_info.value)


def test_invalid_input_type():
    """Test error when invalid type is provided for quantity field"""

    class TestModel(QuantityModel):
        length: QuantityField

    # Test with set (invalid type)
    with pytest.raises(ValidationError) as exc_info:
        TestModel(length={10.0, "m"})

    assert "Invalid input for quantity field" in str(exc_info.value)


def test_model_dump_json_condensed():
    """Test JSON string serialization with condensed format (default)"""

    class TestModel(QuantityModel):
        length: QuantityField
        name: str

    model = TestModel(length=Quantity(10.0, "m"), name="test")
    json_str = model.model_dump_json()

    # Parse JSON and verify structure
    import json

    data = json.loads(json_str)
    assert data["length"] == [10.0, "meter"]
    assert data["name"] == "test"


def test_model_dump_json_verbose():
    """Test JSON string serialization with verbose format"""

    class TestModel(QuantityModel):
        length: QuantityField
        name: str

    model = TestModel(length=Quantity(10.0, "m"), name="test")
    json_str = model.model_dump_json(context={"verbose": True})

    # Parse JSON and verify structure
    import json

    data = json.loads(json_str)
    assert data["length"]["magnitude"] == 10.0
    assert data["length"]["units"] == "meter"
    assert data["name"] == "test"


def test_from_dict_method():
    """Test the from_dict class method"""

    class TestModel(QuantityModel):
        length: QuantityField
        width: QuantityField

    data = {"length": [10.0, "m"], "width": {"magnitude": 5.0, "units": "m"}}
    model = TestModel.from_dict(data)

    assert isinstance(model.length, Quantity)
    assert model.length.magnitude == 10.0
    assert str(model.length.units) == "meter"
    assert isinstance(model.width, Quantity)
    assert model.width.magnitude == 5.0


def test_quantity_field_with_optional():
    """Test QuantityField with None/optional values"""

    class TestModel(QuantityModel):
        length: QuantityField
        optional_width: QuantityField = None

    model = TestModel(length=Quantity(10.0, "m"))
    assert model.length.magnitude == 10.0
    assert model.optional_width is None

    # Test serialization with None value
    serialized = model.to_dict()
    assert serialized["length"] == [10.0, "meter"]
    assert serialized["optional_width"] is None
