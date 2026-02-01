"""MCP tool integration for MAVEN.

Provides external tools that models can use to:
- Calculate precise numerical answers
- Search for factual information
- Verify claims
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Tool(ABC):
    """Abstract base class for tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool with given parameters."""
        pass

    def __repr__(self) -> str:
        return f"Tool({self.name})"


class CalculatorTool(Tool):
    """Tool for performing precise calculations."""

    def __init__(self):
        super().__init__(
            name="calculator",
            description="Performs precise mathematical calculations. Use for arithmetic, algebra, etc."
        )

    def execute(self, expression: str) -> str:
        """Evaluate a mathematical expression.

        Args:
            expression: Mathematical expression to evaluate (e.g., "15 + 27", "sqrt(144)")

        Returns:
            Result as a string
        """
        import ast
        import operator
        import math
        
        try:
            # Safe operators mapping
            operators = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.FloorDiv: operator.floordiv,
                ast.Mod: operator.mod,
                ast.Pow: operator.pow,
                ast.USub: operator.neg,
                ast.UAdd: operator.pos,
            }
            
            # Safe functions mapping
            safe_functions = {
                'sqrt': math.sqrt,
                'abs': abs,
                'pow': pow,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'log': math.log,
                'log10': math.log10,
                'exp': math.exp,
                'floor': math.floor,
                'ceil': math.ceil,
                'round': round,
            }
            
            # Preprocess expression
            safe_expr = expression.replace('^', '**')
            
            def _eval_node(node):
                """Safely evaluate an AST node."""
                if isinstance(node, ast.Constant):  # Python 3.8+
                    return node.value
                elif isinstance(node, ast.Num):  # Python 3.7 compat
                    return node.n
                elif isinstance(node, ast.BinOp):
                    left = _eval_node(node.left)
                    right = _eval_node(node.right)
                    op = operators.get(type(node.op))
                    if op is None:
                        raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
                    return op(left, right)
                elif isinstance(node, ast.UnaryOp):
                    operand = _eval_node(node.operand)
                    op = operators.get(type(node.op))
                    if op is None:
                        raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
                    return op(operand)
                elif isinstance(node, ast.Call):
                    func_name = node.func.id if isinstance(node.func, ast.Name) else None
                    if func_name not in safe_functions:
                        raise ValueError(f"Unsupported function: {func_name}")
                    args = [_eval_node(arg) for arg in node.args]
                    return safe_functions[func_name](*args)
                elif isinstance(node, ast.Name):
                    # Handle constants like pi, e
                    if node.id == 'pi':
                        return math.pi
                    elif node.id == 'e':
                        return math.e
                    raise ValueError(f"Unknown variable: {node.id}")
                else:
                    raise ValueError(f"Unsupported expression type: {type(node).__name__}")
            
            tree = ast.parse(safe_expr, mode='eval')
            result = _eval_node(tree.body)

            logger.info(f"Calculator: {expression} = {result}")
            return str(result)

        except Exception as e:
            logger.error(f"Calculator error: {e}")
            return f"Error: {str(e)}"


class WikipediaSearchTool(Tool):
    """Tool for searching Wikipedia for factual information."""

    def __init__(self):
        super().__init__(
            name="wikipedia",
            description="Searches Wikipedia for factual information about people, places, events, concepts."
        )

    def execute(self, query: str, sentences: int = 3) -> str:
        """Search Wikipedia and return summary.

        Args:
            query: Search query
            sentences: Number of sentences to return (default 3)

        Returns:
            Wikipedia summary or error message
        """
        try:
            import wikipediaapi
            wiki = wikipediaapi.Wikipedia(
                user_agent='MAVEN/1.0 (https://github.com/rwondo/maven; hallucination-detection)',
                language='en'
            )

            page = wiki.page(query)

            if not page.exists():
                # Try searching for similar pages
                return f"No Wikipedia page found for '{query}'. Try a more specific query."

            # Get summary (first few sentences)
            summary = page.summary.split('.')[:sentences]
            result = '. '.join(summary) + '.'

            logger.info(f"Wikipedia: Found info for '{query}'")
            return result

        except ImportError:
            return "Error: wikipedia-api package not installed. Run: pip install wikipedia-api"
        except Exception as e:
            logger.error(f"Wikipedia error: {e}")
            return f"Error searching Wikipedia: {str(e)}"


class FactCheckTool(Tool):
    """Tool for basic fact verification."""

    def __init__(self):
        super().__init__(
            name="fact_check",
            description="Verifies basic factual claims using simple rules and lookups."
        )
        # Simple fact database for common verifications
        self.facts = {
            "planets_in_solar_system": 8,
            "days_in_week": 7,
            "continents": 7,
            "us_states": 50,
        }

    def execute(self, claim: str) -> str:
        """Verify a factual claim.

        Args:
            claim: Claim to verify

        Returns:
            Verification result
        """
        claim_lower = claim.lower()

        # Check for numerical claims
        numbers = re.findall(r'\d+', claim)

        # Simple pattern matching for common facts
        if "planet" in claim_lower and "solar system" in claim_lower:
            expected = self.facts["planets_in_solar_system"]
            if numbers and int(numbers[0]) == expected:
                return f"VERIFIED: There are {expected} planets in our solar system"
            else:
                return f"INCORRECT: There are {expected} planets, not {numbers[0] if numbers else 'unknown'}"

        if "days" in claim_lower and "week" in claim_lower:
            expected = self.facts["days_in_week"]
            if numbers and int(numbers[0]) == expected:
                return f"VERIFIED: There are {expected} days in a week"
            else:
                return f"INCORRECT: There are {expected} days, not {numbers[0] if numbers else 'unknown'}"

        return "Cannot verify this claim with available data"


class ToolRegistry:
    """Registry of available tools."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool."""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        """List all available tools."""
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self.tools.values()
        ]

    def get_tools_description(self) -> str:
        """Get formatted description of all tools for prompts."""
        descriptions = []
        for tool in self.tools.values():
            descriptions.append(f"- {tool.name}: {tool.description}")
        return "\n".join(descriptions)


# Default tool registry
default_registry = ToolRegistry()
default_registry.register(CalculatorTool())
default_registry.register(WikipediaSearchTool())
default_registry.register(FactCheckTool())


def extract_tool_calls(text: str) -> List[Dict[str, Any]]:
    """Extract tool calls from model output.

    Looks for patterns like:
    USE_TOOL: calculator
    EXPRESSION: 15 + 27

    Or:
    USE_TOOL: wikipedia
    QUERY: Albert Einstein

    Returns:
        List of tool calls with tool name and parameters
    """
    tool_calls = []

    # Pattern: USE_TOOL: <name>
    tool_matches = re.finditer(r'USE_TOOL:\s*(\w+)', text, re.IGNORECASE)

    for match in tool_matches:
        tool_name = match.group(1).lower()
        start_pos = match.end()

        # Extract parameters until next tool call or end
        next_match = re.search(r'USE_TOOL:', text[start_pos:], re.IGNORECASE)
        if next_match:
            params_text = text[start_pos:start_pos + next_match.start()]
        else:
            params_text = text[start_pos:]

        # Extract parameter pairs (PARAM: value)
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


def execute_tool_calls(tool_calls: List[Dict[str, Any]], registry: ToolRegistry = default_registry) -> str:
    """Execute tool calls and return results.

    Args:
        tool_calls: List of tool calls from extract_tool_calls
        registry: Tool registry to use

    Returns:
        Formatted results from all tool calls
    """
    if not tool_calls:
        return ""

    results = []
    for call in tool_calls:
        tool_name = call["tool"]
        params = call["params"]

        tool = registry.get(tool_name)
        if not tool:
            results.append(f"[{tool_name}] ERROR: Tool not found")
            continue

        try:
            # Map common parameter names
            if tool_name == "calculator":
                expression = params.get("expression") or params.get("calc") or params.get("input")
                if expression:
                    result = tool.execute(expression=expression)
                    results.append(f"[{tool_name}] {expression} = {result}")
            elif tool_name == "wikipedia":
                query = params.get("query") or params.get("search") or params.get("topic")
                if query:
                    result = tool.execute(query=query)
                    results.append(f"[{tool_name}] {result}")
            elif tool_name == "fact_check":
                claim = params.get("claim") or params.get("statement")
                if claim:
                    result = tool.execute(claim=claim)
                    results.append(f"[{tool_name}] {result}")
            else:
                results.append(f"[{tool_name}] ERROR: Unknown parameter format")

        except Exception as e:
            results.append(f"[{tool_name}] ERROR: {str(e)}")

    return "\n".join(results)


if __name__ == "__main__":
    # Test the tools
    print("Testing MAVEN Tools")
    print("=" * 70)

    calc = CalculatorTool()
    print(f"\n[Calculator Test]")
    print(f"15 + 27 = {calc.execute('15 + 27')}")
    print(f"sqrt(144) = {calc.execute('sqrt(144)')}")

    print(f"\n[Fact Check Test]")
    fact = FactCheckTool()
    print(fact.execute("There are 8 planets in our solar system"))
    print(fact.execute("There are 9 planets in our solar system"))

    print(f"\n[Tool Call Extraction Test]")
    text = """
    Let me calculate this:
    USE_TOOL: calculator
    EXPRESSION: 15 + 27

    And verify:
    USE_TOOL: fact_check
    CLAIM: There are 8 planets in our solar system
    """

    calls = extract_tool_calls(text)
    print(f"Extracted {len(calls)} tool calls:")
    print(json.dumps(calls, indent=2))

    print(f"\n[Tool Execution Test]")
    results = execute_tool_calls(calls)
    print(results)

    print("\n" + "=" * 70)
