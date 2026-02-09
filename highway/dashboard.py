"""
Agent Highway Dashboard - Terminal visualization
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich import box

console = Console()


class HighwayDashboard:
    """Terminal-based dashboard for Agent Highway"""
    
    def __init__(self, data_dir: Path = Path("./data")):
        self.data_dir = data_dir
        self.refresh_interval = 5
        
    def build_layout(self) -> Layout:
        """Build dashboard layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )
        
        return layout
        
    def render_header(self) -> Panel:
        """Render header panel"""
        return Panel(
            "[bold cyan]🛣️  Agent Highway - Live Dashboard[/bold cyan]",
            border_style="blue"
        )
        
    def render_stats(self) -> Panel:
        """Render statistics panel"""
        # Load stats from storage
        try:
            from .storage import HighwayStorage
            storage = HighwayStorage(self.data_dir)
            stats = storage.get_stats()
        except:
            stats = {"total_agents": 0, "backend": "json"}
            
        content = f"""
[bold cyan]Highway Statistics[/bold cyan]

Total Agents: {stats.get('total_agents', 0)}
Backend: {stats.get('backend', 'json')}
Data Dir: {stats.get('data_dir', './data')}
        """
        
        return Panel(content, title="📊 Stats", border_style="green")
        
    def render_recent(self) -> Panel:
        """Render recent discoveries panel"""
        # Load recent agents
        try:
            from .storage import HighwayStorage
            storage = HighwayStorage(self.data_dir)
            agents = storage.query_agents()[:10]
        except:
            agents = []
            
        if agents:
            content = "\n".join([
                f"• {a.get('name', 'Unknown')} ({a.get('agent_type', 'unknown')})"
                for a in agents[:5]
            ])
        else:
            content = "No agents discovered yet.\nRun: python run.py collect"
            
        return Panel(content, title="🤖 Recent Agents", border_style="yellow")
        
    def render_footer(self) -> Panel:
        """Render footer panel"""
        return Panel(
            "[dim]Press Ctrl+C to exit | Run 'python run.py collect' to add data[/dim]",
            border_style="blue"
        )
        
    def render(self) -> Layout:
        """Render full dashboard"""
        layout = self.build_layout()
        
        layout["header"].update(self.render_header())
        layout["left"].update(self.render_stats())
        layout["right"].update(self.render_recent())
        layout["footer"].update(self.render_footer())
        
        return layout
        
    async def run(self):
        """Run live dashboard"""
        with Live(self.render(), refresh_per_second=1) as live:
            try:
                while True:
                    await asyncio.sleep(self.refresh_interval)
                    live.update(self.render())
            except KeyboardInterrupt:
                pass
                

async def launch_dashboard(port: int = 8080):
    """Launch the dashboard"""
    dashboard = HighwayDashboard()
    await dashboard.run()


if __name__ == "__main__":
    asyncio.run(launch_dashboard())
