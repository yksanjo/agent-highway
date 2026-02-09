"""
Agent Detection - Multi-factor agent identification
"""

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum


class AgentType(Enum):
    UNKNOWN = "unknown"
    CHATBOT = "chatbot"
    CODE_AGENT = "code_agent"
    RESEARCH_AGENT = "research_agent"
    TRADING_AGENT = "trading_agent"
    SOCIAL_AGENT = "social_agent"
    ORCHESTRATOR = "orchestrator"
    AUTONOMOUS = "autonomous_agent"
    GATEWAY = "gateway"


@dataclass
class DetectionResult:
    agent_id: str
    confidence: float
    agent_type: AgentType
    signals: List[str]
    capabilities: List[str]
    source: str


class AgentDetector:
    """Multi-factor agent detection engine"""
    
    # Detection patterns by source type
    PATTERNS = {
        "github": {
            "name_indicators": [
                r"agent", r"bot", r"ai-", r"autonomous", r"assistant",
                r"llm-", r"gpt-", r"claude", r"openai",
            ],
            "description_indicators": [
                r"ai agent", r"autonomous", r"llm powered", r"gpt",
                r"assistant", r"chatbot", r"automation",
            ],
            "file_indicators": [
                r"agent\.py", r"bot\.py", r"autonomous",
                r"\.env.*openai", r"requirements.*langchain",
            ],
            "topic_indicators": [
                "agent", "bot", "automation", "ai", "llm", "gpt",
            ],
        },
        "openclaw": {
            "name_indicators": [
                r"openclaw", r"clawbot", r"clawdbot", r"claw",
            ],
            "config_indicators": [
                r"gateway", r"subagent", r"telegram", r"discord",
            ],
        },
        "telegram": {
            "username_patterns": [
                r".*bot$", r".*_bot$",
            ],
            "behavior_indicators": [
                r"ai assistant", r"powered by",
            ],
        },
        "discord": {
            "name_patterns": [
                r".*bot$", r"ai.*", r"assistant.*",
            ],
        },
    }
    
    def __init__(self, confidence_threshold: float = 0.6, min_signals: int = 3):
        self.confidence_threshold = confidence_threshold
        self.min_signals = min_signals
        
    def detect(self, item: Dict, source: str) -> Optional[DetectionResult]:
        """
        Detect if item represents an agent
        
        Args:
            item: Data item to analyze
            source: Source of the item (github, openclaw, etc.)
            
        Returns:
            DetectionResult if agent detected, None otherwise
        """
        signals = []
        capabilities = []
        
        # Get patterns for this source
        patterns = self.PATTERNS.get(source, {})
        
        # Analyze name/title
        name = self._extract_name(item)
        name_score, name_signals = self._analyze_name(name, patterns)
        signals.extend(name_signals)
        
        # Analyze description
        desc = self._extract_description(item)
        desc_score, desc_signals = self._analyze_description(desc, patterns)
        signals.extend(desc_signals)
        
        # Analyze content/files
        content_score, content_signals = self._analyze_content(item, patterns)
        signals.extend(content_signals)
        
        # Calculate confidence
        total_score = name_score + desc_score + content_score
        confidence = min(total_score / 3, 1.0)  # Normalize to 0-1
        
        # Check threshold
        if confidence < self.confidence_threshold:
            return None
            
        if len(signals) < self.min_signals:
            return None
            
        # Determine agent type
        agent_type = self._classify_type(signals, capabilities, source)
        
        # Generate ID
        agent_id = self._generate_id(item, source)
        
        return DetectionResult(
            agent_id=agent_id,
            confidence=confidence,
            agent_type=agent_type,
            signals=signals,
            capabilities=capabilities,
            source=source
        )
        
    def _extract_name(self, item: Dict) -> str:
        """Extract name/title from item"""
        for key in ["name", "title", "username", "repo", "full_name"]:
            if key in item:
                return str(item[key])
        return ""
        
    def _extract_description(self, item: Dict) -> str:
        """Extract description from item"""
        for key in ["description", "desc", "about", "bio"]:
            if key in item:
                return str(item[key])
        return ""
        
    def _analyze_name(self, name: str, patterns: Dict) -> Tuple[float, List[str]]:
        """Analyze name for agent indicators"""
        score = 0.0
        signals = []
        
        name_lower = name.lower()
        
        for pattern in patterns.get("name_indicators", []):
            if re.search(pattern, name_lower):
                score += 0.3
                signals.append(f"name:{pattern}")
                
        return min(score, 1.0), signals
        
    def _analyze_description(self, desc: str, patterns: Dict) -> Tuple[float, List[str]]:
        """Analyze description for agent indicators"""
        score = 0.0
        signals = []
        
        if not desc:
            return score, signals
            
        desc_lower = desc.lower()
        
        for pattern in patterns.get("description_indicators", []):
            if re.search(pattern, desc_lower):
                score += 0.25
                signals.append(f"desc:{pattern}")
                
        return min(score, 1.0), signals
        
    def _analyze_content(self, item: Dict, patterns: Dict) -> Tuple[float, List[str]]:
        """Analyze content/files for agent indicators"""
        score = 0.0
        signals = []
        
        # Check topics
        topics = item.get("topics", [])
        for topic in topics:
            for indicator in patterns.get("topic_indicators", []):
                if indicator.lower() in topic.lower():
                    score += 0.2
                    signals.append(f"topic:{indicator}")
                    
        # Check for config indicators
        for indicator in patterns.get("config_indicators", []):
            if indicator in str(item):
                score += 0.15
                signals.append(f"config:{indicator}")
                
        return min(score, 1.0), signals
        
    def _classify_type(self, signals: List[str], capabilities: List[str], source: str) -> AgentType:
        """Classify agent type based on signals"""
        signal_str = " ".join(signals).lower()
        
        if "openclaw" in signal_str or "clawbot" in signal_str or source == "openclaw":
            return AgentType.GATEWAY
            
        if "autonomous" in signal_str:
            return AgentType.AUTONOMOUS
            
        if "orchestrator" in signal_str or "multi-agent" in signal_str:
            return AgentType.ORCHESTRATOR
            
        if "chat" in signal_str or "discord" in signal_str or "telegram" in signal_str:
            return AgentType.CHATBOT
            
        if "code" in signal_str or "github" in signal_str:
            return AgentType.CODE_AGENT
            
        return AgentType.UNKNOWN
        
    def _generate_id(self, item: Dict, source: str) -> str:
        """Generate unique agent ID"""
        # Create deterministic ID from item data
        name = self._extract_name(item)
        content = f"{source}:{name}:{item.get('detected_at', '')}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class BatchDetector:
    """Detect agents in batches"""
    
    def __init__(self, detector: AgentDetector):
        self.detector = detector
        
    async def detect_batch(self, items: List[Dict], source: str) -> List[DetectionResult]:
        """Detect agents in a batch of items"""
        results = []
        
        for item in items:
            result = self.detector.detect(item, source)
            if result:
                results.append(result)
                
        return results
