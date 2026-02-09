"""
Agent Highway - The unified superhighway for AI agent discovery
"""

__version__ = "1.0.0"
__author__ = "Agent Highway Team"

from .core import AgentHighway, HighwayConfig
from .collect import CollectorRunner
from .process import StreamProcessor
from .detect import AgentDetector

__all__ = [
    "AgentHighway",
    "HighwayConfig",
    "CollectorRunner",
    "StreamProcessor",
    "AgentDetector",
]
