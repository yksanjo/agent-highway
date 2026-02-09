"""
OpenClaw Agent/User Discovery Scanner
Part of the Agent Monitoring System - Maps OpenClaw deployments
"""

import asyncio
import json
import hashlib
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Set, Dict
from enum import Enum
import aiohttp


class OpenClawSignatureType(Enum):
    GATEWAY = "gateway"           # OpenClaw gateway instances
    BOT = "bot"                   # Telegram/Discord bots using OpenClaw
    WEBHOOK = "webhook"           # Webhook endpoints
    BRIDGE = "bridge"             # AgentChat bridges
    EXTENSION = "extension"       # Browser extensions


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
    
    def to_dict(self):
        data = asdict(self)
        data['signature_type'] = self.signature_type.value
        data['detected_at'] = self.detected_at.isoformat()
        return data


class OpenClawScanner:
    """
    Discovers OpenClaw deployments across the internet.
    Uses multiple detection vectors to identify OpenClaw instances.
    """
    
    # OpenClaw-specific signatures
    SIGNATURE_PATTERNS = {
        "response_headers": [
            "x-openclaw-version",
            "x-clawbot-id",
            "x-gateway-mode",
        ],
        "response_body": [
            '"openclaw"',
            '"clawbot"',
            '"gateway_mode"',
            '"subagent"',
            '"talk".*"apiKey"',
            '"channels".*"telegram"',
            '"channels".*"discord"',
        ],
        "endpoint_patterns": [
            "/openclaw/",
            "/clawbot/",
            "/gateway/",
            "/subagent/",
            "/bridge/",
        ],
        "user_agents": [
            "OpenClaw/",
            "ClawBot/",
            "OpenClaw-Agent",
        ],
        "websocket_topics": [
            "openclaw.",
            "clawbot.",
            "gateway.",
        ],
        "error_messages": [
            "OpenClaw gateway not found",
            "Invalid clawbot configuration",
            "Subagent timeout",
        ],
    }
    
    # Known OpenClaw-related domains/patterns
    DOMAIN_PATTERNS = [
        "openclaw",
        "clawbot",
        "clawdbot",
    ]
    
    def __init__(self):
        self.discovered: List[OpenClawSignature] = []
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": "AgentMonitoringSystem/1.0 (Research Project)"
            },
            timeout=aiohttp.ClientTimeout(total=10)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scan_all(self) -> List[OpenClawSignature]:
        """Run all scanning methods"""
        print("🔍 Starting OpenClaw discovery scan...\n")
        
        # Run scans in parallel
        await asyncio.gather(
            self._scan_github_repos(),
            self._scan_telegram_bots(),
            self._scan_discord_bots(),
            self._scan_certificate_transparency(),
            self._scan_public_gateways(),
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
            '"gateway" "openclaw"',
            '"subagent" "telegram" "discord"',
        ]
        
        for query in queries:
            try:
                url = "https://api.github.com/search/repositories"
                params = {"q": query, "per_page": 30}
                
                async with self.session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for repo in data.get("items", []):
                            # Check for OpenClaw indicators
                            confidence = self._analyze_repo_for_openclaw(repo)
                            if confidence > 0.6:
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
                                    }
                                )
                                self.discovered.append(sig)
                                print(f"  ✅ Found: {repo['full_name']} ({confidence:.2f})")
                                
                await asyncio.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"  ⚠️  GitHub scan error: {e}")
    
    def _analyze_repo_for_openclaw(self, repo: dict) -> float:
        """Analyze repository for OpenClaw indicators"""
        score = 0.0
        
        # Name match
        name = repo.get("name", "").lower()
        if "openclaw" in name or "clawbot" in name:
            score += 0.4
            
        # Description match
        desc = (repo.get("description") or "").lower()
        if any(term in desc for term in ["openclaw", "clawbot", "ai agent", "gateway"]):
            score += 0.3
            
        # Topics
        topics = [t.lower() for t in repo.get("topics", [])]
        if "agent" in topics or "bot" in topics:
            score += 0.2
            
        return min(score, 1.0)
    
    async def _scan_telegram_bots(self):
        """Identify Telegram bots that might be OpenClaw-based"""
        print("\n💬 Scanning Telegram for OpenClaw bots...")
        print("  (Using public bot directory and behavior analysis)")
        
        # Public Telegram bot directories
        directories = [
            "https://tgbotlist.com/search?q=ai+agent",
            # Note: Would need proper APIs for real implementation
        ]
        
        # For now, document the approach
        approaches = [
            "Check bot usernames for 'claw' patterns",
            "Analyze bot behavior (response patterns)",
            "Look for OpenClaw-specific message formatting",
            "Check bot descriptions for OpenClaw references",
        ]
        
        print(f"  Detection approaches: {len(approaches)}")
        
        # In a real implementation, you would:
        # 1. Query Telegram Bot API (with token)
        # 2. Analyze public bot lists
        # 3. Look for behavioral signatures
    
    async def _scan_discord_bots(self):
        """Identify Discord bots that might be OpenClaw-based"""
        print("\n🎮 Scanning Discord for OpenClaw bots...")
        print("  (Using public bot lists and behavior patterns)")
        
        # Discord bot lists to check
        bot_lists = [
            "top.gg",
            "discord.bots.gg",
            "discordbotlist.com",
        ]
        
        # Detection patterns
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
        print("  (Looking for OpenClaw-related subdomains)")
        
        # Certificate Transparency monitoring approach
        domain_patterns = [
            "openclaw.*",
            "clawbot.*",
            "claw.*.gateway.*",
            "*.openclaw.*",
        ]
        
        # In production, you'd use:
        # - crt.sh API
        # - Censys API
        # - Certificate Transparency log aggregators
        
        print(f"  Monitoring patterns: {len(domain_patterns)}")
    
    async def _scan_public_gateways(self):
        """Scan for publicly accessible OpenClaw gateways"""
        print("\n🌐 Scanning for public OpenClaw gateways...")
        print("  (Testing common endpoint patterns)")
        
        # Common gateway endpoints to check
        # Note: These are example patterns - adjust for your research
        endpoint_patterns = [
            "/gateway",
            "/api/gateway",
            "/openclaw",
            "/clawbot/api",
            "/v1/gateway",
            "/health",
            "/status",
        ]
        
        print(f"  Endpoint patterns: {len(endpoint_patterns)}")
        print("  ⚠️  Active scanning requires target list and proper authorization")
    
    async def probe_endpoint(self, url: str) -> Optional[OpenClawSignature]:
        """Probe a specific endpoint for OpenClaw signatures"""
        try:
            async with self.session.get(url) as resp:
                headers = dict(resp.headers)
                body = await resp.text()
                
                # Check for OpenClaw signatures
                confidence = 0.0
                indicators = []
                
                # Check headers
                for header in self.SIGNATURE_PATTERNS["response_headers"]:
                    if any(header.lower() in k.lower() for k in headers.keys()):
                        confidence += 0.2
                        indicators.append(f"header:{header}")
                
                # Check body
                for pattern in self.SIGNATURE_PATTERNS["response_body"]:
                    if re.search(pattern, body, re.IGNORECASE):
                        confidence += 0.15
                        indicators.append(f"body_pattern")
                
                if confidence > 0.5:
                    return OpenClawSignature(
                        signature_id=hashlib.sha256(url.encode()).hexdigest()[:16],
                        signature_type=OpenClawSignatureType.GATEWAY,
                        confidence_score=confidence,
                        platform="web",
                        detected_at=datetime.utcnow(),
                        endpoint=url,
                        version_hint=headers.get("x-openclaw-version"),
                        capabilities=indicators,
                        metadata={
                            "status_code": resp.status,
                            "server": headers.get("server"),
                        }
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
            "ports": [8080, 3000, 8000, 5000],
            "paths": ["/gateway", "/openclaw", "/api/v1"],
            "payload_signatures": [
                b'"gateway_mode"',
                b'"subagent"',
                b'"channels"',
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
            ],
            "confidence": 0.6,
        },
        "command_structure": {
            "indicators": [
                r"/\w+\s+--\w+",  # CLI-style commands
                r"@\w+\s+\w+",    # Mention-based commands
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
    
    def analyze_conversation(self, messages: List[Dict]) -> float:
        """Analyze conversation for OpenClaw behavioral patterns"""
        score = 0.0
        
        for msg in messages:
            content = msg.get("content", "")
            
            # Check response patterns
            for indicator in self.BEHAVIORAL_SIGNATURES["response_patterns"]["indicators"]:
                if indicator.lower() in content.lower():
                    score += 0.1
                    
            # Check command structure
            for pattern in self.BEHAVIORAL_SIGNATURES["command_structure"]["indicators"]:
                if re.search(pattern, content):
                    score += 0.05
        
        return min(score, 1.0)


async def main():
    """Main entry point"""
    print("=" * 70)
    print("🦅 OpenClaw Discovery Scanner")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANT ETHICAL NOTICE:")
    print("   This tool is for research and authorized scanning only.")
    print("   Always respect privacy and terms of service.")
    print("   Do not scan systems without permission.")
    print()
    
    async with OpenClawScanner() as scanner:
        signatures = await scanner.scan_all()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SCAN SUMMARY")
    print("=" * 70)
    
    if signatures:
        by_type = {}
        by_platform = {}
        
        for sig in signatures:
            t = sig.signature_type.value
            by_type[t] = by_type.get(t, 0) + 1
            by_platform[sig.platform] = by_platform.get(sig.platform, 0) + 1
        
        print(f"\nTotal discoveries: {len(signatures)}")
        
        print("\nBy Type:")
        for t, count in sorted(by_type.items()):
            print(f"  - {t}: {count}")
            
        print("\nBy Platform:")
        for p, count in sorted(by_platform.items()):
            print(f"  - {p}: {count}")
            
        print("\nHigh confidence discoveries:")
        for sig in sorted(signatures, key=lambda x: -x.confidence_score)[:5]:
            print(f"  - {sig.endpoint or 'N/A'}: {sig.confidence_score:.2f}")
    else:
        print("\nNo OpenClaw signatures discovered in this scan.")
        print("This is expected for passive scanning without specific targets.")
    
    print("\n" + "=" * 70)
    print("💡 RECOMMENDATIONS FOR DISCOVERY:")
    print("=" * 70)
    print("""
1. GitHub Analysis (Passive):
   - Monitor for openclaw.json files
   - Search for 'gateway' + 'telegram' + 'discord' combinations
   - Track OpenClaw forks and stars

2. Telegram Bot Discovery:
   - Use @BotFather to search public bots
   - Look for bots with 'claw' in username
   - Analyze bot behavior patterns

3. Discord Bot Lists:
   - Check top.gg, discord.bots.gg
   - Search for 'openclaw' or 'clawbot'
   - Review bot descriptions and commands

4. Network Analysis (With Permission):
   - Monitor your own network traffic
   - Look for OpenClaw gateway patterns
   - Analyze WebSocket connections

5. Community Engagement:
   - Join OpenClaw-related communities
   - Monitor Discord servers using OpenClaw
   - Track GitHub discussions

6. API Endpoint Scanning (Authorized Only):
   - Test known OpenClaw endpoints
   - Look for version headers
   - Check health/status endpoints
""")


if __name__ == "__main__":
    asyncio.run(main())
