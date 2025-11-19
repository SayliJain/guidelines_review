# **📘 Internal User Guide: Using GitHub Copilot Code Review in VS Code**

# **1. Overview**

This guide explains **how to use GitHub Copilot Code Review directly inside VS Code**
You will learn:

* How Copilot Code Review works in VS Code
* All the different ways to trigger a review
* How Copilot displays and applies suggestions
* How to use **custom instructions** to enforce our internal coding standards
* Best practices to get consistent, high-quality reviews

---

# **2. What Copilot Code Review Can Do**

In VS Code, Copilot Code Review can:

✔️ Review all **uncommitted local changes**
✔️ Review **a single file**, a function, or a code selection
✔️ Review code via **Copilot Chat**
✔️ Provide **inline comments** in your code
✔️ Suggest patches that you can **apply with 1 click**
✔️ Respect **custom code review rules** defined inside your repository

It essentially acts as an AI-powered teammate who reviews code *before you commit or push to GitLab*.

---

# **3. Setup Requirements**

Before you use Copilot review:

1. Install **GitHub Copilot** extension in VS Code
2. Sign in with your GitHub account that has **Copilot Pro**
3. Open a **Git repository** (GitLab clone) in VS Code

That’s it — no additional tools or GitHub.com configuration required.

---

# **4. Using Copilot Code Review**

Copilot review is available in **three different modes** inside VS Code:

---

## **4.1 Mode A — Review ALL Uncommitted Changes (Recommended Pre-Commit Step)**

This is the most powerful and most commonly used mode.

### **How to use:**

1. Open your project in VS Code
2. Click the **Source Control** icon on the left sidebar
3. At the top of the CHANGES panel, click:

👉 **“Copilot: Review Uncommitted Changes”**

Copilot will:

* Scan every uncommitted file
* Analyze diff chunks (added/modified lines)
* Insert **inline comments** with explanations + fix suggestions

### **How to act on Copilot comments:**

Open any changed file → You’ll see comments in the gutter.

Each comment may contain:

* What the issue is
* Why it matters
* A concrete **code patch**
* Buttons like:

  * **Apply suggestion**
  * **Apply & move to next**

This method is ideal as a **pre-commit AI quality gate**.

---

## **4.2 Mode B — Review a Specific File, Function, or Code Selection**

Use this when you want to focus on one area only.

### **Method 1 — From editor (right-click)**

1. Select the lines you want reviewed
2. Right-click → **Copilot → Review and Comment**

### **Method 2 — From Command Palette**

1. Press **Ctrl+Shift+P**
2. Type: **“GitHub Copilot: Review and Comment”**
3. Select the command

Copilot will ONLY review:

* The selection (if selected)
* Otherwise, usually the entire file

This is useful for:

* Complex functions
* Critical logic
* Refactoring work
* Reviewing code you're uncertain about

---

## **4.3 Mode C — Code Review Through Copilot Chat**

This is a conversational review.

### **How to use:**

1. Open **Copilot Chat** panel

2. Attach a file using:

   * The “Add file” button, **or**
   * Right-click → “Ask Copilot”

3. Ask:

   > “Review this file for bugs, performance issues, and bad patterns.”

OR:

> “Review only the changes I made today.”

Chat-based review allows back-and-forth fixes:

* “Explain that issue in detail.”
* “Rewrite the function following your suggested approach.”
* “Generate tests for the edge cases you found.”

Useful when refining tricky code.

---

# **5. Custom Instructions (Strongly Recommended)**

Custom instructions allow us to **enforce internal coding standards automatically**.
Even though we use GitLab, VS Code still reads `.github` folders locally — no GitHub hosting required.

## **5.1 Why use custom instructions?**

With instructions we can enforce:

* Code style
* Test requirements
* Architecture conventions
* Security standards
* Team preferences

Copilot will then review code **according to our rules**, not generic suggestions.

---

## **5.2 Repository-Wide Instructions**

Location:

```
.github/copilot-instructions.md
```

This file automatically influences:

* Code review comments
* Copilot Chat replies
* Suggestions & fixes

### **How to create it:**

1. Create `.github/` in your repo root
2. Inside it, create `copilot-instructions.md`
3. Add natural language rules

### **Example:**

```markdown
# Repository Coding Standards

## General
- Prefer small, single-purpose functions.
- Flag any duplicated logic—suggest reusable helpers.
- Enforce strict error handling in network, file I/O, or async operations.

## Python
- Require type hints for all new and modified functions.
- Recommend using pathlib over os.path.
- Warn against broad `except:` clauses.

## C++
- Use RAII and smart pointers instead of raw pointers.
- Prefer std::vector and safe container operations.
- Flag missing null checks or out-of-bounds access.

## TypeScript/React
- No `any` in new code.
- Always type props and state.
- Use functional components and hooks only.
- Enforce consistent styling and proper accessibility attributes.

## Testing
- Highlight untested behavior in new changes.
- Suggest missing edge-case tests.

## Security
- Flag hard-coded secrets.
- Ensure logs never include sensitive data.
```

Once this file is present, **all Copilot reviews in VS Code will follow it**.

---

## **5.3 Path-Specific Instructions**

Use when different parts of the repo have different rules.

### **Location:**

```
.github/instructions/*.instructions.md
```

### **Example: Backend Rules**

File: `.github/instructions/backend.instructions.md`

```yaml
---
applyTo: "backend/**/*.py"
---
```

```markdown
# Backend-Specific Rules
- Enforce async database operations where possible.
- Use our standard error response helper.
- Avoid direct HTTP calls; use our shared http_client wrapper.
```

### **Example: Frontend Rules**

File: `.github/instructions/frontend.instructions.md`

```yaml
---
applyTo: "frontend/**/*.{ts,tsx}"
---
```

```markdown
# Frontend Standards
- Use our design-system components first.
- Always validate props with TypeScript interfaces.
- Ensure proper ARIA attributes for interactive elements.
```

Copilot will use the correct rules based on file paths.

---

## **5.4 How to confirm instructions are working**

Add a temporary debug line:

```
- Copilot should include the phrase “Guidelines applied.”
```

Run **Review and Comment**.

If you see “Guidelines applied.” → it works.
Remove the debug line afterward.

---

# **6. Best Practices**

### **1. Run a review before every commit**

You’ll catch 80% of issues before they reach GitLab.

### **2. Keep your instruction files updated**

If Copilot suggests something undesirable → add a rule to prevent it.

### **3. Use selection reviews for hotspots**

Deep refactor? New business logic? Review *only* that part.

### **4. Validate Copilot suggestions**

Copilot is powerful, but not perfect — always use judgment.

### **5. Treat custom instructions as your “team brain”**

Put every recurring rule once → Copilot enforces them forever.

---

# **7. Summary**

Using GitHub Copilot Pro in VS Code with GitLab repos gives you:

* AI-powered pre-commit code review
* Granular, selection-based review
* Conversation-based review in Copilot Chat
* Inline suggestions with quick apply
* Enforceable team coding standards via local `.github` instructions

This workflow significantly improves code quality, reduces review cycles, and helps maintain consistent standards across the team.

