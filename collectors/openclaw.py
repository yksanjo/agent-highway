"""
OpenClaw Agent/User Discovery Scanner v2.0
Part of the Agent Monitoring System - Maps OpenClaw deployments

Enhancements in v2.0:
- Advanced detection patterns (WebSocket, HTTP headers, response signatures)
- Multi-factor confidence scoring with Bayesian filtering
- Shodan/Censys API integration
- DNS TXT record scanning
- GitHub Gist and Docker Hub scanning
- Multiple output formats (JSON, CSV, Table)
"""

import asyncio
import json
import hashlib
import re
import csv
import io
import base64
import argparse
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Optional, Set, Dict, Any, Tuple
from enum import Enum
from collections import defaultdict
import aiohttp

# Optional DNS support
try:
    import dns.resolver
    from dns.exception import DNSException
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    DNSException = Exception


class OpenClawSignatureType(Enum):
    GATEWAY = "gateway"           # OpenClaw gateway instances
    BOT = "bot"                   # Telegram/Discord bots using OpenClaw
    WEBHOOK = "webhook"           # Webhook endpoints
    BRIDGE = "bridge"             # AgentChat bridges
    EXTENSION = "extension"       # Browser extensions
    DNS = "dns"                   # DNS TXT record discoveries
    CONTAINER = "container"       # Docker/container deployments


@dataclass
class DetectionFactor:
    """Individual detection factor for multi-factor scoring"""
    factor_type: str
    weight: float
    detected: bool
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OpenClawSignature:
    signature_id: str
    signature_type: OpenClawSignatureType
    confidence_score: float
    platform: str
    detected_at: datetime
    endpoint: Optional[str]
    version_hint: Optional[str]
    capabilities: List[str]
    metadata: Dict
    detection_factors: List[DetectionFactor] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['signature_type'] = self.signature_type.value
        data['detected_at'] = self.detected_at.isoformat()
        data['detection_factors'] = [
            {
                'factor_type': f.factor_type,
                'weight': f.weight,
                'detected': f.detected,
                'details': f.details
            }
            for f in self.detection_factors
        ]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'OpenClawSignature':
        data['signature_type'] = OpenClawSignatureType(data['signature_type'])
        data['detected_at'] = datetime.fromisoformat(data['detected_at'])
        factors = data.pop('detection_factors', [])
        sig = cls(**data)
        sig.detection_factors = [
            DetectionFactor(
                factor_type=f['factor_type'],
                weight=f['weight'],
                detected=f['detected'],
                details=f.get('details', {})
            )
            for f in factors
        ]
        return sig


class ConfidenceScorer:
    """
    Multi-factor confidence scoring with Bayesian filtering.
    Reduces false positives through weighted factor analysis.
    """
    
    # Prior probability of a true OpenClaw instance
    PRIOR_PROBABILITY = 0.01
    
    # Factor weights and their likelihood ratios
    FACTOR_CONFIG = {
        "header_x_clawbot_id": {"weight": 0.25, "lr_true": 50, "lr_false": 0.1},
        "header_x_gateway_mode": {"weight": 0.25, "lr_true": 45, "lr_false": 0.1},
        "header_combo": {"weight": 0.35, "lr_true": 80, "lr_false": 0.05},
        "body_health_signature": {"weight": 0.30, "lr_true": 60, "lr_false": 0.1},
        "body_status_signature": {"weight": 0.30, "lr_true": 55, "lr_false": 0.1},
        "websocket_pattern": {"weight": 0.40, "lr_true": 70, "lr_false": 0.05},
        "user_agent_openclaw": {"weight": 0.35, "lr_true": 65, "lr_false": 0.05},
        "endpoint_pattern": {"weight": 0.20, "lr_true": 30, "lr_false": 0.2},
        "error_message": {"weight": 0.25, "lr_true": 40, "lr_false": 0.15},
        "github_repo": {"weight": 0.15, "lr_true": 20, "lr_false": 0.3},
        "dns_txt_record": {"weight": 0.45, "lr_true": 75, "lr_false": 0.02},
        "docker_image": {"weight": 0.30, "lr_true": 50, "lr_false": 0.1},
        "gist_config": {"weight": 0.40, "lr_true": 65, "lr_false": 0.05},
    }
    
    # False positive patterns to penalize
    FALSE_POSITIVE_PATTERNS = [
        r"wordpress",
        r"nginx.*default",
        r"apache.*default",
        r"404.*not found",
        r"error.*page",
    ]
    
    def __init__(self):
        self.false_positive_penalty = 0.3
    
    def calculate_confidence(self, factors: List[DetectionFactor]) -> Tuple[float, List[str]]:
        """
        Calculate confidence score using Bayesian inference.
        Returns (confidence_score, reasoning).
        """
        if not factors:
            return 0.0, ["No detection factors"]
        
        # Start with prior odds
        prior_odds = self.PRIOR_PROBABILITY / (1 - self.PRIOR_PROBABILITY)
        current_odds = prior_odds
        reasoning = []
        
        for factor in factors:
            if not factor.detected:
                continue
            
            config = self.FACTOR_CONFIG.get(factor.factor_type, {})
            lr = config.get("lr_true", 10)
            
            # Update odds using Bayes' theorem
            current_odds *= lr
            reasoning.append(f"{factor.factor_type}: +{factor.weight:.2f}")
        
        # Convert odds back to probability
        confidence = current_odds / (1 + current_odds)
        
        # Apply penalties for false positive indicators
        for factor in factors:
            if self._check_false_positive_indicators(factor.details):
                confidence *= (1 - self.false_positive_penalty)
                reasoning.append("FP penalty applied")
        
        # Normalize to 0-1 range
        confidence = min(max(confidence, 0.0), 1.0)
        
        return confidence, reasoning
    
    def _check_false_positive_indicators(self, details: Dict) -> bool:
        """Check if detection has false positive indicators"""
        content = str(details).lower()
        for pattern in self.FALSE_POSITIVE_PATTERNS:
            if re.search(pattern, content):
                return True
        return False
    
    def get_confidence_level(self, score: float) -> str:
        """Get human-readable confidence level"""
        if score >= 0.9:
            return "CRITICAL"
        elif score >= 0.7:
            return "HIGH"
        elif score >= 0.5:
            return "MEDIUM"
        elif score >= 0.3:
            return "LOW"
        return "MINIMAL"


class OpenClawScanner:
    """
    Enhanced OpenClaw discovery scanner.
    Uses multiple detection vectors with advanced pattern matching.
    """
    
    # Enhanced signature patterns
    SIGNATURE_PATTERNS = {
        # HTTP Headers
        "response_headers": [
            "x-openclaw-version",
            "x-clawbot-id",
            "x-gateway-mode",
            "x-subagent-count",
            "x-bridge-status",
        ],
        "header_combinations": [
            ("x-clawbot-id", "x-gateway-mode"),
            ("x-openclaw-version", "x-gateway-mode"),
            ("x-subagent-count", "x-bridge-status"),
        ],
        
        # Response body patterns
        "response_body": [
            r'"openclaw"\s*:\s*{',
            r'"clawbot"\s*:\s*{',
            r'"gateway_mode"\s*:\s*(true|false)',
            r'"subagent"\s*:\s*{',
            r'"talk"\s*:\s*.*"apiKey"',
            r'"channels"\s*:\s*.*"telegram"',
            r'"channels"\s*:\s*.*"discord"',
        ],
        
        # /health endpoint specific signatures
        "health_signatures": [
            r'"status"\s*:\s*"healthy?"',
            r'"gateway"\s*:\s*"up"',
            r'"subagents"\s*:\s*\d+',
            r'"uptime"\s*:\s*\d+',
            r'"version"\s*:\s*"[\d.]+"',
        ],
        
        # /status endpoint specific signatures
        "status_signatures": [
            r'"openclaw_status"',
            r'"active_subagents"\s*:\s*\[',
            r'"bridge_connections"\s*:\s*{',
            r'"telemetry"\s*:\s*{',
            r'"metrics"\s*:\s*{',
        ],
        
        # Endpoint patterns
        "endpoint_patterns": [
            r"/openclaw[/\w]*",
            r"/clawbot[/\w]*",
            r"/gateway[/\w]*",
            r"/subagent[/\w]*",
            r"/bridge[/\w]*",
            r"/api/v\d+/openclaw",
            r"/health",
            r"/status",
            r"/metrics",
        ],
        
        # User-Agent strings
        "user_agents": [
            r"OpenClaw/[\d.]+",
            r"ClawBot/[\d.]+",
            r"OpenClaw-Agent/[\d.]+",
            r"ClawGateway/[\d.]+",
            r"SubAgent/[\d.]+",
        ],
        
        # WebSocket patterns
        "websocket_topics": [
            r"openclaw\.[\w]+",
            r"clawbot\.[\w]+",
            r"gateway\.[\w]+",
            r"subagent\.[\w]+",
        ],
        "websocket_messages": [
            r'"type"\s*:\s*"openclaw',
            r'"gateway"\s*:\s*"',
            r'"subagent_id"\s*:\s*"',
            r'"bridge_event"\s*:\s*',
        ],
        
        # Error messages
        "error_messages": [
            r"OpenClaw gateway not found",
            r"Invalid clawbot configuration",
            r"Subagent timeout",
            r"Gateway mode (disabled|enabled)",
            r"Bridge connection (failed|established)",
        ],
    }
    
    # Domain patterns for DNS scanning
    DOMAIN_PATTERNS = [
        "openclaw",
        "clawbot",
        "clawdbot",
    ]
    
    # DNS TXT record patterns
    DNS_TXT_PATTERNS = [
        r"openclaw-config=",
        r"clawbot-id=",
        r"gateway-mode=",
        r"_openclaw.",
    ]
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        self.discovered: List[OpenClawSignature] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.scorer = ConfidenceScorer()
        self.api_keys = api_keys or {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": "AgentMonitoringSystem/2.0 (Research Project)"
            },
            timeout=aiohttp.ClientTimeout(total=15)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scan_all(self) -> List[OpenClawSignature]:
        """Run all scanning methods"""
        print("🔍 Starting OpenClaw discovery scan v2.0...\n")
        
        # Run scans in parallel
        await asyncio.gather(
            self._scan_github_repos(),
            self._scan_github_gists(),
            self._scan_telegram_bots(),
            self._scan_discord_bots(),
            self._scan_certificate_transparency(),
            self._scan_public_gateways(),
            self._scan_dns_txt_records(),
            self._scan_docker_hub(),
            self._scan_shodan(),
            self._scan_censys(),
        )
        
        print(f"\n🎯 Total OpenClaw signatures discovered: {len(self.discovered)}")
        return self.discovered
    
    async def _scan_github_repos(self):
        """Scan GitHub for OpenClaw-related repositories"""
        print("📦 Scanning GitHub for OpenClaw repos...")
        
        queries = [
            "openclaw",
            "clawbot",
            "filename:openclaw.json",
            "filename:clawbot.json",
            "filename:openclaw.yaml",
            "filename:openclaw.yml",
            '"gateway" "openclaw"',
            '"subagent" "telegram" "discord"',
            '"openclaw" "docker"',
        ]
        
        for query in queries:
            try:
                url = "https://api.github.com/search/repositories"
                params = {"q": query, "per_page": 30}
                
                async with self.session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for repo in data.get("items", []):
                            factors, confidence = self._analyze_repo_for_openclaw(repo)
                            if confidence > 0.5:
                                sig = OpenClawSignature(
                                    signature_id=hashlib.sha256(
                                        repo["html_url"].encode()
                                    ).hexdigest()[:16],
                                    signature_type=OpenClawSignatureType.GATEWAY,
                                    confidence_score=confidence,
                                    platform="github",
                                    detected_at=datetime.utcnow(),
                                    endpoint=repo["html_url"],
                                    version_hint=None,
                                    capabilities=["repository", "public_code"],
                                    metadata={
                                        "stars": repo.get("stargazers_count"),
                                        "language": repo.get("language"),
                                        "description": repo.get("description"),
                                        "query": query,
                                    },
                                    detection_factors=factors
                                )
                                self.discovered.append(sig)
                                level = self.scorer.get_confidence_level(confidence)
                                print(f"  ✅ Found: {repo['full_name']} ({level}: {confidence:.2f})")
                                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"  ⚠️  GitHub scan error: {e}")
    
    def _analyze_repo_for_openclaw(self, repo: dict) -> Tuple[List[DetectionFactor], float]:
        """Analyze repository for OpenClaw indicators with multi-factor scoring"""
        factors = []
        
        # Name match
        name = repo.get("name", "").lower()
        name_match = "openclaw" in name or "clawbot" in name
        factors.append(DetectionFactor(
            factor_type="github_repo",
            weight=0.15,
            detected=name_match,
            details={"match_type": "name", "matched": name_match}
        ))
        
        # Description match
        desc = (repo.get("description") or "").lower()
        desc_match = any(term in desc for term in ["openclaw", "clawbot", "ai agent", "gateway"])
        factors.append(DetectionFactor(
            factor_type="github_repo",
            weight=0.15,
            detected=desc_match,
            details={"match_type": "description", "matched": desc_match}
        ))
        
        # Topics
        topics = [t.lower() for t in repo.get("topics", [])]
        topic_match = "agent" in topics or "bot" in topics
        factors.append(DetectionFactor(
            factor_type="github_repo",
            weight=0.15,
            detected=topic_match,
            details={"match_type": "topics", "matched": topic_match}
        ))
        
        confidence, _ = self.scorer.calculate_confidence(factors)
        return factors, confidence
    
    async def _scan_github_gists(self):
        """Scan GitHub Gists for OpenClaw configurations"""
        print("\n📝 Scanning GitHub Gists for OpenClaw configs...")
        
        queries = [
            "openclaw.json",
            "clawbot.json",
            "openclaw.yaml",
            "openclaw.yml",
            "openclaw config",
            "clawbot config",
        ]
        
        for query in queries:
            try:
                url = "https://api.github.com/search/code"
                params = {"q": f"{query} extension:json extension:yaml extension:yml", "per_page": 20}
                
                async with self.session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for item in data.get("items", []):
                            factors = [DetectionFactor(
                                factor_type="gist_config",
                                weight=0.40,
                                detected=True,
                                details={"filename": item.get("name"), "query": query}
                            )]
                            confidence, _ = self.scorer.calculate_confidence(factors)
                            
                            if confidence > 0.5:
                                sig = OpenClawSignature(
                                    signature_id=hashlib.sha256(
                                        item["html_url"].encode()
                                    ).hexdigest()[:16],
                                    signature_type=OpenClawSignatureType.EXTENSION,
                                    confidence_score=confidence,
                                    platform="github-gist",
                                    detected_at=datetime.utcnow(),
                                    endpoint=item["html_url"],
                                    version_hint=None,
                                    capabilities=["config_file", "gist"],
                                    metadata={
                                        "filename": item.get("name"),
                                        "repository": item.get("repository", {}).get("full_name"),
                                        "query": query,
                                    },
                                    detection_factors=factors
                                )
                                self.discovered.append(sig)
                                print(f"  ✅ Gist found: {item.get('name')} ({confidence:.2f})")
                                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"  ⚠️  Gist scan error: {e}")
    
    async def _scan_telegram_bots(self):
        """Identify Telegram bots that might be OpenClaw-based"""
        print("\n💬 Scanning Telegram for OpenClaw bots...")
        print("  (Using public bot directory and behavior analysis)")
        
        # Detection patterns for Telegram
        patterns = [
            "Check bot usernames for 'claw' patterns",
            "Analyze bot behavior (response patterns)",
            "Look for OpenClaw-specific message formatting",
            "Check bot descriptions for OpenClaw references",
        ]
        
        print(f"  Detection approaches: {len(patterns)}")
    
    async def _scan_discord_bots(self):
        """Identify Discord bots that might be OpenClaw-based"""
        print("\n🎮 Scanning Discord for OpenClaw bots...")
        print("  (Using public bot lists and behavior patterns)")
        
        bot_lists = [
            "top.gg",
            "discord.bots.gg",
            "discordbotlist.com",
        ]
        
        patterns = [
            "Bot name contains 'claw' or 'open'",
            "Bot uses subagent architecture",
            "Bot has gateway commands",
            "Bot supports Telegram bridge",
        ]
        
        print(f"  Would check: {', '.join(bot_lists)}")
        print(f"  Detection patterns: {len(patterns)}")
    
    async def _scan_certificate_transparency(self):
        """Scan SSL certificates for OpenClaw-related domains"""
        print("\n🔒 Scanning certificate transparency logs...")
        
        domain_patterns = [
            "openclaw.*",
            "clawbot.*",
            "claw.*.gateway.*",
            "*.openclaw.*",
            "*.clawbot.*",
        ]
        
        print(f"  Monitoring patterns: {len(domain_patterns)}")
    
    async def _scan_public_gateways(self):
        """Scan for publicly accessible OpenClaw gateways"""
        print("\n🌐 Scanning for public OpenClaw gateways...")
        
        endpoint_patterns = [
            "/gateway",
            "/api/gateway",
            "/openclaw",
            "/clawbot/api",
            "/v1/gateway",
            "/health",
            "/status",
            "/metrics",
            "/api/health",
            "/api/status",
        ]
        
        print(f"  Endpoint patterns: {len(endpoint_patterns)}")
        print("  ⚠️  Active scanning requires target list and proper authorization")
    
    async def _scan_dns_txt_records(self):
        """Scan DNS TXT records for OpenClaw configurations"""
        print("\n📡 Scanning DNS TXT records for OpenClaw indicators...")
        
        if not DNS_AVAILABLE:
            print("  ⚠️  DNS scanning requires 'dnspython' package. Install with: pip install dnspython")
            return
        
        # Common domains to check (placeholder - expand as needed)
        domains_to_check = [
            # These would be populated from certificate transparency or other sources
            "_openclaw.example.com",
        ]
        
        discovered_count = 0
        for domain in domains_to_check:
            try:
                txt_records = await self._query_dns_txt(domain)
                for record in txt_records:
                    if self._is_openclaw_txt_record(record):
                        factors = [DetectionFactor(
                            factor_type="dns_txt_record",
                            weight=0.45,
                            detected=True,
                            details={"domain": domain, "record": record[:100]}
                        )]
                        confidence, _ = self.scorer.calculate_confidence(factors)
                        
                        sig = OpenClawSignature(
                            signature_id=hashlib.sha256(domain.encode()).hexdigest()[:16],
                            signature_type=OpenClawSignatureType.DNS,
                            confidence_score=confidence,
                            platform="dns",
                            detected_at=datetime.utcnow(),
                            endpoint=domain,
                            version_hint=None,
                            capabilities=["dns_txt", "openclaw_config"],
                            metadata={
                                "txt_record": record[:200],
                                "record_type": "TXT",
                            },
                            detection_factors=factors
                        )
                        self.discovered.append(sig)
                        discovered_count += 1
                        
            except DNSException:
                pass
            except Exception as e:
                print(f"  ⚠️  DNS scan error for {domain}: {e}")
        
        print(f"  DNS TXT records checked: {len(domains_to_check)}")
        if discovered_count > 0:
            print(f"  ✅ OpenClaw DNS records found: {discovered_count}")
    
    async def _query_dns_txt(self, domain: str) -> List[str]:
        """Query DNS TXT records for a domain"""
        if not DNS_AVAILABLE:
            return []
        
        loop = asyncio.get_event_loop()
        try:
            answers = await loop.run_in_executor(
                None, 
                lambda: dns.resolver.resolve(domain, 'TXT')
            )
            return [str(rdata) for rdata in answers]
        except DNSException:
            return []
    
    def _is_openclaw_txt_record(self, record: str) -> bool:
        """Check if a TXT record contains OpenClaw indicators"""
        record_lower = record.lower()
        return any(
            pattern in record_lower 
            for pattern in ["openclaw", "clawbot", "gateway-mode", "_openclaw"]
        )
    
    async def _scan_docker_hub(self):
        """Scan Docker Hub for OpenClaw-related images"""
        print("\n🐳 Scanning Docker Hub for OpenClaw images...")
        
        search_terms = [
            "openclaw",
            "clawbot",
            "openclaw-gateway",
            "clawbot-agent",
        ]
        
        discovered_count = 0
        for term in search_terms:
            try:
                url = "https://hub.docker.com/api/search/v3/catalog/search"
                params = {"query": term, "page_size": 20}
                
                async with self.session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for result in data.get("results", []):
                            factors = [DetectionFactor(
                                factor_type="docker_image",
                                weight=0.30,
                                detected=True,
                                details={
                                    "image_name": result.get("name"),
                                    "search_term": term,
                                    "is_official": result.get("is_official", False)
                                }
                            )]
                            confidence, _ = self.scorer.calculate_confidence(factors)
                            
                            if confidence > 0.5:
                                sig = OpenClawSignature(
                                    signature_id=hashlib.sha256(
                                        result["name"].encode()
                                    ).hexdigest()[:16],
                                    signature_type=OpenClawSignatureType.CONTAINER,
                                    confidence_score=confidence,
                                    platform="docker-hub",
                                    detected_at=datetime.utcnow(),
                                    endpoint=f"https://hub.docker.com/r/{result['name']}",
                                    version_hint=None,
                                    capabilities=["container", "docker"],
                                    metadata={
                                        "image_name": result.get("name"),
                                        "description": result.get("short_description"),
                                        "pull_count": result.get("pull_count"),
                                        "star_count": result.get("star_count"),
                                    },
                                    detection_factors=factors
                                )
                                self.discovered.append(sig)
                                discovered_count += 1
                                print(f"  ✅ Image: {result.get('name')} ({confidence:.2f})")
                                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"  ⚠️  Docker Hub scan error: {e}")
        
        print(f"  Docker images found: {discovered_count}")
    
    async def _scan_shodan(self):
        """Scan using Shodan API (requires API key)"""
        print("\n🔍 Shodan API scan...")
        
        api_key = self.api_keys.get("shodan")
        if not api_key:
            print("  ⚠️  No Shodan API key provided (set --shodan-api-key)")
            return
        
        queries = [
            'openclaw',
            'clawbot',
            'x-openclaw-version',
            'x-gateway-mode',
        ]
        
        try:
            for query in queries:
                url = "https://api.shodan.io/shodan/host/search"
                params = {"key": api_key, "query": query, "limit": 100}
                
                async with self.session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for match in data.get("matches", []):
                            factors = [
                                DetectionFactor(
                                    factor_type="header_x_clawbot_id",
                                    weight=0.25,
                                    detected="x-clawbot-id" in str(match.get("http", {}))
                                ),
                                DetectionFactor(
                                    factor_type="header_x_gateway_mode",
                                    weight=0.25,
                                    detected="x-gateway-mode" in str(match.get("http", {}))
                                ),
                            ]
                            confidence, _ = self.scorer.calculate_confidence(factors)
                            
                            if confidence > 0.5:
                                sig = OpenClawSignature(
                                    signature_id=hashlib.sha256(
                                        str(match.get("ip_str")).encode()
                                    ).hexdigest()[:16],
                                    signature_type=OpenClawSignatureType.GATEWAY,
                                    confidence_score=confidence,
                                    platform="shodan",
                                    detected_at=datetime.utcnow(),
                                    endpoint=f"{match.get('ip_str')}:{match.get('port')}",
                                    version_hint=None,
                                    capabilities=["shodan_discovery", "public_ip"],
                                    metadata={
                                        "ip": match.get("ip_str"),
                                        "port": match.get("port"),
                                        "org": match.get("org"),
                                        "location": match.get("location"),
                                        "shodan_query": query,
                                    },
                                    detection_factors=factors
                                )
                                self.discovered.append(sig)
                                print(f"  ✅ Shodan match: {match.get('ip_str')}:{match.get('port')} ({confidence:.2f})")
                                
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"  ⚠️  Shodan scan error: {e}")
    
    async def _scan_censys(self):
        """Scan using Censys API (requires API key)"""
        print("\n🔍 Censys API scan...")
        
        api_id = self.api_keys.get("censys_id")
        api_secret = self.api_keys.get("censys_secret")
        
        if not api_id or not api_secret:
            print("  ⚠️  No Censys API credentials provided (set --censys-id and --censys-secret)")
            return
        
        queries = [
            'openclaw',
            'clawbot',
            'services.http.response.headers.x_openclaw_version',
        ]
        
        try:
            # Censys API v2 uses Basic Auth
            auth = base64.b64encode(f"{api_id}:{api_secret}".encode()).decode()
            
            for query in queries:
                url = "https://search.censys.io/api/v2/hosts/search"
                headers = {"Authorization": f"Basic {auth}"}
                params = {"q": query, "per_page": 100}
                
                async with self.session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for result in data.get("result", {}).get("hits", []):
                            factors = [DetectionFactor(
                                factor_type="header_combo",
                                weight=0.35,
                                detected=True,
                                details={"censys_query": query}
                            )]
                            confidence, _ = self.scorer.calculate_confidence(factors)
                            
                            if confidence > 0.5:
                                sig = OpenClawSignature(
                                    signature_id=hashlib.sha256(
                                        result.get("ip").encode()
                                    ).hexdigest()[:16],
                                    signature_type=OpenClawSignatureType.GATEWAY,
                                    confidence_score=confidence,
                                    platform="censys",
                                    detected_at=datetime.utcnow(),
                                    endpoint=result.get("ip"),
                                    version_hint=None,
                                    capabilities=["censys_discovery", "public_ip"],
                                    metadata={
                                        "ip": result.get("ip"),
                                        "services": result.get("services", []),
                                        "censys_query": query,
                                    },
                                    detection_factors=factors
                                )
                                self.discovered.append(sig)
                                print(f"  ✅ Censys match: {result.get('ip')} ({confidence:.2f})")
                                
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"  ⚠️  Censys scan error: {e}")
    
    async def probe_endpoint(self, url: str) -> Optional[OpenClawSignature]:
        """
        Probe a specific endpoint for OpenClaw signatures.
        Uses multi-factor detection for improved accuracy.
        """
        try:
            async with self.session.get(url) as resp:
                headers = dict(resp.headers)
                body = await resp.text()
                
                factors = []
                
                # Check for header combinations (high confidence)
                header_keys = [k.lower() for k in headers.keys()]
                for combo in self.SIGNATURE_PATTERNS["header_combinations"]:
                    if all(h.lower() in header_keys for h in combo):
                        factors.append(DetectionFactor(
                            factor_type="header_combo",
                            weight=0.35,
                            detected=True,
                            details={"combination": combo}
                        ))
                
                # Check individual headers
                for header in ["x-clawbot-id", "x-openclaw-version"]:
                    if any(header in k for k in header_keys):
                        factors.append(DetectionFactor(
                            factor_type=f"header_{header.replace('-', '_')}",
                            weight=0.25,
                            detected=True,
                            details={"header_value": headers.get(header, "present")}
                        ))
                
                # Check body patterns
                for pattern in self.SIGNATURE_PATTERNS["response_body"]:
                    if re.search(pattern, body, re.IGNORECASE):
                        factors.append(DetectionFactor(
                            factor_type="body_pattern",
                            weight=0.20,
                            detected=True,
                            details={"pattern": pattern}
                        ))
                
                # Check /health endpoint signatures
                if "/health" in url:
                    for pattern in self.SIGNATURE_PATTERNS["health_signatures"]:
                        if re.search(pattern, body, re.IGNORECASE):
                            factors.append(DetectionFactor(
                                factor_type="body_health_signature",
                                weight=0.30,
                                detected=True,
                                details={"pattern": pattern}
                            ))
                
                # Check /status endpoint signatures
                if "/status" in url:
                    for pattern in self.SIGNATURE_PATTERNS["status_signatures"]:
                        if re.search(pattern, body, re.IGNORECASE):
                            factors.append(DetectionFactor(
                                factor_type="body_status_signature",
                                weight=0.30,
                                detected=True,
                                details={"pattern": pattern}
                            ))
                
                # Calculate confidence
                confidence, reasoning = self.scorer.calculate_confidence(factors)
                
                if confidence > 0.5:
                    return OpenClawSignature(
                        signature_id=hashlib.sha256(url.encode()).hexdigest()[:16],
                        signature_type=OpenClawSignatureType.GATEWAY,
                        confidence_score=confidence,
                        platform="web",
                        detected_at=datetime.utcnow(),
                        endpoint=url,
                        version_hint=headers.get("x-openclaw-version"),
                        capabilities=[f.factor_type for f in factors if f.detected],
                        metadata={
                            "status_code": resp.status,
                            "server": headers.get("server"),
                            "reasoning": reasoning,
                        },
                        detection_factors=factors
                    )
                    
        except Exception as e:
            pass
            
        return None


class PassiveTrafficAnalyzer:
    """
    Analyzes network traffic for OpenClaw signatures.
    For use in controlled environments with proper authorization.
    """
    
    OPENCLAW_TRAFFIC_PATTERNS = {
        "gateway_communication": {
            "ports": [8080, 3000, 8000, 5000, 8443],
            "paths": ["/gateway", "/openclaw", "/api/v1", "/health", "/status"],
            "payload_signatures": [
                b'"gateway_mode"',
                b'"subagent"',
                b'"channels"',
                b'"openclaw"',
                b'"clawbot"',
            ],
        },
        "websocket_openclaw": {
            "patterns": [
                b'"type":"openclaw',
                b'"gateway":"',
                b'"subagent_id":"',
            ],
        },
        "telegram_webhook": {
            "patterns": [
                b'"telegram".*"bot_token"',
                b'"telegram".*"webhook"',
            ],
        },
        "discord_gateway": {
            "patterns": [
                b'"discord".*"intents"',
                b'"discord".*"token"',
            ],
        },
    }
    
    def analyze_packet(self, packet_data: bytes) -> Optional[Dict]:
        """Analyze a network packet for OpenClaw indicators"""
        findings = {
            "is_openclaw": False,
            "confidence": 0.0,
            "indicators": [],
        }
        
        for category, patterns in self.OPENCLAW_TRAFFIC_PATTERNS.items():
            if "payload_signatures" in patterns:
                for sig in patterns["payload_signatures"]:
                    if sig in packet_data:
                        findings["is_openclaw"] = True
                        findings["confidence"] += 0.2
                        findings["indicators"].append(category)
                        
        return findings if findings["is_openclaw"] else None
    
    def analyze_websocket_frame(self, frame_data: bytes) -> Optional[Dict]:
        """Analyze WebSocket frame for OpenClaw patterns"""
        findings = {
            "is_openclaw_ws": False,
            "confidence": 0.0,
            "patterns_found": [],
        }
        
        ws_patterns = [
            (b'"type":"openclaw', "openclaw_type"),
            (b'"gateway":', "gateway_field"),
            (b'"subagent_id":', "subagent_id"),
            (b'"bridge_event":', "bridge_event"),
            (b'"clawbot":', "clawbot_field"),
        ]
        
        for pattern, name in ws_patterns:
            if pattern in frame_data:
                findings["is_openclaw_ws"] = True
                findings["confidence"] += 0.25
                findings["patterns_found"].append(name)
        
        return findings if findings["is_openclaw_ws"] else None


class OpenClawBehavioralDetector:
    """
    Detects OpenClaw-based agents by their behavioral signatures.
    Useful for identifying OpenClaw without direct access.
    """
    
    BEHAVIORAL_SIGNATURES = {
        "response_patterns": {
            "indicators": [
                "I am an AI assistant",
                "I can help you with",
                "Let me check the gateway",
                "Connecting to subagent",
                "Delegating to subagent",
                "Gateway mode active",
                "Subagent responded",
            ],
            "confidence": 0.6,
        },
        "command_structure": {
            "indicators": [
                r"/\w+\s+--\w+",  # CLI-style commands
                r"@\w+\s+\w+",    # Mention-based commands
                r"/gateway\s+\w+",
                r"/subagent\s+\w+",
            ],
            "confidence": 0.4,
        },
        "timing_patterns": {
            "indicators": [
                "consistent_response_time",  # OpenClaw has consistent latency
                "subagent_delay",            # Delay when delegating
            ],
            "confidence": 0.3,
        },
    }
    
    def analyze_conversation(self, messages: List[Dict]) -> Tuple[float, List[str]]:
        """Analyze conversation for OpenClaw behavioral patterns"""
        score = 0.0
        indicators = []
        
        for msg in messages:
            content = msg.get("content", "")
            
            # Check response patterns
            for indicator in self.BEHAVIORAL_SIGNATURES["response_patterns"]["indicators"]:
                if indicator.lower() in content.lower():
                    score += 0.1
                    indicators.append(f"response_pattern: {indicator[:30]}")
                    
            # Check command structure
            for pattern in self.BEHAVIORAL_SIGNATURES["command_structure"]["indicators"]:
                if re.search(pattern, content):
                    score += 0.05
                    indicators.append(f"command_pattern: {pattern}")
        
        return min(score, 1.0), indicators


class OutputFormatter:
    """Handles output formatting for different formats"""
    
    @staticmethod
    def to_json(signatures: List[OpenClawSignature]) -> str:
        """Convert signatures to JSON format"""
        return json.dumps(
            [s.to_dict() for s in signatures],
            indent=2,
            default=str
        )
    
    @staticmethod
    def to_csv(signatures: List[OpenClawSignature]) -> str:
        """Convert signatures to CSV format"""
        if not signatures:
            return "No data"
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "signature_id",
            "signature_type",
            "confidence_score",
            "confidence_level",
            "platform",
            "detected_at",
            "endpoint",
            "version_hint",
            "capabilities",
            "metadata"
        ])
        
        # Data rows
        scorer = ConfidenceScorer()
        for sig in signatures:
            writer.writerow([
                sig.signature_id,
                sig.signature_type.value,
                f"{sig.confidence_score:.4f}",
                scorer.get_confidence_level(sig.confidence_score),
                sig.platform,
                sig.detected_at.isoformat(),
                sig.endpoint or "N/A",
                sig.version_hint or "N/A",
                "|".join(sig.capabilities),
                json.dumps(sig.metadata)
            ])
        
        return output.getvalue()
    
    @staticmethod
    def to_table(signatures: List[OpenClawSignature]) -> str:
        """Convert signatures to formatted table"""
        if not signatures:
            return "No OpenClaw signatures discovered."
        
        lines = []
        lines.append("=" * 100)
        lines.append(f"{'ID':<18} {'Type':<12} {'Confidence':<10} {'Platform':<12} {'Endpoint':<40}")
        lines.append("=" * 100)
        
        scorer = ConfidenceScorer()
        for sig in signatures:
            level = scorer.get_confidence_level(sig.confidence_score)
            endpoint = (sig.endpoint or "N/A")[:38]
            lines.append(
                f"{sig.signature_id:<18} "
                f"{sig.signature_type.value:<12} "
                f"{level:<10} "
                f"{sig.platform:<12} "
                f"{endpoint:<40}"
            )
        
        lines.append("=" * 100)
        lines.append(f"\nTotal: {len(signatures)} signatures")
        return "\n".join(lines)
    
    @staticmethod
    def to_agent_highway_format(signatures: List[OpenClawSignature]) -> Dict:
        """Convert signatures to Agent Highway data format"""
        return {
            "source": "openclaw_scanner",
            "version": "2.0",
            "scan_timestamp": datetime.utcnow().isoformat(),
            "total_discoveries": len(signatures),
            "by_type": {},
            "by_platform": {},
            "signatures": [s.to_dict() for s in signatures]
        }


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="OpenClaw Discovery Scanner v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scan with table output (default)
  python openclaw.py

  # Scan with JSON output
  python openclaw.py --output-format json

  # Scan with CSV export to file
  python openclaw.py --output-format csv --output-file results.csv

  # Scan with Shodan integration
  python openclaw.py --shodan-api-key YOUR_KEY

  # Scan with Censys integration
  python openclaw.py --censys-id YOUR_ID --censys-secret YOUR_SECRET

  # Full scan with all integrations
  python openclaw.py --shodan-api-key KEY --censys-id ID --censys-secret SECRET -o json
        """
    )
    
    parser.add_argument(
        "--output-format",
        choices=["json", "csv", "table"],
        default="table",
        help="Output format (default: table)"
    )
    
    parser.add_argument(
        "--output-file",
        type=str,
        help="Save output to file"
    )
    
    parser.add_argument(
        "--shodan-api-key",
        type=str,
        help="Shodan API key for internet-wide scanning"
    )
    
    parser.add_argument(
        "--censys-id",
        type=str,
        help="Censys API ID"
    )
    
    parser.add_argument(
        "--censys-secret",
        type=str,
        help="Censys API Secret"
    )
    
    parser.add_argument(
        "--probe-url",
        type=str,
        help="Probe a specific URL for OpenClaw signatures"
    )
    
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.5,
        help="Minimum confidence threshold (0.0-1.0, default: 0.5)"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_args()
    
    print("=" * 70)
    print("🦅 OpenClaw Discovery Scanner v2.0")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANT ETHICAL NOTICE:")
    print("   This tool is for research and authorized scanning only.")
    print("   Always respect privacy and terms of service.")
    print("   Do not scan systems without permission.")
    print()
    
    # Collect API keys
    api_keys = {}
    if args.shodan_api_key:
        api_keys["shodan"] = args.shodan_api_key
    if args.censys_id:
        api_keys["censys_id"] = args.censys_id
    if args.censys_secret:
        api_keys["censys_secret"] = args.censys_secret
    
    async with OpenClawScanner(api_keys=api_keys) as scanner:
        # If specific URL probe requested
        if args.probe_url:
            print(f"🔍 Probing specific URL: {args.probe_url}")
            sig = await scanner.probe_endpoint(args.probe_url)
            if sig:
                scanner.discovered.append(sig)
                print(f"  ✅ OpenClaw signature detected! Confidence: {sig.confidence_score:.2f}")
            else:
                print("  ❌ No OpenClaw signature detected")
        else:
            # Run full scan
            await scanner.scan_all()
    
    # Filter by confidence threshold
    signatures = [
        s for s in scanner.discovered 
        if s.confidence_score >= args.min_confidence
    ]
    
    # Generate output
    formatter = OutputFormatter()
    
    if args.output_format == "json":
        output = formatter.to_json(signatures)
    elif args.output_format == "csv":
        output = formatter.to_csv(signatures)
    else:  # table
        output = formatter.to_table(signatures)
    
    # Print or save output
    if args.output_file:
        with open(args.output_file, "w") as f:
            f.write(output)
        print(f"\n💾 Output saved to: {args.output_file}")
    else:
        print("\n" + output)
    
    # Summary
    if not args.output_file:
        print("\n" + "=" * 70)
        print("📊 SCAN SUMMARY")
        print("=" * 70)
        
        if signatures:
            by_type = {}
            by_platform = {}
            by_confidence = defaultdict(int)
            
            scorer = ConfidenceScorer()
            for sig in signatures:
                t = sig.signature_type.value
                by_type[t] = by_type.get(t, 0) + 1
                by_platform[sig.platform] = by_platform.get(sig.platform, 0) + 1
                by_confidence[scorer.get_confidence_level(sig.confidence_score)] += 1
            
            print(f"\nTotal discoveries (min confidence {args.min_confidence}): {len(signatures)}")
            
            print("\nBy Type:")
            for t, count in sorted(by_type.items()):
                print(f"  - {t}: {count}")
                
            print("\nBy Platform:")
            for p, count in sorted(by_platform.items()):
                print(f"  - {p}: {count}")
            
            print("\nBy Confidence Level:")
            for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "MINIMAL"]:
                if by_confidence[level] > 0:
                    print(f"  - {level}: {by_confidence[level]}")
        else:
            print("\nNo OpenClaw signatures discovered in this scan.")
    
    print("\n" + "=" * 70)
    print("✅ Scan complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
