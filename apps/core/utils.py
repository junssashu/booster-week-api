import uuid


def generate_prefixed_id(prefix):
    """Generate a short prefixed ID like usr_abc123."""
    short = uuid.uuid4().hex[:12]
    return f'{prefix}_{short}'
