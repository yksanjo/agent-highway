"""
Decorators for automatic beacon emission.

These decorators allow agents to automatically emit beacons
without manually calling beacon methods.
"""

import functools
import asyncio
from typing import Callable, Optional, Any
import logging

from .beacon_sdk import AgentBeacon, EventType

logger = logging.getLogger(__name__)


def beacon_task(
    task_id_arg: Optional[str] = None,
    beacon_attr: str = "_beacon",
    emit_result: bool = False
):
    """
    Decorator that emits task_start and task_complete beacons around a function.
    
    Args:
        task_id_arg: Name of argument to use as task_id (or None for auto-generated)
        beacon_attr: Name of attribute on self that holds the AgentBeacon
        emit_result: Whether to include return value in task_complete payload
        
    Example:
        >>> class MyAgent:
        ...     def __init__(self):
        ...         self._beacon = AgentBeacon("my-agent", "worker")
        ...     
        ...     @beacon_task(task_id_arg="task_name")
        ...     async def process(self, task_name: str, data: dict):
        ...         # Beacon automatically emitted on entry and exit
        ...         return await self._do_work(data)
    """
    def decorator(func: Callable) -> Callable:
        is_async = asyncio.iscoroutinefunction(func)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get beacon from self argument
            self = args[0] if args else None
            beacon = getattr(self, beacon_attr, None) if self else None
            
            # Get task_id
            if task_id_arg and task_id_arg in kwargs:
                task_id = kwargs[task_id_arg]
            elif task_id_arg and len(args) > 1:
                # Try to get from positional args
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if task_id_arg in params:
                    idx = params.index(task_id_arg)
                    if idx < len(args):
                        task_id = args[idx]
                    else:
                        task_id = f"{func.__name__}-{id(asyncio.current_task())}"
                else:
                    task_id = f"{func.__name__}-{id(asyncio.current_task())}"
            else:
                task_id = f"{func.__name__}-{id(asyncio.current_task())}"
            
            # Emit task_start
            if beacon:
                try:
                    await beacon.task_start(task_id, {"args": str(args[1:]), "kwargs": list(kwargs.keys())})
                except Exception as e:
                    logger.warning(f"Failed to emit task_start beacon: {e}")
            
            try:
                result = await func(*args, **kwargs)
                
                # Emit task_complete (success)
                if beacon:
                    try:
                        payload = {"result": "success"}
                        if emit_result:
                            payload["return_type"] = type(result).__name__
                        await beacon.task_complete(task_id, "success", payload)
                    except Exception as e:
                        logger.warning(f"Failed to emit task_complete beacon: {e}")
                
                return result
                
            except Exception as e:
                # Emit error
                if beacon:
                    try:
                        await beacon.error(e, {"task_id": task_id, "function": func.__name__})
                    except Exception as beacon_e:
                        logger.warning(f"Failed to emit error beacon: {beacon_e}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't easily emit async beacons
            # User should use the sync wrapper or call manually
            logger.warning(f"@beacon_task on sync function {func.__name__} - beacons not emitted")
            return func(*args, **kwargs)
        
        return async_wrapper if is_async else sync_wrapper
    return decorator


def beacon_agent(
    agent_type: str,
    auto_heartbeat: bool = True,
    heartbeat_interval: int = 30
):
    """
    Class decorator that adds beacon capabilities to an agent class.
    
    This decorator:
    1. Initializes a beacon on __init__
    2. Optionally starts heartbeat
    3. Emits death beacon on __del__ or explicit cleanup
    
    Args:
        agent_type: Type of agent for beacon identification
        auto_heartbeat: Whether to start heartbeat automatically
        heartbeat_interval: Seconds between heartbeats
        
    Example:
        >>> @beacon_agent("worker", auto_heartbeat=True)
        ... class MyWorker:
        ...     async def run(self):
        ...         # Beacon is already initialized and heartbeating
        ...         await self.do_work()
    """
    def decorator(cls):
        original_init = cls.__init__
        
        @functools.wraps(original_init)
        def new_init(self, *args, **kwargs):
            # Initialize beacon
            self._beacon = AgentBeacon(
                agent_id=kwargs.pop('agent_id', None),
                agent_type=agent_type,
                config=kwargs.pop('beacon_config', None)
            )
            
            # Call original init
            original_init(self, *args, **kwargs)
            
            # Emit birth and start heartbeat
            asyncio.create_task(self._beacon.birth())
            if auto_heartbeat:
                asyncio.create_task(self._beacon.start_heartbeat(heartbeat_interval))
        
        cls.__init__ = new_init
        
        # Add cleanup method
        async def cleanup(self):
            """Clean up beacon resources."""
            if hasattr(self, '_beacon'):
                await self._beacon.shutdown()
        
        cls.cleanup = cleanup
        
        return cls
    return decorator


def with_beacon(func: Callable) -> Callable:
    """
    Simple decorator that ensures a beacon attribute exists on self.
    
    Creates a default beacon if one doesn't exist.
    """
    is_async = asyncio.iscoroutinefunction(func)
    
    @functools.wraps(func)
    async def async_wrapper(self, *args, **kwargs):
        if not hasattr(self, '_beacon') or self._beacon is None:
            self._beacon = AgentBeacon(
                agent_id=f"{self.__class__.__name__.lower()}-{id(self)}",
                agent_type=self.__class__.__name__
            )
            await self._beacon.birth()
        return await func(self, *args, **kwargs)
    
    @functools.wraps(func)
    def sync_wrapper(self, *args, **kwargs):
        if not hasattr(self, '_beacon') or self._beacon is None:
            # Can't easily do async init in sync context
            logger.warning("Beacon not available in sync context")
        return func(self, *args, **kwargs)
    
    return async_wrapper if is_async else sync_wrapper
