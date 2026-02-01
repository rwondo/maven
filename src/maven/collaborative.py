"""Collaborative reasoning protocol for MAVEN.

Instead of adversarial debate or verification, models work together
to build reasoning step-by-step, each contributing to the final solution.
"""

import logging
from typing import Any, Dict, List, Optional

from maven.consensus import VerificationResult, TraceStep
from maven.models import ModelInterface, create_model
from maven.tools import extract_tool_calls, execute_tool_calls, default_registry
from maven.utils import generate_trace_id, get_timestamp, merge_configs, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


class CollaborativeOrchestrator:
    """Collaborative reasoning orchestrator.

    Instead of debate or verification, models work together:
    1. Model 1: Initial analysis and reasoning
    2. Model 2: Extends and refines Model 1's work
    3. Model 3: Synthesizes and finalizes

    Each model builds on the previous, creating a collaborative
    chain of reasoning.
    """

    def __init__(
        self,
        models: List[str],
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize collaborative orchestrator.

        Args:
            models: List of model identifiers (minimum 2 required).
            config: Optional configuration dictionary.

        Raises:
            ValueError: If fewer than 2 models provided.
        """
        if len(models) < 2:
            raise ValueError("At least 2 models required for collaboration")

        self.model_ids = models
        self.config = merge_configs(DEFAULT_CONFIG, config)
        self._models: Dict[str, ModelInterface] = {}
        self._trace: List[TraceStep] = []

        logger.info(f"Initialized CollaborativeOrchestrator with {len(models)} models")

    def _get_model(self, model_id: str) -> ModelInterface:
        """Get or create model instance."""
        if model_id not in self._models:
            self._models[model_id] = create_model(model_id)
        return self._models[model_id]

    def _generate_with_tools(
        self,
        model_id: str,
        prompt: str,
        role: str,
    ) -> str:
        """Generate response and execute any tool calls."""
        model = self._get_model(model_id)

        try:
            content = model.generate(prompt, role)
        except Exception as e:
            logger.error(f"Model {model_id} failed: {e}")
            content = f"Error: {e}"

        # Check for tool calls
        tool_calls = extract_tool_calls(content)
        if tool_calls:
            logger.info(f"Model {model_id} requested {len(tool_calls)} tool(s)")
            tool_results = execute_tool_calls(tool_calls, default_registry)
            logger.debug(f"Tool results: {tool_results}")
            content = f"{content}\n\n[TOOL RESULTS]\n{tool_results}"

        return content

    def reason(self, query: str) -> VerificationResult:
        """Run collaborative reasoning on a query.

        Args:
            query: The question to reason about.

        Returns:
            VerificationResult with collaborative answer.
        """
        trace_id = generate_trace_id()
        logger.info(f"Starting collaborative reasoning {trace_id}")

        self._trace = []

        # Collaborative prompts
        ANALYZER_PROMPT = f"""You are the first of a team working together to answer a question.

Your role: Analyze the problem and start reasoning toward a solution.

TOOLS AVAILABLE:
- calculator: For precise calculations
  Example: USE_TOOL: calculator
           EXPRESSION: 15 + 27
- wikipedia: For factual lookups
  Example: USE_TOOL: wikipedia
           QUERY: topic

Guidelines:
- Break down the problem step-by-step
- Use tools when helpful
- Show your reasoning clearly
- Don't rush to a final answer - focus on analysis

Question: {query}

Provide your initial analysis and reasoning:"""

        EXTENDER_PROMPT = """You are the second teammate building on previous work.

PREVIOUS WORK:
{previous_work}

Your role: Extend and refine the reasoning above.

TOOLS AVAILABLE:
- calculator: USE_TOOL: calculator / EXPRESSION: ...
- wikipedia: USE_TOOL: wikipedia / QUERY: ...

Guidelines:
- Build on what the first teammate started
- Add calculations or verifications using tools
- Identify any gaps and fill them
- Extend the reasoning toward a complete solution

Continue the reasoning:"""

        SYNTHESIZER_PROMPT = """You are the final teammate completing the solution.

PREVIOUS WORK:
{previous_work}

Your role: Synthesize the work above into a final answer.

TOOLS AVAILABLE:
- calculator: USE_TOOL: calculator / EXPRESSION: ...

Guidelines:
- Review all the reasoning so far
- Complete any remaining steps
- Provide a clear, final answer
- Use tools to verify your final answer if helpful

Format your response as:
FINAL_ANSWER: [Clear, direct answer to the original question]
REASONING: [Brief summary of how we arrived at this answer]
CONFIDENCE: [High/Medium/Low]

Complete the solution:"""

        # Step 1: Analyzer
        logger.info("Step 1/3: Initial analysis")
        analyzer_id = self.model_ids[0]
        analysis = self._generate_with_tools(
            analyzer_id,
            ANALYZER_PROMPT,
            "analyzer"
        )

        self._trace.append(TraceStep(
            iteration=1,
            role="analyzer",
            model=analyzer_id,
            content=analysis,
        ))

        # Step 2: Extender (if we have at least 3 models)
        if len(self.model_ids) >= 3:
            logger.info("Step 2/3: Extending reasoning")
            extender_id = self.model_ids[1]
            extender_prompt = EXTENDER_PROMPT.format(previous_work=analysis)

            extension = self._generate_with_tools(
                extender_id,
                extender_prompt,
                "extender"
            )

            self._trace.append(TraceStep(
                iteration=2,
                role="extender",
                model=extender_id,
                content=extension,
            ))

            previous_work = f"{analysis}\n\n---\n\n{extension}"
        else:
            previous_work = analysis

        # Step 3: Synthesizer
        logger.info("Step 3/3: Synthesizing final answer")
        synthesizer_id = self.model_ids[-1]
        synthesizer_prompt = SYNTHESIZER_PROMPT.format(previous_work=previous_work)

        synthesis = self._generate_with_tools(
            synthesizer_id,
            synthesizer_prompt,
            "synthesizer"
        )

        self._trace.append(TraceStep(
            iteration=3,
            role="synthesizer",
            model=synthesizer_id,
            content=synthesis,
        ))

        # Extract final answer
        final_answer = synthesis
        confidence = 60.0  # Default

        # Try to extract structured answer
        if "FINAL_ANSWER:" in synthesis:
            parts = synthesis.split("FINAL_ANSWER:", 1)
            if len(parts) > 1:
                answer_line = parts[1].split("\n")[0].strip()
                if answer_line:
                    final_answer = answer_line

        # Extract confidence
        synthesis_upper = synthesis.upper()
        if "CONFIDENCE: HIGH" in synthesis_upper:
            confidence = 85.0
        elif "CONFIDENCE: MEDIUM" in synthesis_upper:
            confidence = 60.0
        elif "CONFIDENCE: LOW" in synthesis_upper:
            confidence = 35.0

        logger.info(f"Collaborative reasoning complete (confidence: {confidence:.1f}%)")

        return VerificationResult(
            verdict="COLLABORATIVE",
            answer=final_answer,
            errors=[],
            confidence=confidence,
            trace=self._trace,
            metadata={
                "trace_id": trace_id,
                "query": query,
                "models": self.model_ids,
                "protocol": "collaborative",
                "completed_at": get_timestamp(),
            },
        )

    def get_trace(self) -> List[TraceStep]:
        """Get the reasoning trace from the last run."""
        return self._trace.copy()
