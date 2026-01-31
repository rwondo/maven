"""
Code security review example using MAVEN.

This example demonstrates how MAVEN can be used to review code
for security issues through multi-model consensus.

Usage:
    python code_security_review.py

Requirements:
    - ANTHROPIC_API_KEY environment variable
    - OPENAI_API_KEY environment variable
    - GOOGLE_API_KEY environment variable
"""

from maven import ConsensusOrchestrator

# Sample code to review - intentionally has issues
SAMPLE_CODE = '''
def login(username, password):
    """Authenticate user and return session token."""
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)

    if result:
        token = username + str(time.time())
        return token
    return None

def get_user_data(user_id):
    """Retrieve user data by ID."""
    data = db.execute(f"SELECT * FROM users WHERE id={user_id}")
    return data

def upload_file(filename, content):
    """Save uploaded file to disk."""
    path = f"/uploads/{filename}"
    with open(path, 'w') as f:
        f.write(content)
    return path
'''


def main():
    """Run security review on sample code."""
    print("MAVEN - Code Security Review Example")
    print("=" * 60)

    orchestrator = ConsensusOrchestrator(
        models=["claude-sonnet-4", "gpt-4", "gemini-pro"],
        config={
            "max_iterations": 3,
            "consensus_threshold": 0.75,
        },
    )

    query = f"""Review the following Python code for security vulnerabilities.
Identify all issues and explain the risks.

```python
{SAMPLE_CODE}
```

Focus on:
1. Injection attacks
2. Authentication weaknesses
3. File handling issues
4. Any other security concerns
"""

    print("Reviewing code sample...")
    print("-" * 60)

    result = orchestrator.verify(query)

    print("\nSecurity Assessment")
    print("=" * 60)
    print(f"\nFindings:\n{result.consensus}")
    print(f"\nConfidence: {result.confidence:.1f}%")
    print(f"Verification rounds: {result.iterations}")

    if result.dissent:
        print(f"\nNote: {result.dissent}")

    # Show which models participated and in what roles
    print("\n" + "=" * 60)
    print("Review Process:")
    print("=" * 60)

    seen_iterations = set()
    for step in result.trace:
        if step.iteration not in seen_iterations:
            if seen_iterations:
                print()
            print(f"\n--- Round {step.iteration} ---")
            seen_iterations.add(step.iteration)

        print(f"  {step.role}: {step.model}")


def review_custom_code(code: str) -> None:
    """Review custom code snippet.

    Args:
        code: Python code to review.
    """
    orchestrator = ConsensusOrchestrator(
        models=["claude-sonnet-4", "gpt-4", "gemini-pro"]
    )

    query = f"""Review this code for security issues:

```python
{code}
```

Provide a severity rating (Critical/High/Medium/Low) for each issue found.
"""

    result = orchestrator.verify(query)
    print(result.consensus)


if __name__ == "__main__":
    main()
