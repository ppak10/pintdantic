[![pytest](https://github.com/ppak10/pintdantic/actions/workflows/pytest.yml/badge.svg)](https://github.com/ppak10/pintdantic/actions/workflows/pytest.yml)
[![codecov](https://codecov.io/gh/ppak10/pintdantic/graph/badge.svg?token=542K2LPT47)](https://codecov.io/gh/ppak10/pintdantic)

# pintdantic
Pydantic bindings for Pint

## Installation

```bash
pip install pintdantic
```

## Quick Start

```python
from pintdantic import QuantityModel, QuantityField
from pint import Quantity

class MyModel(QuantityModel):
    length: QuantityField
    width: QuantityField

# Create a model with Quantity objects
model = MyModel(
    length=Quantity(10.0, "m"),
    width=Quantity(5.0, "m")
)

# Serialize to dict (condensed format by default)
data = model.to_dict()
# {"length": [10.0, "meter"], "width": [5.0, "meter"]}

# Load from dict
loaded_model = MyModel.from_dict(data)
```

## Serialization Formats

Pintdantic supports two serialization formats for Quantity values:

### Condensed Format (Default)

By default, Quantity values are serialized to a compact array format:

```python
model = MyModel(length=Quantity(100.0, "watt"))
data = model.to_dict()
# {"length": [100.0, "watt"]}
```

This format is more compact and produces smaller JSON payloads.

### Verbose Format

You can use the verbose format (dict-based) by setting `verbose=True`:

```python
# Serialize with verbose format
data = model.to_dict(verbose=True)
# {"length": {"magnitude": 100.0, "units": "watt"}}

# Save to file with verbose format
model.save("output.json", verbose=True)

# Using Pydantic's model_dump with context
data = model.model_dump(context={'verbose': True})
```

### Backwards Compatibility

Pintdantic can load data in either format, providing full backwards compatibility:

```python
# Both formats work for loading
condensed_data = {"length": [10.0, "meter"], "width": [5.0, "meter"]}
verbose_data = {
    "length": {"magnitude": 10.0, "units": "meter"},
    "width": {"magnitude": 5.0, "units": "meter"}
}

model1 = MyModel.from_dict(condensed_data)  # Works!
model2 = MyModel.from_dict(verbose_data)    # Also works!
```

## Input Formats

Pintdantic accepts multiple input formats for Quantity fields:

```python
# Quantity objects
MyModel(length=Quantity(10.0, "m"))

# Tuples (magnitude, units)
MyModel(length=(10.0, "m"))

# Lists [magnitude, units] - JSON-compatible
MyModel(length=[10.0, "m"])

# Dicts (verbose format)
MyModel(length={"magnitude": 10.0, "units": "m"})

# Bare numbers (if defaults are set)
class ModelWithDefaults(QuantityModel):
    length: QuantityField = (10.0, "m")

ModelWithDefaults(length=5.0)  # Uses default units "m"
```

## Nested Models

The verbose flag works with nested models and propagates through the entire serialization tree:

```python
class Inner(QuantityModel):
    measurement: QuantityField

class Outer(QuantityModel):
    name: str
    inner: Inner
    height: QuantityField

outer = Outer(
    name="test",
    inner=Inner(measurement=Quantity(5.0, "cm")),
    height=Quantity(10.0, "m")
)

# Condensed (default)
data = outer.to_dict()
# {
#     "name": "test",
#     "inner": {"measurement": [5.0, "centimeter"]},
#     "height": [10.0, "meter"]
# }

# Verbose
data = outer.to_dict(verbose=True)
# {
#     "name": "test",
#     "inner": {"measurement": {"magnitude": 5.0, "units": "centimeter"}},
#     "height": {"magnitude": 10.0, "units": "meter"}
# }
```

## Usage with Pydantic BaseModel

When using QuantityModel within a regular Pydantic BaseModel, you can control the serialization format using Pydantic's context:

```python
from pydantic import BaseModel

class RegularModel(BaseModel):
    id: int
    quantities: MyQuantityModel

model = RegularModel(id=1, quantities=MyQuantityModel(...))

# Condensed format (default)
data = model.model_dump()

# Verbose format using context
data = model.model_dump(context={'verbose': True})
```
