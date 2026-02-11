"""
Beacon SDK Tests

Tests for the Agent Beacon SDK including:
- SignalLien creation and serialization
- EventType enum validation
- AgentBeacon connection and emission
- Heartbeat functionality
- Error handling
"""

import asyncio
import json
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import aiohttp

from beacon.beacon_sdk import (
    AgentBeacon,
    BeaconConfig,
    BeaconError,
    AuthenticationError,
    EventType,
    NetworkError,
    SignalLien
)


# =============================================================================
# SignalLien Tests
# =============================================================================

class TestSignalLien:
    """Tests for SignalLien dataclass."""
    
    def test_signallien_creation(self, sample_signal_lien):
        """Test basic SignalLien creation."""
        assert sample_signal_lien.agent_id == "test-agent-001"
        assert sample_signal_lien.agent_type == "test_worker"
        assert sample_signal_lien.event_type == EventType.TASK_START
        assert sample_signal_lien.sequence == 1
        
    def test_signallien_to_dict(self, sample_signal_lien):
        """Test SignalLien serialization to dictionary."""
        data = sample_signal_lien.to_dict()
        
        assert data["agent_id"] == "test-agent-001"
        assert data["agent_type"] == "test_worker"
        assert data["timestamp"] == 1704067200000
        assert data["event_type"] == EventType.TASK_START
        assert data["sequence"] == 1
        assert data["signature"] == "abc123def456"
        assert data["task_id"] == "task-123"
        assert data["payload_hash"] == "hash123"
        assert data["public_key"] == "pubkey123"
        assert data["metadata"] == {"priority": "high"}
        assert data["lane"] == "test"
        
    def test_signallien_to_dict_removes_none(self):
        """Test that to_dict removes None values."""
        lien = SignalLien(
            agent_id="test",
            agent_type="worker",
            timestamp=1234567890,
            event_type=EventType.HEARTBEAT,
            sequence=1,
            signature="sig123",
            task_id=None,
            parent_agent_id=None,
            metadata=None
        )
        data = lien.to_dict()
        
        assert "task_id" not in data
        assert "parent_agent_id" not in data
        assert "metadata" not in data
        assert "agent_id" in data
        
    def test_signallien_with_all_fields(self):
        """Test SignalLien with all optional fields populated."""
        lien = SignalLien(
            agent_id="agent-1",
            agent_type="orchestrator",
            timestamp=int(time.time() * 1000),
            event_type=EventType.HANDOFF,
            sequence=42,
            signature="sig",
            task_id="task-abc",
            parent_agent_id="parent-1",
            target_agent_id="target-1",
            payload_hash="hash789",
            public_key="pubkey",
            metadata={"context": "migration"},
            lane="a2a"
        )
        
        data = lien.to_dict()
        assert data["parent_agent_id"] == "parent-1"
        assert data["target_agent_id"] == "target-1"
        assert data["lane"] == "a2a"


# =============================================================================
# EventType Tests
# =============================================================================

class TestEventType:
    """Tests for EventType enum."""
    
    def test_event_type_values(self):
        """Test that EventType enum has expected values."""
        assert EventType.BIRTH.value == "birth"
        assert EventType.HEARTBEAT.value == "heartbeat"
        assert EventType.TASK_START.value == "task_start"
        assert EventType.TASK_COMPLETE.value == "task_complete"
        assert EventType.DEATH.value == "death"
        assert EventType.HANDOFF.value == "handoff"
        assert EventType.ERROR.value == "error"
        
    def test_event_type_from_string(self):
        """Test creating EventType from string."""
        assert EventType("birth") == EventType.BIRTH
        assert EventType("heartbeat") == EventType.HEARTBEAT
        assert EventType("task_start") == EventType.TASK_START
        
    def test_event_type_invalid_value(self):
        """Test that invalid EventType raises ValueError."""
        with pytest.raises(ValueError):
            EventType("invalid_event")
            
    def test_event_type_is_string(self):
        """Test that EventType is a string enum."""
        assert isinstance(EventType.BIRTH, str)
        assert EventType.BIRTH == "birth"


# =============================================================================
# BeaconConfig Tests
# =============================================================================

class TestBeaconConfig:
    """Tests for BeaconConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = BeaconConfig()
        
        assert config.endpoint == "https://agent-highway-origin.yksanjo.workers.dev"
        assert config.heartbeat_interval == 30
        assert config.timeout == 5
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.auto_heartbeat is True
        assert config.lane == "default"
        
    def test_custom_config(self):
        """Test custom configuration values."""
        config = BeaconConfig(
            endpoint="https://custom.example.com",
            heartbeat_interval=60,
            timeout=10,
            max_retries=5,
            retry_delay=2.0,
            auto_heartbeat=False,
            lane="custom"
        )
        
        assert config.endpoint == "https://custom.example.com"
        assert config.heartbeat_interval == 60
        assert config.timeout == 10
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
        assert config.auto_heartbeat is False
        assert config.lane == "custom"


# =============================================================================
# AgentBeacon Tests
# =============================================================================

class TestAgentBeacon:
    """Tests for AgentBeacon class."""
    
    @pytest.mark.asyncio
    async def test_beacon_initialization(self, beacon):
        """Test beacon initialization."""
        assert beacon.agent_id == "test-agent-001"
        assert beacon.agent_type == "test_worker"
        assert beacon._sequence == 0
        assert beacon._shutdown is False
        assert beacon.config.lane == "test"
        
    @pytest.mark.asyncio
    async def test_beacon_auto_agent_id(self, beacon_config):
        """Test that beacon generates UUID if no agent_id provided."""
        beacon = AgentBeacon(agent_type="test", config=beacon_config)
        assert beacon.agent_id is not None
        assert len(beacon.agent_id) > 0
        assert beacon.agent_type == "test"
        
    @pytest.mark.asyncio
    async def test_connect_creates_session(self, beacon):
        """Test that connect creates a ClientSession."""
        assert beacon._session is None
        await beacon.connect()
        assert beacon._session is not None
        assert isinstance(beacon._session, aiohttp.ClientSession)
        await beacon.disconnect()
        
    @pytest.mark.asyncio
    async def test_disconnect_closes_session(self, beacon):
        """Test that disconnect closes the session."""
        await beacon.connect()
        assert beacon._session is not None
        await beacon.disconnect()
        assert beacon._session is None
        
    @pytest.mark.asyncio
    async def test_emit_increments_sequence(self, beacon, mock_beacon_server):
        """Test that emit increments sequence number."""
        await beacon.connect()
        
        assert beacon._sequence == 0
        await beacon.emit(EventType.TASK_START)
        assert beacon._sequence == 1
        await beacon.emit(EventType.HEARTBEAT)
        assert beacon._sequence == 2
        
    @pytest.mark.asyncio
    async def test_emit_success(self, beacon, mock_beacon_server):
        """Test successful beacon emission."""
        await beacon.connect()
        result = await beacon.emit(EventType.TASK_START, task_id="task-123")
        
        assert result is True
        mock_beacon_server.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_emit_with_payload(self, beacon, mock_beacon_server):
        """Test emission with payload."""
        await beacon.connect()
        payload = {"status": "running", "progress": 50}
        result = await beacon.emit(EventType.TASK_START, payload=payload, task_id="task-123")
        
        assert result is True
        
    @pytest.mark.asyncio
    async def test_emit_authentication_error(self, beacon):
        """Test handling of authentication error (401)."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status = 401
            mock_response.text = AsyncMock(return_value='Unauthorized')
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aexit__ = AsyncMock(return_value=False)
            
            await beacon.connect()
            result = await beacon.emit(EventType.TASK_START)
            
            assert result is False
            
    @pytest.mark.asyncio
    async def test_emit_server_error(self, beacon):
        """Test handling of server error (500)."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status = 500
            mock_response.text = AsyncMock(return_value='Internal Server Error')
            mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_post.return_value.__aexit__ = AsyncMock(return_value=False)
            
            await beacon.connect()
            result = await beacon.emit(EventType.TASK_START)
            
            # Should retry and eventually fail
            assert result is False
            
    @pytest.mark.asyncio
    async def test_emit_timeout(self, beacon):
        """Test handling of timeout error."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError()
            
            await beacon.connect()
            result = await beacon.emit(EventType.TASK_START)
            
            assert result is False
            
    @pytest.mark.asyncio
    async def test_emit_network_error(self, beacon):
        """Test handling of network error."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = aiohttp.ClientError("Connection refused")
            
            await beacon.connect()
            result = await beacon.emit(EventType.TASK_START)
            
            assert result is False
            
    @pytest.mark.asyncio
    async def test_emit_after_shutdown(self, beacon):
        """Test that emit fails after shutdown."""
        await beacon.connect()
        await beacon.shutdown()
        
        result = await beacon.emit(EventType.TASK_START)
        assert result is False
        
    @pytest.mark.asyncio
    async def test_emit_string_event_type(self, beacon, mock_beacon_server):
        """Test emission with string event type."""
        await beacon.connect()
        result = await beacon.emit("task_start", task_id="task-123")
        
        assert result is True
        
    @pytest.mark.asyncio
    async def test_birth(self, beacon, mock_beacon_server):
        """Test birth event emission."""
        await beacon.connect()
        result = await beacon.birth(metadata={"version": "1.0.0"})
        
        assert result is True
        
    @pytest.mark.asyncio
    async def test_death(self, beacon, mock_beacon_server):
        """Test death event emission."""
        await beacon.connect()
        result = await beacon.death(reason="shutdown", payload={"exit_code": 0})
        
        assert result is True
        
    @pytest.mark.asyncio
    async def test_heartbeat(self, beacon, mock_beacon_server):
        """Test heartbeat event emission."""
        await beacon.connect()
        result = await beacon.heartbeat(metadata={"memory": "50%"})
        
        assert result is True
        
    @pytest.mark.asyncio
    async def test_task_start(self, beacon, mock_beacon_server):
        """Test task_start event emission."""
        await beacon.connect()
        result = await beacon.task_start("task-123", payload={"input": "data"})
        
        assert result is True
        assert "task-123" in beacon._active_tasks
        
    @pytest.mark.asyncio
    async def test_task_complete(self, beacon, mock_beacon_server):
        """Test task_complete event emission."""
        await beacon.connect()
        await beacon.task_start("task-123")
        result = await beacon.task_complete("task-123", result="success", payload={"output": "done"})
        
        assert result is True
        assert "task-123" not in beacon._active_tasks
        
    @pytest.mark.asyncio
    async def test_handoff(self, beacon, mock_beacon_server):
        """Test handoff event emission."""
        await beacon.connect()
        result = await beacon.handoff(
            target_agent_id="agent-002",
            context={"state": "partial"},
            task_id="task-123"
        )
        
        assert result is True
        
    @pytest.mark.asyncio
    async def test_error(self, beacon, mock_beacon_server):
        """Test error event emission."""
        await beacon.connect()
        error = ValueError("Something went wrong")
        result = await beacon.error(error, context={"operation": "process"})
        
        assert result is True
        
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_start_heartbeat(self, beacon, mock_beacon_server):
        """Test starting periodic heartbeat."""
        await beacon.connect()
        await beacon.start_heartbeat(interval=0.1)
        
        assert beacon._heartbeat_task is not None
        assert not beacon._heartbeat_task.done()
        
        # Wait for a couple heartbeats
        await asyncio.sleep(0.25)
        
        await beacon.stop_heartbeat()
        assert beacon._heartbeat_task is None
        
    @pytest.mark.asyncio
    async def test_stop_heartbeat_no_task(self, beacon):
        """Test stopping heartbeat when no task exists."""
        assert beacon._heartbeat_task is None
        await beacon.stop_heartbeat()  # Should not raise
        
    @pytest.mark.asyncio
    async def test_shutdown(self, beacon, mock_beacon_server):
        """Test graceful shutdown."""
        await beacon.connect()
        await beacon.start_heartbeat(interval=0.1)
        
        await beacon.shutdown(reason="test_complete")
        
        assert beacon._shutdown is True
        assert beacon._heartbeat_task is None
        assert beacon._session is None
        
    @pytest.mark.asyncio
    async def test_shutdown_idempotent(self, beacon, mock_beacon_server):
        """Test that shutdown is idempotent."""
        await beacon.connect()
        await beacon.shutdown()
        
        # Second shutdown should not raise
        await beacon.shutdown()
        assert beacon._shutdown is True
        
    @pytest.mark.asyncio
    async def test_context_manager(self, beacon_config, mock_beacon_server):
        """Test async context manager."""
        async with AgentBeacon(
            agent_id="ctx-test",
            agent_type="test",
            config=beacon_config
        ) as beacon:
            assert beacon._session is not None
            assert beacon._shutdown is False
            
        # After exiting context
        assert beacon._shutdown is True
        
    @pytest.mark.asyncio
    async def test_signature_generation(self, beacon, sample_signal_lien):
        """Test signature generation."""
        signature = beacon._generate_signature(sample_signal_lien)
        
        assert signature is not None
        assert len(signature) > 0
        assert isinstance(signature, str)
        
    @pytest.mark.asyncio
    async def test_payload_hashing(self, beacon):
        """Test payload hashing."""
        payload = {"key": "value", "number": 42}
        hash1 = beacon._hash_payload(payload)
        hash2 = beacon._hash_payload(payload)
        
        assert hash1 is not None
        assert len(hash1) == 16  # First 16 chars of SHA256
        assert hash1 == hash2  # Deterministic
        
        # Different payload should give different hash
        different_payload = {"key": "different"}
        hash3 = beacon._hash_payload(different_payload)
        assert hash1 != hash3
        
    @pytest.mark.asyncio
    async def test_payload_hashing_none(self, beacon):
        """Test payload hashing with None."""
        result = beacon._hash_payload(None)
        assert result is None
        
    @pytest.mark.asyncio
    async def test_metadata_merging(self, beacon, mock_beacon_server):
        """Test metadata merging."""
        await beacon.connect()
        
        # Beacon has base metadata {"test": True}
        result = await beacon.emit(
            EventType.TASK_START,
            metadata={"additional": "data"}
        )
        
        assert result is True
        
    @pytest.mark.asyncio
    async def test_retry_with_backoff(self, beacon):
        """Test retry with exponential backoff."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Fail twice, then succeed
            mock_response_fail = MagicMock()
            mock_response_fail.status = 503
            mock_response_fail.text = AsyncMock(return_value='Service Unavailable')
            
            mock_response_success = MagicMock()
            mock_response_success.status = 201
            mock_response_success.text = AsyncMock(return_value='{"status": "ok"}')
            
            mock_post.return_value.__aenter__ = AsyncMock(
                side_effect=[mock_response_fail, mock_response_fail, mock_response_success]
            )
            mock_post.return_value.__aexit__ = AsyncMock(return_value=False)
            
            with patch('asyncio.sleep', new=AsyncMock()) as mock_sleep:
                await beacon.connect()
                result = await beacon.emit(EventType.TASK_START)
                
                assert result is True
                # Should have slept with exponential backoff
                assert mock_sleep.call_count == 2


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""
    
    def test_beacon_error_inheritance(self):
        """Test BeaconError exception inheritance."""
        assert issubclass(AuthenticationError, BeaconError)
        assert issubclass(NetworkError, BeaconError)
        
    def test_beacon_error_can_be_caught(self):
        """Test that BeaconError can catch subclasses."""
        try:
            raise AuthenticationError("Auth failed")
        except BeaconError as e:
            assert "Auth failed" in str(e)
            
        try:
            raise NetworkError("Network failed")
        except BeaconError as e:
            assert "Network failed" in str(e)
