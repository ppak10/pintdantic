from typing import Any

from .types import Number, QuantityInput


def parse_cli_input(
    value: str | None | tuple[Number, str] | Any
) -> QuantityInput | None:
    """
    Convert CLI input into a QuantityInput type.

    Accepted formats:
      "5"                  -> 5 (int)
      "5.5"                -> 5.5 (float)
      "5e-5"               -> 5e-5 (float)
      "5,meter"            -> (5, "meter")
      "1.1 m/s"            -> (1.1, "m/s")
      None                 -> None
      (5, "m")             -> (5, "m")   (passthrough)
      "(5e-05, 'meter')"   -> (5e-05, "meter")
    """
    if value is None:
        return None

    # If already a tuple, pass through
    if isinstance(value, tuple):
        if len(value) != 2:
            raise ValueError(f"Invalid quantity tuple: {value!r}")
        num, unit = value
        if not isinstance(num, (int, float)) or not isinstance(unit, str):
            raise ValueError(f"Invalid types in tuple: {value!r}")
        return num, unit

    if not isinstance(value, str):
        raise TypeError(f"Unsupported type for quantity: {type(value)}")

    value = value.strip()

    # Handle stringified tuple input like "(5e-05, 'meter')"
    if value.startswith("(") and value.endswith(")"):
        try:
            parsed = eval(value, {"__builtins__": {}})
            if isinstance(parsed, tuple) and len(parsed) == 2:
                num, unit = parsed
                if isinstance(num, (int, float)) and isinstance(unit, str):
                    return num, unit
        except Exception:
            raise ValueError(f"Invalid tuple-like quantity string: {value!r}")

    try:
        # number,unit (comma separated)
        if "," in value:
            num_str, unit = value.split(",", 1)
            num_str = num_str.strip()
            unit = unit.strip().strip("'\"")
            number = (
                float(num_str)
                if "." in num_str or "e" in num_str.lower()
                else int(num_str)
            )
            return (number, unit)

        # number unit (space separated, e.g. "1.1 m/s")
        parts = value.split(maxsplit=1)
        if len(parts) == 2:
            num_str, unit = parts
            number = (
                float(num_str)
                if "." in num_str or "e" in num_str.lower()
                else int(num_str)
            )
            return (number, unit.strip())

        # plain number
        return float(value) if "." in value or "e" in value.lower() else int(value)

    except Exception as e:
        raise ValueError(f"Invalid quantity string: {value!r}") from e
