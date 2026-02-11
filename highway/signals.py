"""
🚦 Visual Signaling System for Agent Highway
Fun, colorful real-time signals for agent activity
"""

import asyncio
import random
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Callable
import logging

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.style import Style
from rich.color import Color

console = Console()


class SignalType(Enum):
    """Types of visual signals"""
    AGENT_DISCOVERED = auto()
    DATA_RECEIVED = auto()
    ALERT = auto()
    HEARTBEAT = auto()
    COLLECTION_START = auto()
    COLLECTION_END = auto()
    HIGH_CONFIDENCE = auto()
    SWARM_DETECTED = auto()


@dataclass
class Signal:
    """A visual signal event"""
    signal_type: SignalType
    message: str
    agent_id: Optional[str] = None
    confidence: float = 0.0
    timestamp: datetime = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class SignalTower:
    """
    🗼 A visual signal tower that broadcasts colorful signals
    Like a lighthouse for the agent highway
    """
    
    SIGNAL_COLORS = {
        SignalType.AGENT_DISCOVERED: "bright_green",
        SignalType.DATA_RECEIVED: "cyan",
        SignalType.ALERT: "bright_red",
        SignalType.HEARTBEAT: "dim",
        SignalType.COLLECTION_START: "bright_yellow",
        SignalType.COLLECTION_END: "bright_blue",
        SignalType.HIGH_CONFIDENCE: "gold1",
        SignalType.SWARM_DETECTED: "magenta",
    }
    
    SIGNAL_ICONS = {
        SignalType.AGENT_DISCOVERED: "🤖",
        SignalType.DATA_RECEIVED: "📡",
        SignalType.ALERT: "🚨",
        SignalType.HEARTBEAT: "💓",
        SignalType.COLLECTION_START: "🚀",
        SignalType.COLLECTION_END: "🏁",
        SignalType.HIGH_CONFIDENCE: "⭐",
        SignalType.SWARM_DETECTED: "🐝",
    }
    
    def __init__(self, max_history: int = 20):
        self.signals: List[Signal] = []
        self.max_history = max_history
        self.signal_handlers: List[Callable] = []
        self._pulse = 0
        self._running = False
        
    def emit(self, signal_type: SignalType, message: str, **kwargs):
        """Emit a visual signal"""
        signal = Signal(
            signal_type=signal_type,
            message=message,
            **kwargs
        )
        self.signals.append(signal)
        
        # Keep only recent signals
        if len(self.signals) > self.max_history:
            self.signals = self.signals[-self.max_history:]
        
        # Trigger visual effect
        self._flash(signal)
        
        # Notify handlers
        for handler in self.signal_handlers:
            try:
                handler(signal)
            except Exception:
                pass
        
        return signal
    
    def _flash(self, signal: Signal):
        """Create a visual flash effect in terminal"""
        color = self.SIGNAL_COLORS.get(signal.signal_type, "white")
        icon = self.SIGNAL_ICONS.get(signal.signal_type, "💫")
        
        # Create pulsing effect
        pulse_chars = ["◐", "◓", "◑", "◒"]
        self._pulse = (self._pulse + 1) % len(pulse_chars)
        pulse = pulse_chars[self._pulse]
        
        text = Text()
        text.append(f"{pulse} ", style=f"bold {color}")
        text.append(f"{icon} ", style=color)
        text.append(signal.message, style=f"bold {color}")
        
        if signal.confidence > 0:
            text.append(f" (confidence: {signal.confidence:.2f})", style=f"dim {color}")
        
        console.print(text)
    
    def add_handler(self, handler: Callable):
        """Add a signal handler"""
        self.signal_handlers.append(handler)
    
    def get_recent(self, count: int = 10) -> List[Signal]:
        """Get recent signals"""
        return self.signals[-count:]
    
    def render_tower(self) -> Panel:
        """Render the signal tower visualization"""
        # Build tower ASCII art
        tower_art = """
            🌟
           ╱│╲
          ╱ │ ╲
         ╱  │  ╲
        ╱   │   ╲
       ╱    │    ╲
      ╱     │     ╲
     ═══════╧═══════
         │   │
         │   │
         │   │
         │   │
    ═════╧═══╧═════
        """
        
        # Add recent signals as "light beams"
        if self.signals:
            recent = self.signals[-5:]
            beam_colors = [self.SIGNAL_COLORS.get(s.signal_type, "white") for s in recent]
            
            # Create colorful beam effect
            beams = ""
            for color in beam_colors[-3:]:
                beams += f"[{color}]▓▓▓[/{color}]"
            
            tower_art = tower_art.replace("🌟", f"{beams}\n           🌟")
        
        return Panel(
            tower_art,
            title="🗼 Signal Tower",
            border_style="bright_yellow"
        )


class TrafficLight:
    """
    🚦 Visual traffic light for highway status
    """
    
    def __init__(self):
        self.status = "green"
        self.blinking = False
        self._blink_state = True
        
    def set_status(self, status: str):
        """Set traffic light status"""
        self.status = status
        
    def render(self) -> Panel:
        """Render traffic light"""
        lights = {
            "red": "🔴" if self.status == "red" else "⚪",
            "yellow": "🟡" if self.status == "yellow" else "⚪",
            "green": "🟢" if self.status == "green" else "⚪",
        }
        
        # Add blinking effect
        if self.blinking and self.status != "green":
            self._blink_state = not self._blink_state
            if not self._blink_state:
                lights[self.status] = "⚪"
        
        light_display = f"""
    ┌─────────┐
    │  {lights['red']}    │
    │         │
    │  {lights['yellow']}    │
    │         │
    │  {lights['green']}    │
    └─────────┘
        """
        
        border_color = {
            "red": "red",
            "yellow": "yellow", 
            "green": "green"
        }.get(self.status, "white")
        
        return Panel(
            light_display,
            title="🚦 Highway Status",
            border_style=border_color
        )


class SignalDashboard:
    """
    🎨 Visual signal dashboard with animations
    """
    
    def __init__(self, tower: Optional[SignalTower] = None):
        self.tower = tower or SignalTower()
        self.traffic_light = TrafficLight()
        self.agent_count = 0
        self.event_count = 0
        self._running = False
        
    def build_layout(self) -> Layout:
        """Build the dashboard layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=5)
        )
        
        layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="center", ratio=2),
            Layout(name="right", ratio=1)
        )
        
        return layout
    
    def render_header(self) -> Panel:
        """Render animated header"""
        # Animated title with wave effect
        wave = "~" * 50
        title = f"🛣️  AGENT HIGHWAY SIGNAL STATION  🛣️"
        
        return Panel(
            Text(title, style="bold cyan", justify="center"),
            border_style="cyan"
        )
    
    def render_signal_stream(self) -> Panel:
        """Render recent signals as a stream"""
        signals = self.tower.get_recent(8)
        
        if not signals:
            return Panel(
                "[dim]Waiting for signals...[/dim]",
                title="📡 Signal Stream",
                border_style="blue"
            )
        
        table = Table(show_header=False, box=None)
        table.add_column("Icon", width=3)
        table.add_column("Signal", width=40)
        table.add_column("Time", width=8)
        
        for signal in reversed(signals):
            icon = SignalTower.SIGNAL_ICONS.get(signal.signal_type, "💫")
            color = SignalTower.SIGNAL_COLORS.get(signal.signal_type, "white")
            time_str = signal.timestamp.strftime("%H:%M:%S")
            
            # Truncate message
            msg = signal.message[:35] + "..." if len(signal.message) > 35 else signal.message
            
            table.add_row(
                icon,
                f"[{color}]{msg}[/{color}]",
                f"[dim]{time_str}[/dim]"
            )
        
        return Panel(table, title="📡 Signal Stream", border_style="blue")
    
    def render_metrics(self) -> Panel:
        """Render animated metrics"""
        # Create pulsing effect for active metrics
        pulse = "●" if int(time.time() * 2) % 2 == 0 else "○"
        
        content = f"""
[bold cyan]Highway Metrics[/bold cyan]

Agents Discovered: {pulse} [bold]{self.agent_count}[/bold]
Events Processed:  {pulse} [bold]{self.event_count}[/bold]
Signals Emitted:   {pulse} [bold]{len(self.tower.signals)}[/bold]

[cyan]Traffic Status:[/cyan]
{self._get_traffic_bar()}
        """
        
        return Panel(content, title="📊 Metrics", border_style="green")
    
    def _get_traffic_bar(self) -> str:
        """Generate a visual traffic bar"""
        intensity = min(self.agent_count / 100, 1.0)
        filled = int(intensity * 20)
        bar = "█" * filled + "░" * (20 - filled)
        
        if intensity < 0.3:
            color = "green"
        elif intensity < 0.7:
            color = "yellow"
        else:
            color = "red"
        
        return f"[{color}]{bar}[/{color}] {intensity*100:.0f}%"
    
    def render_footer(self) -> Panel:
        """Render animated footer"""
        animations = [
            "◐ Collecting ◓",
            "◓ Collecting ◑", 
            "◑ Collecting ◒",
            "◒ Collecting ◐"
        ]
        frame = animations[int(time.time() * 4) % 4]
        
        status = f"""
[dim]{frame}[/dim]  
[dim]Press Ctrl+C to exit | Signals: {len(self.tower.signals)}[/dim]
        """
        
        return Panel(status, border_style="dim")
    
    def render(self) -> Layout:
        """Render full dashboard"""
        layout = self.build_layout()
        
        layout["header"].update(self.render_header())
        layout["left"].update(self.traffic_light.render())
        layout["center"].update(self.render_signal_stream())
        layout["right"].update(self.render_metrics())
        layout["footer"].update(self.render_footer())
        
        return layout
    
    async def run(self, duration: Optional[float] = None):
        """Run the signal dashboard"""
        self._running = True
        start_time = time.time()
        
        with Live(self.render(), refresh_per_second=4) as live:
            try:
                while self._running:
                    # Check duration
                    if duration and (time.time() - start_time) > duration:
                        break
                    
                    # Update display
                    live.update(self.render())
                    await asyncio.sleep(0.25)
                    
            except KeyboardInterrupt:
                pass
        
        self._running = False


class SignalEffects:
    """
    🎭 Special visual effects for different events
    """
    
    @staticmethod
    def celebration():
        """Celebration effect for major discoveries"""
        confetti = ["🎉", "✨", "🎊", "💫", "⭐", "🌟"]
        colors = ["bright_yellow", "gold1", "bright_green", "cyan", "magenta"]
        
        for _ in range(10):
            line = " ".join(random.choice(confetti) for _ in range(8))
            color = random.choice(colors)
            console.print(f"[{color}]{line}[/{color}]")
            time.sleep(0.1)
    
    @staticmethod
    def alert_flash(message: str, count: int = 3):
        """Red alert flashing effect"""
        for _ in range(count):
            console.print(f"[bold red on_red] 🚨 {message} 🚨 [/bold red on_red]")
            time.sleep(0.3)
            console.print(f"[bold red] 🚨 {message} 🚨 [/bold red]")
            time.sleep(0.3)
    
    @staticmethod
    def agent_ripple(agent_name: str):
        """Ripple effect for agent discovery"""
        waves = ["○", "◎", "◉", "◉", "◎", "○"]
        colors = ["cyan", "blue", "bright_blue", "bright_blue", "blue", "cyan"]
        
        for wave, color in zip(waves, colors):
            padding = " " * 20
            console.print(f"[{color}]{padding}{wave} {agent_name} {wave}[/{color}]")
            time.sleep(0.15)
    
    @staticmethod
    def progress_spiral(duration: float = 2.0):
        """Spiral progress indicator"""
        spirals = ["◐", "◓", "◑", "◒"]
        start = time.time()
        
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Processing signals...", total=None)
            
            while time.time() - start < duration:
                time.sleep(0.1)


class SignalEmitter:
    """
    📡 High-level signal emitter for the highway
    """
    
    def __init__(self):
        self.tower = SignalTower()
        self.dashboard = SignalDashboard(self.tower)
        
    def agent_found(self, name: str, confidence: float, source: str):
        """Signal when an agent is discovered"""
        signal_type = SignalType.HIGH_CONFIDENCE if confidence > 0.9 else SignalType.AGENT_DISCOVERED
        
        self.tower.emit(
            signal_type=signal_type,
            message=f"Agent discovered: {name} from {source}",
            confidence=confidence
        )
        
        # Special effect for high confidence
        if confidence > 0.9:
            SignalEffects.celebration()
        else:
            SignalEffects.agent_ripple(name)
    
    def collection_started(self, source: str):
        """Signal collection start"""
        self.tower.emit(
            signal_type=SignalType.COLLECTION_START,
            message=f"Started collecting from {source}"
        )
    
    def collection_complete(self, source: str, count: int):
        """Signal collection completion"""
        self.tower.emit(
            signal_type=SignalType.COLLECTION_END,
            message=f"Collection complete: {count} items from {source}"
        )
    
    def swarm_alert(self, swarm_size: int):
        """Alert for detected swarm"""
        self.tower.emit(
            signal_type=SignalType.SWARM_DETECTED,
            message=f"🐝 SWARM DETECTED: {swarm_size} coordinated agents!"
        )
        SignalEffects.alert_flash("SWARM DETECTED", count=2)
    
    def heartbeat(self):
        """Regular heartbeat signal"""
        self.tower.emit(
            signal_type=SignalType.HEARTBEAT,
            message="Highway operational"
        )
    
    async def demo_mode(self):
        """Run a demo of all signal types"""
        console.print("\n[bold cyan]🎭 SIGNAL SYSTEM DEMO 🎭[/bold cyan]\n")
        
        # Start dashboard
        dashboard_task = asyncio.create_task(self.dashboard.run(duration=30))
        
        # Emit various signals
        signals = [
            (SignalType.COLLECTION_START, "Started GitHub collector", None, 0),
            (SignalType.DATA_RECEIVED, "Received 50 repositories", None, 0),
            (SignalType.AGENT_DISCOVERED, "Agent discovered: ChatBot-v2", "agent_001", 0.75),
            (SignalType.AGENT_DISCOVERED, "Agent discovered: CodeAgent-Pro", "agent_002", 0.88),
            (SignalType.HIGH_CONFIDENCE, "⭐ HIGH CONFIDENCE: AutoGPT-Fork", "agent_003", 0.95),
            (SignalType.DATA_RECEIVED, "Processing swarm data...", None, 0),
            (SignalType.SWARM_DETECTED, "🐝 Coordinated bot network found!", None, 0),
            (SignalType.COLLECTION_END, "GitHub collection complete: 150 agents", None, 0),
        ]
        
        for signal_type, message, agent_id, confidence in signals:
            await asyncio.sleep(2)
            self.tower.emit(
                signal_type=signal_type,
                message=message,
                agent_id=agent_id,
                confidence=confidence
            )
            
            # Update dashboard counters
            if signal_type == SignalType.AGENT_DISCOVERED:
                self.dashboard.agent_count += 1
            self.dashboard.event_count += 1
        
        await dashboard_task


# Convenience function for quick usage
def create_signal_show():
    """Create and return a signal emitter for easy use"""
    return SignalEmitter()


async def main():
    """Main demo entry point"""
    console.print("""
[bold cyan]
╔══════════════════════════════════════════════════════════╗
║         🚦 AGENT HIGHWAY - VISUAL SIGNALING 🚦           ║
║                                                            ║
║   Bringing color and life to agent monitoring!           ║
╚══════════════════════════════════════════════════════════╝
[/bold cyan]
    """)
    
    emitter = SignalEmitter()
    await emitter.demo_mode()


if __name__ == "__main__":
    asyncio.run(main())
