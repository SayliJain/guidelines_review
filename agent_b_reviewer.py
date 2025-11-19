import json
import re
from pathlib import Path
from typing import List, Dict, Any

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from agent_a_analyzer import run_agent_a_analyze_and_select, load_code


# ---------- 1. Load guidelines index ----------

GUIDELINES_INDEX_PATH = Path("guidelines_index.json")
GUIDELINES_INDEX: List[Dict[str, Any]] = json.loads(
    GUIDELINES_INDEX_PATH.read_text(encoding="utf-8")
)


def select_rules_by_categories(categories: List[str]) -> List[Dict[str, Any]]:
    """Filter all rules by category prefix (e.g. IDN, PRM, MOD-MEM, APP-SMARTPTR)."""
    cats = set(categories)
    return [r for r in GUIDELINES_INDEX if r.get("category") in cats]


def slim_rules_for_llm(rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Reduce each rule to only the fields the LLM needs.
    This keeps prompts small even if the full JSON has raw_markdown, examples, etc.
    """
    slimmed: List[Dict[str, Any]] = []
    for r in rules:
        slimmed.append(
            {
                "rule_id": r.get("rule_id"),
                "section": r.get("section"),
                "subsection": r.get("subsection"),
                "category": r.get("category"),
                "severity": r.get("severity"),
                "description": r.get("description"),
            }
        )
    return slimmed


def add_line_numbers(code: str) -> str:
    """Prefix each line with a 3-digit line number."""
    lines = code.splitlines()
    return "\n".join(f"{i+1:03}  {line}" for i, line in enumerate(lines))


# ---------- 2. Optional: refine categories using simple heuristics ----------

def refine_categories_from_code(code: str, a_result: Dict[str, Any]) -> Dict[str, Any]:
    """Use simple pattern checks to correct/augment Agent A's output."""
    cats = set(a_result.get("selected_rule_categories", []))
    features = a_result.get("code_features", {}) or {}

    # quick string checks (you can make these regexes later)
    if "struct " in code:
        features["has_structs"] = True
        cats.add("UDT-STRUCT")

    if "std::vector" in code or "std::map" in code or "std::unordered_map" in code:
        cats.add("MOD-CONTAINER")

    if (
        "std::unique_ptr" in code
        or "std::shared_ptr" in code
        or "make_unique" in code
        or "make_shared" in code
    ):
        cats.update(["MOD-MEM", "APP-SMARTPTR"])

    if "//" in code or "/*" in code:
        features["has_comments"] = True
        cats.add("DOC")

    # threads / concurrency
    if (
        "std::thread" in code
        or "std::mutex" in code
        or "std::atomic" in code
        or "std::jthread" in code
    ):
        cats.update(["MOD-CONC", "APP-CONC"])

    a_result["code_features"] = features
    a_result["selected_rule_categories"] = sorted(cats)
    return a_result


# ---------- 3. LLM client for Agent B ----------

llm = ChatOllama(
    model="qwen2.5:14b-instruct",  # or "qwen3:4b-instruct", "qwen2.5-coder:7b", etc.
    temperature=0.0,
    num_predict=2048,
)


# ---------- 4. Reviewer prompt (Agent B) ----------

reviewer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a STRICT C++ coding guideline reviewer.

You receive:
1) C++ code with line numbers at the start of each line.
2) A list of guideline rules (JSON objects with: rule_id, section, subsection, category, severity, description).

Your job:

- For EACH rule in the list:
  - Decide if the code: **passes**, **fails**, or the rule is **not_applicable**.
  - If it FAILS, create a violation entry with line_range, description, and suggested_fix.

You MUST return ONLY JSON with this exact shape:

{{
  "mode": "quick" | "full",
  "summary": {{
    "errors": int,
    "warnings": int,
    "info": int,
    "rules_checked": int,
    "rules_failed": int,
    "rules_passed": int,
    "rules_not_applicable": int
  }},
  "violations": [
    {{
      "rule_id": "MOD-MEM-001",
      "severity": "Error",
      "section": "Modern C++ Guidelines / Memory Management",
      "line_range": [3, 6],
      "violation_description": "short description",
      "suggested_fix": "short fix"
    }}
  ],
  "per_rule_status": [
    {{
      "rule_id": "MOD-MEM-001",
      "status": "fail",  // one of: "pass", "fail", "not_applicable"
      "severity": "Error"
    }}
  ]
}}

### HOW TO APPLY RULES (IMPORTANT)

- Use the 'severity' field from the rule as-is; do NOT change it.
- A rule is "fail" ONLY if the code CLEARLY contradicts the rule description.
- A rule is "pass" if the code clearly follows the rule where it applies.
- A rule is "not_applicable" if the code does not contain anything related to that rule.

Examples:

- For naming rules like IDN-001 (preprocessor identifiers must use UPPERCASE with underscores):
  - `#define MAX_COUNT 10` → this COMPLIES and should NOT be a violation.
  - `#define maxCount 10` → this VIOLATES and should be "fail".

- For smart pointer / memory rules (MOD-MEM-001, APP-SMARTPTR-001):
  - If the code uses `std::unique_ptr` or `std::make_unique` for ownership, that is GOOD and should be "pass".
  - Only mark "fail" if you see raw owning pointers (e.g. `T* ptr;` with `new`/`delete`) or missing smart pointers where they are clearly needed.

- For struct initialization rules (e.g. UDT-STRUCT-003):
  - `struct Point {{ int x; int y; }};` with no defaults → likely a VIOLATION (uninitialized members).
  - `struct Point {{ int x = 0; int y = 0; }};` → PASS.

### QUICK vs FULL MODE

- In "quick" mode:
  - You MUST still set per_rule_status for every rule.
  - But you may limit the `violations` array to at most 10 items, prioritizing:
    - 1st: "Error"
    - 2nd: "Warning"
    - 3rd: "Info".

- In "full" mode:
  - Evaluate EVERY rule and report all failures in `violations`.

### LINE RANGES

- Use the line numbers at the start of each code line.
- If the problem is on a single line, set line_range to [N, N].
- If the problem spans multiple lines (like a whole struct or class), use [start_line, end_line].

Do NOT output anything before or after the JSON.
""",
        ),
        (
            "human",
            "Mode: {mode}\n\nC++ code with line numbers:\n```cpp\n{code_with_lines}\n```\n\nGuideline rules (JSON array):\n```json\n{rules_json}\n```",
        ),
    ]
)

reviewer_chain = reviewer_prompt | llm


# ---------- 5. Helper to extract JSON ----------

def _extract_json(content: str) -> Dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise ValueError(f"Agent B returned non-JSON:\n{content}")
        return json.loads(match.group(0))


# ---------- 6. Public function for Agent B ----------

def run_agent_b_review(
    code: str,
    selected_categories: List[str],
    mode: str = "quick",
) -> Dict[str, Any]:
    # 1) Filter rules by categories
    rules_for_review = select_rules_by_categories(selected_categories)

    # 2) Slim rules before sending to the LLM
    rules_for_llm = slim_rules_for_llm(rules_for_review)

    # DEBUG: see which rules are actually sent to Agent B
    print("Rules sent to Agent B:", [r.get("rule_id") for r in rules_for_llm])

    # 3) Prepare inputs
    code_with_lines = add_line_numbers(code)
    rules_json = json.dumps(rules_for_llm, ensure_ascii=False, indent=2)

    # 4) Invoke the chain
    resp = reviewer_chain.invoke(
        {
            "mode": mode,
            "code_with_lines": code_with_lines,
            "rules_json": rules_json,
        }
    )

    parsed = _extract_json(resp.content)
    return parsed


# ---------- 7. Manual test combining Agent A + B ----------

if __name__ == "__main__":
    code_path = "samples/example1.cpp"  # your sample file

    code = load_code(code_path)

    # Step A: analyze & select categories
    a_raw = run_agent_a_analyze_and_select(code)
    a_refined = refine_categories_from_code(code, a_raw)
    selected_categories = a_refined.get("selected_rule_categories", [])

    print("=== Agent A Selected Categories (refined) ===")
    print(selected_categories)

    # Step B: review
    b_result = run_agent_b_review(
        code=code,
        selected_categories=selected_categories,
        mode="quick",  # change to "full" for full audit
    )

    print("\n=== Agent B Review Result ===")
    print(json.dumps(b_result, indent=2))
