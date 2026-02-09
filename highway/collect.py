"""
Unified Collector Runner - Bundles all data collection
"""

import asyncio
import importlib
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class CollectorRunner:
    """Runs all enabled collectors"""
    
    COLLECTOR_MAP = {
        "github": "collectors.github.GitHubAgentCollector",
        "openclaw": "collectors.openclaw.OpenClawScanner",
        "discord": "collectors.discord.DiscordCollector",
        "telegram": "collectors.telegram.TelegramCollector",
        "pypi": "collectors.pypi.PyPICollector",
    }
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.collectors: Dict[str, Any] = {}
        self._load_collectors()
        
    def _load_collectors(self):
        """Load collector classes dynamically"""
        for name, class_path in self.COLLECTOR_MAP.items():
            collector_config = self.config.get(name, {})
            
            if collector_config.get("enabled", False):
                try:
                    module_path, class_name = class_path.rsplit(".", 1)
                    module = importlib.import_module(module_path)
                    collector_class = getattr(module, class_name)
                    
                    self.collectors[name] = collector_class(collector_config)
                    logger.info(f"✅ Loaded collector: {name}")
                    
                except Exception as e:
                    logger.warning(f"⚠️  Could not load collector {name}: {e}")
                    
    async def collect(self, source: Optional[str] = None) -> List[Dict]:
        """
        Run data collection
        
        Args:
            source: Specific collector to run, or None for all
            
        Returns:
            List of collected items
        """
        all_results = []
        
        if source:
            # Run specific collector
            if source in self.collectors:
                results = await self._run_collector(source)
                all_results.extend(results)
            else:
                logger.error(f"❌ Collector not found: {source}")
        else:
            # Run all enabled collectors in parallel
            tasks = []
            for name in self.collectors:
                task = self._run_collector(name)
                tasks.append(task)
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_results.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"❌ Collector error: {result}")
                    
        return all_results
        
    async def _run_collector(self, name: str) -> List[Dict]:
        """Run a single collector"""
        collector = self.collectors[name]
        
        try:
            logger.info(f"🔍 Running collector: {name}")
            
            # Run collection
            if hasattr(collector, 'collect'):
                if asyncio.iscoroutinefunction(collector.collect):
                    results = await collector.collect()
                else:
                    results = collector.collect()
            else:
                logger.warning(f"⚠️  Collector {name} has no collect method")
                return []
                
            # Normalize results
            normalized = []
            for item in results:
                normalized.append({
                    "_source": name,
                    "_collected_at": asyncio.get_event_loop().time(),
                    **self._normalize_item(item, name)
                })
                
            logger.info(f"✅ Collector {name} found {len(normalized)} items")
            return normalized
            
        except Exception as e:
            logger.error(f"❌ Error in collector {name}: {e}")
            return []
            
    def _normalize_item(self, item: Any, source: str) -> Dict:
        """Normalize collector output to standard format"""
        if isinstance(item, dict):
            return item
            
        # Handle dataclass objects
        if hasattr(item, '__dataclass_fields__'):
            from dataclasses import asdict
            return asdict(item)
            
        # Handle objects with to_dict method
        if hasattr(item, 'to_dict'):
            return item.to_dict()
            
        # Fallback
        return {"data": str(item)}
        
    def list_collectors(self) -> List[str]:
        """List available collectors"""
        return list(self.COLLECTOR_MAP.keys())
        
    def get_status(self) -> Dict[str, Any]:
        """Get collector status"""
        return {
            "enabled": list(self.collectors.keys()),
            "available": list(self.COLLECTOR_MAP.keys()),
            "count": len(self.collectors),
        }


# Convenience functions for CLI
async def run_collection(source: Optional[str] = None, config_path: Optional[str] = None):
    """Run collection from CLI"""
    from .core import HighwayConfig
    
    if config_path:
        highway_config = HighwayConfig.from_yaml(config_path)
    else:
        highway_config = HighwayConfig()
        
    runner = CollectorRunner(highway_config.collectors)
    results = await runner.collect(source)
    
    print(f"\n🎯 Collection complete: {len(results)} items")
    
    # Group by source
    by_source = {}
    for item in results:
        src = item.get("_source", "unknown")
        by_source[src] = by_source.get(src, 0) + 1
        
    print("\nBy Source:")
    for src, count in sorted(by_source.items()):
        print(f"  - {src}: {count}")
        
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Highway Collector")
    parser.add_argument("--source", "-s", help="Specific collector to run")
    parser.add_argument("--config", "-c", help="Config file path")
    
    args = parser.parse_args()
    
    asyncio.run(run_collection(args.source, args.config))
