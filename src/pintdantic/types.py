from pint import Quantity

from typing import List, Tuple
from typing_extensions import TypeAlias, TypedDict

Number: TypeAlias = float | int
QuantityInput = Number | Tuple[Number, str] | List[Number | str]
QuantityField = Quantity | QuantityInput | None

# Condensed format (default): [magnitude, units]
QuantityList: TypeAlias = List[float | str]


class QuantityDict(TypedDict):
    """
    TypedDict for Quantity serialized as dict (verbose format)
    """

    magnitude: float
    units: str
