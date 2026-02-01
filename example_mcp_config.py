#!/usr/bin/env python3
"""
Example MCP Server Configuration for MAVEN

This shows how to configure external MCP servers for hallucination detection.
Users can add any MCP server for domain-specific verification.
"""

from maven import HallucinationDetector

# Example 1: Using Wikipedia MCP Server (via stdio)
detector_with_wikipedia = HallucinationDetector(
    models=[
        "together/llama-3.1-8b",
        "together/qwen-2.5-7b",
        "together/mixtral-8x7b"
    ],
    mcp_servers=[
        {
            "name": "wikipedia",
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-wikipedia"]
        }
    ]
)

# Example 2: Using Multiple MCP Servers for Medical Domain
detector_medical = HallucinationDetector(
    models=["together/llama-3.1-8b", "together/qwen-2.5-7b"],
    mcp_servers=[
        {
            "name": "pubmed",
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-pubmed"]
        },
        {
            "name": "drugbank",
            "type": "http",
            "url": "https://api.drugbank.com/mcp",
            "api_key": "your-drugbank-api-key"
        },
        {
            "name": "fda",
            "type": "http",
            "url": "https://api.fda.gov/mcp",
            "headers": {
                "User-Agent": "MAVEN/0.2.0"
            }
        }
    ]
)

# Example 3: Using Legal Research MCP Servers
detector_legal = HallucinationDetector(
    models=["claude-sonnet-4", "gpt-4"],
    mcp_servers=[
        {
            "name": "caselaw",
            "type": "stdio",
            "command": "caselaw-mcp-server",
            "args": ["--database", "/path/to/caselaw.db"]
        },
        {
            "name": "courtlistener",
            "type": "http",
            "url": "https://www.courtlistener.com/api/mcp",
            "api_key": "your-courtlistener-key"
        }
    ]
)

# Example 4: Custom Financial Verification Server
detector_financial = HallucinationDetector(
    models=["together/llama-3.3-70b", "together/qwen-2.5-72b"],
    mcp_servers=[
        {
            "name": "sec_edgar",
            "type": "http",
            "url": "https://api.sec.gov/mcp",
            "headers": {
                "User-Agent": "MyCompany hallucination-detector (contact@example.com)"
            }
        },
        {
            "name": "wolfram",
            "type": "http",
            "url": "https://api.wolframalpha.com/mcp",
            "api_key": "your-wolfram-key"
        }
    ]
)

# Example 5: No MCP Servers (models only, no external verification)
detector_minimal = HallucinationDetector(
    models=[
        "together/llama-3.1-8b",
        "together/qwen-2.5-7b",
        "together/mixtral-8x7b"
    ]
    # No mcp_servers - rely solely on model agreement
)


def test_with_mcp_servers():
    """Test hallucination detection with MCP servers."""

    # Test with Wikipedia verification
    report = detector_with_wikipedia.detect(
        query="When was the Eiffel Tower built?",
        answer="The Eiffel Tower was constructed between 1891 and 1893.",
        domain="general"
    )

    print("=" * 70)
    print("Hallucination Detection with Wikipedia MCP Server")
    print("=" * 70)
    print(f"Risk Level: {report.risk_level}")
    print(f"Confidence: {report.confidence_score}%")
    print(f"Flags: {report.flags}")
    print(f"\nAvailable MCP Tools:")
    # The detector will list available tools from MCP servers
    print("  - wikipedia:search (Wikipedia MCP)")
    print("  - wikipedia:get_page (Wikipedia MCP)")
    print()

    # Test medical claim with PubMed
    medical_report = detector_medical.detect(
        query="What are the effects of aspirin on cardiovascular health?",
        answer="According to the 2023 Johnson Study in NEJM, aspirin reduces heart attack risk by 89%.",
        domain="medical"
    )

    print("=" * 70)
    print("Medical Hallucination Detection with PubMed MCP")
    print("=" * 70)
    print(f"Risk Level: {medical_report.risk_level}")
    print(f"Confidence: {medical_report.confidence_score}%")
    print(f"Flags: {medical_report.flags}")
    print(f"\nAvailable MCP Tools:")
    print("  - pubmed:search_papers (PubMed MCP)")
    print("  - drugbank:check_interaction (DrugBank MCP)")
    print("  - fda:verify_approval (FDA MCP)")
    print()


if __name__ == "__main__":
    print("""
    MAVEN MCP Server Configuration Examples
    ========================================

    This file demonstrates how to configure MAVEN with various MCP servers
    for domain-specific hallucination detection.

    To run these examples:
    1. Install required MCP servers (see README.md)
    2. Set up API keys in environment variables
    3. Run: python example_mcp_config.py

    MCP Servers Used:
    - Wikipedia: General fact verification
    - PubMed: Medical paper verification
    - DrugBank: Drug interaction checking
    - FDA: FDA approval verification
    - CourtListener: Legal case verification
    - SEC EDGAR: Financial filing verification
    - WolframAlpha: Advanced calculations

    Note: MCP servers are OPTIONAL. MAVEN works without them,
    relying on model agreement for hallucination detection.
    """)

    # Uncomment to test
    # test_with_mcp_servers()
