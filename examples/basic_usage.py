"""
Basic usage example for the Agent Highway Beacon SDK.

Shows how to emit signal liens from an agent.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from highway.beacon import AgentBeacon, BeaconConfig


async def main():
    """Example agent that emits beacons."""
    
    # Configure beacon endpoint
    config = BeaconConfig(
        endpoint="http://localhost:8787",  # Local dev server
        heartbeat_interval=10,  # Heartbeat every 10 seconds
        lane="demo"
    )
    
    # Create and start beacon
    async with AgentBeacon(
        agent_id="demo-agent-001",
        agent_type="example_worker",
        config=config,
        metadata={"version": "1.0", "region": "us-east"}
    ) as beacon:
        
        print(f"🚀 Agent {beacon.agent_id} started")
        
        # Start heartbeat
        await beacon.start_heartbeat()
        print("💓 Heartbeat started")
        
        # Simulate some work
        for i in range(3):
            task_id = f"task-{i+1}"
            
            # Start task
            await beacon.task_start(task_id, {"iteration": i})
            print(f"📋 Started {task_id}")
            
            # Do "work"
            await asyncio.sleep(2)
            
            # Complete task
            await beacon.task_complete(
                task_id, 
                result="success",
                payload={"items_processed": (i + 1) * 10}
            )
            print(f"✅ Completed {task_id}")
        
        # Stop heartbeat before shutdown
        await beacon.stop_heartbeat()
        print("🛑 Heartbeat stopped")
    
    print("👋 Agent shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
