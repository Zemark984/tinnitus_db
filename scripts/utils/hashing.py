import hashlib

def hash_id(prefix, val):
    """Создает короткий хеш для ID"""
    return prefix + "_" + hashlib.sha256(val.encode()).hexdigest()[:16]
