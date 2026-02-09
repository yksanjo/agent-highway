"""
Agent Highway Core - The central nervous system
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

from .collect import CollectorRunner
from .process import StreamProcessor
from .detect import AgentDetector
from .storage import HighwayStorage


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class HighwayConfig:
    """Configuration for Agent Highway"""
    name: str = "Agent Highway"
    version: str = "1.0.0"
    data_dir: Path = field(default_factory=lambda: Path("./data"))
    
    # Collector settings
    collectors: Dict[str, Any] = field(default_factory=dict)
    
    # Processing settings
    batch_size: int = 100
    flush_interval: int = 5
    
    # Detection settings
    confidence_threshold: float = 0.6
    min_signals: int = 3
    
    @classmethod
    def from_yaml(cls, path: str) -> "HighwayConfig":
        """Load configuration from YAML file"""
        with open(path) as f:
            config = yaml.safe_load(f)
        
        highway_config = config.get("highway", {})
        
        return cls(
            name=highway_config.get("name", "Agent Highway"),
            version=highway_config.get("version", "1.0.0"),
            data_dir=Path(highway_config.get("data_dir", "./data")),
            collectors=config.get("collectors", {}),
            batch_size=config.get("processing", {}).get("batch_size", 100),
            flush_interval=config.get("processing", {}).get("flush_interval", 5),
            confidence_threshold=config.get("detection", {}).get("confidence_threshold", 0.6),
            min_signals=config.get("detection", {}).get("min_signals", 3),
        )


class AgentHighway:
    """
    The main Agent Highway orchestrator.
    Coordinates collectors, processing, and analysis.
    """
    
    def __init__(self, config: Optional[HighwayConfig] = None):
        self.config = config or HighwayConfig()
        self.storage = HighwayStorage(self.config.data_dir)
        self.collector_runner = CollectorRunner(self.config.collectors)
        self.processor = StreamProcessor(
            batch_size=self.config.batch_size,
            flush_interval=self.config.flush_interval
        )
        self.detector = AgentDetector(
            confidence_threshold=self.config.confidence_threshold,
            min_signals=self.config.min_signals
        )
        
        self._running = False
        self._metrics = {
            "agents_discovered": 0,
            "events_processed": 0,
            "collectors_run": 0,
            "start_time": None,
        }
        
    async def start(self):
        """Start the highway system"""
        logger.info(f"🛣️  Starting {self.config.name} v{self.config.version}")
        
        self._running = True
        self._metrics["start_time"] = datetime.utcnow()
        
        # Initialize storage
        await self.storage.initialize()
        
        # Start stream processor
        asyncio.create_task(self.processor.run())
        
        logger.info("✅ Agent Highway is operational")
        
    async def stop(self):
        """Stop the highway system"""
        logger.info("🛑 Stopping Agent Highway...")
        
        self._running = False
        await self.processor.stop()
        await self.storage.close()
        
        logger.info("✅ Agent Highway stopped")
        
    async def collect(self, source: Optional[str] = None, continuous: bool = False):
        """
        Run data collection
        
        Args:
            source: Specific collector to run (None = all enabled)
            continuous: Whether to run continuously
        """
        logger.info(f"🔍 Starting collection from: {source or 'all enabled sources'}")
        
        if continuous:
            while self._running:
                await self._run_collection(source)
                await asyncio.sleep(300)  # 5 minute interval
        else:
            await self._run_collection(source)
            
    async def _run_collection(self, source: Optional[str] = None):
        """Execute collection run"""
        try:
            results = await self.collector_runner.collect(source)
            
            for item in results:
                # Process through pipeline
                await self.processor.submit(item)
                
            self._metrics["collectors_run"] += 1
            self._metrics["events_processed"] += len(results)
            
            logger.info(f"✅ Collected {len(results)} items from {source or 'all'}")
            
        except Exception as e:
            logger.error(f"❌ Collection error: {e}")
            
    async def analyze(self, analysis_type: str = "all") -> Dict:
        """
        Run analysis on collected data
        
        Args:
            analysis_type: Type of analysis (network, trends, swarms, all)
            
        Returns:
            Analysis results
        """
        logger.info(f"📊 Running {analysis_type} analysis...")
        
        results = {}
        
        if analysis_type in ("network", "all"):
            results["network"] = await self._analyze_network()
            
        if analysis_type in ("trends", "all"):
            results["trends"] = await self._analyze_trends()
            
        if analysis_type in ("swarms", "all"):
            results["swarms"] = await self._analyze_swarms()
            
        return results
        
    async def _analyze_network(self) -> Dict:
        """Analyze agent network relationships"""
        from insights.network import NetworkAnalyzer
        
        analyzer = NetworkAnalyzer(self.storage)
        return await analyzer.analyze()
        
    async def _analyze_trends(self) -> Dict:
        """Analyze growth trends"""
        from insights.trends import TrendAnalyzer
        
        analyzer = TrendAnalyzer(self.storage)
        return await analyzer.analyze()
        
    async def _analyze_swarms(self) -> Dict:
        """Detect agent swarms"""
        from insights.swarms import SwarmDetector
        
        detector = SwarmDetector(self.storage)
        return await detector.detect()
        
    def query(self, **filters) -> List[Dict]:
        """
        Query discovered agents
        
        Args:
            **filters: Query filters (type, platform, min_confidence, etc.)
            
        Returns:
            List of matching agents
        """
        return self.storage.query_agents(**filters)
        
    def get_metrics(self) -> Dict:
        """Get highway metrics"""
        uptime = None
        if self._metrics["start_time"]:
            uptime = (datetime.utcnow() - self._metrics["start_time"]).total_seconds()
            
        return {
            **self._metrics,
            "uptime_seconds": uptime,
            "is_running": self._running,
        }
        
    def get_status(self) -> str:
        """Get highway status summary"""
        metrics = self.get_metrics()
        
        status = f"""
╔══════════════════════════════════════════════════════════╗
║                    🛣️ AGENT HIGHWAY                      ║
╠══════════════════════════════════════════════════════════╣
║  Status: {'🟢 OPERATIONAL' if self._running else '🔴 STOPPED'}              ║
║  Version: {self.config.version:<48}║
╠══════════════════════════════════════════════════════════╣
║  METRICS                                                 ║
║  ─────────────────────────────────────────────────────── ║
║  Agents Discovered: {metrics['agents_discovered']:<31}║
║  Events Processed:  {metrics['events_processed']:<31}║
║  Collectors Run:    {metrics['collectors_run']:<31}║
║  Uptime:            {metrics['uptime_seconds'] or 0:.0f}s{'':<28}║
╚══════════════════════════════════════════════════════════╝
        """
        return status


# Singleton instance
_highway_instance: Optional[AgentHighway] = None


def get_highway() -> AgentHighway:
    """Get or create the singleton highway instance"""
    global _highway_instance
    if _highway_instance is None:
        _highway_instance = AgentHighway()
    return _highway_instance
