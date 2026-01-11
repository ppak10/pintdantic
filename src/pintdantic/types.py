from pint import Quantity

from typing import Annotated, Any, List, Tuple
from typing_extensions import TypeAlias, TypedDict
from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

Number: TypeAlias = float | int
QuantityInput = Number | Tuple[Number, str] | List[Number | str]


class _QuantityPydanticAnnotation:
    """Custom Pydantic annotation for Quantity fields with proper JSON schema support."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        handler: Any,
    ) -> core_schema.CoreSchema:
        """
        Defines how Pydantic should validate Quantity fields.
        We use the default handler to preserve QuantityModel's model_validator behavior,
        but provide a custom JSON schema.
        """
        # Get the default schema from Pydantic
        # This allows the model validator to still run and convert plain numbers
        python_schema = handler(_source_type)

        return python_schema

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _core_schema: core_schema.CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        """
        Defines the JSON schema for Quantity fields.
        This tells JSON schema consumers what format to expect.
        """
        # Return a schema that describes the possible input/output formats
        return {
            "anyOf": [
                {"type": "number"},  # Direct number (uses default units)
                {"type": "integer"},  # Direct integer (uses default units)
                {  # Condensed list format [magnitude, units]
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "prefixItems": [
                        {"anyOf": [{"type": "number"}, {"type": "integer"}]},
                        {"type": "string"},
                    ],
                },
                {  # Verbose dict format {"magnitude": ..., "units": ...}
                    "type": "object",
                    "properties": {
                        "magnitude": {
                            "anyOf": [{"type": "number"}, {"type": "integer"}]
                        },
                        "units": {"type": "string"},
                    },
                    "required": ["magnitude", "units"],
                },
                {"type": "null"},  # None
            ]
        }


# Use Annotated to attach the custom schema handler
QuantityField = Annotated[
    Quantity | QuantityInput | None,
    _QuantityPydanticAnnotation,
]

# Condensed format (default): [magnitude, units]
QuantityList: TypeAlias = List[float | str]


class QuantityDict(TypedDict):
    """
    TypedDict for Quantity serialized as dict (verbose format)
    """

    magnitude: float
    units: str
