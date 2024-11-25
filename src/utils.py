# create hash from text
import hashlib
import os
import tiktoken
import traceback
import json
from typing import Dict, Any
from copy import deepcopy

def update_nested_dict(data: Dict[str, Any], keys: list, value: Any) -> Dict[str, Any]:
    """
    Safely updates a nested dictionary, creating intermediate dictionaries if they don't exist.
    
    Args:
        data: The original dictionary to update
        keys: List of keys representing the path to the value to update
        value: The value to set at the specified path
    
    Returns:
        Updated dictionary
    """
    # Create a deep copy to avoid modifying the original
    result = deepcopy(data)
    
    # Start at the root
    current = result
    
    # Navigate through all but the last key
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    # Set the final value
    current[keys[-1]] = value
    
    return result
def log_traceback():
    return traceback.format_exc()

def hash_text(text):
    return hashlib.md5(text.encode()).hexdigest()

def makedirs(paths):
    for path in paths:
        if not os.path.exists(path):
            os.makedirs(path)

def num_tokens_from_string(string: str, model_name = 'gpt-3.5-turbo') -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens