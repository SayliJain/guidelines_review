Absolutely — here are **polished, production-ready** versions of both:

---

# ✅ **README.md (Beautiful, Professional, GitHub-Optimized)**

You can paste this directly into your repo.

---

# **C++ Code Review Multi-Agent System**

*Automated static analysis using LangChain, Ollama, and local LLMs*

![banner](https://img.shields.io/badge/AI%20Code%20Review-C%2B%2B-blue?style=for-the-badge)
![framework](https://img.shields.io/badge/LangChain-Agentic%20Pipeline-green?style=flat-square)
![model](https://img.shields.io/badge/Ollama-Qwen%202.5%20%2F%20Qwen%203-yellow?style=flat-square)


---

## 🚀 Overview

This project implements a **three-agent AI pipeline** that performs an end-to-end **C++ code review** using a structured set of coding guidelines.
It is designed for **local, offline execution** using **Ollama** + **LangChain**, and supports scalable rule-based review via JSON guideline definitions.

---

## 🧠 Architecture

```
┌────────────┐       ┌──────────────┐       ┌──────────────┐
│ Agent A     │       │ Agent B       │       │ Agent C       │
│ Analyzer    │  →    │ Reviewer      │  →    │ Report Writer │
└────────────┘       └──────────────┘       └──────────────┘
      │                     │                        │
      │                     │                        │
 Detect features      Apply rules from        Generates Markdown
 Select categories    guidelines_index.json   + Executive summary
```

---

## 📌 Features

### **Agent A – Code Analyzer**

* Extracts features from code
* Detects: macros, enums, classes, structs, pointers, containers, threads
* Selects applicable rule categories
* Produces structured JSON

### **Agent B – Guideline Reviewer**

* Loads rules from `guidelines_index.json`
* Uses line-numbered code
* Checks pass/fail/not_applicable for each rule
* Outputs:

  * Violations list
  * per_rule_status
  * summary
* Supports *quick* and *full* modes

### **Agent C – Report Generator**

* Converts Agent B’s JSON into:

  * Professional Markdown report
  * Executive summary (manager-friendly)
* Saves `.md`, `.json`, `.txt`

---

## 📂 Project Structure

```
cpp-code-review-agent/
│
├── agent_a_analyzer.py
├── agent_b_reviewer.py
├── agent_c_reporter.py
├── run_full_pipeline.py
│
├── guidelines_index.json
│
├── samples/
│   ├── example1.cpp
│   └── bad_example.cpp
│
├── outputs/
│   └── (...auto-generated reports...)
│
├── requirements.txt
└── README.md
```

---

## 🔧 Installation

### **1. Create virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### **2. Install dependencies**

```bash
pip install -r requirements.txt
```

### **3. Install an LLM model using Ollama**

Examples:

```bash
ollama pull qwen2.5:14b-instruct
ollama pull qwen3:4b-instruct
ollama pull qwen2.5-coder:7b
```

---

## ▶️ Running the full pipeline

```bash
python run_full_pipeline.py
```

Pipeline output will be stored in:

```
outputs/
  agent_a_202402xx_xxxx.json
  agent_b_202402xx_xxxx.json
  agent_c_summary_202402xx_xxxx.txt
  agent_c_report_202402xx_xxxx.md
```

---

## 📘 Guideline Rules

Your project uses a **2000+ line JSON rule index** (MIC C++ coding standards):

Each rule follows this schema:

```json
{
  "rule_id": "IDN-001",
  "category": "IDN",
  "section": "Identifier Naming",
  "subsection": "Macros",
  "severity": "Error",
  "description": "Preprocessor identifiers must use UPPERCASE...",
  "raw_markdown": "Full rule text..."
}
```

Agent B automatically selects and evaluates relevant rules.

---

## 🧪 Sample Code

Add your own C++ code to `samples/` and reference it in your runner script.

---

## 🤖 Recommended Models

| Model                    | Performance  | Notes                          |
| ------------------------ | ------------ | ------------------------------ |
| **Qwen2.5-Coder 3B**     | ⚡ Fast       | Lightweight, good for testing  |
| **Qwen3 4B Instruct**    | ⭐ Balanced   | Best balance speed/accuracy    |
| **Qwen2.5 14B Instruct** | 🔥 Strongest | Best reasoning, best reporting |

---
