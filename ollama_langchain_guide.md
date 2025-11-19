# A quick Ollama and Langchain guide


## 1. What is Ollama?

**Ollama** is a local LLM runtime. Think of it as:

> “Like using OpenAI, but everything runs on your own GPU/CPU.”

* It:

  * Downloads models (Llama, Qwen, Mistral, etc.).
  * Manages GPU/CPU usage.
  * Exposes a **local HTTP API** (default: `http://localhost:11434`).
* Good match for your **RTX A4000 (16 GB VRAM)** – can comfortably run:

  * 7B models easily,
  * 8–14B with decent performance,
  * larger ones with some performance trade-offs.

---

## 2. Install Ollama on your office desktop (Windows)
### Ollama is already installed on this system so you can skip this step

### Step 2.1 – Download & Install

1. Go to **ollama.com** (on your office machine).
2. Download the **Windows installer (.exe)**.
3. Run the installer → follow defaults.
4. After installation, open **Command Prompt** or **PowerShell** and type:

```bash
ollama --version
```

If it prints a version string (e.g., `ollama version 0.4.x`), you’re good.

> If Ollama doesn’t start, restart the machine once. On Windows, Ollama usually runs as a background service automatically.

---

## 3. Pull and test a model

Let’s use **Llama 3.1 (8B)** or **Qwen 2.5 (7B)** – both are good all-rounders that fit nicely in 16 GB VRAM.

### 3.1 – Download (pull) a model

In PowerShell:

```bash
ollama pull llama3.1
```

or

```bash
ollama pull qwen2.5
```

This:

* Downloads the model weights,
* Prepares them for local use.



To list already available/downloaded models, use the following command


```bash
ollama list
```
### 3.2 – Chat with the model from terminal

```bash
ollama run llama3.1
```

You’ll see a prompt like:

```text
>>> 
```

Type a question:

```text
>>> What can you do as a local AI assistant?
```

To exit: type `Ctrl + C` or `/bye` depending on the shell.

---

## 4. Using the Ollama HTTP API (concept)

For **LangChain**, we don’t use the terminal directly. We talk to Ollama over **HTTP**.

* By default, Ollama exposes an API at:

  * `http://localhost:11434/api/chat` for chat models.

Basic request structure (you don’t have to memorize this; LangChain hides it):

```json
POST /api/chat
{
  "model": "llama3.1",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ]
}
```

LangChain will handle this under the hood with its `Ollama` classes.

---

## 5. Setting up Python and LangChain

### 5.1 – Install Python (if not already)

* Install **Python 3.10+** from python.org.
* In the installer, **tick**: “Add Python to PATH”.

### 5.2 – Create a project folder

Example (you can adapt folder names to your GE workspace):

```bash
mkdir ollama_langchain_agent
cd ollama_langchain_agent
```

### 5.3 – Create a virtual environment (good practice even for beginners)

```bash
python -m venv .venv
.\.venv\Scripts\activate  # on Windows PowerShell
```

You should now see something like `(.venv)` at the beginning of your terminal prompt.

### 5.4 – Install required Python packages

We’ll keep the stack small:

```bash
pip install langchain langchain-ollama pydantic typing-extensions
```

> `langchain-ollama` is the official integration package; it knows how to talk to your local Ollama server.

---

## 6. Your first LangChain + Ollama script

Create a file called `basic_chat.py`:

```python
from langchain_ollama import ChatOllama

def main():
    # 1. Connect to local Ollama model
    llm = ChatOllama(
        model="llama3.1",      # or "qwen2.5"
        temperature=0.7,       # how creative vs deterministic
    )

    # 2. Simple one-off chat call
    user_question = "Explain what a GPU is in simple terms for a 12-year-old."
    response = llm.invoke(user_question)

    print("User:", user_question)
    print("Model:", response.content)

if __name__ == "__main__":
    main()
```

Run it:

```bash
python basic_chat.py
```

You should see your question and the model’s answer printed.

### What’s happening?

* `ChatOllama` → tells LangChain: “Use Ollama as the backend.”
* `llm.invoke(text)` → sends your text to `localhost:11434`.
* Response is a **chat message object**; we print `response.content`.

---

## 7. Turning this into a *very basic agent*

An “agent” is just:

> A loop where the AI:
>
> 1. Reads your question,
> 2. Decides whether to use tools (functions),
> 3. Calls them if needed,
> 4. Responds with the final answer.

We’ll build:

* A **toy agent** with:

  * A **calculator tool** (e.g., “What is 13*7 + 22?”).
  * The LLM decides when to use that tool.

This keeps it understandable for beginners but still “agentic”.

---

## 8. Step 1 – Define a simple tool

Create `basic_agent.py`:

```python
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage

# 1. Define a simple Python tool
@tool
def calculator(expression: str) -> str:
    """
    Evaluate a basic math expression safely.
    Example: "13 * 7 + 22"
    """
    try:
        # WARNING: eval is dangerous in real-world use.
        # For demo purposes only. Use a math parser in production.
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"


def main():
    # 2. Connect to Ollama LLM
    llm = ChatOllama(
        model="llama3.1",  # or "qwen2.5"
        temperature=0.2,   # low temperature for reasoning
    )

    # 3. Bind tools to the LLM (so it “knows” it can call them)
    llm_with_tools = llm.bind_tools([calculator])

    # 4. System prompt: tell the model how to behave
    system_prompt = (
        "You are a helpful assistant. "
        "When the user asks a math question, use the 'calculator' tool. "
        "If it's not math, just answer normally. "
        "Always explain your reasoning in simple terms."
    )

    # 5. Get user input (for demo, we hardcode; can use input() instead)
    user_question = "If I have 13 apples and buy 7 more, then give away 4, how many do I have?"

    # 6. Create messages for the LLM
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_question),
    ]

    # 7. Call the LLM with tools enabled
    ai_message = llm_with_tools.invoke(messages)

    print("User:", user_question)
    print("\nRaw AI message:", ai_message)

    # 8. Check if the model wants to call a tool
    if ai_message.tool_calls:
        for call in ai_message.tool_calls:
            if call["name"] == "calculator":
                expr = call["args"]["expression"]
                tool_result = calculator(expr)
                print(f"\n[Tool call] calculator({expr}) = {tool_result}")

                # 9. Send the tool result back to the model for final answer
                followup_messages = messages + [
                    ai_message,
                    # simulate tool result message:
                    HumanMessage(content=f"The result of your calculation is: {tool_result}")
                ]
                final_answer = llm.invoke(followup_messages)
                print("\nFinal answer:\n", final_answer.content)
    else:
        # If no tools used, just print the response
        print("\nAssistant:\n", ai_message.content)


if __name__ == "__main__":
    main()
```

Run:

```bash
python basic_agent.py
```

### What you should observe

* The model:

  * Receives the system instructions.
  * Sees it can use `calculator`.
  * For math questions, it **may** emit a `tool_calls` field.
* We:

  * Detect `tool_calls`,
  * Execute the Python tool,
  * Send the tool result back to the LLM,
  * Get a final, human-friendly answer.

This is a minimal example of an **agent loop**.

---

## 9. Making it friendlier for non-programmers

If some teammates are not comfortable editing Python, you can:

### 9.1 – Turn user_question into `input()`

Modify in `main()`:

```python
    user_question = input("Ask me anything (math or general): ")
```

Now they can just run:

```bash
python basic_agent.py
```

and type questions interactively.

### 9.2 – Add simple comments in plain English

For colleagues with less experience, you can add comments like:

```python
# This connects to the local AI model that is already running via Ollama.
llm = ChatOllama(model="llama3.1", temperature=0.2)
```

---

## 10. Example: Simple “internal docs” helper

Imagine later you want to build a **code review helper** or **doc Q&A** using local models. A basic RAG-style helper using Ollama + LangChain looks like this:

> I’ll keep it short and conceptual so it doesn’t overwhelm non-programmers.

### 10.1 – High-level idea

1. **Load documents** (e.g., `.txt` / `.md` / `.pdf`).
2. **Split into chunks**.
3. **Convert to embeddings** and store in a vector store.
4. When user asks a question:

   * Retrieve the most relevant chunks.
   * Provide these chunks + question to Ollama via LangChain.

### 10.2 – Minimal code skeleton (no real docs yet)

```python
from langchain_ollama import ChatOllama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores import FAISS

def build_simple_rag():
    # 1. Fake “docs” – replace with your real text later
    docs = [
        "Our code review agent checks C++ code for guideline violations.",
        "It runs on the RTX A4000 machine in the MIC team.",
    ]

    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
    split_docs = splitter.create_documents(docs)

    # 2. Use Ollama embeddings
    embeddings = OllamaEmbeddings(model="llama3.1")  # or another embedding-capable model
    vectordb = FAISS.from_documents(split_docs, embeddings)

    # 3. Ask a question
    question = "Where does our code review agent run?"
    relevant_docs = vectordb.similarity_search(question, k=2)

    # 4. Send context + question to LLM
    context_text = "\n\n".join([d.page_content for d in relevant_docs])

    llm = ChatOllama(model="llama3.1", temperature=0)
    prompt = f"Use the context below to answer the question.\n\nContext:\n{context_text}\n\nQuestion: {question}\nAnswer:"

    answer = llm.invoke(prompt)
    print("Q:", question)
    print("A:", answer.content)

if __name__ == "__main__":
    build_simple_rag()
```

This is a **tiny version of a local RAG agent**:

* Helpful starting point for your internal code review / MIC documentation helpers.

---

## 11. RTX A4000 specific notes 

On  **RTX A4000 (16 GB VRAM)**:

* Good model sizes:

  * **7B / 8B**: smooth, fast.
  * **14B**: okay, but slower; still usable for code tasks.
* Tips:

  * Prefer **smaller, instruction-tuned** models for agents (e.g., `qwen2.5:14b-instruct`, `llama3.1` variants).
  * If you hit **OOM (out-of-memory)**:

    * Use the `Q4_K_M` quantized variants (Ollama usually does this automatically).
    * Try a smaller model (`qwen2.5:7b` instead of `14b`, etc.).



