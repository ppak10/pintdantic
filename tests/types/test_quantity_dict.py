from pintdantic import QuantityDict, QuantityField, QuantityModel


def test_quantity_field_json_schema():
    """Test that QuantityField generates correct JSON schema"""

    class TestModel(QuantityModel):
        length: QuantityField
        width: QuantityField = (5.0, "m")

    schema = TestModel.model_json_schema()

    # Verify the schema is generated
    assert "properties" in schema
    assert "length" in schema["properties"]
    assert "width" in schema["properties"]

    # Check that QuantityField has anyOf schema with multiple formats
    length_schema = schema["properties"]["length"]
    assert "anyOf" in length_schema

    # Verify all expected input formats are in the schema
    any_of = length_schema["anyOf"]
    schema_types = [item.get("type") for item in any_of if "type" in item]

    # Should support: number, integer, array (list), object (dict), null
    assert "number" in schema_types
    assert "integer" in schema_types
    assert "array" in schema_types
    assert "object" in schema_types
    assert "null" in schema_types


def test_valid_quantity_dict_with_float():
    q: QuantityDict = {"magnitude": 1.23, "units": "m"}
    assert isinstance(q["magnitude"], float)
    assert q["magnitude"] == 1.23
    assert q["units"] == "m"


def test_valid_quantity_dict_with_int():
    q: QuantityDict = {"magnitude": 5, "units": "s"}
    assert isinstance(q["magnitude"], int)
    assert q["magnitude"] == 5
    assert q["units"] == "s"


def test_invalid_magnitude_type():
    q: QuantityDict = {"magnitude": "not_a_number", "units": "m"}
    # Validate manually since TypedDict doesn't enforce types
    assert isinstance(q["magnitude"], str)
    assert not isinstance(q["magnitude"], (int, float))


def test_invalid_units_type():
    q: QuantityDict = {"magnitude": 1.0, "units": 123}
    assert isinstance(q["units"], int)
    assert not isinstance(q["units"], str)


def test_missing_keys():
    # Missing magnitude
    q: dict = {"units": "m"}
    assert "magnitude" not in q
    # Missing units
    q: dict = {"magnitude": 10}
    assert "units" not in q
