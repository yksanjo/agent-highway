"""
OpenClaw Scanner Tests

Tests for the OpenClaw discovery scanner including:
- Detection pattern matching
- Confidence scoring
- Output formatting (JSON, CSV, table)
- Endpoint probing
"""

import asyncio
import json
import re
from datetime import datetime
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

import pytest
import aiohttp

from collectors.openclaw import (
    OpenClawScanner,
    OpenClawSignature,
    OpenClawSignatureType,
    DetectionFactor,
    ConfidenceScorer,
    PassiveTrafficAnalyzer
)


# =============================================================================
# DetectionFactor Tests
# =============================================================================

class TestDetectionFactor:
    """Tests for DetectionFactor dataclass."""
    
    def test_detection_factor_creation(self):
        """Test DetectionFactor creation."""
        factor = DetectionFactor(
            factor_type="header_x_clawbot_id",
            weight=0.25,
            detected=True,
            details={"value": "test"}
        )
        
        assert factor.factor_type == "header_x_clawbot_id"
        assert factor.weight == 0.25
        assert factor.detected is True
        assert factor.details == {"value": "test"}
        
    def test_detection_factor_defaults(self):
        """Test DetectionFactor default values."""
        factor = DetectionFactor(
            factor_type="test",
            weight=0.5,
            detected=False
        )
        
        assert factor.details == {}


# =============================================================================
# ConfidenceScorer Tests
# =============================================================================

class TestConfidenceScorer:
    """Tests for ConfidenceScorer class."""
    
    @pytest.fixture
    def scorer(self):
        """Create a ConfidenceScorer instance."""
        return ConfidenceScorer()
    
    def test_calculate_confidence_empty_factors(self, scorer):
        """Test confidence calculation with no factors."""
        confidence, reasoning = scorer.calculate_confidence([])
        
        assert confidence == 0.0
        assert reasoning == ["No detection factors"]
        
    def test_calculate_confidence_single_factor(self, scorer):
        """Test confidence with single detected factor."""
        factors = [
            DetectionFactor(
                factor_type="header_x_clawbot_id",
                weight=0.25,
                detected=True,
                details={}
            )
        ]
        
        confidence, reasoning = scorer.calculate_confidence(factors)
        
        assert confidence > 0.0
        assert confidence <= 1.0
        assert len(reasoning) > 0
        
    def test_calculate_confidence_multiple_factors(self, scorer):
        """Test confidence with multiple detected factors."""
        factors = [
            DetectionFactor(
                factor_type="header_x_clawbot_id",
                weight=0.25,
                detected=True,
                details={}
            ),
            DetectionFactor(
                factor_type="header_x_gateway_mode",
                weight=0.25,
                detected=True,
                details={}
            ),
            DetectionFactor(
                factor_type="header_combo",
                weight=0.35,
                detected=True,
                details={}
            )
        ]
        
        confidence, reasoning = scorer.calculate_confidence(factors)
        
        assert confidence > 0.5  # Should be fairly high
        assert confidence <= 1.0
        assert len(reasoning) == 3
        
    def test_calculate_confidence_undetected_factors(self, scorer):
        """Test confidence with undetected factors."""
        factors = [
            DetectionFactor(
                factor_type="header_x_clawbot_id",
                weight=0.25,
                detected=False,
                details={}
            ),
            DetectionFactor(
                factor_type="header_x_gateway_mode",
                weight=0.25,
                detected=False,
                details={}
            )
        ]
        
        confidence, reasoning = scorer.calculate_confidence(factors)
        
        # No factors detected, should be at prior probability level
        assert confidence < 0.1
        
    def test_calculate_confidence_mixed_factors(self, scorer):
        """Test confidence with mixed detected/undetected factors."""
        factors = [
            DetectionFactor(
                factor_type="header_x_clawbot_id",
                weight=0.25,
                detected=True,
                details={}
            ),
            DetectionFactor(
                factor_type="header_x_gateway_mode",
                weight=0.25,
                detected=False,
                details={}
            )
        ]
        
        confidence, reasoning = scorer.calculate_confidence(factors)
        
        assert 0.0 < confidence < 1.0
        
    def test_calculate_confidence_false_positive_penalty(self, scorer):
        """Test false positive penalty application."""
        factors = [
            DetectionFactor(
                factor_type="body_pattern",
                weight=0.20,
                detected=True,
                details={"content": "wordpress default page"}
            )
        ]
        
        confidence, reasoning = scorer.calculate_confidence(factors)
        
        # Should have FP penalty applied
        assert "FP penalty applied" in reasoning
        
    def test_get_confidence_level_critical(self, scorer):
        """Test confidence level classification - CRITICAL."""
        assert scorer.get_confidence_level(0.95) == "CRITICAL"
        assert scorer.get_confidence_level(0.90) == "CRITICAL"
        
    def test_get_confidence_level_high(self, scorer):
        """Test confidence level classification - HIGH."""
        assert scorer.get_confidence_level(0.89) == "HIGH"
        assert scorer.get_confidence_level(0.70) == "HIGH"
        
    def test_get_confidence_level_medium(self, scorer):
        """Test confidence level classification - MEDIUM."""
        assert scorer.get_confidence_level(0.69) == "MEDIUM"
        assert scorer.get_confidence_level(0.50) == "MEDIUM"
        
    def test_get_confidence_level_low(self, scorer):
        """Test confidence level classification - LOW."""
        assert scorer.get_confidence_level(0.49) == "LOW"
        assert scorer.get_confidence_level(0.30) == "LOW"
        
    def test_get_confidence_level_minimal(self, scorer):
        """Test confidence level classification - MINIMAL."""
        assert scorer.get_confidence_level(0.29) == "MINIMAL"
        assert scorer.get_confidence_level(0.0) == "MINIMAL"


# =============================================================================
# OpenClawSignature Tests
# =============================================================================

class TestOpenClawSignature:
    """Tests for OpenClawSignature dataclass."""
    
    def test_signature_creation(self, sample_openclaw_signature):
        """Test signature creation."""
        sig = sample_openclaw_signature
        
        assert sig.signature_id == "sig1234567890abcd"
        assert sig.signature_type == OpenClawSignatureType.GATEWAY
        assert sig.confidence_score == 0.85
        assert sig.platform == "web"
        assert sig.endpoint == "https://test-gateway.example.com"
        
    def test_signature_to_dict(self, sample_openclaw_signature):
        """Test signature serialization to dict."""
        data = sample_openclaw_signature.to_dict()
        
        assert data["signature_id"] == "sig1234567890abcd"
        assert data["signature_type"] == "gateway"
        assert data["confidence_score"] == 0.85
        assert "detected_at" in data
        assert isinstance(data["detected_at"], str)
        
    def test_signature_to_dict_with_factors(self):
        """Test serialization with detection factors."""
        sig = OpenClawSignature(
            signature_id="test",
            signature_type=OpenClawSignatureType.BOT,
            confidence_score=0.75,
            platform="telegram",
            detected_at=datetime.utcnow(),
            endpoint="https://t.me/testbot",
            version_hint="1.0",
            capabilities=["bot", "webhook"],
            metadata={},
            detection_factors=[
                DetectionFactor(
                    factor_type="telegram_pattern",
                    weight=0.5,
                    detected=True,
                    details={"pattern": "@testbot"}
                )
            ]
        )
        
        data = sig.to_dict()
        assert len(data["detection_factors"]) == 1
        assert data["detection_factors"][0]["factor_type"] == "telegram_pattern"
        
    def test_signature_from_dict(self):
        """Test signature deserialization from dict."""
        data = {
            "signature_id": "test123",
            "signature_type": "gateway",
            "confidence_score": 0.8,
            "platform": "web",
            "detected_at": "2024-01-01T00:00:00",
            "endpoint": "https://example.com",
            "version_hint": "2.0",
            "capabilities": ["gateway"],
            "metadata": {"key": "value"},
            "detection_factors": [
                {
                    "factor_type": "header",
                    "weight": 0.5,
                    "detected": True,
                    "details": {}
                }
            ]
        }
        
        sig = OpenClawSignature.from_dict(data)
        
        assert sig.signature_id == "test123"
        assert sig.signature_type == OpenClawSignatureType.GATEWAY
        assert sig.confidence_score == 0.8
        assert isinstance(sig.detected_at, datetime)
        assert len(sig.detection_factors) == 1


# =============================================================================
# OpenClawSignatureType Tests
# =============================================================================

class TestOpenClawSignatureType:
    """Tests for OpenClawSignatureType enum."""
    
    def test_signature_type_values(self):
        """Test signature type enum values."""
        assert OpenClawSignatureType.GATEWAY.value == "gateway"
        assert OpenClawSignatureType.BOT.value == "bot"
        assert OpenClawSignatureType.WEBHOOK.value == "webhook"
        assert OpenClawSignatureType.BRIDGE.value == "bridge"
        assert OpenClawSignatureType.EXTENSION.value == "extension"
        assert OpenClawSignatureType.DNS.value == "dns"
        assert OpenClawSignatureType.CONTAINER.value == "container"
        
    def test_signature_type_from_string(self):
        """Test creating signature type from string."""
        assert OpenClawSignatureType("gateway") == OpenClawSignatureType.GATEWAY
        assert OpenClawSignatureType("bot") == OpenClawSignatureType.BOT


# =============================================================================
# OpenClawScanner Tests
# =============================================================================

class TestOpenClawScanner:
    """Tests for OpenClawScanner class."""
    
    @pytest.fixture
    async def scanner(self):
        """Create scanner with mocked session."""
        scanner = OpenClawScanner(api_keys={})
        yield scanner
        if scanner.session:
            await scanner.session.close()
    
    @pytest.mark.asyncio
    async def test_scanner_initialization(self, scanner):
        """Test scanner initialization."""
        assert scanner.discovered == []
        assert scanner.session is None
        assert scanner.scorer is not None
        assert scanner.api_keys == {}
        
    @pytest.mark.asyncio
    async def test_scanner_context_manager(self):
        """Test async context manager."""
        async with OpenClawScanner(api_keys={"shodan": "test_key"}) as scanner:
            assert scanner.session is not None
            assert isinstance(scanner.session, aiohttp.ClientSession)
            
    @pytest.mark.asyncio
    async def test_scanner_analyze_repo_for_openclaw(self, scanner):
        """Test repository analysis for OpenClaw indicators."""
        repo = {
            "name": "openclaw-gateway",
            "description": "OpenClaw gateway for AI agents",
            "topics": ["agent", "gateway"],
            "stargazers_count": 50,
            "language": "TypeScript"
        }
        
        factors, confidence = scanner._analyze_repo_for_openclaw(repo)
        
        assert len(factors) == 3
        assert confidence > 0.5
        assert any(f.factor_type == "github_repo" for f in factors)
        
    @pytest.mark.asyncio
    async def test_scanner_analyze_repo_no_indicators(self, scanner):
        """Test repository analysis with no OpenClaw indicators."""
        repo = {
            "name": "random-project",
            "description": "A random project",
            "topics": ["utility"],
            "stargazers_count": 5,
            "language": "Python"
        }
        
        factors, confidence = scanner._analyze_repo_for_openclaw(repo)
        
        assert confidence < 0.5
        
    @pytest.mark.asyncio
    async def test_scanner_is_openclaw_txt_record(self, scanner):
        """Test TXT record OpenClaw detection."""
        assert scanner._is_openclaw_txt_record("openclaw-config=somevalue") is True
        assert scanner._is_openclaw_txt_record("clawbot-id=12345") is True
        assert scanner._is_openclaw_txt_record("gateway-mode=cloudflare") is True
        assert scanner._is_openclaw_txt_record("_openclaw.example.com") is True
        assert scanner._is_openclaw_txt_record("regular-txt-record") is False
        
    @pytest.mark.asyncio
    async def test_probe_endpoint_success(self, scanner):
        """Test endpoint probing with OpenClaw indicators."""
        # Mock the session and response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {
            "x-clawbot-id": "clawbot-123",
            "x-gateway-mode": "cloudflare",
            "x-openclaw-version": "2.1.0"
        }
        mock_response.text = AsyncMock(return_value='{"status": "healthy", "gateway": "up"}')
        
        scanner.session = MagicMock()
        scanner.session.get = MagicMock()
        scanner.session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        scanner.session.get.return_value.__aexit__ = AsyncMock(return_value=False)
        
        result = await scanner.probe_endpoint("https://test.example.com/health")
        
        assert result is not None
        assert result.signature_type == OpenClawSignatureType.GATEWAY
        assert result.confidence_score > 0.5
        assert result.version_hint == "2.1.0"
        
    @pytest.mark.asyncio
    async def test_probe_endpoint_no_indicators(self, scanner):
        """Test endpoint probing with no OpenClaw indicators."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"server": "nginx"}
        mock_response.text = AsyncMock(return_value='<html>Regular page</html>')
        
        scanner.session = MagicMock()
        scanner.session.get = MagicMock()
        scanner.session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        scanner.session.get.return_value.__aexit__ = AsyncMock(return_value=False)
        
        result = await scanner.probe_endpoint("https://test.example.com")
        
        assert result is None
        
    @pytest.mark.asyncio
    async def test_probe_endpoint_error(self, scanner):
        """Test endpoint probing with error."""
        scanner.session = MagicMock()
        scanner.session.get = MagicMock()
        scanner.session.get.return_value.__aenter__ = AsyncMock(
            side_effect=aiohttp.ClientError("Connection refused")
        )
        scanner.session.get.return_value.__aexit__ = AsyncMock(return_value=False)
        
        result = await scanner.probe_endpoint("https://test.example.com")
        
        assert result is None
        
    @pytest.mark.asyncio
    async def test_scan_github_repos(self, scanner, mock_github_api_response):
        """Test GitHub repository scanning."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_github_api_response)
        
        scanner.session = MagicMock()
        scanner.session.get = MagicMock()
        scanner.session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        scanner.session.get.return_value.__aexit__ = AsyncMock(return_value=False)
        
        await scanner._scan_github_repos()
        
        # Should have found at least one signature
        assert len(scanner.discovered) >= 1
        
    @pytest.mark.asyncio
    async def test_scan_github_repos_rate_limit(self, scanner):
        """Test GitHub scanning with rate limit error."""
        mock_response = MagicMock()
        mock_response.status = 403
        mock_response.text = AsyncMock(return_value='API rate limit exceeded')
        
        scanner.session = MagicMock()
        scanner.session.get = MagicMock()
        scanner.session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        scanner.session.get.return_value.__aexit__ = AsyncMock(return_value=False)
        
        # Should handle gracefully
        await scanner._scan_github_repos()
        
    @pytest.mark.asyncio
    async def test_scan_docker_hub(self, scanner, mock_docker_hub_response):
        """Test Docker Hub scanning."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_docker_hub_response)
        
        scanner.session = MagicMock()
        scanner.session.get = MagicMock()
        scanner.session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        scanner.session.get.return_value.__aexit__ = AsyncMock(return_value=False)
        
        await scanner._scan_docker_hub()
        
        assert len(scanner.discovered) >= 1
        
    @pytest.mark.asyncio
    async def test_scan_docker_hub_error(self, scanner):
        """Test Docker Hub scanning with error."""
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value='Internal Server Error')
        
        scanner.session = MagicMock()
        scanner.session.get = MagicMock()
        scanner.session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        scanner.session.get.return_value.__aexit__ = AsyncMock(return_value=False)
        
        # Should handle gracefully
        await scanner._scan_docker_hub()


# =============================================================================
# PassiveTrafficAnalyzer Tests
# =============================================================================

class TestPassiveTrafficAnalyzer:
    """Tests for PassiveTrafficAnalyzer class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create a PassiveTrafficAnalyzer instance."""
        return PassiveTrafficAnalyzer()
    
    def test_analyze_packet_with_openclaw(self, analyzer):
        """Test packet analysis with OpenClaw indicators."""
        packet_data = b'{"gateway_mode": true, "subagent": {"id": "123"}}'
        
        result = analyzer.analyze_packet(packet_data)
        
        assert result is not None
        assert result["is_openclaw"] is True
        assert result["confidence"] > 0.0
        assert "gateway_communication" in result["indicators"]
        
    def test_analyze_packet_without_openclaw(self, analyzer):
        """Test packet analysis without OpenClaw indicators."""
        packet_data = b'{"status": "ok", "data": "regular response"}'
        
        result = analyzer.analyze_packet(packet_data)
        
        assert result is None
        
    def test_analyze_websocket_frame_with_openclaw(self, analyzer):
        """Test WebSocket frame analysis with OpenClaw."""
        frame_data = b'{"type":"openclaw.event", "gateway":"main"}'
        
        result = analyzer.analyze_websocket_frame(frame_data)
        
        assert result is not None
        assert result["is_openclaw_ws"] is True
        
    def test_analyze_websocket_frame_without_openclaw(self, analyzer):
        """Test WebSocket frame analysis without OpenClaw."""
        frame_data = b'{"type":"chat", "message":"hello"}'
        
        result = analyzer.analyze_websocket_frame(frame_data)
        
        assert result is None


# =============================================================================
# Signature Pattern Tests
# =============================================================================

class TestSignaturePatterns:
    """Tests for signature pattern matching."""
    
    @pytest.fixture
    def scanner(self):
        return OpenClawScanner(api_keys={})
    
    def test_header_patterns(self, scanner):
        """Test header signature patterns."""
        headers = scanner.SIGNATURE_PATTERNS["response_headers"]
        
        assert "x-openclaw-version" in headers
        assert "x-clawbot-id" in headers
        assert "x-gateway-mode" in headers
        assert "x-subagent-count" in headers
        
    def test_body_patterns(self, scanner):
        """Test body signature patterns."""
        patterns = scanner.SIGNATURE_PATTERNS["response_body"]
        
        # Test that patterns compile
        for pattern in patterns:
            compiled = re.compile(pattern, re.IGNORECASE)
            assert compiled is not None
            
    def test_body_pattern_matches(self, scanner):
        """Test that body patterns match expected content."""
        patterns = scanner.SIGNATURE_PATTERNS["response_body"]
        
        test_content = '{"openclaw": {"version": "2.0"}}'
        assert re.search(patterns[0], test_content, re.IGNORECASE)
        
        test_content = '{"gateway_mode": true}'
        assert re.search(patterns[2], test_content, re.IGNORECASE)
        
    def test_health_endpoint_patterns(self, scanner):
        """Test health endpoint patterns."""
        patterns = scanner.SIGNATURE_PATTERNS["health_signatures"]
        
        test_content = '{"status": "healthy", "gateway": "up", "uptime": 3600}'
        for pattern in patterns[:4]:
            assert re.search(pattern, test_content, re.IGNORECASE)
            
    def test_status_endpoint_patterns(self, scanner):
        """Test status endpoint patterns."""
        patterns = scanner.SIGNATURE_PATTERNS["status_signatures"]
        
        test_content = '{"openclaw_status": {"active_subagents": [], "metrics": {}}}'
        for pattern in patterns[:3]:
            assert re.search(pattern, test_content, re.IGNORECASE)
            
    def test_endpoint_patterns(self, scanner):
        """Test endpoint URL patterns."""
        patterns = scanner.SIGNATURE_PATTERNS["endpoint_patterns"]
        
        test_urls = [
            "/openclaw/health",
            "/clawbot/api",
            "/gateway/v1/status",
            "/api/v1/openclaw"
        ]
        
        for url in test_urls:
            assert any(re.search(p, url) for p in patterns), f"No pattern matched {url}"
            
    def test_user_agent_patterns(self, scanner):
        """Test User-Agent patterns."""
        patterns = scanner.SIGNATURE_PATTERNS["user_agents"]
        
        test_agents = [
            "OpenClaw/2.1.0",
            "ClawBot/1.5.0",
            "OpenClaw-Agent/2.0"
        ]
        
        for agent in test_agents:
            assert any(re.search(p, agent) for p in patterns), f"No pattern matched {agent}"


# =============================================================================
# API Integration Tests
# =============================================================================

class TestAPIIntegrations:
    """Tests for external API integrations."""
    
    @pytest.mark.asyncio
    async def test_scan_shodan_no_api_key(self):
        """Test Shodan scanning without API key."""
        scanner = OpenClawScanner(api_keys={})
        scanner.session = MagicMock()
        
        # Should return early without API key
        await scanner._scan_shodan()
        scanner.session.get.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_scan_shodan_with_api_key(self):
        """Test Shodan scanning with API key."""
        scanner = OpenClawScanner(api_keys={"shodan": "test_key"})
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "matches": [
                {
                    "ip_str": "1.2.3.4",
                    "port": 8080,
                    "org": "Test Org",
                    "location": {"country_code": "US"},
                    "http": {"headers": {"X-Clawbot-Id": "test"}}
                }
            ]
        })
        
        scanner.session = MagicMock()
        scanner.session.get = MagicMock()
        scanner.session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        scanner.session.get.return_value.__aexit__ = AsyncMock(return_value=False)
        
        await scanner._scan_shodan()
        
        scanner.session.get.assert_called()
        
    @pytest.mark.asyncio
    async def test_scan_censys_no_credentials(self):
        """Test Censys scanning without credentials."""
        scanner = OpenClawScanner(api_keys={})
        scanner.session = MagicMock()
        
        await scanner._scan_censys()
        scanner.session.get.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_scan_censys_with_credentials(self):
        """Test Censys scanning with credentials."""
        scanner = OpenClawScanner(api_keys={
            "censys_id": "test_id",
            "censys_secret": "test_secret"
        })
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "result": {
                "hits": [
                    {"ip": "1.2.3.4", "services": [{"port": 8080}]}
                ]
            }
        })
        
        scanner.session = MagicMock()
        scanner.session.get = MagicMock()
        scanner.session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        scanner.session.get.return_value.__aexit__ = AsyncMock(return_value=False)
        
        await scanner._scan_censys()
        
        scanner.session.get.assert_called()
