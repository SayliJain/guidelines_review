import json
from pathlib import Path
from datetime import datetime

from agent_a_analyzer import run_agent_a_analyze_and_select, load_code
from agent_b_reviewer import refine_categories_from_code, run_agent_b_review
from agent_c_reporter import run_agent_c_reporter


# ---------- 1. Config ----------

CODE_PATH = Path("samples/example1.cpp")   # change this as needed
OUTPUT_DIR = Path("outputs")              # all agent outputs go here


def _timestamp() -> str:
    """Return a compact timestamp string for filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------- 2. Main pipeline ----------

def run_full_pipeline(code_path: Path):
    _ensure_output_dir()

    # 1) Load code
    code = load_code(str(code_path))

    # 2) Agent A: analyze + select categories
    a_result = run_agent_a_analyze_and_select(code)
    a_refined = refine_categories_from_code(code, a_result)

    # 3) Agent B: review based on selected categories
    selected_categories = a_refined.get("selected_rule_categories", [])
    b_result = run_agent_b_review(
        code=code,
        selected_categories=selected_categories,
        mode="quick",  # or "full"
    )

    # 4) Agent C: reporting
    c_result = run_agent_c_reporter(b_result, code)

    # ---------- 5. Save to files ----------

    ts = _timestamp()

    agent_a_file = OUTPUT_DIR / f"agent_a_result_{ts}.json"
    agent_b_file = OUTPUT_DIR / f"agent_b_result_{ts}.json"
    agent_c_json_file = OUTPUT_DIR / f"agent_c_result_{ts}.json"
    agent_c_md_file = OUTPUT_DIR / f"agent_c_report_{ts}.md"
    agent_c_summary_file = OUTPUT_DIR / f"agent_c_summary_{ts}.txt"

    # Save Agent A raw + refined in one JSON
    with agent_a_file.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "raw": a_result,
                "refined": a_refined,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    # Save Agent B result
    with agent_b_file.open("w", encoding="utf-8") as f:
        json.dump(b_result, f, ensure_ascii=False, indent=2)

    # Save Agent C combined (JSON view)
    with agent_c_json_file.open("w", encoding="utf-8") as f:
        json.dump(c_result, f, ensure_ascii=False, indent=2)

    # Save Agent C markdown report
    with agent_c_md_file.open("w", encoding="utf-8") as f:
        f.write(c_result.get("markdown_report", ""))

    # Save Agent C executive summary as plain text
    with agent_c_summary_file.open("w", encoding="utf-8") as f:
        f.write(c_result.get("executive_summary", ""))

    print("=== Pipeline complete ===")
    print(f"Agent A JSON  -> {agent_a_file}")
    print(f"Agent B JSON  -> {agent_b_file}")
    print(f"Agent C JSON  -> {agent_c_json_file}")
    print(f"Agent C MD    -> {agent_c_md_file}")
    print(f"Agent C Summary -> {agent_c_summary_file}")


if __name__ == "__main__":
    run_full_pipeline(CODE_PATH)
