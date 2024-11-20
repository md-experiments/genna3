# create hash from text
import hashlib

def hash_text(text):
    return hashlib.md5(text.encode()).hexdigest()