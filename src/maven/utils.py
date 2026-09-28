"""Small helpers shared by the detectors."""

import uuid
from datetime import datetime, timezone


def generate_trace_id() -> str:
    """Return a random ID that ties together the steps of one detection run."""
    return str(uuid.uuid4())


def get_timestamp() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()
