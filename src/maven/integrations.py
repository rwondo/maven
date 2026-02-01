"""
LangChain and LlamaIndex Integration for MAVEN.

Provides seamless integration with popular LLM frameworks for hallucination detection.

LangChain Integration:
    - MAVENCallbackHandler: Automatically detect hallucinations in chain outputs
    - MAVENChain: Wrapper chain that adds hallucination detection
    - MAVENRetriever: Retriever with built-in hallucination checks

LlamaIndex Integration:
    - MAVENQueryEngine: Query engine with hallucination detection
    - MAVENResponseEvaluator: Evaluate LlamaIndex responses for hallucinations
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from maven.hallucination_detector import HallucinationDetector, HallucinationReport

logger = logging.getLogger(__name__)


# ============================================================================
# LangChain Integration
# ============================================================================

@dataclass
class HallucinationCheckResult:
    """Result of hallucination check for framework integrations."""
    
    is_hallucination: bool
    risk_level: str
    confidence_score: float
    flags: List[str]
    original_output: str
    report: Optional[HallucinationReport] = None
    
    def __bool__(self) -> bool:
        """Returns True if NOT a hallucination (safe to use)."""
        return not self.is_hallucination


class MAVENCallbackHandler:
    """LangChain callback handler for automatic hallucination detection.

    Monitors LLM outputs and flags potential hallucinations in real-time.

    Example:
        from langchain.llms import OpenAI
        from maven.integrations import MAVENCallbackHandler

        handler = MAVENCallbackHandler(
            models=["together/llama-3.1-8b", "together/qwen-2.5-7b"],
            risk_threshold=["CRITICAL", "HIGH"]
        )

        llm = OpenAI(callbacks=[handler])
        result = llm.invoke("What is the capital of France?")

        # Check if any hallucinations were detected
        if handler.last_detection and handler.last_detection.is_hallucination:
            print("Warning: Possible hallucination detected!")
    """

    def __init__(
        self,
        models: List[str],
        risk_threshold: Optional[List[str]] = None,
        domain: Optional[str] = None,
        auto_block: bool = False,
    ):
        """Initialize callback handler.

        Args:
            models: List of model identifiers for detection.
            risk_threshold: Risk levels to flag (default: CRITICAL, HIGH).
            domain: Optional domain context.
            auto_block: If True, raise exception on hallucination.
        """
        self.detector = HallucinationDetector(models=models)
        self.risk_threshold = risk_threshold or ["CRITICAL", "HIGH"]
        self.domain = domain
        self.auto_block = auto_block
        self.last_detection: Optional[HallucinationCheckResult] = None
        self._pending_input: Optional[str] = None

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """Called when LLM starts generating."""
        if prompts:
            self._pending_input = prompts[0]

    def on_llm_end(self, response: Any, **kwargs) -> None:
        """Called when LLM finishes generating."""
        try:
            # Extract output text
            if hasattr(response, 'generations') and response.generations:
                output = response.generations[0][0].text
            elif hasattr(response, 'content'):
                output = response.content
            else:
                output = str(response)

            # Run hallucination detection
            query = self._pending_input or "Unknown query"
            report = self.detector.detect(query, output, self.domain)

            is_hallucination = report.risk_level in self.risk_threshold
            self.last_detection = HallucinationCheckResult(
                is_hallucination=is_hallucination,
                risk_level=report.risk_level,
                confidence_score=report.confidence_score,
                flags=report.flags,
                original_output=output,
                report=report,
            )

            if is_hallucination:
                logger.warning(f"Hallucination detected: {report.risk_level} risk")
                if self.auto_block:
                    raise HallucinationError(
                        f"Hallucination detected with {report.risk_level} risk level",
                        report=report
                    )

        except Exception as e:
            if isinstance(e, HallucinationError):
                raise
            logger.error(f"Error in hallucination detection callback: {e}")

    def on_llm_error(self, error: Exception, **kwargs) -> None:
        """Called when LLM errors."""
        self._pending_input = None

    def get_last_report(self) -> Optional[HallucinationReport]:
        """Get the full report from last detection."""
        if self.last_detection:
            return self.last_detection.report
        return None


class HallucinationError(Exception):
    """Raised when a hallucination is detected with auto_block enabled."""

    def __init__(self, message: str, report: Optional[HallucinationReport] = None):
        super().__init__(message)
        self.report = report


class MAVENChain:
    """LangChain-compatible chain wrapper with built-in hallucination detection.

    Wraps any LangChain chain and adds hallucination detection to outputs.

    Example:
        from langchain.chains import LLMChain
        from langchain.llms import OpenAI
        from maven.integrations import MAVENChain

        base_chain = LLMChain(llm=OpenAI(), prompt=my_prompt)
        safe_chain = MAVENChain(
            chain=base_chain,
            models=["together/llama-3.1-8b", "together/qwen-2.5-7b"]
        )

        result = safe_chain.invoke({"input": "What is aspirin?"})
        print(f"Output: {result['output']}")
        print(f"Is safe: {result['is_safe']}")
        print(f"Risk level: {result['risk_level']}")
    """

    def __init__(
        self,
        chain: Any,
        models: List[str],
        risk_threshold: Optional[List[str]] = None,
        domain: Optional[str] = None,
        include_report: bool = False,
    ):
        """Initialize wrapped chain.

        Args:
            chain: The LangChain chain to wrap.
            models: Model identifiers for hallucination detection.
            risk_threshold: Risk levels to flag as unsafe.
            domain: Optional domain context.
            include_report: Include full report in output.
        """
        self.chain = chain
        self.detector = HallucinationDetector(models=models)
        self.risk_threshold = risk_threshold or ["CRITICAL", "HIGH"]
        self.domain = domain
        self.include_report = include_report

    def invoke(self, inputs: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Run chain with hallucination detection.

        Args:
            inputs: Input dictionary for the chain.
            **kwargs: Additional arguments.

        Returns:
            Dict with original output plus hallucination check results.
        """
        # Run the underlying chain
        result = self.chain.invoke(inputs, **kwargs)

        # Extract output
        if isinstance(result, dict):
            output = result.get("output") or result.get("text") or str(result)
        else:
            output = str(result)

        # Extract query
        query = inputs.get("input") or inputs.get("query") or inputs.get("question") or str(inputs)

        # Run hallucination detection
        report = self.detector.detect(query, output, self.domain)
        is_safe = report.risk_level not in self.risk_threshold

        # Build result
        output_dict = {
            "output": output,
            "is_safe": is_safe,
            "risk_level": report.risk_level,
            "confidence_score": report.confidence_score,
            "flags": report.flags,
        }

        if self.include_report:
            output_dict["report"] = report

        return output_dict

    def __call__(self, inputs: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Alias for invoke()."""
        return self.invoke(inputs, **kwargs)


class MAVENRetriever:
    """Retriever wrapper that checks retrieved documents for hallucinations.

    Useful for RAG pipelines to verify retrieved content before use.

    Example:
        from langchain.retrievers import WikipediaRetriever
        from maven.integrations import MAVENRetriever

        base_retriever = WikipediaRetriever()
        safe_retriever = MAVENRetriever(
            retriever=base_retriever,
            models=["together/llama-3.1-8b", "together/qwen-2.5-7b"]
        )

        # Get verified documents
        docs = safe_retriever.get_relevant_documents("What is quantum computing?")
    """

    def __init__(
        self,
        retriever: Any,
        models: List[str],
        check_content: bool = True,
        domain: Optional[str] = None,
    ):
        """Initialize retriever wrapper.

        Args:
            retriever: The base retriever to wrap.
            models: Model identifiers for detection.
            check_content: Whether to check document content.
            domain: Optional domain context.
        """
        self.retriever = retriever
        self.detector = HallucinationDetector(models=models)
        self.check_content = check_content
        self.domain = domain

    def get_relevant_documents(self, query: str) -> List[Any]:
        """Retrieve and verify documents.

        Args:
            query: The search query.

        Returns:
            List of documents with verification metadata.
        """
        docs = self.retriever.get_relevant_documents(query)

        if not self.check_content:
            return docs

        # Check each document
        verified_docs = []
        for doc in docs:
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)

            report = self.detector.detect(query, content, self.domain)

            # Add verification metadata
            if hasattr(doc, 'metadata'):
                doc.metadata['maven_risk_level'] = report.risk_level
                doc.metadata['maven_confidence'] = report.confidence_score
                doc.metadata['maven_flags'] = report.flags

            verified_docs.append(doc)

        return verified_docs


# ============================================================================
# LlamaIndex Integration
# ============================================================================

class MAVENQueryEngine:
    """LlamaIndex query engine wrapper with hallucination detection.

    Wraps any LlamaIndex query engine and validates responses.

    Example:
        from llama_index import VectorStoreIndex
        from maven.integrations import MAVENQueryEngine

        index = VectorStoreIndex.from_documents(documents)
        base_engine = index.as_query_engine()

        safe_engine = MAVENQueryEngine(
            query_engine=base_engine,
            models=["together/llama-3.1-8b", "together/qwen-2.5-7b"]
        )

        response = safe_engine.query("What is machine learning?")
        print(f"Answer: {response.response}")
        print(f"Is verified: {response.is_verified}")
    """

    def __init__(
        self,
        query_engine: Any,
        models: List[str],
        risk_threshold: Optional[List[str]] = None,
        domain: Optional[str] = None,
        block_on_hallucination: bool = False,
    ):
        """Initialize query engine wrapper.

        Args:
            query_engine: The LlamaIndex query engine to wrap.
            models: Model identifiers for detection.
            risk_threshold: Risk levels to flag.
            domain: Optional domain context.
            block_on_hallucination: If True, raise on detection.
        """
        self.query_engine = query_engine
        self.detector = HallucinationDetector(models=models)
        self.risk_threshold = risk_threshold or ["CRITICAL", "HIGH"]
        self.domain = domain
        self.block_on_hallucination = block_on_hallucination

    def query(self, query_str: str) -> "MAVENResponse":
        """Query with hallucination detection.

        Args:
            query_str: The query string.

        Returns:
            MAVENResponse with verification results.
        """
        # Run the query
        response = self.query_engine.query(query_str)

        # Extract response text
        response_text = str(response)

        # Run hallucination detection
        report = self.detector.detect(query_str, response_text, self.domain)
        is_verified = report.risk_level not in self.risk_threshold

        if not is_verified and self.block_on_hallucination:
            raise HallucinationError(
                f"Hallucination detected: {report.risk_level}",
                report=report
            )

        return MAVENResponse(
            response=response_text,
            source_response=response,
            is_verified=is_verified,
            risk_level=report.risk_level,
            confidence_score=report.confidence_score,
            flags=report.flags,
            report=report,
        )


@dataclass
class MAVENResponse:
    """Response wrapper with hallucination verification results."""

    response: str
    source_response: Any
    is_verified: bool
    risk_level: str
    confidence_score: float
    flags: List[str]
    report: Optional[HallucinationReport] = None

    def __str__(self) -> str:
        return self.response

    def __bool__(self) -> bool:
        """Returns True if verified (safe to use)."""
        return self.is_verified


class MAVENResponseEvaluator:
    """Evaluate LlamaIndex responses for hallucinations.

    Standalone evaluator for post-hoc analysis of responses.

    Example:
        from maven.integrations import MAVENResponseEvaluator

        evaluator = MAVENResponseEvaluator(
            models=["together/llama-3.1-8b", "together/qwen-2.5-7b"]
        )

        # Evaluate a response
        result = evaluator.evaluate(
            query="What is the speed of light?",
            response="The speed of light is approximately 299,792 km/s"
        )

        if result.is_verified:
            print("Response verified!")
        else:
            print(f"Issues found: {result.flags}")
    """

    def __init__(
        self,
        models: List[str],
        domain: Optional[str] = None,
    ):
        """Initialize evaluator.

        Args:
            models: Model identifiers for detection.
            domain: Optional domain context.
        """
        self.detector = HallucinationDetector(models=models)
        self.domain = domain

    def evaluate(
        self,
        query: str,
        response: Union[str, Any],
        domain: Optional[str] = None,
    ) -> HallucinationCheckResult:
        """Evaluate a response for hallucinations.

        Args:
            query: The original query.
            response: The response to evaluate.
            domain: Optional domain override.

        Returns:
            HallucinationCheckResult with verification status.
        """
        response_text = str(response)
        check_domain = domain or self.domain

        report = self.detector.detect(query, response_text, check_domain)

        return HallucinationCheckResult(
            is_hallucination=report.risk_level in ["CRITICAL", "HIGH"],
            risk_level=report.risk_level,
            confidence_score=report.confidence_score,
            flags=report.flags,
            original_output=response_text,
            report=report,
        )

    def evaluate_batch(
        self,
        items: List[Dict[str, str]],
        domain: Optional[str] = None,
    ) -> List[HallucinationCheckResult]:
        """Evaluate multiple responses.

        Args:
            items: List of dicts with 'query' and 'response' keys.
            domain: Optional domain context.

        Returns:
            List of HallucinationCheckResult.
        """
        results = []
        for item in items:
            result = self.evaluate(
                query=item.get("query", ""),
                response=item.get("response", ""),
                domain=domain,
            )
            results.append(result)
        return results


# ============================================================================
# Convenience Functions
# ============================================================================

def create_langchain_callback(
    models: List[str],
    **kwargs
) -> MAVENCallbackHandler:
    """Create a LangChain callback handler.

    Args:
        models: Model identifiers for detection.
        **kwargs: Additional arguments for MAVENCallbackHandler.

    Returns:
        Configured callback handler.
    """
    return MAVENCallbackHandler(models=models, **kwargs)


def wrap_langchain_chain(
    chain: Any,
    models: List[str],
    **kwargs
) -> MAVENChain:
    """Wrap a LangChain chain with hallucination detection.

    Args:
        chain: The chain to wrap.
        models: Model identifiers for detection.
        **kwargs: Additional arguments for MAVENChain.

    Returns:
        Wrapped chain with detection.
    """
    return MAVENChain(chain=chain, models=models, **kwargs)


def wrap_llamaindex_engine(
    query_engine: Any,
    models: List[str],
    **kwargs
) -> MAVENQueryEngine:
    """Wrap a LlamaIndex query engine with hallucination detection.

    Args:
        query_engine: The query engine to wrap.
        models: Model identifiers for detection.
        **kwargs: Additional arguments for MAVENQueryEngine.

    Returns:
        Wrapped query engine with detection.
    """
    return MAVENQueryEngine(query_engine=query_engine, models=models, **kwargs)
