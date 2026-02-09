"""
Signal types and constants
"""

from enum import Enum
from typing import Any, Dict
from dataclasses import dataclass


class Lane(Enum):
    """Signal lanes (priority levels)."""
    CRITICAL = "critical"      # 0.1ms - System breaking issues
    STANDARD = "standard"      # 1ms - Normal operations  
    BACKGROUND = "background"  # 10ms - Learning, exploration


@dataclass
class Signal:
    """A signal traveling on the highway."""
    intent: str
    emitter: str
    lane: str = "standard"
    payload: Any = None
    amplitude: float = 0.8
    decay: int = 2000  # milliseconds
    
    def to_dict(self) -> Dict:
        return {
            "intent": self.intent,
            "emitter": self.emitter,
            "lane": self.lane,
            "payload": self.payload,
            "amplitude": self.amplitude,
            "decay": self.decay
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Signal':
        return cls(
            intent=data.get("intent", ""),
            emitter=data.get("emitter", "unknown"),
            lane=data.get("lane", "standard"),
            payload=data.get("payload"),
            amplitude=data.get("amplitude", 0.8),
            decay=data.get("decay", 2000)
        )
