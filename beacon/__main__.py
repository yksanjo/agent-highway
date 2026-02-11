"""
Command-line interface for the Beacon SDK.

Usage:
    python -m highway.beacon test --endpoint http://localhost:8787
    python -m highway.beacon emit --agent-id test --event birth
"""

import asyncio
import argparse
import sys
import time

from .beacon_sdk import AgentBeacon, BeaconConfig, EventType


async def test_command(args):
    """Test connection to beacon collector."""
    print(f"🧪 Testing connection to {args.endpoint}")
    
    config = BeaconConfig(endpoint=args.endpoint, lane="test")
    
    async with AgentBeacon(
        agent_id=f"test-{int(time.time())}",
        agent_type="cli_test",
        config=config
    ) as beacon:
        print(f"✅ Connected as {beacon.agent_id}")
        
        # Emit test liens
        await beacon.task_start("cli-test-task")
        print("📋 Task started")
        
        await asyncio.sleep(1)
        
        await beacon.task_complete("cli-test-task", payload={"test": True})
        print("✅ Task completed")
        
        print("\n✅ Test successful!")


async def emit_command(args):
    """Emit a single beacon."""
    config = BeaconConfig(endpoint=args.endpoint, lane=args.lane)
    
    beacon = AgentBeacon(
        agent_id=args.agent_id,
        agent_type=args.agent_type,
        config=config
    )
    
    await beacon.connect()
    
    success = await beacon.emit(
        event_type=args.event,
        task_id=args.task_id,
        metadata=args.metadata
    )
    
    if success:
        print(f"✅ Emitted {args.event} beacon")
    else:
        print("❌ Failed to emit beacon")
        sys.exit(1)
    
    await beacon.disconnect()


def main():
    parser = argparse.ArgumentParser(description="Agent Highway Beacon CLI")
    parser.add_argument("--endpoint", default="http://localhost:8787", help="Beacon endpoint")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test connection")
    
    # Emit command
    emit_parser = subparsers.add_parser("emit", help="Emit a beacon")
    emit_parser.add_argument("--agent-id", default=f"cli-{int(time.time())}", help="Agent ID")
    emit_parser.add_argument("--agent-type", default="cli", help="Agent type")
    emit_parser.add_argument("--event", choices=[e.value for e in EventType], required=True)
    emit_parser.add_argument("--task-id", help="Task ID")
    emit_parser.add_argument("--lane", default="cli", help="Lane")
    emit_parser.add_argument("--metadata", type=dict, default={}, help="Metadata JSON")
    
    args = parser.parse_args()
    
    if args.command == "test":
        asyncio.run(test_command(args))
    elif args.command == "emit":
        asyncio.run(emit_command(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
