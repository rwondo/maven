"""Hallucination detection system for MAVEN.

For high-stakes domains (law, medicine), detecting when AI is hallucinating
is critical. This system uses multiple models to flag suspicious answers.

Key features:
- Consistency checking across models
- Citation/fact verification
- Confidence estimation
- Risk scoring for different types of hallucinations
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from maven.consensus import TraceStep, VerificationResult
from maven.models import ModelInterface, create_model
from maven.mcp_integration import MCPServerRegistry, create_mcp_server
from maven.utils import generate_trace_id, get_timestamp, merge_configs, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class HallucinationReport:
    """Report on potential hallucinations in a response."""

    # Overall risk assessment
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    confidence_score: float  # 0-100, higher = more confident answer is accurate

    # Specific hallucination flags
    flags: List[str]  # Specific issues detected
    consistency_score: float  # How well models agree (0-100)

    # Detailed checks
    fact_checks: List[Dict[str, Any]]  # Results from fact verification
    citation_checks: List[Dict[str, Any]]  # Results from citation verification
    logic_checks: List[Dict[str, Any]]  # Results from logical consistency checks

    # Supporting evidence
    model_responses: List[str]  # What each model said
    disagreements: List[str]  # Where models disagreed

    # Trace and metadata
    trace: List[TraceStep]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "risk_level": self.risk_level,
            "confidence_score": self.confidence_score,
            "flags": self.flags,
            "consistency_score": self.consistency_score,
            "fact_checks": self.fact_checks,
            "citation_checks": self.citation_checks,
            "logic_checks": self.logic_checks,
            "model_responses": self.model_responses,
            "disagreements": self.disagreements,
            "metadata": self.metadata
        }


class HallucinationDetector:
    """Multi-model hallucination detection system.

    Uses multiple models to verify a response and flag potential hallucinations.
    Particularly valuable for high-stakes domains like law and medicine.
    """

    def __init__(
        self,
        models: List[str],
        config: Optional[Dict[str, Any]] = None,
        mcp_servers: Optional[List[Dict[str, Any]]] = None,
    ):
        """Initialize hallucination detector.

        Args:
            models: List of model identifiers (minimum 2 required).
            config: Optional configuration dictionary.
            mcp_servers: Optional list of MCP server configurations.
                Each server config should have:
                - name: Server name
                - type: "stdio" or "http"
                - Additional fields based on type (command, url, api_key, etc.)

        Example:
            detector = HallucinationDetector(
                models=["llama", "qwen", "mixtral"],
                mcp_servers=[
                    {
                        "name": "wikipedia",
                        "type": "stdio",
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-wikipedia"]
                    }
                ]
            )
        """
        if len(models) < 2:
            raise ValueError("At least 2 models required for hallucination detection")

        self.model_ids = models
        self.config = merge_configs(DEFAULT_CONFIG, config)
        self._models: Dict[str, ModelInterface] = {}
        self._trace: List[TraceStep] = []

        # Initialize MCP server registry
        self.mcp_registry = MCPServerRegistry()
        if mcp_servers:
            for server_config in mcp_servers:
                server_type = server_config.get("type", "stdio")
                server_name = server_config.get("name", f"server_{len(self.mcp_registry.servers)}")
                server = create_mcp_server(server_type, server_name, server_config)
                if server:
                    self.mcp_registry.register_server(server)

        logger.info(f"Initialized HallucinationDetector with {len(models)} models and {len(self.mcp_registry.servers)} MCP servers")

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
        """Generate response and execute any tool calls via MCP servers."""
        model = self._get_model(model_id)

        try:
            content = model.generate(prompt, role)
        except Exception as e:
            logger.error(f"Model {model_id} failed: {e}")
            content = f"Error: {e}"

        # Execute tool calls if MCP servers are configured
        if self.mcp_registry.servers:
            tool_calls = self._extract_mcp_tool_calls(content)
            if tool_calls:
                logger.info(f"Model {model_id} requested {len(tool_calls)} MCP tool(s)")
                tool_results = self._execute_mcp_tools(tool_calls)
                content = f"{content}\n\n[TOOL RESULTS]\n{tool_results}"

        return content

    def _extract_mcp_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """Extract MCP tool calls from model output.

        Looks for patterns like:
        USE_TOOL: wikipedia:search
        QUERY: Albert Einstein

        Or:
        USE_TOOL: pubmed:search_papers
        QUERY: aspirin cardiovascular
        """
        import re

        tool_calls = []
        tool_matches = re.finditer(r'USE_TOOL:\s*([^\n]+)', text, re.IGNORECASE)

        for match in tool_matches:
            tool_name = match.group(1).strip()
            start_pos = match.end()

            # Extract parameters until next tool call or end
            next_match = re.search(r'USE_TOOL:', text[start_pos:], re.IGNORECASE)
            if next_match:
                params_text = text[start_pos:start_pos + next_match.start()]
            else:
                params_text = text[start_pos:]

            # Extract parameter pairs
            params = {}
            param_matches = re.finditer(r'(\w+):\s*([^\n]+)', params_text)
            for param_match in param_matches:
                key = param_match.group(1).lower()
                value = param_match.group(2).strip()
                params[key] = value

            tool_calls.append({
                "tool": tool_name,
                "params": params
            })

        return tool_calls

    def _execute_mcp_tools(self, tool_calls: List[Dict[str, Any]]) -> str:
        """Execute tool calls via MCP servers."""
        if not tool_calls:
            return ""

        results = []
        for call in tool_calls:
            tool_name = call["tool"]
            params = call["params"]

            try:
                result = self.mcp_registry.execute_tool(tool_name, params)
                results.append(f"[{tool_name}] {result}")
            except Exception as e:
                results.append(f"[{tool_name}] Error: {str(e)}")

        return "\n".join(results)

    def detect(
        self,
        query: str,
        answer: str,
        domain: Optional[str] = None,
    ) -> HallucinationReport:
        """Detect potential hallucinations in an answer.

        Args:
            query: The original question/query
            answer: The answer to verify for hallucinations
            domain: Optional domain context (e.g., "medical", "legal")

        Returns:
            HallucinationReport with risk assessment and detailed checks
        """
        trace_id = generate_trace_id()
        logger.info(f"Starting hallucination detection {trace_id}")

        self._trace = []

        # Verification prompts
        CONSISTENCY_PROMPT = f"""You are verifying an AI-generated answer for potential hallucinations.

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

        FACT_CHECK_PROMPT = f"""You are fact-checking an AI answer for a critical application.

Original Question: {query}

Answer to Check:
{answer}

TOOLS AVAILABLE:
- wikipedia: Verify factual claims
  Example: USE_TOOL: wikipedia / QUERY: topic
- calculator: Verify calculations
  Example: USE_TOOL: calculator / EXPRESSION: 2+2

Your task: Verify specific factual claims in this answer.

Use tools to check any verifiable facts. Report:
FACTS_VERIFIED: [List what you checked]
FACTS_FAILED: [List any facts that couldn't be verified or were wrong]
CONFIDENCE: [High/Medium/Low]"""

        CITATION_PROMPT = f"""You are checking an answer for fabricated or misleading citations/sources.

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

        # Run verification checks in parallel
        model_responses = []
        fact_checks = []
        citation_checks = []
        consistency_checks = []

        # Consistency check (all models)
        for i, model_id in enumerate(self.model_ids):
            logger.info(f"Running consistency check {i+1}/{len(self.model_ids)}")

            response = self._generate_with_tools(
                model_id,
                CONSISTENCY_PROMPT,
                f"consistency_checker_{i}"
            )

            self._trace.append(TraceStep(
                iteration=1,
                role="consistency_checker",
                model=model_id,
                content=response,
            ))

            model_responses.append(response)

            # Parse verdict
            verdict = "QUESTIONABLE"  # Default
            if "VERDICT: RELIABLE" in response.upper():
                verdict = "RELIABLE"
            elif "VERDICT: UNRELIABLE" in response.upper():
                verdict = "UNRELIABLE"

            consistency_checks.append({
                "model": model_id,
                "verdict": verdict,
                "response": response[:300]
            })

        # Fact check (use first model with tools)
        logger.info("Running fact check")
        fact_response = self._generate_with_tools(
            self.model_ids[0],
            FACT_CHECK_PROMPT,
            "fact_checker"
        )

        self._trace.append(TraceStep(
            iteration=2,
            role="fact_checker",
            model=self.model_ids[0],
            content=fact_response,
        ))

        fact_checks.append({
            "model": self.model_ids[0],
            "response": fact_response[:500],
            "tools_used": "[TOOL RESULTS]" in fact_response
        })

        # Citation check (use second model)
        logger.info("Running citation check")
        citation_response = self._generate_with_tools(
            self.model_ids[1] if len(self.model_ids) > 1 else self.model_ids[0],
            CITATION_PROMPT,
            "citation_checker"
        )

        self._trace.append(TraceStep(
            iteration=3,
            role="citation_checker",
            model=self.model_ids[1] if len(self.model_ids) > 1 else self.model_ids[0],
            content=citation_response,
        ))

        citation_checks.append({
            "model": self.model_ids[1] if len(self.model_ids) > 1 else self.model_ids[0],
            "response": citation_response[:500]
        })

        # Analyze results
        flags = []
        disagreements = []

        # Check consistency across models
        verdicts = [c["verdict"] for c in consistency_checks]
        reliable_count = verdicts.count("RELIABLE")
        unreliable_count = verdicts.count("UNRELIABLE")

        if unreliable_count > 0:
            flags.append(f"{unreliable_count}/{len(verdicts)} models flagged as UNRELIABLE")

        if len(set(verdicts)) > 1:
            disagreements.append(f"Models disagree on reliability: {verdicts}")

        # Check fact verification
        if "FACTS_FAILED" in fact_response and "None" not in fact_response.split("FACTS_FAILED")[1][:100]:
            flags.append("Fact verification failed for some claims")

        # Check citations
        if "SUSPICIOUS" in citation_response and "None" not in citation_response.split("SUSPICIOUS")[1][:100]:
            flags.append("Suspicious or unsourced citations detected")

        # Calculate scores
        consistency_score = (reliable_count / len(verdicts)) * 100
        confidence_score = consistency_score  # Base on consistency for now

        # Determine risk level with improved logic
        # Key principle: Be conservative - prioritize catching hallucinations over avoiding FPs
        #
        # Analysis from TruthfulQA benchmark showed:
        # - Old MEDIUM threshold: 93.6% of answers were actually untruthful
        # - Old LOW threshold: 93.3% of answers were actually untruthful
        # This means we need to be much more aggressive with flagging

        # CRITICAL: 2+ models said UNRELIABLE, or 2+ flags
        if unreliable_count >= 2 or len(flags) >= 2:
            risk_level = "CRITICAL"
        # HIGH: Any model said UNRELIABLE, or any flags present
        elif unreliable_count > 0 or len(flags) > 0:
            risk_level = "HIGH"
        # MEDIUM: Low consistency (models disagree) even if no explicit UNRELIABLE
        elif confidence_score < 75:
            risk_level = "MEDIUM"
        # LOW: High consistency, all models agree it's RELIABLE, no flags
        else:
            risk_level = "LOW"

        logger.info(f"Detection complete: {risk_level} risk ({confidence_score:.1f}% confidence)")

        return HallucinationReport(
            risk_level=risk_level,
            confidence_score=confidence_score,
            flags=flags,
            consistency_score=consistency_score,
            fact_checks=fact_checks,
            citation_checks=citation_checks,
            logic_checks=[],  # Placeholder for future logic checking
            model_responses=model_responses,
            disagreements=disagreements,
            trace=self._trace,
            metadata={
                "trace_id": trace_id,
                "query": query,
                "answer": answer[:500],
                "domain": domain,
                "models": self.model_ids,
                "completed_at": get_timestamp(),
            }
        )

    def get_trace(self) -> List[TraceStep]:
        """Get the detection trace from the last run."""
        return self._trace.copy()
