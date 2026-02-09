#!/usr/bin/env python3
"""
Agent Highway - Unified CLI Runner
The main entry point for the Agent Highway system
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from highway.core import AgentHighway, HighwayConfig


async def cmd_start(args):
    """Start the highway system"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                    🛣️ AGENT HIGHWAY                      ║
╠══════════════════════════════════════════════════════════╣
║          The unified superhighway for AI agents          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Load config
    if args.config:
        config = HighwayConfig.from_yaml(args.config)
    else:
        config = HighwayConfig()
        
    # Create and start highway
    highway = AgentHighway(config)
    
    try:
        await highway.start()
        print(highway.get_status())
        
        if args.collect:
            await highway.collect(continuous=args.continuous)
        elif args.continuous:
            # Just run the highway continuously
            while True:
                await asyncio.sleep(1)
                
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
    finally:
        await highway.stop()


async def cmd_collect(args):
    """Run collection only"""
    print("🚀 Agent Highway Collection Run\n")
    
    if args.config:
        config = HighwayConfig.from_yaml(args.config)
    else:
        config = HighwayConfig()
        
    highway = AgentHighway(config)
    await highway.start()
    
    try:
        await highway.collect(source=args.source, continuous=args.continuous)
    finally:
        await highway.stop()


async def cmd_analyze(args):
    """Run analysis"""
    print("📊 Agent Highway Analysis\n")
    
    config = HighwayConfig.from_yaml(args.config) if args.config else HighwayConfig()
    highway = AgentHighway(config)
    await highway.start()
    
    try:
        results = await highway.analyze(analysis_type=args.type)
        
        print("\n📈 Analysis Results:")
        print("=" * 50)
        
        for analysis_type, data in results.items():
            print(f"\n{analysis_type.upper()}:")
            print(json.dumps(data, indent=2, default=str))
            
    finally:
        await highway.stop()


async def cmd_dashboard(args):
    """Launch dashboard"""
    print("📺 Launching Agent Highway Dashboard...")
    
    try:
        from highway.dashboard import launch_dashboard
        await launch_dashboard(port=args.port)
    except ImportError:
        print("❌ Dashboard not available. Install with: pip install rich")


async def cmd_status(args):
    """Show highway status"""
    config = HighwayConfig.from_yaml(args.config) if args.config else HighwayConfig()
    storage = __import__('highway.storage', fromlist=['HighwayStorage']).HighwayStorage(config.data_dir)
    
    stats = storage.get_stats()
    
    print("""
╔══════════════════════════════════════════════════════════╗
║                    🛣️ HIGHWAY STATUS                     ║
╠══════════════════════════════════════════════════════════╣
""")
    print(f"║  Data Directory: {stats['data_dir']:<39}║")
    print(f"║  Backend: {stats['backend']:<46}║")
    print(f"║  Total Agents: {stats['total_agents']:<41}║")
    print("""╚══════════════════════════════════════════════════════════╝
""")


def cmd_init(args):
    """Initialize highway"""
    print("🔧 Initializing Agent Highway...\n")
    
    # Create directories
    dirs = ["data", "data/agents", "data/events", "data/insights", "config", "logs"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created {d}/")
        
    # Create example config
    example_config = '''# Agent Highway Configuration
highway:
  name: "Agent Highway"
  version: "1.0.0"
  data_dir: "./data"

collectors:
  github:
    enabled: true
    rate_limit: 5000
    
  openclaw:
    enabled: true
    scan_github: true
    
  discord:
    enabled: false
    
  telegram:
    enabled: false

processing:
  batch_size: 100
  flush_interval: 5

detection:
  confidence_threshold: 0.6
  min_signals: 3

dashboard:
  enabled: true
  port: 8080
'''
    
    config_path = Path("config/highway.yaml")
    if not config_path.exists():
        with open(config_path, "w") as f:
            f.write(example_config)
        print(f"  ✓ Created config/highway.yaml")
        
    # Create example env
    example_env = '''# Agent Highway Environment Variables

# GitHub Token (recommended)
GITHUB_TOKEN=your_github_token_here

# Discord Bot Token (optional)
DISCORD_TOKEN=your_discord_token_here

# Telegram Bot Token (optional)
TELEGRAM_TOKEN=your_telegram_token_here
'''
    
    env_path = Path("config/.env")
    if not env_path.exists():
        with open(env_path, "w") as f:
            f.write(example_env)
        print(f"  ✓ Created config/.env")
        
    print("""
✅ Initialization complete!

Next steps:
  1. Edit config/highway.yaml to enable collectors
  2. Edit config/.env with your API tokens
  3. Run: python run.py collect --source github
  4. Run: python run.py dashboard
""")


def main():
    parser = argparse.ArgumentParser(
        description="Agent Highway - The unified superhighway for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize the highway
  python run.py init
  
  # Collect from all enabled sources
  python run.py collect --all
  
  # Collect from specific source
  python run.py collect --source github
  
  # Start the full highway system
  python run.py start --collect --continuous
  
  # Run analysis
  python run.py analyze --type network
  
  # Launch dashboard
  python run.py dashboard --port 8080
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # init
    init_parser = subparsers.add_parser("init", help="Initialize Agent Highway")
    
    # start
    start_parser = subparsers.add_parser("start", help="Start the highway system")
    start_parser.add_argument("--config", "-c", help="Config file path")
    start_parser.add_argument("--collect", action="store_true", help="Start collecting immediately")
    start_parser.add_argument("--continuous", action="store_true", help="Run continuously")
    
    # collect
    collect_parser = subparsers.add_parser("collect", help="Run data collection")
    collect_parser.add_argument("--source", "-s", help="Specific collector to run")
    collect_parser.add_argument("--config", "-c", help="Config file path")
    collect_parser.add_argument("--continuous", action="store_true", help="Run continuously")
    collect_parser.add_argument("--all", action="store_true", help="Run all enabled collectors")
    
    # analyze
    analyze_parser = subparsers.add_parser("analyze", help="Run analysis")
    analyze_parser.add_argument("--type", "-t", default="all", 
                               choices=["all", "network", "trends", "swarms"],
                               help="Type of analysis")
    analyze_parser.add_argument("--config", "-c", help="Config file path")
    
    # dashboard
    dashboard_parser = subparsers.add_parser("dashboard", help="Launch dashboard")
    dashboard_parser.add_argument("--port", "-p", type=int, default=8080, help="Dashboard port")
    
    # status
    status_parser = subparsers.add_parser("status", help="Show highway status")
    status_parser.add_argument("--config", "-c", help="Config file path")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    # Run command
    commands = {
        "init": cmd_init,
        "start": cmd_start,
        "collect": cmd_collect,
        "analyze": cmd_analyze,
        "dashboard": cmd_dashboard,
        "status": cmd_status,
    }
    
    cmd = commands[args.command]
    
    if asyncio.iscoroutinefunction(cmd):
        asyncio.run(cmd(args))
    else:
        cmd(args)


if __name__ == "__main__":
    import json  # Required for cmd_analyze
    main()
