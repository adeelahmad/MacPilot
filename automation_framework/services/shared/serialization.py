# File: automation_framework/services/shared/serialization.py

from datetime import datetime
from typing import Any, Dict, List, Optional
import json
from pydantic import BaseModel
import logging
import numbers

logger = logging.getLogger(__name__)

def recursive_dict_conversion(obj: Any) -> Any:
    """Recursively convert objects to serializable dictionaries."""
    if obj is None:
        return None
    elif isinstance(obj, (datetime,)):
        return obj.isoformat()
    elif isinstance(obj, (int, float, str, bool)):
        return obj
    elif isinstance(obj, numbers.Number):  # Handle NSCFNumber
        return float(obj)
    elif hasattr(obj, 'model_dump'):
        return recursive_dict_conversion(obj.model_dump())
    elif isinstance(obj, dict):
        return {k: recursive_dict_conversion(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [recursive_dict_conversion(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return recursive_dict_conversion(obj.__dict__)
    elif hasattr(obj, '_asdict'):  # Handle namedtuples
        return recursive_dict_conversion(obj._asdict())
    try:
        # Try to convert to a basic type
        return float(obj) if isinstance(obj, numbers.Number) else str(obj)
    except:
        return str(obj)  # Fallback to string representation

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects and models."""
    def default(self, obj: Any) -> Any:
        try:
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, BaseModel):
                return recursive_dict_conversion(obj.model_dump())
            elif isinstance(obj, numbers.Number):  # Handle NSCFNumber
                return float(obj)
            elif hasattr(obj, 'model_dump'):
                return recursive_dict_conversion(obj.model_dump())
            return recursive_dict_conversion(obj)
        except Exception as e:
            logger.warning(f"Serialization fallback for {type(obj)}: {e}")
            return str(obj)  # Fallback to string representation
