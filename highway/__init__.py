"""
Agent Highway - The unified superhighway for AI agent discovery
"""

__version__ = "1.0.0"
__author__ = "Agent Highway Team"

from .core import AgentHighway, HighwayConfig
from .collect import CollectorRunner
from .process import StreamProcessor
from .detect import AgentDetector

# Visual signaling components
from .signals import (
    SignalEmitter,
    SignalTower,
    SignalDashboard,
    SignalEffects,
    SignalType,
)
from .visual import VisualHighway, SignalCLI
from .banners import HighwayBanners, FunMessages

__all__ = [
    "AgentHighway",
    "HighwayConfig",
    "CollectorRunner",
    "StreamProcessor",
    "AgentDetector",
    # Visual signaling
    "SignalEmitter",
    "SignalTower",
    "SignalDashboard",
    "SignalEffects",
    "SignalType",
    "VisualHighway",
    "SignalCLI",
    "HighwayBanners",
    "FunMessages",
]
