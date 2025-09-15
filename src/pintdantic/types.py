from pint import Quantity

from typing import Tuple
from typing_extensions import TypeAlias, TypedDict

Number: TypeAlias = float | int
QuantityInput = Number | Tuple[Number, str]
QuantityField = Quantity | QuantityInput | None


class QuantityDict(TypedDict):
    """
    TypedDict for Quantity serialized as dict
    """

    magnitude: float
    units: str
