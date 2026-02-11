"""
🎨 Banners and ASCII Art for Agent Highway
Because why not make it beautiful?
"""

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
import random

console = Console()


class HighwayBanners:
    """
    Collection of fun ASCII art banners for Agent Highway
    """
    
    HIGHWAY_LARGE = """
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║   ██╗  ██╗██╗ ██████╗ ██╗  ██╗██╗    ██╗ █████╗ ██╗   ██╗    ║
    ║   ██║  ██║██║██╔════╝ ██║  ██║██║    ██║██╔══██╗╚██╗ ██╔╝    ║
    ║   ███████║██║██║  ███╗███████║██║ █╗ ██║███████║ ╚████╔╝     ║
    ║   ██╔══██║██║██║   ██║██╔══██║██║███╗██║██╔══██║  ╚██╔╝      ║
    ║   ██║  ██║██║╚██████╔╝██║  ██║╚███╔███╔╝██║  ██║   ██║       ║
    ║   ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝       ║
    ║                                                                ║
    ║              🛣️  THE UNIFIED SUPERHIGHWAY  🛣️                  ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """
    
    HIGHWAY_COMPACT = """
╔════════════════════════════════════╗
║   🛣️  AGENT HIGHWAY  🛣️           ║
║   All roads lead to agents         ║
╚════════════════════════════════════╝
    """
    
    SIGNAL_TOWER = """
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
        ═════╧═══╧═════
       
       🗼 SIGNAL TOWER ACTIVE
    """
    
    TRAFFIC_SCENE = """
        🌅 Morning on the Highway
    ═══════════════════════════════════
    
          ☁️  ☁️      ☁️
       ☀️              ☁️
    ═══════════════════════════════════
          🚗        🚕
    🛣️══════════════════════════════🛣️
        🚙        🏎️      🚓
    ═══════════════════════════════════
        
        Traffic: FLOWING
        Agents:  ON THE MOVE
    """
    
    DISCOVERY_CELEBRATION = """
    ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨
    ✨                                      ✨
    ✨     🎊 NEW AGENT DISCOVERED! 🎊      ✨
    ✨                                      ✨
    ✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨
    """
    
    AGENT_TYPES = {
        "autonomous": """
    🤖 AUTONOMOUS AGENT
    ═══════════════════
       ┌─────────┐
       │  ◕  ◕  │
       │    ▽   │
       │ ═══════ │
       └─────────┘
       Fully self-directed
        """,
        
        "chatbot": """
    💬 CHATBOT AGENT
    ═══════════════════
       ┌─────────┐
       │  ^   ^  │
       │   (◠‿◠) │
       │ ═══════ │
       └─────────┘
       Conversation ready
        """,
        
        "orchestrator": """
    🎭 ORCHESTRATOR AGENT
    ═══════════════════
       ┌─────────┐
       │  ◉  ◉  │
       │    ◯   │
       │ ═══════ │
       └─────────┘
       Multi-agent coordination
        """,
        
        "code_agent": """
    💻 CODE AGENT
    ═══════════════════
       ┌─────────┐
       │  { } { }│
       │   [ ]   │
       │ ═══════ │
       └─────────┘
       Programming specialist
        """,
    }
    
    LOADING_ANIMATIONS = [
        ["◐", "◓", "◑", "◒"],
        ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
        ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃"],
        ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"],
        ["◢", "◣", "◤", "◥"],
        ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"],
    ]
    
    SUCCESS_FRAMES = [
        "✅",
        "✓",
        "🎉",
        "🌟",
        "⭐",
        "💫",
    ]
    
    @classmethod
    def get_random_loading(cls) -> list:
        """Get a random loading animation"""
        return random.choice(cls.LOADING_ANIMATIONS)
    
    @classmethod
    def print_highway(cls, compact: bool = False):
        """Print the highway banner"""
        banner = cls.HIGHWAY_COMPACT if compact else cls.HIGHWAY_LARGE
        console.print(f"[bold cyan]{banner}[/bold cyan]")
    
    @classmethod
    def print_signal_tower(cls):
        """Print signal tower"""
        console.print(f"[bold yellow]{cls.SIGNAL_TOWER}[/bold yellow]")
    
    @classmethod
    def print_traffic_scene(cls):
        """Print traffic scene"""
        console.print(f"[bright_blue]{cls.TRAFFIC_SCENE}[/bright_blue]")
    
    @classmethod
    def print_agent(cls, agent_type: str):
        """Print agent ASCII art"""
        art = cls.AGENT_TYPES.get(agent_type, cls.AGENT_TYPES["autonomous"])
        console.print(f"[green]{art}[/green]")
    
    @classmethod
    def print_discovery(cls):
        """Print discovery celebration"""
        console.print(f"[bold yellow]{cls.DISCOVERY_CELEBRATION}[/bold yellow]")
    
    @classmethod
    def create_road(cls, width: int = 60) -> str:
        """Create a visual road"""
        road = "═" * width
        return f"🛣️{road}🛣️"
    
    @classmethod
    def create_traffic_bar(cls, percent: float, width: int = 30) -> str:
        """Create a traffic intensity bar"""
        filled = int((percent / 100) * width)
        empty = width - filled
        
        if percent < 30:
            color = "green"
            emoji = "🟢"
        elif percent < 70:
            color = "yellow"
            emoji = "🟡"
        else:
            color = "red"
            emoji = "🔴"
        
        bar = f"[{color}]{'█' * filled}{'░' * empty}[/{color}]"
        return f"{emoji} {bar} {percent:.0f}%"
    
    @classmethod
    def create_speedometer(cls, value: float, max_val: float = 100) -> str:
        """Create a speedometer-style display"""
        percent = min(value / max_val, 1.0)
        segments = 20
        filled = int(percent * segments)
        
        gauge = "▰" * filled + "▱" * (segments - filled)
        
        if percent < 0.3:
            color = "dim"
        elif percent < 0.7:
            color = "cyan"
        else:
            color = "bright_cyan"
        
        return f"[{color}]⚡ {gauge} {value:.0f} events/s[/{color}]"
    
    @classmethod
    def create_counter(cls, label: str, value: int, icon: str = "📊") -> Panel:
        """Create a counter panel"""
        # Create large number with icon
        text = Text()
        text.append(f"{icon}\n", style="dim")
        text.append(f"{value:,}", style="bold bright_cyan")
        text.append(f"\n{label}", style="dim")
        
        return Panel(
            Align.center(text),
            border_style="cyan"
        )
    
    @classmethod
    def create_live_indicator(cls, is_live: bool = True) -> str:
        """Create a live/recording indicator"""
        if is_live:
            return "[bold red]● LIVE[/bold red]"
        return "[dim]○ OFFLINE[/dim]"


class FunMessages:
    """
    Fun status messages and quips
    """
    
    STARTUP_MESSAGES = [
        "🛣️  All lanes open - ready for agents!",
        "🚦 Highway systems initialized - green light!",
        "📡 Signal tower online - watching for agents...",
        "🤖 Agent detection ready - scanning the horizon",
        "⚡ Highway energized - let's find some agents!",
    ]
    
    DISCOVERY_QUIPS = [
        "🎯 Bullseye! Found one!",
        "🔍 Another agent spotted!",
        "🎣 Reeled in a big one!",
        "🕵️  Agent detected in the wild!",
        "🌟 EUREKA! Agent found!",
        "🎊 Agent acquired!",
    ]
    
    HIGH_CONFIDENCE_QUIPS = [
        "🏆 JACKPOT! High-value agent!",
        "💎 Rare agent discovered!",
        "🌟 LEGENDARY agent found!",
        "🔥 This one's a game-changer!",
        "⭐ EXCEPTIONAL agent detected!",
    ]
    
    COLLECTION_MESSAGES = [
        "📦 Collecting data packages...",
        "🔍 Scanning the interwebs...",
        "📡 Pinging agent repositories...",
        "🕸️  Crawling the agent web...",
        "🔎 On the hunt for agents...",
    ]
    
    SWARM_MESSAGES = [
        "🐝 HIVE DETECTED! Multiple agents!",
        "🌊 WAVE INCOMING! Agent swarm!",
        "🎯 TARGET RICH ENVIRONMENT!",
        "🔥 HOT ZONE! Agent activity spike!",
    ]
    
    COMPLETION_MESSAGES = [
        "🏁 Collection complete - great haul!",
        "✅ Mission accomplished!",
        "🎉 Another successful run!",
        "📊 Data capture complete!",
    ]
    
    @classmethod
    def get_startup(cls) -> str:
        return random.choice(cls.STARTUP_MESSAGES)
    
    @classmethod
    def get_discovery(cls, high_confidence: bool = False) -> str:
        if high_confidence:
            return random.choice(cls.HIGH_CONFIDENCE_QUIPS)
        return random.choice(cls.DISCOVERY_QUIPS)
    
    @classmethod
    def get_collection(cls) -> str:
        return random.choice(cls.COLLECTION_MESSAGES)
    
    @classmethod
    def get_swarm(cls) -> str:
        return random.choice(cls.SWARM_MESSAGES)
    
    @classmethod
    def get_completion(cls) -> str:
        return random.choice(cls.COMPLETION_MESSAGES)


# Quick demo
def show_all_banners():
    """Display all banners"""
    console.print("\n[bold]=== HIGHWAY BANNERS ===[/bold]\n")
    HighwayBanners.print_highway()
    
    console.print("\n[bold]=== COMPACT VERSION ===[/bold]\n")
    HighwayBanners.print_highway(compact=True)
    
    console.print("\n[bold]=== SIGNAL TOWER ===[/bold]\n")
    HighwayBanners.print_signal_tower()
    
    console.print("\n[bold]=== TRAFFIC SCENE ===[/bold]\n")
    HighwayBanners.print_traffic_scene()
    
    console.print("\n[bold]=== AGENT TYPES ===[/bold]\n")
    for agent_type in HighwayBanners.AGENT_TYPES:
        HighwayBanners.print_agent(agent_type)
    
    console.print("\n[bold]=== DISCOVERY ===[/bold]\n")
    HighwayBanners.print_discovery()
    
    console.print("\n[bold]=== FUN MESSAGES ===[/bold]\n")
    console.print(FunMessages.get_startup())
    console.print(FunMessages.get_discovery())
    console.print(FunMessages.get_discovery(high_confidence=True))
    console.print(FunMessages.get_collection())
    console.print(FunMessages.get_swarm())
    console.print(FunMessages.get_completion())
    
    console.print("\n[bold]=== VISUAL ELEMENTS ===[/bold]\n")
    console.print(HighwayBanners.create_road())
    console.print(HighwayBanners.create_traffic_bar(45))
    console.print(HighwayBanners.create_speedometer(850))
    console.print(HighwayBanners.create_live_indicator())


if __name__ == "__main__":
    show_all_banners()
