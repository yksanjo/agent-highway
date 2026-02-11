"""
Pytest configuration and fixtures for Agent Highway / OpenClaw test suite.
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import aiohttp
from aiohttp import web

# Add parent directories to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../tools'))

from beacon.beacon_sdk import AgentBeacon, BeaconConfig, EventType, SignalLien
from collectors.openclaw import (
    OpenClawScanner, 
    OpenClawSignature, 
    OpenClawSignatureType,
    DetectionFactor,
    ConfidenceScorer
)
from tools.openclaw_config_validator import OpenClawValidator, ValidationResult


# ============================================================================
# Beacon SDK Fixtures
# ============================================================================

@pytest.fixture
def beacon_config():
    """Default beacon configuration for testing."""
    return BeaconConfig(
        endpoint="https://test-agent-highway.example.com",
        heartbeat_interval=5,
        timeout=2,
        max_retries=2,
        retry_delay=0.1,
        auto_heartbeat=False,
        lane="test"
    )


@pytest.fixture
async def beacon(beacon_config):
    """Create an AgentBeacon instance for testing."""
    beacon = AgentBeacon(
        agent_id="test-agent-001",
        agent_type="test_worker",
        config=beacon_config,
        metadata={"test": True}
    )
    yield beacon
    # Cleanup
    if not beacon._shutdown:
        await beacon.shutdown()


@pytest.fixture
def sample_signal_lien():
    """Create a sample SignalLien for testing."""
    return SignalLien(
        agent_id="test-agent-001",
        agent_type="test_worker",
        timestamp=1704067200000,  # 2024-01-01 00:00:00 UTC
        event_type=EventType.TASK_START,
        sequence=1,
        signature="abc123def456",
        task_id="task-123",
        payload_hash="hash123",
        public_key="pubkey123",
        metadata={"priority": "high"},
        lane="test"
    )


@pytest.fixture
def mock_beacon_server():
    """Mock beacon server responses."""
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status = 201
        mock_response.text = AsyncMock(return_value='{"status": "ok"}')
        mock_post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aexit__ = AsyncMock(return_value=False)
        yield mock_post


# ============================================================================
# OpenClaw Scanner Fixtures
# ============================================================================

@pytest.fixture
async def openclaw_scanner():
    """Create an OpenClawScanner instance for testing."""
    scanner = OpenClawScanner(api_keys={})
    yield scanner


@pytest.fixture
def sample_detection_factors():
    """Sample detection factors for testing confidence scoring."""
    return [
        DetectionFactor(
            factor_type="header_x_clawbot_id",
            weight=0.25,
            detected=True,
            details={"header_value": "clawbot-123"}
        ),
        DetectionFactor(
            factor_type="header_x_gateway_mode",
            weight=0.25,
            detected=True,
            details={"header_value": "cloudflare"}
        ),
        DetectionFactor(
            factor_type="body_health_signature",
            weight=0.30,
            detected=True,
            details={"pattern": r'"status"\s*:\s*"healthy"'}
        )
    ]


@pytest.fixture
def sample_openclaw_signature():
    """Create a sample OpenClawSignature for testing."""
    return OpenClawSignature(
        signature_id="sig1234567890abcd",
        signature_type=OpenClawSignatureType.GATEWAY,
        confidence_score=0.85,
        platform="web",
        detected_at=datetime.utcnow(),
        endpoint="https://test-gateway.example.com",
        version_hint="2.1.0",
        capabilities=["gateway", "subagent", "bridge"],
        metadata={"status_code": 200, "server": "cloudflare"},
        detection_factors=[]
    )


@pytest.fixture
def mock_github_api_response():
    """Mock GitHub API response for repository search."""
    return {
        "items": [
            {
                "id": 12345,
                "name": "openclaw-gateway",
                "full_name": "user/openclaw-gateway",
                "html_url": "https://github.com/user/openclaw-gateway",
                "description": "OpenClaw gateway implementation for AI agents",
                "stargazers_count": 42,
                "language": "TypeScript",
                "topics": ["agent", "gateway", "ai"]
            },
            {
                "id": 12346,
                "name": "my-clawbot",
                "full_name": "user/my-clawbot",
                "html_url": "https://github.com/user/my-clawbot",
                "description": "Custom clawbot implementation",
                "stargazers_count": 10,
                "language": "Python",
                "topics": ["bot", "telegram"]
            }
        ],
        "total_count": 2
    }


@pytest.fixture
def mock_docker_hub_response():
    """Mock Docker Hub API response."""
    return {
        "results": [
            {
                "name": "user/openclaw-gateway",
                "short_description": "OpenClaw gateway container",
                "pull_count": 1500,
                "star_count": 25,
                "is_official": False
            }
        ]
    }


# ============================================================================
# Config Validator Fixtures
# ============================================================================

@pytest.fixture
def valid_openclaw_config():
    """Valid OpenClaw configuration for testing."""
    return {
        "channels": {
            "telegram": {
                "enabled": True,
                "botToken": "${TELEGRAM_BOT_TOKEN}",
                "dmPolicy": "pairing",
                "groupPolicy": "allowlist",
                "streamMode": "full"
            },
            "discord": {
                "enabled": False,
                "token": "${DISCORD_TOKEN}",
                "intents": {
                    "guildMembers": True
                }
            }
        },
        "gateway": {
            "mode": "cloudflare",
            "bind": "0.0.0.0",
            "port": 8787,
            "auth": {
                "mode": "token",
                "token": "${GATEWAY_AUTH_TOKEN}"
            }
        },
        "talk": {
            "apiKey": "${TALK_API_KEY}",
            "model": "claude-3-opus-20240229"
        },
        "agents": {
            "defaults": {
                "maxConcurrent": 5,
                "subagents": {
                    "maxConcurrent": 10
                }
            }
        },
        "messages": {
            "ackReactionScope": "group-mentions"
        },
        "commands": {
            "restart": True
        },
        "meta": {
            "lastTouchedVersion": "2.1.0"
        },
        "plugins": {
            "entries": {
                "telegram": {"enabled": True}
            }
        }
    }


@pytest.fixture
def invalid_openclaw_config():
    """Invalid OpenClaw configuration for testing validation errors."""
    return {
        "channels": {
            "telegram": {
                "enabled": True,
                # Missing botToken
                "dmPolicy": "invalid_policy",
                "streamMode": "invalid_mode"
            }
        },
        "gateway": {
            "mode": "invalid_mode",
            "auth": {
                "mode": "invalid_auth",
                "token": "weak"  # Low entropy token
            }
        },
        "talk": {
            "apiKey": "hardcoded-api-key-123"  # Should be env var
        }
    }


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    def _create_config(config_dict):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_dict, f)
            return Path(f.name)
    return _create_config


@pytest.fixture
def config_validator():
    """Create a ConfigValidator instance."""
    return OpenClawValidator(strict=False)


@pytest.fixture
def strict_config_validator():
    """Create a strict ConfigValidator instance."""
    return OpenClawValidator(strict=True)


# ============================================================================
# Integration Test Fixtures
# ============================================================================

@pytest.fixture
async def mock_highway_api():
    """Create a mock Highway API server for integration tests."""
    async def handle_status(request):
        return web.json_response({
            "online": True,
            "cycle": 100,
            "rotation": 0.5,
            "agents": 5,
            "signals": 25,
            "seats": 8,
            "peers": 0
        })
    
    async def handle_topology(request):
        return web.json_response({
            "agents": [
                {"id": "agent-1", "seat": "seat-1", "capabilities": ["process"]},
                {"id": "agent-2", "seat": "seat-2", "capabilities": ["analyze"]}
            ],
            "vortex": {"rotation": 0.5}
        })
    
    app = web.Application()
    app.router.add_get('/api/v1/status', handle_status)
    app.router.add_get('/api/v1/topology', handle_topology)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8081)
    await site.start()
    
    yield "http://localhost:8081"
    
    await runner.cleanup()


@pytest.fixture
def mock_websocket_server():
    """Mock WebSocket server for testing beacon connections."""
    with patch('aiohttp.ClientSession.ws_connect') as mock_ws:
        mock_ws_conn = AsyncMock()
        mock_ws_conn.send_str = AsyncMock()
        mock_ws_conn.receive = AsyncMock()
        mock_ws_conn.close = AsyncMock()
        mock_ws.return_value = mock_ws_conn
        yield mock_ws


# ============================================================================
# Helper Fixtures
# ============================================================================

@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks after each test."""
    yield
    # Cleanup happens automatically with pytest-mock


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "network: marks tests that require network")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip network tests by default."""
    skip_network = pytest.mark.skip(reason="Network tests disabled")
    skip_slow = pytest.mark.skip(reason="Slow tests disabled")
    
    for item in items:
        if "network" in item.keywords and not config.getoption("--network"):
            item.add_marker(skip_network)
        if "slow" in item.keywords and not config.getoption("--run-slow"):
            item.add_marker(skip_slow)


# Add custom command line options
def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--network",
        action="store_true",
        default=False,
        help="Run network-dependent tests"
    )
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests"
    )
