"""
Commands for managing and using specialized sub-agents.
"""
from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from .specialized_agents import specialized_agents
from .factory import create_agent


console = Console()


def list_specialized_agents() -> None:
    """List all available specialized agents."""
    agents = specialized_agents.list_agents()
    
    table = Table(title="🤖 Available Specialized Agents", show_header=True, header_style="bold cyan")
    table.add_column("Agent", style="bold green", width=20)
    table.add_column("Description", style="dim", width=50)
    table.add_column("Best For", style="yellow", width=30)
    
    # Add agent information
    agent_expertise = {
        "code_reviewer": "Code quality, bugs, security, performance",
        "architect": "System design, patterns, tech decisions",
        "debugger": "Complex bugs, error analysis, root causes", 
        "performance_expert": "Optimization, bottlenecks, scalability",
        "devops_engineer": "CI/CD, infrastructure, monitoring"
    }
    
    for agent_id, description in agents.items():
        expertise = agent_expertise.get(agent_id, "General assistance")
        table.add_row(agent_id, description, expertise)
    
    console.print()
    console.print(table)
    console.print()
    console.print("💡 [dim]Use[/dim] [cyan]/agent <agent_id> <question>[/cyan] [dim]to consult a specific agent[/dim]")
    console.print("💡 [dim]Use[/dim] [cyan]/agent auto <question>[/cyan] [dim]to auto-route to best agent[/dim]")


def consult_specialized_agent(agent_id: str, question: str, context: Dict[str, Any] = None) -> None:
    """Consult a specific specialized agent."""
    if context is None:
        context = {}
    
    # Validate agent exists
    agent_info = specialized_agents.get_agent_info(agent_id)
    if not agent_info:
        console.print(f"❌ [red]Unknown agent:[/red] {agent_id}")
        console.print("💡 Use [cyan]/agent list[/cyan] to see available agents")
        return
    
    # Show which agent we're consulting
    console.print(Panel.fit(
        f"🤖 Consulting: [bold cyan]{agent_info['name']}[/bold cyan]\n"
        f"📋 Specialty: {agent_info['description']}\n"
        f"❓ Question: {question}",
        title="Specialized Agent Consultation",
        border_style="cyan"
    ))
    
    try:
        # Get specialized prompt
        specialized_prompt = specialized_agents.get_agent_prompt(agent_id)
        
        # Create agent with specialized prompt
        specialized_agent = create_agent(
            system_prompt=specialized_prompt,
            use_claude_code_prompt=False  # Use specialized prompt instead
        )
        
        # Add context to question
        contextualized_question = question
        if context:
            context_info = []
            if context.get("project_path"):
                context_info.append(f"Project: {context['project_path']}")
            if context.get("file_path"):
                context_info.append(f"File: {context['file_path']}")
            if context_info:
                contextualized_question = f"Context: {', '.join(context_info)}\n\nQuestion: {question}"
        
        # Invoke specialized agent
        result = specialized_agent.invoke({
            "messages": [{"role": "user", "content": contextualized_question}]
        })
        
        # Extract and display response
        from ..cli import _safe_str
        response = _safe_str(result)
        
        if response.strip():
            console.print(Panel(
                Markdown(response),
                title=f"✨ {agent_info['name']} Response",
                border_style="green"
            ))
        else:
            console.print("❌ [red]No response from specialized agent[/red]")
            
    except Exception as e:
        console.print(Panel.fit(
            f"🚨 Error consulting {agent_info['name']}:\n{str(e)}\n\n"
            f"💡 Try:\n• Simplifying your question\n• Using /agent auto for automatic routing\n• Checking your API configuration",
            title="Agent Error",
            border_style="red"
        ))


def auto_route_question(question: str, context: Dict[str, Any] = None) -> None:
    """Automatically route a question to the best specialized agent."""
    if context is None:
        context = {}
    
    # Find best agent
    best_agent_id = specialized_agents.route_request(question, context)
    
    if not best_agent_id:
        console.print(Panel.fit(
            f"🤔 No specialized agent found for this question.\n"
            f"💭 Question: {question}\n\n"
            f"💡 This seems like a general question that doesn't require specialized expertise.\n"
            f"Try asking it directly to DeepAgents without the /agent command.",
            title="Auto-Routing Result",
            border_style="yellow"
        ))
        return
    
    # Show routing decision
    agent_info = specialized_agents.get_agent_info(best_agent_id)
    scores = specialized_agents._calculate_agent_scores(question)
    confidence = scores.get(best_agent_id, 0.0)
    
    console.print(Panel.fit(
        f"🎯 [bold green]Auto-Routing Decision:[/bold green]\n"
        f"🤖 Selected Agent: [cyan]{agent_info['name']}[/cyan]\n"
        f"📊 Confidence: [yellow]{confidence:.1%}[/yellow]\n"
        f"🎯 Reason: Best match for your question type",
        title="Intelligent Agent Routing",
        border_style="blue"
    ))
    
    # Consult the selected agent
    consult_specialized_agent(best_agent_id, question, context)


def show_routing_stats() -> None:
    """Show statistics about agent routing and usage."""
    stats = specialized_agents.get_routing_stats()
    
    if stats["total_requests"] == 0:
        console.print("📊 [dim]No specialized agent requests yet[/dim]")
        return
    
    table = Table(title="📈 Specialized Agent Usage Statistics", show_header=True)
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="cyan")
    
    table.add_row("Total Requests", str(stats["total_requests"]))
    table.add_row("Recent Requests (1h)", str(stats["recent_requests"]))
    table.add_row("Average Confidence", f"{stats['average_confidence']:.1%}")
    
    console.print()
    console.print(table)
    
    if stats.get("agent_usage"):
        console.print()
        usage_table = Table(title="🤖 Agent Usage (Recent)", show_header=True)
        usage_table.add_column("Agent", style="bold green")
        usage_table.add_column("Requests", style="cyan")
        usage_table.add_column("Percentage", style="yellow")
        
        total_recent = sum(stats["agent_usage"].values())
        for agent_id, count in sorted(stats["agent_usage"].items(), key=lambda x: x[1], reverse=True):
            agent_info = specialized_agents.get_agent_info(agent_id)
            agent_name = agent_info["name"] if agent_info else agent_id
            percentage = (count / total_recent) * 100
            usage_table.add_row(agent_name, str(count), f"{percentage:.1f}%")
        
        console.print(usage_table)


def get_agent_help() -> None:
    """Show help for agent commands."""
    help_text = """
# 🤖 Specialized Agents Help

## Available Commands:
- `/agent list` - Show all available specialized agents
- `/agent <agent_id> <question>` - Consult a specific agent
- `/agent auto <question>` - Auto-route to the best agent
- `/agent stats` - Show usage statistics

## Available Agents:
- **code_reviewer** - Code quality, bug detection, security review
- **architect** - System design, architecture patterns, tech decisions  
- **debugger** - Complex bug diagnosis and root cause analysis
- **performance_expert** - Performance optimization and bottleneck analysis
- **devops_engineer** - CI/CD, infrastructure, deployment, monitoring

## Examples:
```
/agent code_reviewer Can you review this authentication function for security issues?
/agent architect What's the best architecture pattern for a microservices API?  
/agent debugger I'm getting a null pointer exception in my React component
/agent performance_expert My database queries are running slowly
/agent auto How should I structure my CI/CD pipeline?
```

## Tips:
- Use **auto** when you're not sure which agent to consult
- Specialized agents have deep domain expertise and tailored prompts
- Each agent focuses on their specialty for better, more targeted responses
- Agents remember context about files and projects you're working on
    """
    
    console.print(Panel(
        Markdown(help_text),
        title="🤖 Specialized Agents Guide", 
        border_style="cyan"
    ))