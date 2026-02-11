"""
🎨 Visual Integration - Connect signals to highway events
"""

import asyncio
from typing import Optional
from pathlib import Path

from .signals import SignalEmitter, SignalType, SignalTower, SignalDashboard, SignalEffects
from .core import AgentHighway


class VisualHighway(AgentHighway):
    """
    Agent Highway with visual signaling capabilities
    """
    
    def __init__(self, config=None, enable_visuals: bool = True):
        super().__init__(config)
        self.enable_visuals = enable_visuals
        self.emitter: Optional[SignalEmitter] = None
        
        if enable_visuals:
            self.emitter = SignalEmitter()
            self._setup_signal_hooks()
    
    def _setup_signal_hooks(self):
        """Connect highway events to visual signals"""
        # Hook into storage to detect new agents
        original_save = self.storage.save_agent
        
        async def visual_save_agent(agent):
            # Call original
            await original_save(agent)
            
            # Emit visual signal
            if self.emitter:
                name = agent.get("name", "Unknown")
                confidence = agent.get("confidence_score", 0)
                source = agent.get("source", "unknown")
                
                self.emitter.agent_found(name, confidence, source)
                
                # Update dashboard
                self.emitter.dashboard.agent_count += 1
        
        self.storage.save_agent = visual_save_agent
    
    async def start(self):
        """Start with visual flair"""
        if self.emitter:
            self.emitter.collection_started("highway")
        
        await super().start()
        
        if self.emitter:
            self.emitter.tower.emit(
                SignalType.HEARTBEAT,
                "🛣️  Highway is operational!"
            )
    
    async def collect(self, source=None, continuous=False):
        """Collect with visual feedback"""
        if self.emitter:
            self.emitter.collection_started(source or "all")
        
        await super().collect(source, continuous)
        
        if self.emitter:
            self.emitter.collection_complete(
                source or "all", 
                self._metrics["events_processed"]
            )
    
    async def run_dashboard(self):
        """Run the visual dashboard"""
        if not self.emitter:
            print("Visuals not enabled")
            return
        
        await self.emitter.dashboard.run()


def add_visuals_to_highway(highway: AgentHighway) -> VisualHighway:
    """
    Wrap an existing highway with visual capabilities
    """
    visual_highway = VisualHighway(highway.config, enable_visuals=True)
    
    # Copy over state
    visual_highway.storage = highway.storage
    visual_highway._metrics = highway._metrics
    
    return visual_highway


class SignalCLI:
    """
    🎮 CLI for visual signaling demonstrations
    """
    
    @staticmethod
    def celebrate():
        """Trigger celebration effect"""
        SignalEffects.celebration()
    
    @staticmethod
    def alert(message: str = "ALERT"):
        """Trigger alert effect"""
        SignalEffects.alert_flash(message)
    
    @staticmethod
    def discovery(name: str):
        """Simulate agent discovery"""
        SignalEffects.agent_ripple(name)
    
    @staticmethod
    def tower():
        """Show signal tower"""
        from rich.console import Console
        from rich.live import Live
        import time
        
        console = Console()
        tower = SignalTower()
        
        # Emit some demo signals
        demo_signals = [
            (SignalType.AGENT_DISCOVERED, "Found: AutoGPT-v2"),
            (SignalType.HIGH_CONFIDENCE, "⭐ Super Agent Found!"),
            (SignalType.DATA_RECEIVED, "Batch: 100 repos"),
            (SignalType.HEARTBEAT, "Systems nominal"),
        ]
        
        with Live(tower.render_tower(), refresh_per_second=2) as live:
            for sig_type, msg in demo_signals:
                tower.emit(sig_type, msg)
                live.update(tower.render_tower())
                time.sleep(1)
            
            time.sleep(2)
    
    @staticmethod
    async def dashboard_demo():
        """Run full dashboard demo"""
        emitter = SignalEmitter()
        await emitter.demo_mode()


# Make signals available at highway level
__all__ = [
    'SignalEmitter',
    'SignalType', 
    'SignalTower',
    'SignalDashboard',
    'SignalEffects',
    'VisualHighway',
    'SignalCLI',
    'add_visuals_to_highway',
]
