import hashlib

def generate_hash_str(input_str: str) -> str:
    """Generate a SHA-256 hash of the input string."""
    return hashlib.sha256(input_str.encode()).hexdigest()