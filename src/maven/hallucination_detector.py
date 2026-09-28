"""Multi-model hallucination checks.

One detection run sends the question and the answer to reviewer models:

1. Reliability check: every model is asked whether the answer is RELIABLE,
   QUESTIONABLE or UNRELIABLE.
2. Fact check: the first model lists claims that are wrong or unverifiable.
3. Citation check: the second model lists sources that look made up.

The replies are plain text. They are parsed for their labelled fields and
turned into a risk level by the fixed rules in calculate_risk().
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from maven.models import ModelConfigError, ModelInterface, create_model
from maven.utils import generate_trace_id, get_timestamp

logger = logging.getLogger(__name__)

# Risk levels treated as "likely hallucination" by is_hallucination().
DEFAULT_THRESHOLD = ("MEDIUM", "HIGH", "CRITICAL")

RELIABILITY_PROMPT = """You are verifying an AI-generated answer for potential hallucinations.

CRITICAL: This is for a high-stakes domain. Flag ANY suspicious claims.

Original Question: {query}

Answer to Verify:
{answer}

Your task: Check if this answer is consistent and factually sound.

Look for:
- Fabricated facts or citations
- Logical inconsistencies
- Unsupported claims
- Vague or hedging language that might hide uncertainty

Respond with:
VERDICT: [RELIABLE / QUESTIONABLE / UNRELIABLE]
ISSUES: [List specific problems, or "None" if answer seems sound]
CONFIDENCE: [High/Medium/Low in your assessment]"""

FACT_CHECK_PROMPT = """You are fact-checking an AI answer for a critical application.

Original Question: {query}

Answer to Check:
{answer}

Your task: Verify specific factual claims in this answer.

Report:
FACTS_VERIFIED: [List what you checked]
FACTS_FAILED: [List any facts that couldn't be verified or were wrong]
CONFIDENCE: [High/Medium/Low]"""

CITATION_PROMPT = """You are checking an answer for fabricated or misleading citations/sources.

Original Question: {query}

Answer to Check:
{answer}

Look for:
- Citations or references that seem fabricated
- Vague references ("studies show", "experts say")
- Specific claims without sources
- Real-sounding but potentially fake case names/statutes

Report:
CITATIONS_FOUND: [List any citations/references mentioned]
SUSPICIOUS: [Flag any that seem fabricated or unsourced]
CONFIDENCE: [High/Medium/Low]"""

_VERDICT_RE = re.compile(
    # "VERDICT: RELIABLE", "Verdict: [unreliable]"; "RELIABLE / ..." is an echoed template.
    r"VERDICT\s*:\s*\[?\s*(UNRELIABLE|RELIABLE|QUESTIONABLE)\b(?!\s*/)",
    re.IGNORECASE,
)
_EMPTY_ANSWERS = {"", "none", "n/a", "na", "no", "nothing", "-"}


@dataclass
class TraceStep:
    """One model call made during a detection run."""

    role: str
    model: str
    content: str
    timestamp: str = field(default_factory=get_timestamp)
    error: Optional[str] = None  # set when the API call failed

    @property
    def summary(self) -> str:
        """First 100 characters of the model's reply."""
        max_len = 100
        if len(self.content) <= max_len:
            return self.content
        return self.content[: max_len - 3] + "..."


@dataclass
class HallucinationReport:
    """Result of one detection run."""

    risk_level: str  # "LOW", "MEDIUM", "HIGH" or "CRITICAL"
    reliable_share: float  # % of reviewer models that voted RELIABLE (a vote share, 0-100)
    flags: list[str]  # problems found; any flag means HIGH risk or worse
    verdicts: list[str]  # one reliability verdict per reviewer model, in model order
    fact_checks: list[dict[str, Any]]
    citation_checks: list[dict[str, Any]]
    model_responses: list[str]  # full reliability-check reply from each model
    disagreements: list[str]
    trace: list[TraceStep]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-friendly dict (the trace is left out)."""
        return {
            "risk_level": self.risk_level,
            "reliable_share": self.reliable_share,
            "flags": self.flags,
            "verdicts": self.verdicts,
            "fact_checks": self.fact_checks,
            "citation_checks": self.citation_checks,
            "model_responses": self.model_responses,
            "disagreements": self.disagreements,
            "metadata": self.metadata,
        }


def _strip_markdown(text: str) -> str:
    return re.sub(r"[*`#]", "", text)


def parse_verdict(text: str) -> str:
    """Read the VERDICT field of a reliability reply. Defaults to QUESTIONABLE."""
    match = _VERDICT_RE.search(_strip_markdown(text))
    return match.group(1).upper() if match else "QUESTIONABLE"


def has_reported_items(text: str, label: str) -> bool:
    """Return True if the model listed anything under `label` (e.g. FACTS_FAILED).

    The field runs until the next line that starts with an upper-case label.
    "None", "N/A", "No" and an empty field all count as nothing reported.
    """
    pattern = rf"(?i:{re.escape(label)})\s*:(.*?)(?=\n\s*[A-Z][A-Z_ ]{{2,}}:|\Z)"
    match = re.search(pattern, _strip_markdown(text), re.DOTALL)
    if not match:
        return False
    first_line = match.group(1).strip().strip("[]").strip().split("\n")[0].strip().lower()
    first_word = re.split(r"[\s.,;:!()-]+", first_line.strip("- "), maxsplit=1)[0]
    return first_line not in _EMPTY_ANSWERS and first_word not in {"none", "nothing", "n/a"}


def calculate_risk(
    verdicts: list[str], fact_response: str, citation_response: str, failed_calls: int = 0
) -> tuple[str, float, list[str], list[str]]:
    """Turn parsed replies into (risk_level, reliable_share, flags, disagreements).

    Rules, checked in order:
        CRITICAL  2+ models said UNRELIABLE, or 2+ flags
        HIGH      any flag (one UNRELIABLE vote or any failed API call counts as a flag)
        MEDIUM    fewer than 75% of models said RELIABLE
        LOW       otherwise
    """
    flags = []
    if failed_calls:
        total = len(verdicts) + 2
        flags.append(f"{failed_calls}/{total} model calls failed, so the check is incomplete")
    unreliable = verdicts.count("UNRELIABLE")
    if unreliable:
        flags.append(f"{unreliable}/{len(verdicts)} models rated the answer UNRELIABLE")
    if has_reported_items(fact_response, "FACTS_FAILED"):
        flags.append("Fact check found wrong or unverifiable claims")
    if has_reported_items(citation_response, "SUSPICIOUS"):
        flags.append("Citation check found suspicious or unsourced references")

    disagreements = []
    if len(set(verdicts)) > 1:
        disagreements.append(f"Models disagree on reliability: {', '.join(verdicts)}")

    reliable_share = verdicts.count("RELIABLE") / len(verdicts) * 100

    if unreliable >= 2 or len(flags) >= 2:
        risk_level = "CRITICAL"
    elif flags:
        risk_level = "HIGH"
    elif reliable_share < 75:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    return risk_level, reliable_share, flags, disagreements


def build_report(
    query: str,
    answer: str,
    reliability_steps: list[TraceStep],
    fact_step: TraceStep,
    citation_step: TraceStep,
    **extra_metadata: Any,
) -> HallucinationReport:
    """Assemble a report from the model calls of one run (shared by both detectors)."""
    steps = [*reliability_steps, fact_step, citation_step]
    verdicts = [parse_verdict(step.content) for step in reliability_steps]
    risk_level, reliable_share, flags, disagreements = calculate_risk(
        verdicts,
        fact_step.content,
        citation_step.content,
        failed_calls=sum(1 for step in steps if step.error),
    )
    logger.info(f"Detection complete: {risk_level} ({reliable_share:.0f}% reliable votes)")

    return HallucinationReport(
        risk_level=risk_level,
        reliable_share=reliable_share,
        flags=flags,
        verdicts=verdicts,
        fact_checks=[{"model": fact_step.model, "response": fact_step.content[:500]}],
        citation_checks=[{"model": citation_step.model, "response": citation_step.content[:500]}],
        model_responses=[step.content for step in reliability_steps],
        disagreements=disagreements,
        trace=steps,
        metadata={
            "trace_id": generate_trace_id(),
            "query": query,
            "answer": answer[:500],
            "models": [step.model for step in reliability_steps],
            "completed_at": get_timestamp(),
            **extra_metadata,
        },
    )


def error_report(query: str, error: Exception) -> HallucinationReport:
    """Report used by detect_batch() when one item fails completely."""
    return HallucinationReport(
        risk_level="HIGH",
        reliable_share=0.0,
        flags=[f"Detection error: {error}"],
        verdicts=[],
        fact_checks=[],
        citation_checks=[],
        model_responses=[],
        disagreements=[],
        trace=[],
        metadata={"error": str(error), "query": query},
    )


class HallucinationDetector:
    """Checks answers by asking several reviewer models, one call at a time.

    Example:
        detector = HallucinationDetector(models=["together/llama-3.1-8b", "gpt-4o"])
        report = detector.detect(query="...", answer="...")
    """

    def __init__(self, models: list[str], rate_limit_delay: float = 1.0):
        """Create a detector.

        Args:
            models: Reviewer model identifiers (at least 2). The first also runs the
                fact check and the second the citation check.
            rate_limit_delay: Minimum seconds between two API calls.
        """
        if len(models) < 2:
            raise ValueError("At least 2 models required for hallucination detection")

        self.model_ids = models
        self._models: dict[str, ModelInterface] = {}
        self._rate_limit_delay = rate_limit_delay
        self._last_call_time: float = 0

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_call_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_call_time = time.time()

    def _get_model(self, model_id: str) -> ModelInterface:
        if model_id not in self._models:
            self._models[model_id] = create_model(model_id)
        return self._models[model_id]

    def _call(self, model_id: str, prompt: str, role: str) -> TraceStep:
        """Run one model call. API errors are recorded on the step; setup errors raise."""
        self._rate_limit()
        try:
            content = self._get_model(model_id).generate(prompt, role)
        except ModelConfigError:
            raise
        except Exception as e:
            logger.error(f"Model {model_id} failed: {e}")
            return TraceStep(role=role, model=model_id, content=f"Error: {e}", error=str(e))
        return TraceStep(role=role, model=model_id, content=content)

    def detect(self, query: str, answer: str) -> HallucinationReport:
        """Check one answer. Makes len(models) + 2 API calls, one after another."""
        fields = {"query": query, "answer": answer}
        reliability_steps = [
            self._call(model_id, RELIABILITY_PROMPT.format(**fields), "reliability_check")
            for model_id in self.model_ids
        ]
        fact_step = self._call(self.model_ids[0], FACT_CHECK_PROMPT.format(**fields), "fact_check")
        citation_step = self._call(
            self.model_ids[1], CITATION_PROMPT.format(**fields), "citation_check"
        )
        return build_report(query, answer, reliability_steps, fact_step, citation_step)

    def detect_batch(
        self,
        items: list[dict[str, str]],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> list[HallucinationReport]:
        """Check several {"query": ..., "answer": ...} items in order."""
        results = []
        for i, item in enumerate(items):
            query = item.get("query", "")
            try:
                results.append(self.detect(query, item.get("answer", "")))
            except ModelConfigError:
                raise
            except Exception as e:
                logger.error(f"Error detecting item {i + 1}/{len(items)}: {e}")
                results.append(error_report(query, e))
            if progress_callback:
                progress_callback(i + 1, len(items))
        return results

    def is_hallucination(
        self, query: str, answer: str, threshold: Optional[list[str]] = None
    ) -> bool:
        """True if the risk level is in `threshold` (default: MEDIUM, HIGH, CRITICAL)."""
        levels = threshold if threshold is not None else DEFAULT_THRESHOLD
        return self.detect(query, answer).risk_level in levels
