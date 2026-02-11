"""
Decorator usage example for the Agent Highway Beacon SDK.

Shows how to use the @beacon_task decorator for automatic beacon emission.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from highway.beacon import AgentBeacon, BeaconConfig, beacon_task


class DataProcessor:
    """Example agent class with automatic beacon emission."""
    
    def __init__(self):
        self._beacon = None
        self.processed_count = 0
    
    async def initialize(self):
        """Initialize the beacon."""
        config = BeaconConfig(
            endpoint="http://localhost:8787",
            heartbeat_interval=15,
            lane="processing"
        )
        
        self._beacon = AgentBeacon(
            agent_id="processor-001",
            agent_type="data_processor",
            config=config
        )
        
        await self._beacon.connect()
        await self._beacon.birth()
        await self._beacon.start_heartbeat()
    
    async def cleanup(self):
        """Clean up resources."""
        if self._beacon:
            await self._beacon.shutdown()
    
    @beacon_task(task_id_arg="dataset_name", emit_result=True)
    async def process_dataset(self, dataset_name: str, batch_size: int = 100):
        """
        Process a dataset - automatically emits task_start and task_complete beacons.
        
        The @beacon_task decorator will:
        1. Emit task_start beacon with task_id="dataset_name"
        2. Execute this function
        3. Emit task_complete beacon on success, or error beacon on exception
        """
        print(f"📊 Processing dataset: {dataset_name} (batch_size={batch_size})")
        
        # Simulate processing
        for i in range(5):
            await asyncio.sleep(0.5)
            self.processed_count += batch_size
            print(f"  Processed batch {i+1}/5")
        
        return {"total_processed": self.processed_count, "dataset": dataset_name}
    
    @beacon_task(task_id_arg="job_id")
    async def analyze_data(self, job_id: str, data: dict):
        """Another example task with automatic beacons."""
        print(f"🔍 Analyzing data for job: {job_id}")
        
        # Simulate analysis
        await asyncio.sleep(1)
        
        result = {
            "records": len(data),
            "metrics": {"avg": 42.0, "max": 100}
        }
        
        return result


async def main():
    """Run the example."""
    processor = DataProcessor()
    
    try:
        await processor.initialize()
        print("🚀 Processor initialized\n")
        
        # Process datasets - beacons emitted automatically
        result1 = await processor.process_dataset("users_2024.csv", batch_size=50)
        print(f"✅ Result: {result1}\n")
        
        result2 = await processor.analyze_data(
            "analysis-001",
            {"user1": 100, "user2": 200, "user3": 300}
        )
        print(f"✅ Result: {result2}\n")
        
        # This will emit an error beacon
        print("⚠️ Simulating error...")
        try:
            await processor.analyze_data("analysis-002", None)  # Will cause error
        except Exception as e:
            print(f"Caught expected error: {e}\n")
        
    finally:
        await processor.cleanup()
        print("👋 Processor shutdown")


if __name__ == "__main__":
    asyncio.run(main())
