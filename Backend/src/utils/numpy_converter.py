import numpy as np
import logging

logger = logging.getLogger(__name__)

def convert_numpy_to_python(obj):
    """
    Recursively convert NumPy types to native Python types.
    
    Args:
        obj: Any Python object that might contain NumPy types
        
    Returns:
        The object with all NumPy types converted to Python types
    """
    if isinstance(obj, dict):
        return {key: convert_numpy_to_python(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_python(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_to_python(item) for item in obj)
    elif isinstance(obj, set):
        return {convert_numpy_to_python(item) for item in obj}
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy_to_python(obj.tolist())
    elif isinstance(obj, np.bool_):
        return bool(obj)
    else:
        return obj