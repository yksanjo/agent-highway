#!/usr/bin/env python3
"""
Agent Highway Demo - Run with sample data
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from highway.core import AgentHighway, HighwayConfig


async def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║         🛣️  AGENT HIGHWAY - DEMO MODE  🛣️               ║
╚══════════════════════════════════════════════════════════╝
""")
    
    # Initialize
    print("🔧 Initializing...")
    Path("data").mkdir(exist_ok=True)
    
    # Create sample agent data
    sample_agents = [
        {
            "agent_id": "agent_001",
            "name": "AutoGPT",
            "agent_type": "autonomous_agent",
            "confidence_score": 0.92,
            "source": "github",
            "platform": "github",
            "detected_at": datetime.utcnow().isoformat(),
            "capabilities": ["autonomous", "reasoning", "code_execution"],
            "metadata": {"stars": 158000, "language": "Python"},
        },
        {
            "agent_id": "agent_002",
            "name": "LangChain",
            "agent_type": "code_agent",
            "confidence_score": 0.88,
            "source": "github",
            "platform": "github",
            "detected_at": datetime.utcnow().isoformat(),
            "capabilities": ["framework", "llm_integration", "tool_usage"],
            "metadata": {"stars": 89000, "language": "Python"},
        },
        {
            "agent_id": "agent_003",
            "name": "CrewAI",
            "agent_type": "orchestrator",
            "confidence_score": 0.85,
            "source": "github",
            "platform": "github",
            "detected_at": datetime.utcnow().isoformat(),
            "capabilities": ["multi_agent", "orchestration", "task_management"],
            "metadata": {"stars": 21000, "language": "Python"},
        },
        {
            "agent_id": "agent_004",
            "name": "OpenClaw Gateway",
            "agent_type": "gateway",
            "confidence_score": 0.90,
            "source": "openclaw",
            "platform": "github",
            "detected_at": datetime.utcnow().isoformat(),
            "capabilities": ["gateway", "multi_platform", "telegram", "discord"],
            "metadata": {"source_repo": "https://github.com/openclaw/openclaw.ai"},
        },
        {
            "agent_id": "agent_005",
            "name": "DevAssistant Bot",
            "agent_type": "chatbot",
            "confidence_score": 0.75,
            "source": "discord",
            "platform": "discord",
            "detected_at": datetime.utcnow().isoformat(),
            "capabilities": ["chat", "code_help", "documentation"],
            "metadata": {"server_count": 150},
        },
    ]
    
    # Save sample data
    for agent in sample_agents:
        filepath = Path(f"data/agents/{agent['agent_id']}.json")
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(agent, f, indent=2)
    
    print(f"✅ Loaded {len(sample_agents)} sample agents")
    
    # Start highway
    config = HighwayConfig()
    highway = AgentHighway(config)
    
    await highway.start()
    print(highway.get_status())
    
    # Query agents
    print("\n📊 QUERY EXAMPLES:")
    print("=" * 50)
    
    all_agents = highway.query()
    print(f"\n1. All agents: {len(all_agents)} found")
    
    autonomous = highway.query(agent_type="autonomous_agent")
    print(f"2. Autonomous agents: {len(autonomous)} found")
    
    high_confidence = highway.query(min_confidence=0.8)
    print(f"3. High confidence (>0.8): {len(high_confidence)} found")
    
    github_agents = highway.query(source="github")
    print(f"4. From GitHub: {len(github_agents)} found")
    
    # Show agent list
    print("\n📋 AGENT INVENTORY:")
    print("=" * 50)
    for agent in all_agents:
        print(f"  • {agent['name']:<25} | {agent['agent_type']:<18} | {agent['confidence_score']:.2f}")
    
    # Run analysis
    print("\n📈 RUNNING ANALYSIS...")
    print("=" * 50)
    
    results = await highway.analyze("all")
    
    if "network" in results:
        network = results["network"]
        print(f"\nNetwork Analysis:")
        print(f"  Nodes: {network['stats']['total_nodes']}")
        print(f"  Edges: {network['stats']['total_edges']}")
        print(f"  Avg Degree: {network['stats']['avg_degree']:.2f}")
    
    if "trends" in results:
        trends = results["trends"]
        print(f"\nTrend Analysis:")
        print(f"  Total: {trends.get('total_agents', 'N/A')}")
        print(f"  By Type: {trends.get('by_type', {})}")
        print(f"  By Source: {trends.get('by_source', {})}")
    
    # Show metrics
    print("\n📊 FINAL METRICS:")
    print("=" * 50)
    metrics = highway.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    await highway.stop()
    
    print("""

✅ DEMO COMPLETE!

The Agent Highway is fully operational with:
  • GitHub Collector - Ready
  • OpenClaw Scanner - Ready
  • Stream Processing - Active
  • Storage Layer - JSON backend
  • Analysis Engine - Working
  • Dashboard - Available

Run with real data:
  export GITHUB_TOKEN="your_token"
  python run.py collect --source github

Launch dashboard:
  python run.py dashboard
""")


if __name__ == "__main__":
    asyncio.run(main())
