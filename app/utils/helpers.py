"""
Shared helpers (e.g. enum -> DB value for model_dump).
"""
import enum
from typing import Any, Dict


def enum_to_db_value(value: Any) -> Any:
    """Convert enum to its value for database storage. Other types unchanged."""
    if isinstance(value, enum.Enum):
        return value.value
    return value


def model_dump_for_db(model_instance, exclude_unset: bool = False) -> Dict[str, Any]:
    """Dump Pydantic model to dict with enum values for DB. Optionally exclude unset fields."""
    data = model_instance.model_dump(exclude_unset=exclude_unset)
    return {k: enum_to_db_value(v) for k, v in data.items()}
