"""
Synchronous usage example for the Agent Highway Beacon SDK.

Shows how to use the SyncBeacon wrapper for non-async code.
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from highway.beacon import SyncBeacon, BeaconConfig


def main():
    """Example synchronous agent."""
    
    # Configure beacon
    config = BeaconConfig(
        endpoint="http://localhost:8787",
        lane="sync_demo"
    )
    
    # Create sync beacon
    beacon = SyncBeacon(
        agent_id="sync-agent-001",
        agent_type="sync_worker",
        config=config
    )
    
    # Start beacon (emits birth signal)
    beacon.start()
    print(f"🚀 Agent {beacon._async_beacon.agent_id} started")
    
    # Start heartbeat
    beacon.start_heartbeat(interval=10)
    print("💓 Heartbeat started")
    
    try:
        # Simulate some synchronous work
        for i in range(3):
            task_id = f"sync-task-{i+1}"
            
            # Start task
            beacon.task_start(task_id, {"iteration": i})
            print(f"📋 Started {task_id}")
            
            # Do "work" (blocking sleep)
            time.sleep(1)
            
            # Complete task
            beacon.task_complete(
                task_id,
                result="success",
                payload={"items_processed": (i + 1) * 5}
            )
            print(f"✅ Completed {task_id}")
        
        # Simulate an error
        print("\n⚠️ Simulating error...")
        try:
            1 / 0
        except Exception as e:
            beacon.error(e, {"context": "during calculation"})
            print("📛 Error beacon emitted")
        
    finally:
        # Shutdown (emits death signal)
        beacon.shutdown("normal_completion")
        print("\n👋 Agent shutdown complete")


if __name__ == "__main__":
    main()
