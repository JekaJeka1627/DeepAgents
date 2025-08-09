# 🧠 DeepAgents CLI - Claude Code Equivalent AI Assistant

> **A sophisticated, Claude Code-equivalent conversational AI with complete flexibility and control**

DeepAgents CLI is a **professional-grade AI assistant** that delivers Claude Code-level intelligence and capabilities while providing **complete model flexibility** and **unlimited customization**. Built on the powerful `deepagents` framework, it transforms natural language conversations into sophisticated development assistance.

## 🌟 **Key Features - Claude Code Equivalent Experience**

### 🧠 **Professional AI Intelligence**
- **Claude Code-inspired system prompt** - Professional expertise and sophisticated reasoning
- **Context-aware responses** - Deep understanding of projects, code patterns, and development workflows  
- **Best practices built-in** - Security, performance, and maintainability guidance
- **Error intelligence** - Graceful error handling with intelligent solution suggestions

### 🎨 **Advanced User Experience**
- **Claude Code-style Interface** - Persistent status bar with live updates (TIME, HOST, MODEL, FOLDER, BRANCH, PATH)
- **Smart Command Autocomplete** - Type `/` to see available commands with descriptions (like Claude Code)
- **12-hour time format** - Clean, readable status display
- **Syntax-highlighted output** - Beautiful code blocks with line numbers and themes
- **Context-aware formatting** - Smart formatting for code, files, errors, and git operations
- **Rich CLI interface** - Professional visual panels, progress indicators, and structured displays
- **Progressive disclosure** - Information revealed naturally as the conversation flows

### 🛠️ **30+ Sophisticated Tools**
- **Enhanced file operations** - Read with line numbers, write with backups, intelligent search
- **Smart project analysis** - Intelligent project structure overview and insights  
- **Advanced git integration** - Enhanced status, diffs, commits with visual formatting
- **Multi-file editing** - Atomic operations across multiple files with backup safety
- **Task management** - Built-in todo tracking and project organization
- **Code analysis** - Search, replace, and analyze across entire codebases

### ⚡ **Superior Flexibility**
- **Multi-LLM support** - OpenAI, Claude, Gemini, OpenRouter, or local models
- **Complete customization** - Modify prompts, tools, and behavior for your needs
- **Privacy-first** - Runs locally, your data stays under your control
- **Extensible architecture** - Easy to add new tools, prompts, and capabilities

### 🌱 **Project Origin and Evolution**

DeepAgents started from the concept outlined in [this GitHub repository](https://github.com/hwchase17/deepagents). Initially inspired by the foundational ideas presented there, DeepAgents has evolved significantly to far surpass the original concept. It now offers enhanced capabilities, flexibility, and control, making it a superior alternative to the initial framework.

## 🚀 **Quick Start - Get Running in 2 Minutes**

### **1. Install Dependencies** 
```bash
# Install all required packages (includes deepagents, langchain, rich formatting)
pip install -r requirements.txt
```

### **2. Configure Your LLM Provider**
Set your API key in `.env` file (already configured for OpenAI):
```bash
# OpenAI (Priority 1) - READY TO USE
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o

# OR use Claude (Priority 2) 
# ANTHROPIC_API_KEY=your_anthropic_key
# ANTHROPIC_MODEL=claude-3-5-sonnet-20240620

# OR use Gemini (Priority 3)
# GOOGLE_API_KEY=your_google_key  
# GEMINI_MODEL=gemini-1.5-pro-latest

# OR use OpenRouter (Priority 4 - supports many models)
# OPENROUTER_API_KEY=your_openrouter_key
# OPENROUTER_MODEL=openrouter/auto
```

### **3. Start Your Enhanced AI Assistant**
```bash
# Start the sophisticated CLI with Claude Code-style interface
python -m deepagents_cli.cli

# Features:
# ✅ Persistent status bar with live updates
# ✅ Command autocomplete (type /s to see commands)  
# ✅ 12-hour time format
# ✅ Git branch detection
# ✅ GPT-5 model support
```

## 💬 **Enhanced CLI Commands**

**Core Commands:**
- `:help` — Show comprehensive help with all enhanced features
- `:tools` — List all 30+ available tools with descriptions
- `:model` — Show current LLM configuration and provider priority
- `:quit` / `:exit` — Leave the CLI gracefully

**Claude Code-Style Slash Commands:**
- `/status` — Show comprehensive status line with all details
- `/s` — Autocomplete to see commands starting with 's'
- `/read FILE` — Read file with syntax highlighting
- `/task add DESC` — Add task to current list

**Advanced Commands:**
- `:debug on/off` — Toggle detailed debugging information  
- `:log on/off` — Enable verbose tool execution logging
- `:cd PATH` — Change working directory/sandbox root
- `:ls [PATH]` — List files with enhanced formatting
- `:tree [PATH]` — Show intelligent directory tree view
- `:proposals` — View pending file edit proposals
- `:accept ID` — Apply approved file changes safely

**Professional File Operations:**
- `:glob PATTERN` — Advanced file pattern matching (e.g., `**/*.py`)
- `:save PATH` — Save virtual filesystem state  
- `:load PATH` — Load virtual filesystem state

## 🛠️ **30+ Professional Tools Available**

### **📁 Enhanced File Operations**
- `read_file_with_context()` - Read files with line numbers and context (Claude Code style)
- `write_file_with_backup()` - Safe file writing with automatic backups
- `intelligent_search()` - Search with context lines and smart highlighting
- `multi_file_edit()` - Atomic operations across multiple files
- `fs_read()`, `fs_ls()`, `fs_glob()`, `fs_tree()` - Complete filesystem toolkit

### **🔄 Smart Git Integration**
- `smart_git_status()` - Enhanced git status with visual formatting and insights
- `git_diff()`, `git_log()`, `git_add()`, `git_commit()` - Full git workflow support
- `git_restore()` - Safe git operations with guidance

### **📊 Project Intelligence** 
- `project_structure()` - Intelligent project overview with insights
- `code_search()` - Advanced code search with pattern matching
- `replace_in_files()` - Bulk find/replace operations with safety
- `fs_set_root()` - Dynamic working directory management

### **✅ Task & State Management**
- `tasks_add()`, `tasks_done()`, `tasks_list()` - Built-in task tracking
- `vfs_write_tool()`, `vfs_read_tool()` - Virtual filesystem for persistence
- `propose_write()` - Safe file change proposals with review

### **🔧 System Operations**
- `echo()` - Diagnostic and testing tool
- `search_stub()` - Placeholder for future web search integration

## 🎯 **Usage Examples - See the Power**

### **🧠 Sophisticated Conversation**
```bash
You: "Analyze this Python project and suggest improvements for performance and maintainability"

AI: *Provides professional analysis with specific recommendations, code examples, and implementation strategies*
```

### **📝 File Operations with Intelligence**
```bash
You: "Show me the main.py file with line numbers and explain the key functions"

AI: *Displays beautifully formatted file with line numbers, syntax highlighting, and intelligent explanations*
```

### **🔍 Project Analysis**
```bash  
You: "Give me an overview of this project structure and identify potential issues"

AI: *Generates intelligent project tree, analyzes dependencies, identifies patterns, suggests improvements*
```

### **⚡ Multi-Step Development Tasks**
```bash
You: "Help me refactor this function, update the tests, and commit the changes"

AI: *Systematically handles each step with professional code quality, creates tests, makes intelligent commits*
```

## 🏗️ **Enhanced Project Architecture**

```
DeepAgents/ (Claude Code-Equivalent System)
├── 🧠 deepagents_cli/
│   ├── cli.py                          # Enhanced CLI with advanced formatting
│   └── agent/
│       ├── factory.py                  # Multi-LLM agent creation with enhanced prompts
│       ├── claude_code_prompt.py       # Professional Claude Code-inspired prompts  
│       ├── claude_formatter.py         # Advanced output formatting system
│       ├── claude_tools.py             # 6 enhanced Claude Code-style tools
│       ├── tools.py                    # 24+ comprehensive tool library
│       ├── config.py                   # Security and sandboxing configuration
│       ├── logging.py                  # Advanced debugging and tracing
│       └── state.py                    # Persistent state management
├── 📚 Documentation/
│   ├── README.md                       # This comprehensive guide
│   ├── QUICKSTART.md                   # Quick setup guide  
│   ├── ENHANCED_SUCCESS.md             # Complete feature overview
│   ├── CLAUDE_CODE_ENHANCEMENT_PLAN.md # Technical implementation details
│   └── requirements.txt                # All dependencies
├── 🧪 Testing/
│   ├── test_basic.py                   # Basic functionality tests
│   ├── test_enhanced.py                # Enhanced system tests
│   └── quick_test_enhanced.py          # Quick capability verification
└── 🚀 Utilities/
    ├── start_cli.sh                    # Convenient startup script
    └── .env                            # LLM provider configuration
```

## 🏆 **Why Choose DeepAgents Over Claude Code**

| Feature | Claude Code | **Enhanced DeepAgents** |
|---------|-------------|------------------------|
| **LLM Provider** | Claude only | OpenAI, Claude, Gemini, Local models |
| **Customization** | Fixed system | **Fully customizable prompts & tools** |
| **Privacy** | Cloud-dependent | **Runs locally, your data stays private** |
| **Cost Control** | Anthropic pricing | **Direct API costs, no markup** |
| **Extensions** | Limited | **Unlimited - add any capability** |
| **Tool Count** | Built-in only | **30+ professional tools** |
| **Output Quality** | Standard | **Enhanced formatting & syntax highlighting** |
| **Control** | Anthropic controls | **You control everything** |

## 🎓 **Perfect For**

- **Software Developers** - Professional code assistance, refactoring, debugging
- **DevOps Engineers** - System administration, deployment, infrastructure management  
- **Tech Leads** - Code review, architecture decisions, best practices guidance
- **Students & Learners** - Interactive coding education with professional examples
- **Teams** - Collaborative development with consistent coding standards
- **Anyone** seeking a **private, customizable Claude Code alternative**

## 🌟 **What Makes This Revolutionary**

1. **🧠 True Claude Code Intelligence** - Professional expertise with sophisticated reasoning
2. **🎨 Superior User Experience** - Advanced formatting, syntax highlighting, visual excellence  
3. **🛠️ Extensive Capabilities** - 30+ tools vs Claude Code's built-in limitations
4. **⚡ Complete Flexibility** - Any LLM, complete customization, unlimited extension
5. **🔒 Privacy & Control** - Your data, your models, your rules
6. **💰 Cost Efficiency** - Direct API costs with no platform markup
7. **🚀 Future-Proof** - Extensible architecture that grows with your needs

---

## 🎉 **Ready to Experience the Future of AI Development?**

**Start your enhanced AI assistant now:**

```bash
python3 -m deepagents_cli.cli
```

**Welcome to your Claude Code-equivalent system with complete freedom and control!** ✨

> *"All the intelligence and capability of Claude Code, with the flexibility and control you deserve."*