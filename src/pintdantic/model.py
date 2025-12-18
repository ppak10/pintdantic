import json

from pint import Quantity
from pathlib import Path
from pydantic import BaseModel, ConfigDict, model_validator, model_serializer
from pydantic_core import PydanticUndefined
from typing import Any
from typing_extensions import cast, ClassVar, get_args, TypeVar

from .types import QuantityDict, QuantityField

QUANTITY_FIELD_SET = set(get_args(QuantityField))

T = TypeVar("T", bound="QuantityModel")


class QuantityModel(BaseModel):
    """
    Base pydantic model for handling parsing and serializing quantities in
    child classes.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    # _quantity_defaults: ClassVar[dict[str, Tuple[float | int, str]]] = {}

    @staticmethod
    def _quantity_to_dict(q: Quantity) -> QuantityDict:
        return {"magnitude": cast(float, q.magnitude), "units": str(q.units)}

    @staticmethod
    def _dict_to_quantity(d: QuantityDict) -> Quantity:
        # Create Quantity from magnitude and units string
        return cast(Quantity, Quantity(d["magnitude"], d["units"]))

    def _serialize_value(self, value: Any) -> Any:
        """Recursively serialize a value, handling Quantity and nested QuantityModel instances."""
        if isinstance(value, Quantity):
            return self._quantity_to_dict(value)
        elif isinstance(value, QuantityModel):
            # Recursively serialize nested QuantityModel by getting its dict representation
            nested_data = {}
            for field in value.__class__.model_fields:
                nested_value = getattr(value, field)
                nested_data[field] = self._serialize_value(nested_value)
            return nested_data
        elif isinstance(value, list):
            # Handle lists of any items (including QuantityModel instances)
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            # Handle dictionaries
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            # Return as-is for primitive types
            return value

    @model_serializer
    def serialize_model(self):
        data = {}
        for field in self.__class__.model_fields:
            value = getattr(self, field)
            data[field] = self._serialize_value(value)
        return data

    @model_validator(mode="before")
    @classmethod
    def coerce_quantity_inputs(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Convert various input formats to Quantity if applicable."""
        for name, info in cls.model_fields.items():

            # Check that name is in values argument.
            if name not in values:
                # Use default if field not provided
                if info.default is not PydanticUndefined:
                    if isinstance(info.default, tuple) and len(info.default) == 2:
                        # Just checks if input from dict is tuple to assume quantity
                        values[name] = Quantity(*info.default)
                    else:
                        values[name] = info.default
                continue

            v = values[name]
            field_type_set = set(get_args(info.annotation))

            # If input is intended to be Quantity.
            if QUANTITY_FIELD_SET.issubset(field_type_set):

                # Already a Quantity, keep as is
                if isinstance(v, Quantity):
                    continue

                # Just a number - use default units
                if isinstance(v, (float, int)):
                    if info.default is PydanticUndefined:
                        raise ValueError(
                            f"Default quantity not provided, could not obtain default units"
                        )
                    else:
                        values[name] = Quantity(v, info.default[1])

                # Tuple (magnitude, unit)
                elif isinstance(v, tuple) and len(v) == 2:
                    if not isinstance(v[0], (float, int)):
                        raise ValueError(
                            f"Magnitude must be float or int, got {type(v[0])}"
                        )
                    if not isinstance(v[1], str):
                        raise ValueError(f"Units must be str, got {type(v[1])}")
                    values[name] = Quantity(v[0], v[1])

                # Dict input
                elif isinstance(v, dict):
                    expected_keys = {"magnitude", "units"}
                    if set(v.keys()) != expected_keys:
                        raise ValueError(f"Invalid keys for QuantityDict: {v.keys()}")
                    if not isinstance(v["magnitude"], (float, int)):
                        raise ValueError(
                            f"QuantityDict magnitude must be float or int, got {type(v['magnitude'])}"
                        )
                    if not isinstance(v["units"], str):
                        raise ValueError(
                            f"QuantityDict units must be str, got {type(v['units'])}"
                        )
                    values[name] = Quantity(v["magnitude"], v["units"])

                # Invalid type
                else:
                    raise ValueError(
                        f"Invalid input for quantity field {name}: {type(v)}"
                    )

        return values

    @classmethod
    def load(cls: type[T], path: Path) -> T:
        with path.open("r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return cls.from_dict(data)
        raise ValueError(f"Unexpected JSON structure in {path}: expected dict")

    def save(self, path):
        data = self.to_dict()  # Convert all Quantities to dicts first
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
        return path

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        # Data will be processed by model_validator automatically
        return cls(**data)

    def to_dict(self):
        out = {}
        for field in self.__class__.model_fields:
            value = getattr(self, field)
            out[field] = self._serialize_value(value)
        return out
