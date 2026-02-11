#!/usr/bin/env python3
"""
🚦 Signal Show - Visual fun for Agent Highway
Run this for a dazzling display of agent signaling!
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from highway.signals import (
    SignalEmitter, SignalTower, SignalDashboard, 
    SignalEffects, SignalType, console
)
from highway.visual import VisualHighway, SignalCLI


async def cmd_demo(args):
    """Run full signal demo"""
    console.print("""
[bold cyan]
╔══════════════════════════════════════════════════════════╗
║              🚦 AGENT HIGHWAY SIGNAL SHOW 🚦             ║
╠══════════════════════════════════════════════════════════╣
║   Visual signaling system for the autonomous future      ║
╚══════════════════════════════════════════════════════════╝
[/bold cyan]
    """)
    
    emitter = SignalEmitter()
    await emitter.demo_mode()


def cmd_celebrate(args):
    """Celebration effect"""
    console.print("\n[bold yellow]🎉 CELEBRATION TIME! 🎉[/bold yellow]\n")
    SignalEffects.celebration()


def cmd_alert(args):
    """Alert effect"""
    SignalCLI.alert(args.message or "🚨 HIGH PRIORITY ALERT 🚨")


def cmd_discover(args):
    """Simulate discovery"""
    name = args.name or "SuperAgent-9000"
    SignalEffects.agent_ripple(name)
    console.print(f"\n[bold green]✨ Discovered: {name}[/bold green]\n")


def cmd_tower(args):
    """Show signal tower"""
    SignalCLI.tower()


async def cmd_dashboard(args):
    """Run dashboard"""
    dashboard = SignalDashboard()
    
    # Add some initial signals if requested
    if args.demo:
        tower = dashboard.tower
        for i in range(5):
            tower.emit(
                SignalType.AGENT_DISCOVERED,
                f"Agent-{i+1} discovered from GitHub"
            )
            dashboard.agent_count += 1
    
    await dashboard.run()


def cmd_highway_visual(args):
    """Run highway with visuals"""
    from highway.core import HighwayConfig
    
    config = HighwayConfig.from_yaml(args.config) if args.config else HighwayConfig()
    highway = VisualHighway(config, enable_visuals=True)
    
    async def run():
        await highway.start()
        
        try:
            if args.collect:
                await highway.collect()
            
            # Run dashboard
            await highway.run_dashboard()
            
        except KeyboardInterrupt:
            pass
        finally:
            await highway.stop()
    
    asyncio.run(run())


async def cmd_party_mode(args):
    """Ultimate party mode with all effects"""
    console.print("""
[bold magenta]
╔══════════════════════════════════════════════════════════╗
║                    🎊 PARTY MODE 🎊                      ║
║              Full Visual Signal Activation!              ║
╚══════════════════════════════════════════════════════════╝
[/bold magenta]
    """)
    
    # Quick celebration
    SignalEffects.celebration()
    
    # Start dashboard
    emitter = SignalEmitter()
    dashboard_task = asyncio.create_task(emitter.dashboard.run(duration=20))
    
    # Rapid fire signals
    signal_types = [
        SignalType.COLLECTION_START,
        SignalType.DATA_RECEIVED,
        SignalType.AGENT_DISCOVERED,
        SignalType.AGENT_DISCOVERED,
        SignalType.HIGH_CONFIDENCE,
        SignalType.DATA_RECEIVED,
        SignalType.AGENT_DISCOVERED,
        SignalType.SWARM_DETECTED,
        SignalType.COLLECTION_END,
    ]
    
    messages = [
        "🚀 Launching collectors...",
        "📦 Received 100 repositories",
        "🤖 Found: ChatBot-3000",
        "🤖 Found: CodeAssistant-Pro",
        "⭐ HIGH CONFIDENCE: AutoGPT-Ultra",
        "📦 Processing batch...",
        "🤖 Found: DevHelper-AI",
        "🐝 SWARM DETECTED!",
        "🏁 Collection complete!",
    ]
    
    for sig_type, msg in zip(signal_types, messages):
        await asyncio.sleep(1.5)
        emitter.tower.emit(signal_type=sig_type, message=msg)
        emitter.dashboard.event_count += 1
        
        if "Found" in msg or "CONFIDENCE" in msg:
            emitter.dashboard.agent_count += 1
    
    await dashboard_task
    
    # Grand finale
    console.print("\n[bold yellow]🎆 GRAND FINALE 🎆[/bold yellow]\n")
    SignalEffects.celebration()


def main():
    parser = argparse.ArgumentParser(
        description="🚦 Agent Highway Visual Signaling System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full demo with dashboard
  python signal_show.py demo
  
  # Quick celebration
  python signal_show.py celebrate
  
  # Alert effect
  python signal_show.py alert --message "SWARM INCOMING"
  
  # Simulate discovery
  python signal_show.py discover --name "MySuperAgent"
  
  # Signal tower visualization
  python signal_show.py tower
  
  # Run dashboard
  python signal_show.py dashboard --demo
  
  # PARTY MODE!
  python signal_show.py party
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # demo
    subparsers.add_parser("demo", help="Run full signal demo")
    
    # celebrate
    subparsers.add_parser("celebrate", help="Celebration effect")
    
    # alert
    alert_parser = subparsers.add_parser("alert", help="Alert flash effect")
    alert_parser.add_argument("--message", "-m", help="Alert message")
    
    # discover
    discover_parser = subparsers.add_parser("discover", help="Simulate agent discovery")
    discover_parser.add_argument("--name", "-n", help="Agent name")
    
    # tower
    subparsers.add_parser("tower", help="Show signal tower")
    
    # dashboard
    dashboard_parser = subparsers.add_parser("dashboard", help="Run signal dashboard")
    dashboard_parser.add_argument("--demo", action="store_true", help="Add demo signals")
    
    # highway-visual
    hv_parser = subparsers.add_parser("highway-visual", help="Run highway with visuals")
    hv_parser.add_argument("--config", "-c", help="Config file")
    hv_parser.add_argument("--collect", action="store_true", help="Collect data first")
    
    # party
    subparsers.add_parser("party", help="ULTIMATE PARTY MODE")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Run command
    commands = {
        "demo": cmd_demo,
        "celebrate": cmd_celebrate,
        "alert": cmd_alert,
        "discover": cmd_discover,
        "tower": cmd_tower,
        "dashboard": cmd_dashboard,
        "highway-visual": cmd_highway_visual,
        "party": cmd_party_mode,
    }
    
    cmd = commands[args.command]
    
    if asyncio.iscoroutinefunction(cmd):
        asyncio.run(cmd(args))
    else:
        cmd(args)


if __name__ == "__main__":
    main()
