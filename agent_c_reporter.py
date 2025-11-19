import json
import re
from typing import Dict, Any

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


# ---------- 1. LLM Client ----------

llm = ChatOllama(
    model="qwen2.5:14b-instruct",   # you can switch to "qwen3:4b-instruct" etc.
    temperature=0.0,
    num_predict=2048,
)


# ---------- 2. Agent C Prompt ----------

reporter_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are AGENT C — a professional documentation generator.

You receive:
- The JSON output of Agent B (mode, summary, violations, per_rule_status).
- The original C++ code (optional, for context if needed).

You MUST produce STRICT JSON with exactly:

{{
  "markdown_report": "string",
  "executive_summary": "string"
}}

Where:

### executive_summary
A 4–6 sentence natural-language explanation summarizing:
- How many rules were checked
- How many passed / failed
- Severity levels
- High-level description of the main issues
- Tone: concise, objective, engineer-friendly

### markdown_report
A complete Markdown report with sections:

# C++ Code Review Report

## Summary
A table:

| Metric | Count |
|--------|-------|
| Errors | ... |
| Warnings | ... |
| Info | ... |
| Rules Checked | ... |
| Rules Failed | ... |
| Rules Passed | ... |
| Rules Not Applicable | ... |

## Violations
If there are no violations, write:

> No violations found. Code complies with all checked rules.

Otherwise render a table:

| Rule ID | Severity | Line(s) | Description | Suggested Fix |
|---------|----------|---------|-------------|---------------|

Fill each row using:
- rule_id
- severity
- line_range (join as "N" or "N–M")
- violation_description
- suggested_fix

## Per-Rule Evaluation
Table:

| Rule ID | Status | Severity |
|---------|--------|----------|

- Status is one of: "pass", "fail", "not_applicable".

## Raw Input (Optional)
Include the Agent B JSON at the end in a fenced code block
so that consumers can see the raw data you used.

RULES:
- Do NOT invent rules not present in the JSON.
- Do NOT hallucinate violations.
- Use EXACT data from the input JSON.
- Do NOT output anything before or after the JSON return object.
""",
        ),
        (
            "human",
            # No markdown fences here to avoid confusing the model / tooling
            "Agent B JSON Output:\n{agent_b_json}\n\n"
            "Original code:\n{code}\n"
        ),
    ]
)

reporter_chain = reporter_prompt | llm


# ---------- 3. JSON Extraction Helper ----------

def _extract_json(content: str) -> Dict[str, Any]:
    """Extract the first JSON object from the model output."""
    try:
        return json.loads(content)
    except Exception:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise ValueError(f"Agent C returned non-JSON:\n{content}")
        return json.loads(match.group(0))


# ---------- 4. Public API ----------

def run_agent_c_reporter(agent_b_result: Dict[str, Any], code: str) -> Dict[str, Any]:
    """
    Run Agent C on Agent B's JSON result + original code.

    Returns:
        {
          "markdown_report": "...",
          "executive_summary": "..."
        }
    """
    resp = reporter_chain.invoke(
        {
            "agent_b_json": json.dumps(agent_b_result, indent=2),
            "code": code,
        }
    )
    return _extract_json(resp.content)


# ---------- 5. Manual Test ----------

if __name__ == "__main__":
    sample_agent_b_json = {
        "mode": "quick",
        "summary": {
            "errors": 1,
            "warnings": 2,
            "info": 0,
            "rules_checked": 8,
            "rules_failed": 3,
            "rules_passed": 4,
            "rules_not_applicable": 1,
        },
        "violations": [
            {
                "rule_id": "UDT-STRUCT-003",
                "severity": "Warning",
                "section": "User-defined Types / Structures",
                "line_range": [9, 12],
                "violation_description": "Struct members are not initialized.",
                "suggested_fix": "Initialize struct members with default values.",
            }
        ],
        "per_rule_status": [
            {
                "rule_id": "UDT-STRUCT-003",
                "status": "fail",
                "severity": "Warning",
            },
            {
                "rule_id": "UDT-CLASS-001",
                "status": "pass",
                "severity": "Error",
            },
        ],
    }

    sample_code = """#include <vector>
#include <memory>
#include <iostream>

#define MAX_COUNT 10

struct Point {
    int x;
    int y;
};

class Foo {
public:
    Foo() : data(std::make_unique<int>(42)) {}
    void print() const {
        std::cout << "Value: " << *data << std::endl;
    }
private:
    std::unique_ptr<int> data;
};

int main() {
    std::vector<int> values;
    values.push_back(1);
    Foo foo;
    foo.print();
    return 0;
}
"""

    result = run_agent_c_reporter(sample_agent_b_json, sample_code)
    print("=== Executive Summary ===")
    print(result["executive_summary"])
    print("\n=== Markdown Report ===")
    print(result["markdown_report"])
