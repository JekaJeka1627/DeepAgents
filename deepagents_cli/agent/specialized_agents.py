"""
Specialized Sub-Agents for Domain-Specific Tasks.
Each agent has specialized knowledge and tools for specific development domains.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json
import time


@dataclass
class AgentCapability:
    """Represents a specialized capability of an agent."""
    name: str
    description: str
    keywords: List[str]
    confidence_threshold: float = 0.7


class SpecializedAgentSystem:
    """Manages and routes requests to specialized sub-agents."""
    
    def __init__(self):
        self.agents = self._initialize_agents()
        self.routing_history: List[Dict] = []
    
    def _initialize_agents(self) -> Dict[str, Dict[str, Any]]:
        """Initialize all specialized agents with their capabilities."""
        return {
            "code_reviewer": {
                "name": "Code Reviewer",
                "description": "Expert at reviewing code for bugs, performance, security, and best practices",
                "capabilities": [
                    AgentCapability("bug_detection", "Find potential bugs and logical errors", 
                                  ["bug", "error", "issue", "problem", "broken", "fix"]),
                    AgentCapability("security_review", "Identify security vulnerabilities",
                                  ["security", "vulnerability", "auth", "injection", "xss", "csrf"]),
                    AgentCapability("performance_analysis", "Analyze performance bottlenecks",
                                  ["performance", "slow", "optimize", "bottleneck", "memory", "cpu"]),
                    AgentCapability("code_quality", "Assess code quality and maintainability",
                                  ["quality", "clean", "readable", "maintainable", "refactor"])
                ],
                "system_prompt": """You are a Senior Code Reviewer with 15+ years of experience.

🎯 **Core Expertise:**
- Bug detection and logical error identification
- Security vulnerability assessment
- Performance bottleneck analysis  
- Code quality and maintainability evaluation
- Best practices enforcement

📋 **Review Process:**
1. **Quick Scan**: Identify obvious issues first
2. **Deep Analysis**: Examine logic, edge cases, error handling
3. **Security Check**: Look for vulnerabilities and security gaps
4. **Performance Review**: Assess algorithmic efficiency and resource usage
5. **Quality Assessment**: Evaluate readability, maintainability, and patterns

✅ **Always Provide:**
- Specific line numbers and code snippets
- Clear explanation of issues found
- Concrete improvement suggestions
- Severity ratings (Critical/High/Medium/Low)
- Estimated fix effort

Be thorough but concise. Focus on actionable feedback."""
            },
            
            "architect": {
                "name": "Software Architect",
                "description": "Expert at system design, architecture patterns, and technical decisions",
                "capabilities": [
                    AgentCapability("system_design", "Design scalable system architectures",
                                  ["architecture", "design", "pattern", "structure", "system"]),
                    AgentCapability("tech_stack", "Recommend optimal technology choices",
                                  ["technology", "stack", "framework", "library", "database"]),
                    AgentCapability("scalability", "Plan for growth and scalability",
                                  ["scale", "growth", "performance", "load", "distributed"]),
                    AgentCapability("integration", "Design system integrations and APIs",
                                  ["api", "integration", "microservice", "service", "endpoint"])
                ],
                "system_prompt": """You are a Principal Software Architect with deep expertise in system design.

🏗️ **Core Expertise:**
- System architecture and design patterns
- Scalability and performance planning
- Technology stack evaluation and selection
- API and integration design
- Database design and optimization

🎯 **Architectural Approach:**
1. **Requirements Analysis**: Understand functional and non-functional requirements
2. **Pattern Selection**: Choose appropriate architectural patterns
3. **Technology Evaluation**: Assess tech stack options with trade-offs
4. **Scalability Planning**: Design for current and future scale
5. **Risk Assessment**: Identify architectural risks and mitigation strategies

📐 **Always Deliver:**
- Clear architectural diagrams (ASCII/text-based)
- Technology recommendations with rationale
- Scalability considerations and bottlenecks
- Implementation roadmap and phases
- Risk analysis and mitigation strategies

Think holistically. Consider maintainability, team capabilities, and business constraints."""
            },
            
            "debugger": {
                "name": "Debug Specialist", 
                "description": "Expert at diagnosing and fixing complex bugs and issues",
                "capabilities": [
                    AgentCapability("error_analysis", "Analyze error messages and stack traces",
                                  ["error", "exception", "stack", "trace", "crash", "debug"]),
                    AgentCapability("root_cause", "Find root causes of issues",
                                  ["root cause", "investigation", "diagnosis", "analysis"]),
                    AgentCapability("edge_cases", "Identify problematic edge cases",
                                  ["edge case", "boundary", "corner case", "unexpected"]),
                    AgentCapability("testing_strategy", "Design debugging and testing approaches",
                                  ["test", "reproduce", "isolate", "investigate"])
                ],
                "system_prompt": """You are a Senior Debug Specialist with expertise in complex issue diagnosis.

🔍 **Core Expertise:**
- Stack trace analysis and error interpretation
- Root cause analysis methodology
- Edge case identification and handling
- Debugging strategy and tool selection
- Issue reproduction and isolation

🛠️ **Debug Process:**
1. **Error Analysis**: Parse and interpret error messages/stack traces
2. **Context Gathering**: Understand the conditions when issues occur
3. **Hypothesis Formation**: Develop theories about root causes
4. **Investigation Plan**: Design systematic debugging approach
5. **Solution Validation**: Ensure fixes address root causes

🎯 **Always Provide:**
- Clear problem statement and symptoms
- Root cause analysis with evidence
- Step-by-step debugging strategy
- Specific code changes needed
- Prevention strategies for similar issues

Be methodical and thorough. Think like a detective - follow the evidence."""
            },
            
            "performance_expert": {
                "name": "Performance Engineer",
                "description": "Expert at optimizing application performance and resource usage",
                "capabilities": [
                    AgentCapability("bottleneck_analysis", "Identify performance bottlenecks",
                                  ["bottleneck", "slow", "performance", "latency", "throughput"]),
                    AgentCapability("memory_optimization", "Optimize memory usage and prevent leaks",
                                  ["memory", "leak", "gc", "heap", "allocation"]),
                    AgentCapability("database_tuning", "Optimize database queries and design",
                                  ["database", "query", "index", "slow", "optimization"]),
                    AgentCapability("caching_strategy", "Design effective caching solutions",
                                  ["cache", "caching", "redis", "memcache", "cdn"])
                ],
                "system_prompt": """You are a Senior Performance Engineer focused on optimization and scalability.

⚡ **Core Expertise:**
- Performance profiling and bottleneck identification
- Memory usage optimization and leak prevention
- Database query optimization and indexing
- Caching strategies and implementation
- Load testing and capacity planning

📊 **Performance Analysis Process:**
1. **Measurement**: Define metrics and establish baselines
2. **Profiling**: Identify hotspots and resource usage patterns
3. **Analysis**: Determine root causes of performance issues
4. **Optimization**: Apply targeted performance improvements
5. **Validation**: Measure impact and ensure no regressions

🎯 **Always Deliver:**
- Specific performance metrics and targets
- Bottleneck identification with evidence
- Concrete optimization recommendations
- Implementation priority and effort estimates
- Monitoring and measurement strategies

Focus on data-driven optimization. Measure twice, optimize once."""
            },
            
            "devops_engineer": {
                "name": "DevOps Engineer",
                "description": "Expert at deployment, infrastructure, and operational excellence",
                "capabilities": [
                    AgentCapability("ci_cd", "Design CI/CD pipelines and deployment strategies",
                                  ["ci", "cd", "pipeline", "deploy", "build", "release"]),
                    AgentCapability("infrastructure", "Design and manage cloud infrastructure",
                                  ["infrastructure", "cloud", "docker", "kubernetes", "aws"]),
                    AgentCapability("monitoring", "Implement monitoring and observability",
                                  ["monitoring", "logging", "metrics", "alerts", "observability"]),
                    AgentCapability("security_ops", "Implement operational security practices",
                                  ["security", "compliance", "secrets", "scanning", "hardening"])
                ],
                "system_prompt": """You are a Senior DevOps Engineer with expertise in modern cloud-native operations.

🚀 **Core Expertise:**
- CI/CD pipeline design and implementation
- Container orchestration and Kubernetes
- Cloud infrastructure (AWS/Azure/GCP)
- Monitoring, logging, and observability
- Security and compliance automation

🛠️ **Operational Excellence:**
1. **Automation First**: Automate repetitive tasks and processes
2. **Infrastructure as Code**: Version control all infrastructure
3. **Observability**: Comprehensive monitoring and alerting
4. **Security Integration**: Security built into all processes
5. **Continuous Improvement**: Regular optimization and updates

📋 **Always Provide:**
- Specific configuration files and scripts
- Security best practices and compliance
- Monitoring and alerting strategies
- Disaster recovery and backup plans
- Cost optimization recommendations

Think infrastructure as code. Automate everything possible."""
            }
        }
    
    def route_request(self, user_input: str, context: Dict[str, Any] = None) -> Optional[str]:
        """Route a request to the most appropriate specialized agent."""
        if context is None:
            context = {}
        
        # Analyze user input to determine best agent
        agent_scores = self._calculate_agent_scores(user_input)
        
        # Find best match above threshold
        best_agent = None
        best_score = 0.0
        
        for agent_id, score in agent_scores.items():
            if score > best_score and score >= 0.3:  # Minimum confidence threshold
                best_agent = agent_id
                best_score = score
        
        # Record routing decision
        self.routing_history.append({
            "timestamp": time.time(),
            "user_input": user_input[:100] + "..." if len(user_input) > 100 else user_input,
            "selected_agent": best_agent,
            "confidence": best_score,
            "all_scores": agent_scores
        })
        
        return best_agent
    
    def _calculate_agent_scores(self, user_input: str) -> Dict[str, float]:
        """Calculate confidence scores for each agent based on input."""
        user_lower = user_input.lower()
        agent_scores = {}
        
        for agent_id, agent_info in self.agents.items():
            score = 0.0
            capability_matches = 0
            
            for capability in agent_info["capabilities"]:
                keyword_matches = sum(1 for keyword in capability.keywords if keyword in user_lower)
                if keyword_matches > 0:
                    capability_matches += 1
                    # Weight by number of matching keywords and keyword frequency
                    score += keyword_matches * 0.2
            
            # Bonus for multiple capability matches (indicates better fit)
            if capability_matches > 1:
                score += capability_matches * 0.1
            
            agent_scores[agent_id] = min(score, 1.0)  # Cap at 1.0
        
        return agent_scores
    
    def get_agent_prompt(self, agent_id: str) -> Optional[str]:
        """Get the specialized system prompt for an agent."""
        agent = self.agents.get(agent_id)
        return agent["system_prompt"] if agent else None
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get complete information about a specialized agent."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> Dict[str, str]:
        """List all available agents with brief descriptions."""
        return {
            agent_id: agent_info["description"] 
            for agent_id, agent_info in self.agents.items()
        }
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get statistics about agent routing decisions."""
        if not self.routing_history:
            return {"total_requests": 0}
        
        recent_history = [
            h for h in self.routing_history 
            if time.time() - h["timestamp"] < 3600  # Last hour
        ]
        
        agent_usage = {}
        for h in recent_history:
            if h["selected_agent"]:
                agent_usage[h["selected_agent"]] = agent_usage.get(h["selected_agent"], 0) + 1
        
        return {
            "total_requests": len(self.routing_history),
            "recent_requests": len(recent_history),
            "agent_usage": agent_usage,
            "average_confidence": sum(h["confidence"] for h in recent_history) / len(recent_history) if recent_history else 0
        }


# Global specialized agent system
specialized_agents = SpecializedAgentSystem()


def get_specialized_prompt_for_request(user_input: str, context: Dict[str, Any] = None) -> Optional[str]:
    """Get a specialized agent prompt if the request warrants it."""
    agent_id = specialized_agents.route_request(user_input, context)
    if agent_id:
        return specialized_agents.get_agent_prompt(agent_id)
    return None


def should_use_specialized_agent(user_input: str) -> bool:
    """Determine if the request should use a specialized agent."""
    agent_scores = specialized_agents._calculate_agent_scores(user_input)
    max_score = max(agent_scores.values()) if agent_scores else 0
    return max_score >= 0.4  # Confidence threshold for using specialized agents