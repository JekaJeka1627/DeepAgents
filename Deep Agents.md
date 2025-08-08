https://github.com/hwchase17/deepagents explain this

###### **ChatGPT said:**

Here’s a clear and engaging explanation of **deepagents** from the GitHub repository by **hwchase17**:

---

## **What Are Deep Agents?**

Deep Agents are more advanced than simple LLM‑based agents that loop through tasks. Instead, they’re designed for **longer, more complex tasks** by incorporating four critical features:

1. A **planning tool**

2. The ability to use **sub‑agents**

3. Access to a **(virtual) file system**

4. A **detailed system prompt** guiding the agent’s behavior [LangChain Blog+15GitHub+15colinmcnamara.com+15](https://github.com/hwchase17/deepagents?utm_source=chatgpt.com)

---

## **deepagents Python Package**

The repository provides a **Python package** that makes building your own Deep Agent straightforward:

**Installation**:

 bash  
CopyEdit  
`pip install deepagents`

*  It’s built on top of LangGraph and uses a robust default system prompt inspired by Claude Code’s but made more general [colinmcnamara.com+4GitHub+4LangChain Blog+4](https://github.com/hwchase17/deepagents?utm_source=chatgpt.com).

* **Core Features**:

  * **Planning Tool**: Even though it does nothing functionally—a no‑op—it helps structure the agent’s thought process by maintaining a todo list in context [colinmcnamara.com+3LangChain Blog+3GitHub+3](https://blog.langchain.com/deep-agents/?utm_source=chatgpt.com).

  * **Sub‑Agents**: You can define specialized agents for subtasks (“research agent,” etc.), helping manage context and complexity [GitHub](https://github.com/hwchase17/deepagents?utm_source=chatgpt.com)[LangChain Blog](https://blog.langchain.com/deep-agents/?utm_source=chatgpt.com).

  * **Virtual File System Tools**: Tools like `ls`, `read_file`, `write_file`, and `edit_file` mimic file system behavior using LangGraph’s state rather than affecting your real files [GitHub+1](https://github.com/hwchase17/deepagents?utm_source=chatgpt.com).

  * **Detailed System Prompt**: A well-crafted, comprehensive prompt steers how agents plan, call tools, spawn subagents, and use the file system [colinmcnamara.com+5LangChain Blog+5Hacker News+5](https://blog.langchain.com/deep-agents/?utm_source=chatgpt.com).

---

## **How to Use a Deep Agent — Quick Example**

python  
CopyEdit  
`from deepagents import create_deep_agent`

`# Define a tool`  
`def internet_search(query: str, max_results=5, topic="general", include_raw_content=False):`  
    `# Implementation using an API of your choice`  
    `return search_results`

`# Provide instruction to shape agent behavior`  
`research_instructions = """`  
`You are an expert researcher. Your job is to conduct thorough research, and then write a polished report.`

`You have access to a few tools.`  
`` ## `internet_search` ``  
`Use this to run an internet search for a given query.`  
`"""`

`# Create the Deep Agent`  
`agent = create_deep_agent(`  
    `[internet_search],`  
    `research_instructions,`  
`)`

`# Invoke the agent`  
`result = agent.invoke({"messages": [{"role": "user", "content": "what is LangGraph?"}]})`

This agent leverages planning, subagents, and the built-in systems to perform deeper research tasks [GitHub+1](https://github.com/hwchase17/deepagents?utm_source=chatgpt.com)[colinmcnamara.com](https://www.colinmcnamara.com/blog/deep-agents-part-4-usage-integration-roadmap?utm_source=chatgpt.com).

---

## **Under the Hood & Influence**

* Built atop **LangGraph**, deepagents uses a reactive agent architecture: the LLM evaluates whether to take action or stop, executes tools, and iterates [YouTube+11colinmcnamara.com+11colinmcnamara.com+11](https://colinmcnamara.com/blog/deep-agents-part-1-beyond-shallow?utm_source=chatgpt.com).

* It also supports customizing the **model** (e.g., `claude-sonnet-4-20250514` by default, with a large 64,000 token context window) or switching to your preferred LLM via LangChain [colinmcnamara.com+1](https://colinmcnamara.com/blog/deep-agents-part-1-beyond-shallow?utm_source=chatgpt.com).

* As noted in the LangChain (official) blog, Depth Agents are a growing framework for building intelligent systems that handle long-horizon tasks beyond simple loops [GitHub+10LangChain Blog+10colinmcnamara.com+10](https://blog.langchain.com/deep-agents/?utm_source=chatgpt.com).

---

## **Summary**

| Feature | Purpose |
| ----- | ----- |
| **Planning Tool** | Helps keep the agent on track, even if it's a no‑op |
| **Sub‑Agents** | Manage complexity by delegating specialized tasks |
| **Mock File System** | Enables stateful, persistent context without real file access |
| **Detailed Prompt** | Ensures deep, guided behavior |

`deepagents` thus empowers developers to create **deeply capable, customizable agents** that go beyond superficial LLM interactions—for research, code generation, planning, and more.

---

Want help building a specific deepagent use case, or diving deeper into customization like model selection or sub‑agent workflows? Just let me know\!

Sources

##### **You said:**

I use Claude code. is this similar to that except I can plug in any LLM as main orchestrator, and sub-agents?

###### **ChatGPT said:**

Yes — you're exactly right.

**deepagents** is conceptually **very similar to Claude Code**, but it's designed to be **model-agnostic**, **tool-extensible**, and **highly modular**. Here’s how they compare and why `deepagents` might be a great addition to your stack:

---

## **✅ Similarities to Claude Code**

| Feature | Claude Code | deepagents |
| ----- | ----- | ----- |
| 🧠 **Agent with planning** | Has persistent goals & task memory | Uses an explicit planning step and task list |
| 🤖 **Sub-agents** | Built-in with Claude Code structure | You can define and spawn sub-agents freely |
| 📁 **Virtual file system** | Yes (limited Claude tools) | Yes (via LangGraph state, with read/write/edit) |
| 📜 **System prompt structure** | Detailed and structured | Inspired by Claude Code’s format (but general) |
| 🔁 **Loops through thought/tool/response** | Yes | Yes, using LangGraph reactive loop |

---

## **🔄 Key Differences (Advantages of deepagents)**

| Area | What deepagents Adds or Improves |
| ----- | ----- |
| 💡 **LLM Flexibility** | You can use **any LLM** via LangChain (OpenAI, Claude, Mistral, local, etc.) |
| 🧩 **Custom Tools** | Plug in arbitrary Python functions or toolchains |
| 🔀 **Custom Sub-agent Types** | Sub-agents can have **unique prompts, tools, and models** |
| 💻 **Virtual Filesystem Control** | File-like context is under your control—great for long-term workflows |
| 🧠 **Language Model Planning** | Even if "planning" is a no-op, the agent still **tracks tasks explicitly** |
| 🕸️ **LangGraph Integration** | Full control over graph state, flow, retry logic, etc. |

---

## **🧠 How You Might Use It (Compared to Claude Code)**

If you like **Claude Code** because:

* it gives structure to agents,

* it supports subagents and thought chains,

* and it's highly capable with long context...

...then you'll likely love `deepagents` **if** you want:

* to **swap in any orchestrator model**, including local ones (e.g., Qwen, Holo1, Mistral),

* to **control and customize tools** easily,

* or to extend your system to a **multi-agent architecture** with planning and file memory.

---

## **🛠️ Example Setup You Could Build**

python  
CopyEdit  
`from deepagents import create_deep_agent`

`# Custom tools`  
`def query_github_repo(topic: str) -> str:`  
    `return f"Searching GitHub for {topic}..."`

`# Specialized instructions`  
`sentellent_agent_prompt = """`  
`You're the Sentellent Research Assistant. Your job is to investigate features or legal issues in intelligent assistants.`  
`Use your tools, spawn helper agents if needed, and write findings to file.`  
`"""`

`# Create a top-level orchestrator using Claude, GPT-4, or your own LLM`  
`agent = create_deep_agent(`  
    `tools=[query_github_repo],`  
    `system_prompt=sentellent_agent_prompt,`  
    `llm="your-claude-wrapper-or-openai-client"  # Flexible!`  
`)`

`# Run it`  
`agent.invoke({"messages": [{"role": "user", "content": "Explore auto-delegation in AI assistants"}]})`

---

## **🔍 Should You Use Both?**

* You can **continue using Claude Code** where Anthropic excels (e.g., coding, structured evals).

* Use **deepagents** when you want:

  * more open architecture,

  * deeper tool/subagent orchestration,

  * and full control over models and flows.

---

Would you like help adapting your Claude Code workflows into a `deepagents` architecture — maybe even using Claude itself as one of the LLMs? I can scaffold a starter setup if you want.

##### **You said:**

does it have a built in UI like Claude does? Claude is command line but conversational.

###### **ChatGPT said:**

No — **`deepagents` does *not* come with a built-in UI or conversational CLI like Claude Code currently does**.

Instead, `deepagents` is a **Python library** designed to give you the building blocks to **define, run, and extend multi-agent systems** — but **you have to bring your own interface** if you want a CLI or web UI.

---

### **🧱 Here’s what it provides:**

* An `invoke()` function for calling agents in code.

* LangGraph-backed logic for managing memory, tools, planning, and sub-agents.

* Virtual file system and internal agent state modeling.

* Tool and sub-agent APIs you can extend.

* No UI included — not even a basic REPL loop or CLI out of the box.

---

### **✅ What Claude Code gives you that deepagents doesn’t:**

| Claude Code | deepagents |
| ----- | ----- |
| 🖥️ CLI interface for chat with agents | ❌ No CLI — you call it programmatically |
| 💬 Conversational prompt & reply loop | ❌ Must build your own loop (or use notebooks) |
| 📂 Automatic file scaffolding (via CLI tools) | ❌ You must write scaffolding manually |
| 🤖 Plug-and-play with Anthropic agents | ✅ LLM-agnostic, but you must configure them |

---

### **🛠️ How to get an interactive experience with `deepagents`**

Here are some quick ways you can get something Claude-like:

#### **1\. Simple Python Chat Loop (CLI)**

python  
CopyEdit  
`while True:`  
    `user_input = input("You: ")`  
    `result = agent.invoke({`  
        `"messages": [{"role": "user", "content": user_input}]`  
    `})`  
    `print("Agent:", result["output"])`

#### **2\. Use Streamlit or Gradio for a web UI**

You could wrap the same logic into a simple web app. I can help scaffold that if you want.

#### **3\. Use in Jupyter or IPython**

Each `agent.invoke()` call acts like a prompt-response loop. Great for debugging and testing.

---

### **💡 TL;DR**

* **Claude Code** is a conversational agent with a built-in CLI and dev tooling.

* **deepagents** is a flexible multi-agent library — powerful but **you build the interface**.

* If you want Claude’s friendly REPL style with deepagents’ flexibility, you’ll need to glue them together — and I can help you do that.

Want me to help you build a `deepagents`\-powered command-line chat interface next?

##### **You said:**

yes, it would be great to use this but with a simple interface without sacrificing the power.

###### **ChatGPT said:**

Perfect — let’s build you a **simple yet powerful CLI chat interface** for `deepagents`, giving you Claude Code–style interaction while keeping all the depth of sub-agents, tools, and planning.

---

## **🧠 Overview of What We’ll Build**

A Python script that:

* Initializes a `deepagent` with tools, subagents, etc.

Starts a CLI loop like:

 vbnet  
CopyEdit  
`You: What's the capital of Brazil?`  
`Agent: The capital of Brazil is Brasília.`

*   
* Shows subagent/tool use inline when relevant

* Optionally supports saving/loading file system state

---

## **🛠️ Requirements**

Install these first:

bash  
CopyEdit  
`pip install deepagents langchain langgraph`

Also ensure you have an LLM setup. For OpenAI:

bash  
CopyEdit  
`pip install openai`  
`export OPENAI_API_KEY=your-key`

---

## **🧩 Code: `deepagents_chat.py`**

python  
CopyEdit  
`from deepagents import create_deep_agent`  
`from langchain.chat_models import ChatOpenAI  # swap out for Claude or others`  
`import os`

`# Optional: custom tool`  
`def search_tool(query: str) -> str:`  
    `return f"Searching for '{query}'... (fake result)"`

`# Agent system prompt`  
`system_prompt = """`  
`You're an expert assistant. You can research, reason, and complete complex tasks.`  
`Use planning, the virtual file system, and subagents when helpful.`  
`"""`

`# Initialize agent`  
`agent = create_deep_agent(`  
    `tools=[search_tool],  # Add more tools here`  
    `system_prompt=system_prompt,`  
    `llm=ChatOpenAI(model="gpt-4", temperature=0)  # Replace with your preferred LLM`  
`)`

`def main():`  
    `print("🧠 DeepAgent CLI\nType 'exit' to quit.\n")`

    `while True:`  
        `user_input = input("You: ").strip()`  
        `if user_input.lower() in ["exit", "quit"]:`  
            `break`

        `response = agent.invoke({`  
            `"messages": [{"role": "user", "content": user_input}]`  
        `})`

        `print("Agent:", response.get("output", "[No response]"))`

`if __name__ == "__main__":`  
    `main()`

---

## **🔄 What You Can Add Later**

* 🔧 Real tools (e.g., web search, GitHub query, file I/O)

* 🧠 Sub-agents for code, research, etc.

* 💾 Save/load agent state for persistence across sessions

* 🖥️ Add a Streamlit or TUI frontend

---

## **✅ Next Steps**

Would you like me to:

1. Help you **customize this script with Claude via `anthropic`**?

2. Add **a virtual file system view** (e.g., `ls`, `cat`, `write`)?

3. Add **agent logging** (see how it planned, what tools it used)?

4. Add **real sub-agent definitions**?

Let me know what flavor you want first, and I’ll extend it with you.

