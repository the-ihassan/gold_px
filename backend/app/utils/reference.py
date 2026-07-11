import random
import string
from datetime import datetime


def generate_reference(prefix: str) -> str:
    """e.g. generate_reference('GPX') -> 'GPX-2026-8K4P2Q'"""
    year = datetime.utcnow().year
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{year}-{suffix}"
