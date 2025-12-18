import pytest

from pathlib import Path
from pintdantic import QuantityField, QuantityModel
from pint import Quantity
from pydantic import BaseModel


class InnerModel(QuantityModel):
    """Model with quantity fields"""

    length: QuantityField
    width: QuantityField


class OuterModel(QuantityModel):
    """Model with nested QuantityModel"""

    name: str
    inner: InnerModel
    height: QuantityField


class OuterModelWithList(QuantityModel):
    """Model with list of QuantityModel instances"""

    name: str
    items: list[InnerModel]


class MixedModel(BaseModel):
    """Regular BaseModel that contains a QuantityModel"""

    id: int
    segment: InnerModel


def test_nested_model_serialization():
    """Test that nested QuantityModel instances serialize correctly"""
    inner = InnerModel(length=Quantity(5.0, "m"), width=Quantity(3.0, "m"))
    outer = OuterModel(name="test", inner=inner, height=Quantity(2.0, "m"))

    # Test model_dump_json
    json_str = outer.model_dump_json()
    assert "magnitude" in json_str
    assert "units" in json_str

    # Test to_dict
    d = outer.to_dict()
    assert d["name"] == "test"
    assert d["height"]["magnitude"] == 2.0
    assert d["height"]["units"] == "meter"
    assert d["inner"]["length"]["magnitude"] == 5.0
    assert d["inner"]["length"]["units"] == "meter"
    assert d["inner"]["width"]["magnitude"] == 3.0
    assert d["inner"]["width"]["units"] == "meter"


def test_list_of_nested_models_serialization():
    """Test that lists of QuantityModel instances serialize correctly"""
    item1 = InnerModel(length=Quantity(1.0, "m"), width=Quantity(2.0, "m"))
    item2 = InnerModel(length=Quantity(3.0, "m"), width=Quantity(4.0, "m"))
    outer = OuterModelWithList(name="test_list", items=[item1, item2])

    # Test model_dump_json
    json_str = outer.model_dump_json()
    assert "magnitude" in json_str
    assert "units" in json_str

    # Test to_dict
    d = outer.to_dict()
    assert d["name"] == "test_list"
    assert len(d["items"]) == 2
    assert d["items"][0]["length"]["magnitude"] == 1.0
    assert d["items"][0]["length"]["units"] == "meter"
    assert d["items"][1]["length"]["magnitude"] == 3.0
    assert d["items"][1]["width"]["magnitude"] == 4.0


def test_nested_model_round_trip(tmp_path: Path):
    """Test save and load with nested models"""
    inner = InnerModel(length=Quantity(10.0, "m"), width=Quantity(20.0, "m"))
    outer = OuterModel(name="roundtrip", inner=inner, height=Quantity(30.0, "m"))

    # Save and load
    path = tmp_path / "nested.json"
    outer.save(path)
    loaded = OuterModel.load(path)

    # Verify all fields
    assert loaded.name == "roundtrip"
    assert loaded.height.magnitude == 30.0
    assert loaded.inner.length.magnitude == 10.0
    assert loaded.inner.width.magnitude == 20.0


def test_list_of_models_round_trip(tmp_path: Path):
    """Test save and load with lists of nested models"""
    items = [
        InnerModel(length=Quantity(i, "m"), width=Quantity(i * 2, "m"))
        for i in range(1, 4)
    ]
    outer = OuterModelWithList(name="list_roundtrip", items=items)

    # Save and load
    path = tmp_path / "nested_list.json"
    outer.save(path)
    loaded = OuterModelWithList.load(path)

    # Verify
    assert loaded.name == "list_roundtrip"
    assert len(loaded.items) == 3
    for i, item in enumerate(loaded.items, start=1):
        assert item.length.magnitude == i
        assert item.width.magnitude == i * 2


def test_mixed_base_model_with_quantity_model():
    """Test that regular BaseModel can contain QuantityModel and serialize"""
    inner = InnerModel(length=Quantity(7.0, "m"), width=Quantity(8.0, "m"))
    mixed = MixedModel(id=42, segment=inner)

    # The BaseModel should use QuantityModel's serializer for nested model
    json_str = mixed.model_dump_json()
    assert "magnitude" in json_str
    assert "units" in json_str

    d = mixed.model_dump()
    assert d["id"] == 42
    assert d["segment"]["length"]["magnitude"] == 7.0


def test_deeply_nested_models():
    """Test multiple levels of nesting"""

    class Level3(QuantityModel):
        depth: QuantityField

    class Level2(QuantityModel):
        level3: Level3
        size: QuantityField

    class Level1(QuantityModel):
        level2: Level2
        area: QuantityField

    l3 = Level3(depth=Quantity(1.0, "m"))
    l2 = Level2(level3=l3, size=Quantity(2.0, "m"))
    l1 = Level1(level2=l2, area=Quantity(3.0, "m^2"))

    d = l1.to_dict()
    assert d["area"]["magnitude"] == 3.0
    assert d["level2"]["size"]["magnitude"] == 2.0
    assert d["level2"]["level3"]["depth"]["magnitude"] == 1.0

    json_str = l1.model_dump_json()
    assert "magnitude" in json_str
    assert "units" in json_str


def test_empty_list_of_models():
    """Test that empty lists are handled correctly"""
    outer = OuterModelWithList(name="empty", items=[])
    d = outer.to_dict()
    assert d["items"] == []

    json_str = outer.model_dump_json()
    assert "items" in json_str


def test_complex_real_world_example():
    """Test a complex real-world scenario similar to SolverLayer/SolverSegment"""

    class SolverSegment(QuantityModel):
        x1: QuantityField
        y1: QuantityField
        x2: QuantityField
        y2: QuantityField
        angle: QuantityField
        distance: QuantityField
        travel: bool

    class SolverLayer(BaseModel):
        index: int
        total: int
        segments: list[SolverSegment]

    # Create test data
    segments = [
        SolverSegment(
            x1=Quantity(0.0, "mm"),
            y1=Quantity(0.0, "mm"),
            x2=Quantity(10.0, "mm"),
            y2=Quantity(10.0, "mm"),
            angle=Quantity(45.0, "degree"),
            distance=Quantity(14.14, "mm"),
            travel=False,
        ),
        SolverSegment(
            x1=Quantity(10.0, "mm"),
            y1=Quantity(10.0, "mm"),
            x2=Quantity(20.0, "mm"),
            y2=Quantity(10.0, "mm"),
            angle=Quantity(0.0, "degree"),
            distance=Quantity(10.0, "mm"),
            travel=True,
        ),
    ]

    layer = SolverLayer(index=1, total=10, segments=segments)

    # Test serialization to JSON
    json_str = layer.model_dump_json()
    assert "magnitude" in json_str
    assert "units" in json_str

    # Test to_dict (via model_dump)
    d = layer.model_dump()
    assert d["index"] == 1
    assert d["total"] == 10
    assert len(d["segments"]) == 2
    assert d["segments"][0]["x1"]["magnitude"] == 0.0
    assert d["segments"][0]["distance"]["units"] == "millimeter"
    assert d["segments"][1]["travel"] is True
