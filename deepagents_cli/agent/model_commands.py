"""
Commands for managing AI model selection and GPT-5 variants.
"""
import os
from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown


console = Console()


def show_gpt5_models() -> None:
    """Show available GPT-5 model variants with details."""
    table = Table(title="🚀 GPT-5 Model Variants (Available Now!)", show_header=True)
    table.add_column("Model", style="bold green", width=20)
    table.add_column("Description", style="dim", width=40)
    table.add_column("Input Price", style="cyan", width=15)
    table.add_column("Output Price", style="yellow", width=15)
    table.add_column("Best For", style="magenta", width=25)
    
    gpt5_models = [
        {
            "model": "gpt-5",
            "description": "Full GPT-5 with advanced reasoning and multimodal capabilities",
            "input_price": "$1.25/1M tokens",
            "output_price": "$10/1M tokens",
            "best_for": "Complex reasoning, coding, analysis"
        },
        {
            "model": "gpt-5-mini", 
            "description": "Smaller, faster GPT-5 variant with core capabilities",
            "input_price": "$0.25/1M tokens",
            "output_price": "$2/1M tokens", 
            "best_for": "General tasks, quick responses"
        },
        {
            "model": "gpt-5-nano",
            "description": "Ultra-lightweight GPT-5 for simple tasks",
            "input_price": "$0.05/1M tokens",
            "output_price": "$0.40/1M tokens",
            "best_for": "Simple queries, batch processing"
        },
        {
            "model": "gpt-5-chat-latest",
            "description": "ChatGPT-style GPT-5 without reasoning mode",
            "input_price": "$1.25/1M tokens",
            "output_price": "$10/1M tokens",
            "best_for": "Conversational AI, dialogue"
        }
    ]
    
    for model_info in gpt5_models:
        table.add_row(
            model_info["model"],
            model_info["description"],
            model_info["input_price"],
            model_info["output_price"],
            model_info["best_for"]
        )
    
    console.print()
    console.print(table)
    console.print()
    console.print("💡 [dim]Use[/dim] [cyan]/model set <model_name>[/cyan] [dim]to switch to a specific GPT-5 variant[/dim]")
    console.print("💡 [dim]Use[/dim] [cyan]/model benchmark[/cyan] [dim]to compare performance across models[/dim]")


def set_model(model_name: str) -> None:
    """Set the active model for DeepAgents."""
    # Validate model name
    valid_models = {
        "gpt-5": "Full GPT-5 with advanced reasoning",
        "gpt-5-mini": "Faster, more cost-effective GPT-5",
        "gpt-5-nano": "Ultra-lightweight GPT-5",
        "gpt-5-chat-latest": "ChatGPT-style GPT-5",
        "gpt-4o": "GPT-4 Optimized (previous generation)",
        "gpt-4o-mini": "GPT-4 Mini (cost-effective)",
        "claude-3-5-sonnet-20240620": "Claude 3.5 Sonnet",
        "gemini-1.5-pro-latest": "Google Gemini 1.5 Pro"
    }
    
    if model_name not in valid_models:
        console.print(f"❌ [red]Unknown model:[/red] {model_name}")
        console.print("💡 [dim]Available models:[/dim]")
        for model, desc in valid_models.items():
            console.print(f"   • [cyan]{model}[/cyan] - {desc}")
        return
    
    # Set environment variable
    os.environ["OPENAI_MODEL"] = model_name
    
    # Clear cached selection to force reselection
    from .factory import _get_selection_cache_path
    cache_path = _get_selection_cache_path()
    if cache_path.exists():
        cache_path.unlink()
    
    console.print(Panel.fit(
        f"✅ [bold green]Model updated successfully![/bold green]\n"
        f"🤖 [yellow]New model:[/yellow] [cyan]{model_name}[/cyan]\n"
        f"📝 [dim]Description:[/dim] {valid_models[model_name]}\n\n"
        f"🔄 [yellow]Note:[/yellow] The new model will be used for your next conversation.",
        title="Model Configuration Updated",
        border_style="green"
    ))


def benchmark_models() -> None:
    """Show performance benchmarks for available models."""
    console.print(Panel.fit(
        """🏆 **GPT-5 Performance Benchmarks** (August 2025)

**Coding Performance:**
• **SWE-bench Verified**: 74.9% (State-of-the-art)
• **Aider Polyglot**: 88% (Multi-language coding)
• **HumanEval**: 92%+ (Code generation)

**Key Improvements over GPT-4:**
• **Advanced Reasoning**: Integrated reasoning capabilities
• **256K Context**: Massive context window
• **Multimodal**: Text, code, images in single model
• **Tool Integration**: Better function calling

**Model Comparison:**
```
GPT-5 Full    ████████████████████ (Best reasoning, highest cost)
GPT-5 Mini    ███████████████      (Great performance, balanced cost)  
GPT-5 Nano    ██████████           (Fast responses, lowest cost)
GPT-4o        ████████████         (Previous generation)
Claude 3.5    ███████████████      (Strong alternative)
```

**Recommendation for DeepAgents:**
• **GPT-5** for complex code analysis and architectural decisions
• **GPT-5 Mini** for general development tasks (good balance)
• **GPT-5 Nano** for simple queries and batch operations""",
        title="Model Performance Analysis",
        border_style="blue"
    ))


def show_model_costs() -> None:
    """Show cost analysis for different models."""
    table = Table(title="💰 Model Cost Comparison", show_header=True)
    table.add_column("Model", style="bold")
    table.add_column("Input ($/1M)", style="green")
    table.add_column("Output ($/1M)", style="yellow") 
    table.add_column("Typical Session Cost", style="cyan")
    table.add_column("Best Use Case", style="magenta")
    
    cost_data = [
        ("gpt-5", "$1.25", "$10.00", "$0.15-0.50", "Complex analysis"),
        ("gpt-5-mini", "$0.25", "$2.00", "$0.03-0.10", "General development"),
        ("gpt-5-nano", "$0.05", "$0.40", "$0.01-0.03", "Simple queries"),
        ("gpt-4o", "$5.00", "$15.00", "$0.20-0.75", "Previous generation"),
        ("claude-3-5-sonnet", "$3.00", "$15.00", "$0.18-0.60", "Alternative choice")
    ]
    
    for model, input_cost, output_cost, session_cost, use_case in cost_data:
        table.add_row(model, input_cost, output_cost, session_cost, use_case)
    
    console.print()
    console.print(table)
    console.print()
    console.print("📊 [dim]Typical session = ~5K input tokens, ~2K output tokens[/dim]")
    console.print("💡 [dim]GPT-5 Mini offers the best balance of performance and cost for most development tasks[/dim]")


def show_model_features() -> None:
    """Show feature comparison across models."""
    features_text = """
# 🔧 Model Feature Comparison

## GPT-5 Features (New!)
- ✅ **Advanced Reasoning**: Built-in reasoning capabilities
- ✅ **256K Context**: Handle entire codebases
- ✅ **Multimodal**: Text, code, images, documents
- ✅ **Function Calling**: Enhanced tool integration
- ✅ **Structured Outputs**: JSON, XML, custom formats
- ✅ **Prompt Caching**: Reduced costs for repeated context
- ✅ **Batch API**: Cost-effective batch processing

## Feature Matrix

| Feature | GPT-5 | GPT-5 Mini | GPT-5 Nano | GPT-4o | Claude 3.5 |
|---------|-------|------------|------------|--------|-------------|
| **Reasoning** | ✅ Advanced | ✅ Basic | ❌ None | ❌ None | ✅ Good |
| **Context Length** | 256K | 256K | 128K | 128K | 200K |
| **Code Quality** | ★★★★★ | ★★★★ | ★★★ | ★★★★ | ★★★★★ |
| **Speed** | Medium | Fast | Very Fast | Medium | Medium |
| **Cost** | High | Medium | Low | High | High |
| **Multimodal** | ✅ Full | ✅ Full | ⚠️ Limited | ✅ Full | ✅ Full |

## DeepAgents Recommendations

### For Different Use Cases:
- **Complex Architecture**: GPT-5 (best reasoning)
- **Daily Development**: GPT-5 Mini (balanced performance)  
- **Batch Processing**: GPT-5 Nano (cost-effective)
- **Code Reviews**: GPT-5 or Claude 3.5 (both excellent)
- **Learning/Exploration**: GPT-5 Mini (good balance)

### Current Default: GPT-5
DeepAgents now defaults to GPT-5 for the best possible experience!
    """
    
    console.print(Panel(
        Markdown(features_text),
        title="Model Features & Recommendations",
        border_style="cyan"
    ))


def get_model_help() -> None:
    """Show comprehensive help for model commands."""
    help_text = """
# 🤖 Model Management Help

## Available Commands:
- `/model list` - Show available GPT-5 variants
- `/model set <model>` - Switch to specific model  
- `/model benchmark` - Show performance comparisons
- `/model costs` - Show cost analysis
- `/model features` - Show feature comparisons
- `/model help` - Show this help

## Quick Model Switching:
```bash
# Switch to full GPT-5 (best performance)
/model set gpt-5

# Switch to GPT-5 Mini (balanced)  
/model set gpt-5-mini

# Switch to GPT-5 Nano (cost-effective)
/model set gpt-5-nano

# Switch to ChatGPT-style GPT-5
/model set gpt-5-chat-latest
```

## Model Selection Guide:

### 🚀 **GPT-5** (Default)
- **Best for**: Complex reasoning, architecture decisions, detailed analysis  
- **Cost**: Higher ($1.25 input / $10 output per 1M tokens)
- **Speed**: Medium
- **Use when**: You need the absolute best AI capabilities

### ⚡ **GPT-5 Mini**  
- **Best for**: General development, code reviews, daily tasks
- **Cost**: Medium ($0.25 input / $2 output per 1M tokens)
- **Speed**: Fast  
- **Use when**: You want great performance at reasonable cost

### 💨 **GPT-5 Nano**
- **Best for**: Simple queries, batch processing, quick answers
- **Cost**: Low ($0.05 input / $0.40 output per 1M tokens)  
- **Speed**: Very Fast
- **Use when**: You need fast, cost-effective responses

### 💬 **GPT-5 Chat Latest**
- **Best for**: Conversational AI, dialogue-heavy interactions
- **Cost**: Same as GPT-5 
- **Speed**: Medium
- **Use when**: You prefer ChatGPT-style responses

## Environment Configuration:
You can also set your preferred model via environment variable:
```bash
export OPENAI_MODEL=gpt-5-mini
```

## Pro Tips:
- GPT-5 Mini is often the sweet spot for development work
- Use GPT-5 Nano for batch processing many simple tasks
- GPT-5 full is best for complex architectural decisions
- All variants support the same 256K context window
- Model switching takes effect on your next conversation
    """
    
    console.print(Panel(
        Markdown(help_text),
        title="🤖 Model Management Guide",
        border_style="cyan"
    ))