"""
Stream Processing - Process collected data in real-time
"""

import asyncio
import logging
from collections import deque
from datetime import datetime
from typing import Dict, List, Any, Callable

logger = logging.getLogger(__name__)


class StreamProcessor:
    """Process data streams with batching and filtering"""
    
    def __init__(self, batch_size: int = 100, flush_interval: int = 5):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue: asyncio.Queue = asyncio.Queue()
        self.buffer: deque = deque(maxlen=batch_size * 2)
        self.filters: List[Callable] = []
        self.transformers: List[Callable] = []
        self.handlers: List[Callable] = []
        self._running = False
        
    async def run(self):
        """Run the stream processor"""
        self._running = True
        logger.info("🔄 Stream processor started")
        
        while self._running:
            try:
                # Wait for items or timeout
                item = await asyncio.wait_for(
                    self.queue.get(), 
                    timeout=self.flush_interval
                )
                
                # Process item
                await self._process_item(item)
                
                # Check if buffer needs flushing
                if len(self.buffer) >= self.batch_size:
                    await self._flush_buffer()
                    
            except asyncio.TimeoutError:
                # Flush on timeout
                if self.buffer:
                    await self._flush_buffer()
            except Exception as e:
                logger.error(f"❌ Stream processing error: {e}")
                
    async def stop(self):
        """Stop the stream processor"""
        self._running = False
        
        # Flush remaining items
        if self.buffer:
            await self._flush_buffer()
            
        logger.info("🛑 Stream processor stopped")
        
    async def submit(self, item: Dict):
        """Submit an item to the processing queue"""
        await self.queue.put(item)
        
    async def _process_item(self, item: Dict):
        """Process a single item through the pipeline"""
        # Apply filters
        for filter_fn in self.filters:
            if not filter_fn(item):
                return  # Item filtered out
                
        # Apply transformers
        for transform_fn in self.transformers:
            item = transform_fn(item)
            
        # Add to buffer
        self.buffer.append(item)
        
    async def _flush_buffer(self):
        """Flush buffer to handlers"""
        if not self.buffer:
            return
            
        items = list(self.buffer)
        self.buffer.clear()
        
        # Call handlers
        for handler in self.handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(items)
                else:
                    handler(items)
            except Exception as e:
                logger.error(f"❌ Handler error: {e}")
                
    def add_filter(self, filter_fn: Callable[[Dict], bool]):
        """Add a filter function"""
        self.filters.append(filter_fn)
        
    def add_transformer(self, transform_fn: Callable[[Dict], Dict]):
        """Add a transformer function"""
        self.transformers.append(transform_fn)
        
    def add_handler(self, handler_fn: Callable[[List[Dict]], Any]):
        """Add a handler function"""
        self.handlers.append(handler_fn)


class HighwayPipeline:
    """Pre-configured processing pipeline for Agent Highway"""
    
    @staticmethod
    def create_default(storage=None):
        """Create default processing pipeline"""
        processor = StreamProcessor()
        
        # Add filters
        processor.add_filter(HighwayPipeline._filter_invalid)
        processor.add_filter(HighwayPipeline._filter_low_confidence)
        
        # Add transformers
        processor.add_transformer(HighwayPipeline._add_timestamp)
        processor.add_transformer(HighwayPipeline._normalize_agent)
        
        # Add handlers
        if storage:
            processor.add_handler(storage.save_batch)
        
        processor.add_handler(HighwayPipeline._log_batch)
        
        return processor
        
    @staticmethod
    def _filter_invalid(item: Dict) -> bool:
        """Filter out invalid items"""
        return item is not None and isinstance(item, dict)
        
    @staticmethod
    def _filter_low_confidence(item: Dict) -> bool:
        """Filter out low confidence items"""
        confidence = item.get("confidence_score", 0)
        return confidence >= 0.5
        
    @staticmethod
    def _add_timestamp(item: Dict) -> Dict:
        """Add processing timestamp"""
        item["_processed_at"] = datetime.utcnow().isoformat()
        return item
        
    @staticmethod
    def _normalize_agent(item: Dict) -> Dict:
        """Normalize agent data structure"""
        # Ensure required fields
        if "agent_id" not in item and "id" in item:
            item["agent_id"] = item["id"]
            
        if "detected_at" not in item:
            item["detected_at"] = datetime.utcnow().isoformat()
            
        return item
        
    @staticmethod
    def _log_batch(items: List[Dict]):
        """Log batch processing"""
        logger.info(f"📦 Processed batch of {len(items)} items")
