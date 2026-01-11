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
    """Test that nested QuantityModel instances serialize correctly (condensed by default)"""
    inner = InnerModel(length=Quantity(5.0, "m"), width=Quantity(3.0, "m"))
    outer = OuterModel(name="test", inner=inner, height=Quantity(2.0, "m"))

    # Test to_dict with default condensed format
    d = outer.to_dict()
    assert d["name"] == "test"
    assert d["height"] == [2.0, "meter"]
    assert d["inner"]["length"] == [5.0, "meter"]
    assert d["inner"]["width"] == [3.0, "meter"]


def test_nested_model_serialization_verbose():
    """Test that nested QuantityModel instances serialize correctly with verbose flag"""
    inner = InnerModel(length=Quantity(5.0, "m"), width=Quantity(3.0, "m"))
    outer = OuterModel(name="test", inner=inner, height=Quantity(2.0, "m"))

    # Test to_dict with verbose format
    d = outer.to_dict(verbose=True)
    assert d["name"] == "test"
    assert d["height"]["magnitude"] == 2.0
    assert d["height"]["units"] == "meter"
    assert d["inner"]["length"]["magnitude"] == 5.0
    assert d["inner"]["length"]["units"] == "meter"
    assert d["inner"]["width"]["magnitude"] == 3.0
    assert d["inner"]["width"]["units"] == "meter"


def test_list_of_nested_models_serialization():
    """Test that lists of QuantityModel instances serialize correctly (condensed by default)"""
    item1 = InnerModel(length=Quantity(1.0, "m"), width=Quantity(2.0, "m"))
    item2 = InnerModel(length=Quantity(3.0, "m"), width=Quantity(4.0, "m"))
    outer = OuterModelWithList(name="test_list", items=[item1, item2])

    # Test to_dict with condensed format
    d = outer.to_dict()
    assert d["name"] == "test_list"
    assert len(d["items"]) == 2
    assert d["items"][0]["length"] == [1.0, "meter"]
    assert d["items"][0]["width"] == [2.0, "meter"]
    assert d["items"][1]["length"] == [3.0, "meter"]
    assert d["items"][1]["width"] == [4.0, "meter"]


def test_list_of_nested_models_serialization_verbose():
    """Test that lists of QuantityModel instances serialize correctly with verbose flag"""
    item1 = InnerModel(length=Quantity(1.0, "m"), width=Quantity(2.0, "m"))
    item2 = InnerModel(length=Quantity(3.0, "m"), width=Quantity(4.0, "m"))
    outer = OuterModelWithList(name="test_list", items=[item1, item2])

    # Test to_dict with verbose format
    d = outer.to_dict(verbose=True)
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
    """Test that regular BaseModel can contain QuantityModel and serialize (condensed by default)"""
    inner = InnerModel(length=Quantity(7.0, "m"), width=Quantity(8.0, "m"))
    mixed = MixedModel(id=42, segment=inner)

    # The BaseModel should use QuantityModel's serializer for nested model
    d = mixed.model_dump()
    assert d["id"] == 42
    # Condensed format by default
    assert d["segment"]["length"] == [7.0, "meter"]
    assert d["segment"]["width"] == [8.0, "meter"]


def test_mixed_base_model_with_quantity_model_verbose():
    """Test that regular BaseModel can contain QuantityModel and serialize with verbose flag"""
    inner = InnerModel(length=Quantity(7.0, "m"), width=Quantity(8.0, "m"))
    mixed = MixedModel(id=42, segment=inner)

    # Test with verbose context
    d = mixed.model_dump(context={"verbose": True})
    assert d["id"] == 42
    assert d["segment"]["length"]["magnitude"] == 7.0
    assert d["segment"]["length"]["units"] == "meter"


def test_deeply_nested_models():
    """Test multiple levels of nesting (condensed by default)"""

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

    # Test condensed format
    d = l1.to_dict()
    assert d["area"] == [3.0, "meter ** 2"]
    assert d["level2"]["size"] == [2.0, "meter"]
    assert d["level2"]["level3"]["depth"] == [1.0, "meter"]

    # Test verbose format
    d_verbose = l1.to_dict(verbose=True)
    assert d_verbose["area"]["magnitude"] == 3.0
    assert d_verbose["level2"]["size"]["magnitude"] == 2.0
    assert d_verbose["level2"]["level3"]["depth"]["magnitude"] == 1.0


def test_empty_list_of_models():
    """Test that empty lists are handled correctly"""
    outer = OuterModelWithList(name="empty", items=[])
    d = outer.to_dict()
    assert d["items"] == []

    json_str = outer.model_dump_json()
    assert "items" in json_str


def test_complex_real_world_example():
    """Test a complex real-world scenario similar to SolverLayer/SolverSegment (condensed by default)"""

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

    # Test to_dict (via model_dump) with condensed format
    d = layer.model_dump()
    assert d["index"] == 1
    assert d["total"] == 10
    assert len(d["segments"]) == 2
    assert d["segments"][0]["x1"] == [0.0, "millimeter"]
    assert d["segments"][0]["distance"] == [14.14, "millimeter"]
    assert d["segments"][1]["travel"] is True

    # Test with verbose format
    d_verbose = layer.model_dump(context={"verbose": True})
    assert d_verbose["segments"][0]["x1"]["magnitude"] == 0.0
    assert d_verbose["segments"][0]["distance"]["units"] == "millimeter"


def test_nested_json_loading():
    """Test that nested models can be loaded from JSON"""
    import json

    class InnerModel(QuantityModel):
        length: QuantityField
        width: QuantityField

    class OuterModel(QuantityModel):
        name: str
        inner: InnerModel
        height: QuantityField

    # Create original model
    original = OuterModel(
        name="test",
        inner=InnerModel(length=Quantity(5.0, "m"), width=Quantity(3.0, "m")),
        height=Quantity(2.0, "m"),
    )

    # Serialize to JSON string
    json_str = original.model_dump_json()

    # Parse JSON and recreate model
    json_data = json.loads(json_str)
    loaded = OuterModel(**json_data)

    # Verify all fields are correctly loaded as Quantity objects
    assert isinstance(loaded.height, Quantity)
    assert loaded.height.magnitude == 2.0
    assert str(loaded.height.units) == "meter"

    assert isinstance(loaded.inner, InnerModel)
    assert isinstance(loaded.inner.length, Quantity)
    assert loaded.inner.length.magnitude == 5.0
    assert str(loaded.inner.length.units) == "meter"
    assert isinstance(loaded.inner.width, Quantity)
    assert loaded.inner.width.magnitude == 3.0


def test_nested_list_json_loading():
    """Test that lists of nested models can be loaded from JSON"""
    import json

    class SolverSegment(QuantityModel):
        x: QuantityField
        y: QuantityField
        travel: bool

    class SolverLayer(BaseModel):
        index: int
        segments: list[SolverSegment]

    # Create original model
    original = SolverLayer(
        index=1,
        segments=[
            SolverSegment(x=Quantity(0.0, "mm"), y=Quantity(0.0, "mm"), travel=False),
            SolverSegment(x=Quantity(10.0, "mm"), y=Quantity(5.0, "mm"), travel=True),
        ],
    )

    # Serialize and deserialize
    json_str = original.model_dump_json()
    json_data = json.loads(json_str)
    loaded = SolverLayer(**json_data)

    # Verify
    assert loaded.index == 1
    assert len(loaded.segments) == 2

    assert isinstance(loaded.segments[0].x, Quantity)
    assert loaded.segments[0].x.magnitude == 0.0
    assert str(loaded.segments[0].x.units) == "millimeter"

    assert isinstance(loaded.segments[1].y, Quantity)
    assert loaded.segments[1].y.magnitude == 5.0
    assert loaded.segments[1].travel is True
