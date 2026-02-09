"""
Agent Highway Beacon SDK

A lightweight SDK for AI agents to emit signal liens (existence proofs)
to the Agent Highway Origin beacon collector.

Usage:
    from highway.beacon import AgentBeacon
    
    async with AgentBeacon("my-agent", "worker") as beacon:
        await beacon.start_heartbeat()
        await beacon.task_start("task-123")
        # ... do work ...
        await beacon.task_complete("task-123")
"""

from .beacon_sdk import (
    AgentBeacon,
    SignalLien,
    BeaconConfig,
    BeaconError,
    AuthenticationError,
)
from .decorators import beacon_task, beacon_agent
from .sync_wrapper import SyncBeacon

__version__ = "1.0.0"
__all__ = [
    "AgentBeacon",
    "SignalLien",
    "BeaconConfig",
    "BeaconError",
    "AuthenticationError",
    "beacon_task",
    "beacon_agent",
    "SyncBeacon",
]
