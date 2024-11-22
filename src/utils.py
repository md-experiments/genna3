# create hash from text
import hashlib
import os
import tiktoken
import traceback
import json

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