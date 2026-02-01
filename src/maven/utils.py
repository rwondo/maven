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


def extract_structured_answer(text: str) -> Optional[str]:
    """Extract the core answer from structured response format.

    Looks for ANSWER:, PROPOSED CONSENSUS:, or similar markers.

    Args:
        text: Response text to parse.

    Returns:
        Extracted answer string, or None if not found.
    """
    # Try different markers in order of preference
    markers = [
        "PROPOSED CONSENSUS:",
        "ANSWER:",
        "CONCLUSION:",
        "FINAL ANSWER:",
    ]

    # End markers to stop extraction
    end_markers = [
        "REASONING:",
        "CONFIDENCE:",
        "CONCERNS:",
        "QUESTIONS:",
        "CONCLUSION:",
        "ANSWER:",
        "PROPOSED CONSENSUS:",
        "\n\n",
    ]

    for marker in markers:
        if marker in text:
            idx = text.index(marker)
            answer_section = text[idx + len(marker):].strip()

            # Find the earliest end marker
            earliest_end = len(answer_section)
            for end_marker in end_markers:
                if end_marker != marker and end_marker in answer_section:
                    pos = answer_section.index(end_marker)
                    if pos < earliest_end:
                        earliest_end = pos

            answer_section = answer_section[:earliest_end].strip()

            if answer_section:
                return answer_section

    return None


def extract_numerical_values(text: str) -> List[float]:
    """Extract numerical values from text.

    Args:
        text: Text to parse.

    Returns:
        List of numerical values found.
    """
    import re
    # Match integers and floats (including negatives and decimals)
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(m) for m in matches if m]


def extract_key_claims(text: str) -> List[str]:
    """Extract key claims from a response for consensus comparison.

    Enhanced version that extracts structured answers first,
    then falls back to sentence splitting.

    Args:
        text: Response text to analyze.

    Returns:
        List of extracted claim strings.
    """
    claims = []

    # First try to extract structured answer
    structured = extract_structured_answer(text)
    if structured:
        claims.append(structured)

    # Also extract sentences for additional context
    sentences = []
    text_copy = text
    for delimiter in ['. ', '? ', '! ']:
        text_copy = text_copy.replace(delimiter, '.|')

    raw_sentences = text_copy.split('.|')
    for sentence in raw_sentences:
        cleaned = sentence.strip()
        if cleaned and len(cleaned) > 10:
            sentences.append(cleaned)

    claims.extend(sentences)
    return claims if claims else sentences


def calculate_similarity(claims1: List[str], claims2: List[str]) -> float:
    """Calculate enhanced similarity between two claim lists.

    Uses multiple strategies weighted by importance:
    1. Structured answer comparison (highest weight)
    2. Numerical value comparison (high weight)
    3. Semantic text similarity (medium weight)

    Args:
        claims1: First list of claims.
        claims2: Second list of claims.

    Returns:
        Similarity score between 0.0 and 1.0.
    """
    if not claims1 or not claims2:
        return 0.0

    # Join claims for analysis
    text1 = " ".join(claims1)
    text2 = " ".join(claims2)

    # Strategy 1: Compare structured answers (weight: 0.6)
    answer1 = extract_structured_answer(text1)
    answer2 = extract_structured_answer(text2)

    structured_sim = 0.0
    if answer1 and answer2:
        # Normalize answers for comparison
        norm1 = answer1.lower().strip()
        norm2 = answer2.lower().strip()

        # Check for exact or near-exact match
        if norm1 == norm2:
            structured_sim = 1.0
        else:
            # Try extracting numbers from structured answers
            nums_in_answer1 = extract_numerical_values(answer1)
            nums_in_answer2 = extract_numerical_values(answer2)

            # If both answers are primarily numerical, compare numbers
            if nums_in_answer1 and nums_in_answer2:
                set1 = set(nums_in_answer1)
                set2 = set(nums_in_answer2)
                if set1 & set2:  # Any overlap
                    # Strong match if key numbers align
                    structured_sim = len(set1 & set2) / len(set1 | set2)
                    # Boost if all numbers match
                    if set1 == set2:
                        structured_sim = 1.0

            # Fall back to word overlap if not primarily numerical
            if structured_sim == 0.0:
                # Remove common filler words before comparing
                stopwords = {'the', 'is', 'a', 'an', 'it', 'this', 'that', 'equals', 'answer'}
                words1 = set(w for w in norm1.split() if w not in stopwords and len(w) > 1)
                words2 = set(w for w in norm2.split() if w not in stopwords and len(w) > 1)
                if words1 and words2:
                    structured_sim = len(words1 & words2) / len(words1 | words2)

    # Strategy 2: Compare numerical values (weight: 0.3)
    nums1 = extract_numerical_values(text1)
    nums2 = extract_numerical_values(text2)

    numerical_sim = 0.0
    if nums1 and nums2:
        # Check if key numbers match
        nums1_set = set(nums1)
        nums2_set = set(nums2)
        if nums1_set & nums2_set:  # Any overlap
            # Calculate Jaccard similarity of number sets
            numerical_sim = len(nums1_set & nums2_set) / len(nums1_set | nums2_set)

    # Strategy 3: Semantic text similarity (weight: 0.2)
    # Use enhanced word comparison with stopword filtering
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
                 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}

    words1 = set(w.lower() for claim in claims1 for w in claim.split()
                 if w.lower() not in stopwords and len(w) > 2)
    words2 = set(w.lower() for claim in claims2 for w in claim.split()
                 if w.lower() not in stopwords and len(w) > 2)

    semantic_sim = 0.0
    if words1 and words2:
        semantic_sim = len(words1 & words2) / len(words1 | words2)

    # Weighted combination with boost for strong matches
    weights = {
        'structured': 0.6,  # Increased from 0.5
        'numerical': 0.3,
        'semantic': 0.1,    # Reduced from 0.2
    }

    # Calculate weighted score
    total_weight = 0.0
    weighted_sum = 0.0

    # Structured answer comparison (highest priority)
    if answer1 and answer2:
        weighted_sum += structured_sim * weights['structured']
        total_weight += weights['structured']

        # Boost: If both have numbers and they match, increase confidence
        if nums1 and nums2 and nums1_set & nums2_set:
            weighted_sum += numerical_sim * weights['numerical']
            total_weight += weights['numerical']
    elif nums1 and nums2:
        # No structured answers, but we have numbers - prioritize numerical
        weighted_sum += numerical_sim * 0.7  # High weight for numerical-only comparison
        total_weight += 0.7

    # Always include semantic similarity (but with lower weight)
    weighted_sum += semantic_sim * weights['semantic']
    total_weight += weights['semantic']

    if total_weight == 0.0:
        return 0.0

    final_similarity = weighted_sum / total_weight

    # Boost for exact numerical matches
    if nums1 and nums2 and numerical_sim >= 0.8:
        # If numbers strongly agree, boost overall similarity
        final_similarity = min(1.0, final_similarity * 1.2)

    return final_similarity


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
    "consensus_threshold": 0.7,  # Lowered from 0.8 to better handle paraphrased answers
    "timeout_seconds": 60,
    "enable_role_rotation": True,
    "trace_verbosity": "full",
    "retry_on_error": True,
    "max_retries": 3,
}
