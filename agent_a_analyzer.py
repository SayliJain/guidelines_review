import json
import re
from pathlib import Path
from typing import Dict, Any

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate


# ---------------------------------------------------------
# 1. LLM Client
# ---------------------------------------------------------

llm = ChatOllama(
    model="qwen3:4b-instruct",  # recommended for speed OR "qwen2.5:14b-instruct" for accuracy
    temperature=0.0,
    num_predict=1024,
)


# ---------------------------------------------------------
# 2. Agent A Prompt
# ---------------------------------------------------------

analyzer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a STRICT C++ code analyzer.

Your job has TWO parts:

1) Detect which C++ features are PRESENT in the code.
2) Based ONLY on those features, select which guideline CATEGORIES apply.

You MUST return STRICT JSON with two keys:

{{
  "code_features": {{
    "has_macros": bool,
    "has_enums": bool,
    "has_classes": bool,
    "has_structs": bool,
    "has_functions": bool,
    "has_namespaces": bool,
    "has_raw_pointers": bool,
    "has_smart_pointers": bool,
    "uses_containers": [ "std::vector", "std::map", "std::array", "std::unordered_map" ],
    "uses_threads": bool,
    "uses_file_io": bool,
    "uses_exceptions": bool,
    "uses_numeric_literals": bool,
    "uses_headers": bool,
    "has_comments": bool
  }},
  "selected_rule_categories": [
    "IDN",
    "PRM",
    "FUNC",
    "HDR",
    "NUM",
    "FMT",
    "DOC",
    "FILE",
    "UDT-ENUM",
    "UDT-STRUCT",
    "UDT-CLASS",
    "MOD-TYPE",
    "MOD-MEM",
    "MOD-CONC",
    "MOD-IO",
    "MOD-CLASS",
    "MOD-FUNC",
    "MOD-ALG",
    "MOD-CONTAINER",
    "MOD-ERR",
    "APP-SMARTPTR",
    "APP-CONC"
  ]
}}

-----------------------------------------------------------
### HOW TO DETECT FEATURES (BE LITERAL AND ONLY BASED ON TEXT)
-----------------------------------------------------------

- has_macros → TRUE if you see any `#define`.
- has_enums → TRUE if `enum` or `enum class` appears.
- has_classes → TRUE if `class <Name>` appears.
- has_structs → TRUE if `struct <Name>` appears.
- has_functions → TRUE if you see function definitions (`type name(...) {{`).
- has_namespaces → TRUE if `namespace <name>` appears.
- has_raw_pointers → TRUE ONLY if:
    - You see `T* var`, AND
    - The code uses `new` or `delete`.
- has_smart_pointers → TRUE if:
    - std::unique_ptr, std::shared_ptr, std::weak_ptr, make_unique, make_shared
- uses_containers → detect "std::vector", "std::map", "std::unordered_map", "std::array"
- uses_threads → detect "std::thread", "std::jthread", mutex, atomic
- uses_file_io → detect std::ifstream, std::ofstream, std::fstream, std::filesystem
- uses_exceptions → detect try / catch / throw
- uses_numeric_literals → detect numbers in code
- uses_headers → detect any "#include"
- has_comments → detect // or /* */

If a feature is NOT found → set false.

-----------------------------------------------------------
### HOW TO SELECT CATEGORIES
-----------------------------------------------------------

- If has_macros OR has_enums OR has_functions OR has_classes OR has_structs → include "IDN".
- If uses_numeric_literals OR has_macros → include "NUM" and "PRM".
- If has_functions → include "FUNC" and "MOD-FUNC".
- If has_classes → include "UDT-CLASS", "MOD-CLASS", "MOD-TYPE".
- If has_structs → include "UDT-STRUCT", "MOD-TYPE".
- If has_enums → include "UDT-ENUM", "MOD-TYPE".
- If has_raw_pointers OR has_smart_pointers → include "MOD-MEM" and "APP-SMARTPTR".
- If uses_containers non-empty → include "MOD-CONTAINER" and "MOD-ALG".
- If uses_threads → include "MOD-CONC" and "APP-CONC".
- If uses_file_io → include "MOD-IO" and "MOD-ERR".
- If uses_exceptions → include "MOD-ERR".
- If uses_headers → include "HDR".
- If has_comments → include "DOC".

Formatting ("FMT") and file organization ("FILE") can be included by default for real-world code.

-----------------------------------------------------------
RULES:
- ONLY include categories supported by detected features.
- DO NOT guess features—detect literally from text.
- DO NOT output anything before or after the JSON.
-----------------------------------------------------------
""",
        ),
        (
            "human",
            "Here is the C++ code snippet:\n```cpp\n{code}\n```",
        ),
    ]
)


# Link LLM
analyzer_chain = analyzer_prompt | llm


# ---------------------------------------------------------
# 3. JSON Extraction Helper
# ---------------------------------------------------------

def _extract_json(content: str) -> Dict[str, Any]:
    """Gracefully extract JSON."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise ValueError(f"Agent A output is not JSON:\n{content}")
        return json.loads(match.group(0))


# ---------------------------------------------------------
# 4. Public API
# ---------------------------------------------------------

def run_agent_a_analyze_and_select(code: str) -> Dict[str, Any]:
    """Run Agent A on C++ code."""
    resp = analyzer_chain.invoke({"code": code})
    return _extract_json(resp.content)


# ---------------------------------------------------------
# 5. File Loader
# ---------------------------------------------------------

def load_code(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p.resolve()}")
    return p.read_text(encoding="utf-8")


# ---------------------------------------------------------
# 6. Manual Test
# ---------------------------------------------------------

if __name__ == "__main__":
    sample_code_path = "samples/example1.cpp"
    code = load_code(sample_code_path)
    result = run_agent_a_analyze_and_select(code)

    print("=== Agent A Result ===")
    print(json.dumps(result, indent=2))
