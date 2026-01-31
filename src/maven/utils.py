"""
Utility functions for MAVEN.

This module provides helper functions used throughout the library.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def generate_trace_id() -> str:
    """Generate a unique identifier for a verification trace.

    Returns:
        A UUID string for trace identification.
    """
    return str(uuid.uuid4())


def get_timestamp() -> str:
    """Get current UTC timestamp in ISO format.

    Returns:
        ISO-formatted timestamp string.
    """
    return datetime.now(timezone.utc).isoformat()


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to specified length with ellipsis.

    Args:
        text: Text to truncate.
        max_length: Maximum length before truncation.

    Returns:
        Truncated text with ellipsis if needed.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def extract_key_claims(text: str) -> List[str]:
    """Extract key claims from a response for consensus comparison.

    This is a simple implementation that splits on sentence boundaries.
    More sophisticated implementations could use NLP.

    Args:
        text: Response text to analyze.

    Returns:
        List of extracted claim strings.
    """
    # Simple sentence splitting - could be enhanced with NLP
    sentences = []
    for delimiter in ['. ', '? ', '! ']:
        text = text.replace(delimiter, '.|')

    raw_sentences = text.split('.|')
    for sentence in raw_sentences:
        cleaned = sentence.strip()
        if cleaned and len(cleaned) > 10:
            sentences.append(cleaned)

    return sentences


def calculate_similarity(claims1: List[str], claims2: List[str]) -> float:
    """Calculate simple similarity between two claim lists.

    Uses word overlap as a basic similarity metric.

    Args:
        claims1: First list of claims.
        claims2: Second list of claims.

    Returns:
        Similarity score between 0.0 and 1.0.
    """
    if not claims1 or not claims2:
        return 0.0

    # Convert to word sets for comparison
    words1 = set()
    for claim in claims1:
        words1.update(claim.lower().split())

    words2 = set()
    for claim in claims2:
        words2.update(claim.lower().split())

    # Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    if union == 0:
        return 0.0

    return intersection / union


def validate_models(models: List[str]) -> None:
    """Validate model configuration.

    Args:
        models: List of model identifiers.

    Raises:
        ValueError: If model configuration is invalid.
    """
    if not models:
        raise ValueError("At least one model must be specified")

    if len(models) < 3:
        raise ValueError("MAVEN requires at least 3 models for consensus")

    if len(models) != len(set(models)):
        raise ValueError("Duplicate models are not allowed")


def merge_configs(default: Dict[str, Any], override: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge configuration dictionaries.

    Args:
        default: Default configuration values.
        override: User-provided overrides.

    Returns:
        Merged configuration dictionary.
    """
    result = default.copy()
    if override:
        result.update(override)
    return result


# Default configuration values
DEFAULT_CONFIG: Dict[str, Any] = {
    "max_iterations": 5,
    "consensus_threshold": 0.8,
    "timeout_seconds": 60,
    "enable_role_rotation": True,
    "trace_verbosity": "full",
    "retry_on_error": True,
    "max_retries": 3,
}
