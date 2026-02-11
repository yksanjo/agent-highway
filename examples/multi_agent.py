"""
Multi-agent example showing agent spawning and handoffs.

Demonstrates parent-child relationships and task delegation.
"""

import asyncio
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from highway.beacon import AgentBeacon, BeaconConfig


class WorkerAgent:
    """A worker agent that processes tasks."""
    
    def __init__(self, worker_id: str, parent_id: str):
        self.worker_id = worker_id
        self.parent_id = parent_id
        self.beacon = None
    
    async def start(self):
        """Start the worker."""
        config = BeaconConfig(
            endpoint="http://localhost:8787",
            lane="workers"
        )
        
        self.beacon = AgentBeacon(
            agent_id=self.worker_id,
            agent_type="worker",
            config=config,
            metadata={"parent": self.parent_id}
        )
        
        await self.beacon.connect()
        await self.beacon.birth()
    
    async def process_task(self, task_id: str, work_type: str):
        """Process a single task."""
        await self.beacon.task_start(task_id, {"work_type": work_type})
        
        # Simulate work
        duration = random.uniform(0.5, 2.0)
        await asyncio.sleep(duration)
        
        success = random.random() > 0.2  # 80% success rate
        
        if success:
            await self.beacon.task_complete(
                task_id,
                result="success",
                payload={"duration": duration, "work_type": work_type}
            )
        else:
            await self.beacon.error(
                Exception("Random failure"),
                {"task_id": task_id, "work_type": work_type}
            )
        
        return success
    
    async def shutdown(self):
        """Shutdown the worker."""
        if self.beacon:
            await self.beacon.shutdown()


class OrchestratorAgent:
    """Orchestrator that spawns workers and delegates tasks."""
    
    def __init__(self):
        self.beacon = None
        self.workers = []
    
    async def start(self):
        """Start the orchestrator."""
        config = BeaconConfig(
            endpoint="http://localhost:8787",
            lane="orchestrators"
        )
        
        self.beacon = AgentBeacon(
            agent_id="orch-001",
            agent_type="orchestrator",
            config=config
        )
        
        await self.beacon.connect()
        await self.beacon.birth()
        await self.beacon.start_heartbeat()
    
    async def spawn_worker(self, worker_id: str):
        """Spawn a new worker agent."""
        worker = WorkerAgent(worker_id, self.beacon.agent_id)
        await worker.start()
        self.workers.append(worker)
        
        # Emit handoff beacon to track delegation
        await self.beacon.handoff(
            target_agent_id=worker_id,
            context={"action": "spawn", "worker_type": "standard"}
        )
        
        return worker
    
    async def delegate_task(self, worker: WorkerAgent, task_id: str, work_type: str):
        """Delegate a task to a worker."""
        # Emit handoff for task delegation
        await self.beacon.handoff(
            target_agent_id=worker.worker_id,
            context={"action": "delegate", "task_id": task_id},
            task_id=task_id
        )
        
        # Worker processes the task
        success = await worker.process_task(task_id, work_type)
        
        # Worker returns result (implicit handoff back)
        return success
    
    async def run_workload(self, num_tasks: int = 10):
        """Run a workload with multiple workers."""
        print(f"🚀 Starting workload: {num_tasks} tasks")
        
        await self.beacon.task_start("workload-001", {"num_tasks": num_tasks})
        
        # Spawn workers
        workers = []
        for i in range(3):
            worker_id = f"worker-{i+1:03d}"
            print(f"  👷 Spawning {worker_id}")
            worker = await self.spawn_worker(worker_id)
            workers.append(worker)
        
        # Distribute tasks
        tasks_completed = 0
        for i in range(num_tasks):
            worker = workers[i % len(workers)]
            task_id = f"task-{i+1:03d}"
            work_type = random.choice(["compute", "io", "transform"])
            
            print(f"  📋 Delegating {task_id} to {worker.worker_id}")
            success = await self.delegate_task(worker, task_id, work_type)
            
            if success:
                tasks_completed += 1
                print(f"    ✅ {task_id} completed")
            else:
                print(f"    ❌ {task_id} failed")
        
        await self.beacon.task_complete(
            "workload-001",
            result="success",
            payload={"completed": tasks_completed, "total": num_tasks}
        )
        
        print(f"\n✅ Workload complete: {tasks_completed}/{num_tasks} tasks")
        
        # Shutdown workers
        print("\n🛑 Shutting down workers...")
        for worker in workers:
            await worker.shutdown()
    
    async def shutdown(self):
        """Shutdown the orchestrator."""
        await self.beacon.shutdown()


async def main():
    """Run the multi-agent example."""
    orchestrator = OrchestratorAgent()
    
    try:
        await orchestrator.start()
        print("🎯 Orchestrator ready\n")
        
        await orchestrator.run_workload(num_tasks=6)
        
    finally:
        await orchestrator.shutdown()
        print("\n👋 Orchestrator shutdown")


if __name__ == "__main__":
    asyncio.run(main())
