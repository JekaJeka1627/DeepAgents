"""
Commands for managing and executing smart workflows.
"""
import json
from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from .smart_workflows import workflow_engine


console = Console()


def list_workflows() -> None:
    """List all available smart workflows."""
    workflow_engine.list_workflows()


def execute_workflow(workflow_id: str, params_str: str = "") -> None:
    """Execute a specific workflow with parameters."""
    # Parse parameters
    params = {}
    if params_str.strip():
        try:
            # Try to parse as JSON first
            if params_str.strip().startswith('{'):
                params = json.loads(params_str)
            else:
                # Parse as key=value pairs
                param_pairs = params_str.split()
                for pair in param_pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        params[key.strip()] = value.strip()
        except Exception as e:
            console.print(f"❌ [red]Error parsing parameters:[/red] {e}")
            console.print("💡 Use format: [cyan]key=value key2=value2[/cyan] or JSON: [cyan]{'key': 'value'}[/cyan]")
            return
    
    # Check if workflow exists
    if workflow_id not in workflow_engine.workflows:
        console.print(f"❌ [red]Unknown workflow:[/red] {workflow_id}")
        console.print("💡 Use [cyan]/workflow list[/cyan] to see available workflows")
        return
    
    workflow = workflow_engine.workflows[workflow_id]
    
    # Interactive parameter gathering if needed
    missing_params = []
    all_required_params = set()
    
    for step in workflow["steps"]:
        all_required_params.update(step.required_params)
    
    for param in all_required_params:
        if param not in params:
            missing_params.append(param)
    
    if missing_params:
        console.print(Panel.fit(
            f"🔧 [yellow]Workflow requires additional parameters:[/yellow]\n" +
            "\n".join([f"• {param}" for param in missing_params]),
            title=f"Parameters for {workflow['name']}",
            border_style="yellow"
        ))
        
        # Interactive parameter collection
        for param in missing_params:
            value = Prompt.ask(f"Enter value for [cyan]{param}[/cyan]")
            if value:
                params[param] = value
    
    # Confirm execution
    console.print(Panel.fit(
        f"🚀 [bold]Ready to execute:[/bold] {workflow['name']}\n"
        f"📋 [dim]{workflow['description']}[/dim]\n"
        f"⚙️ [yellow]Parameters:[/yellow] {json.dumps(params, indent=2)}",
        title="Workflow Confirmation",
        border_style="blue"
    ))
    
    if not Confirm.ask("Continue with workflow execution?", default=True):
        console.print("❌ Workflow execution cancelled")
        return
    
    # Execute workflow
    result = workflow_engine.execute_workflow(workflow_id, params)
    
    # Show detailed results
    if result.success:
        show_workflow_results(workflow_id, result)
    else:
        show_workflow_errors(workflow_id, result)


def suggest_workflow(description: str) -> None:
    """Suggest the best workflow based on user description."""
    suggested = workflow_engine.suggest_workflow(description)
    
    if suggested:
        workflow = workflow_engine.workflows[suggested]
        console.print(Panel.fit(
            f"💡 [bold green]Suggested Workflow:[/bold green] {workflow['name']}\n"
            f"📋 [dim]{workflow['description']}[/dim]\n\n"
            f"🚀 [yellow]To execute:[/yellow] [cyan]/workflow {suggested}[/cyan]",
            title="Workflow Suggestion",
            border_style="green"
        ))
        
        # Show workflow details
        console.print("\n📋 **Workflow Steps:**")
        for i, step in enumerate(workflow["steps"], 1):
            console.print(f"   {i}. [bold]{step.name}[/bold] - {step.description}")
        
        console.print(f"\n⏱️ **Estimated Time:** {sum(step.estimate_seconds for step in workflow['steps'])//60} minutes")
        
        if Confirm.ask(f"\nExecute [cyan]{suggested}[/cyan] workflow now?", default=False):
            execute_workflow(suggested)
            
    else:
        console.print(Panel.fit(
            f"🤔 [yellow]No specific workflow found for:[/yellow] \"{description}\"\n\n"
            f"💡 [dim]Available workflows:[/dim]",
            title="No Match Found",
            border_style="yellow"
        ))
        list_workflows()


def show_workflow_results(workflow_id: str, result) -> None:
    """Show detailed workflow execution results."""
    workflow = workflow_engine.workflows[workflow_id]
    
    console.print(Panel.fit(
        f"📊 [bold green]Workflow Results:[/bold green] {workflow['name']}\n"
        f"✅ [green]Status:[/green] Completed Successfully\n"
        f"⏱️ [yellow]Execution Time:[/yellow] {result.execution_time:.1f} seconds\n"
        f"📈 [cyan]Steps Completed:[/cyan] {result.steps_completed}/{result.total_steps}",
        title="Workflow Success Summary",
        border_style="green"
    ))
    
    # Show step-by-step results
    if result.results:
        console.print("\n📋 **Step Results:**")
        for step_key, step_result in result.results.items():
            step_name = step_key.split('_', 2)[-1] if '_' in step_key else step_key
            console.print(f"\n   🔹 **{step_name.title().replace('_', ' ')}**")
            
            if isinstance(step_result, dict):
                for key, value in step_result.items():
                    console.print(f"     • {key.replace('_', ' ').title()}: [cyan]{value}[/cyan]")
            else:
                console.print(f"     • Result: [cyan]{step_result}[/cyan]")


def show_workflow_errors(workflow_id: str, result) -> None:
    """Show workflow execution errors."""
    workflow = workflow_engine.workflows[workflow_id]
    
    console.print(Panel.fit(
        f"❌ [bold red]Workflow Failed:[/bold red] {workflow['name']}\n"
        f"⏱️ [yellow]Execution Time:[/yellow] {result.execution_time:.1f} seconds\n"
        f"📈 [cyan]Steps Completed:[/cyan] {result.steps_completed}/{result.total_steps}\n"
        f"🚨 [red]Errors:[/red] {len(result.errors)}",
        title="Workflow Error Summary",
        border_style="red"
    ))
    
    if result.errors:
        console.print("\n🚨 **Errors Encountered:**")
        for i, error in enumerate(result.errors, 1):
            console.print(f"   {i}. [red]{error}[/red]")
        
        console.print("\n💡 **Troubleshooting Tips:**")
        console.print("   • Check that all required parameters are provided")
        console.print("   • Ensure file paths exist and are accessible")
        console.print("   • Verify API keys and tool dependencies are configured")
        console.print("   • Try running individual steps manually for debugging")


def show_workflow_history() -> None:
    """Show execution history of workflows."""
    if not workflow_engine.execution_history:
        console.print("📜 [dim]No workflow execution history yet[/dim]")
        return
    
    from rich.table import Table
    
    table = Table(title="📜 Workflow Execution History", show_header=True)
    table.add_column("Time", style="dim", width=12)
    table.add_column("Workflow", style="bold", width=20)
    table.add_column("Status", style="bold", width=10)
    table.add_column("Duration", style="cyan", width=10)
    table.add_column("Steps", style="yellow", width=10)
    
    # Show last 10 executions
    recent_history = workflow_engine.execution_history[-10:]
    
    for execution in reversed(recent_history):
        import datetime
        time_str = datetime.datetime.fromtimestamp(execution['timestamp']).strftime('%H:%M %m/%d')
        workflow_name = workflow_engine.workflows[execution['workflow_id']]['name'][:18]
        status = "✅ Success" if execution['success'] else "❌ Failed"
        duration = f"{execution['execution_time']:.1f}s"
        steps = f"{execution['steps_completed']}/{len(workflow_engine.workflows[execution['workflow_id']]['steps'])}"
        
        table.add_row(time_str, workflow_name, status, duration, steps)
    
    console.print()
    console.print(table)


def get_workflow_help() -> None:
    """Show comprehensive help for workflow commands."""
    help_text = """
# 🔄 Smart Workflows Help

## What are Smart Workflows?
Smart Workflows are automated, multi-step processes that handle common development tasks intelligently. Instead of manually running multiple commands, workflows orchestrate the entire process for you.

## Available Commands:
- `/workflow list` - Show all available workflows
- `/workflow <workflow_id> [params]` - Execute a specific workflow
- `/workflow suggest <description>` - Get workflow recommendations
- `/workflow history` - Show execution history
- `/workflow help` - Show this help

## Available Workflows:

### 🏗️ project_setup
Set up a new project with best practices, structure, configs, and documentation.
**Usage:** `/workflow project_setup project_type=web name=my-project path=/path/to/project`

### 🔍 code_review_flow  
Comprehensive code review including security, performance, and quality analysis.
**Usage:** `/workflow code_review_flow path=/path/to/code`

### 🚀 deployment_prep
Prepare project for production deployment with all necessary checks.
**Usage:** `/workflow deployment_prep path=/path/to/project`

### 🐛 bug_investigation
Systematic bug investigation, root cause analysis, and fix generation.
**Usage:** `/workflow bug_investigation description="null pointer error" stack_trace="..."`

### ⚡ performance_optimization
Comprehensive performance analysis and optimization recommendations.
**Usage:** `/workflow performance_optimization path=/path/to/project`

## Parameter Formats:
```bash
# Key-value pairs
/workflow project_setup project_type=web name=my-app

# JSON format  
/workflow project_setup {"project_type": "web", "name": "my-app"}

# Interactive mode (will prompt for missing parameters)
/workflow project_setup
```

## Examples:
```bash
# Set up a new web project
/workflow project_setup project_type=web name=awesome-app path=/home/user/projects/awesome-app

# Get workflow suggestion
/workflow suggest "I want to review my code for security issues"

# Run performance optimization
/workflow performance_optimization path=/home/user/my-project
```

## Tips:
- Use `suggest` when you're not sure which workflow fits your needs
- Workflows can be interrupted safely with Ctrl+C
- Each workflow provides detailed progress and results
- Parameters can be provided interactively if missing
- All executions are logged in history for reference
    """
    
    console.print(Panel(
        Markdown(help_text),
        title="🔄 Smart Workflows Guide",
        border_style="cyan"
    ))