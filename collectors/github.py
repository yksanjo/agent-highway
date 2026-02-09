"""
GitHub Agent Collector - MVP Implementation
Discovers AI agents from GitHub repositories
"""

import asyncio
import hashlib
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Set
from enum import Enum

import aiohttp
from aiohttp import ClientRateLimitError


class AgentType(Enum):
    CHATBOT = "chatbot"
    CODE_AGENT = "code_agent"
    RESEARCH_AGENT = "research_agent"
    AUTONOMOUS = "autonomous_agent"
    TOOL = "tool_orchestrator"
    UNKNOWN = "unknown"


@dataclass
class AgentSignature:
    agent_id: str
    name: str
    confidence_score: float
    agent_type: AgentType
    capabilities: List[str]
    source_repo: str
    detected_at: datetime
    metadata: dict
    
    def to_dict(self):
        data = asdict(self)
        data['agent_type'] = self.agent_type.value
        data['detected_at'] = self.detected_at.isoformat()
        return data


class GitHubAgentCollector:
    """
    Collects agent data from GitHub repositories.
    Uses multiple detection signals to identify AI agents.
    """
    
    # Search queries to find agent repositories
    SEARCH_QUERIES = [
        "AI agent autonomous",
        "LLM agent framework",
        "autonomous agent python",
        "AI assistant bot",
        "langchain agent",
        "autogen agent",
        "crewai agent",
        "agent orchestration",
        "multi-agent system",
        "autonomous coding agent",
    ]
    
    # File patterns that indicate agent code
    AGENT_INDICATORS = {
        "config_files": [
            "agent.yaml", "agent.yml", "agents.json", 
            "config/agent", ".agentrc"
        ],
        "code_patterns": [
            "class.*Agent", "def.*agent", "autonomous",
            "llm.*call", "openai.*completion", "anthropic.*messages",
            "@tool", "@agent", "react.*pattern"
        ],
        "frameworks": [
            "langchain", "llamaindex", "autogen", "crewai",
            "semantic-kernel", "transformers", "openai"
        ]
    }
    
    def __init__(self, github_token: Optional[str] = None):
        self.token = github_token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.session: Optional[aiohttp.ClientSession] = None
        self.discovered_agents: List[AgentSignature] = []
        
    async def __aenter__(self):
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AgentMonitoringSystem/1.0"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
            
        self.session = aiohttp.ClientSession(headers=headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def collect(self, max_repos: int = 100) -> List[AgentSignature]:
        """Main collection method"""
        print(f"🔍 Starting GitHub agent discovery (max {max_repos} repos)...")
        
        # Search for repositories
        repos = await self._search_repositories(max_repos)
        print(f"📦 Found {len(repos)} potential repositories")
        
        # Analyze each repository
        for repo in repos:
            try:
                agent = await self._analyze_repository(repo)
                if agent:
                    self.discovered_agents.append(agent)
                    print(f"  ✅ Found agent: {agent.name} (confidence: {agent.confidence_score:.2f})")
            except Exception as e:
                print(f"  ⚠️  Error analyzing {repo['full_name']}: {e}")
                
        print(f"\n🎯 Total agents discovered: {len(self.discovered_agents)}")
        return self.discovered_agents
    
    async def _search_repositories(self, max_results: int) -> List[dict]:
        """Search GitHub for agent-related repositories"""
        repos = []
        seen = set()
        
        for query in self.SEARCH_QUERIES:
            if len(repos) >= max_results:
                break
                
            url = f"{self.base_url}/search/repositories"
            params = {
                "q": query,
                "sort": "updated",
                "order": "desc",
                "per_page": min(30, max_results - len(repos))
            }
            
            try:
                async with self.session.get(url, params=params) as resp:
                    if resp.status == 403:
                        print("⚠️  Rate limit hit, waiting...")
                        await asyncio.sleep(60)
                        continue
                        
                    data = await resp.json()
                    for repo in data.get("items", []):
                        if repo["full_name"] not in seen:
                            seen.add(repo["full_name"])
                            repos.append(repo)
                            
                    await asyncio.sleep(1)  # Rate limiting
                    
            except Exception as e:
                print(f"Search error for query '{query}': {e}")
                
        return repos[:max_results]
    
    async def _analyze_repository(self, repo: dict) -> Optional[AgentSignature]:
        """Analyze a repository to determine if it contains an agent"""
        signals = []
        capabilities = []
        
        # Signal 1: Repository metadata
        score, caps = self._analyze_metadata(repo)
        signals.append(("metadata", score))
        capabilities.extend(caps)
        
        # Signal 2: README content
        score, caps = await self._analyze_readme(repo)
        signals.append(("readme", score))
        capabilities.extend(caps)
        
        # Signal 3: Code analysis
        score, caps = await self._analyze_code(repo)
        signals.append(("code", score))
        capabilities.extend(caps)
        
        # Calculate overall confidence
        confidence = sum(score for _, score in signals) / len(signals)
        
        if confidence > 0.5:  # Threshold for agent detection
            # Generate unique ID
            agent_id = hashlib.sha256(
                f"{repo['full_name']}:{repo['created_at']}".encode()
            ).hexdigest()[:16]
            
            return AgentSignature(
                agent_id=agent_id,
                name=repo['name'],
                confidence_score=confidence,
                agent_type=self._classify_agent_type(capabilities),
                capabilities=list(set(capabilities)),
                source_repo=repo['html_url'],
                detected_at=datetime.utcnow(),
                metadata={
                    "stars": repo.get("stargazers_count", 0),
                    "language": repo.get("language"),
                    "description": repo.get("description"),
                    "signals": {name: score for name, score in signals}
                }
            )
        
        return None
    
    def _analyze_metadata(self, repo: dict) -> tuple[float, List[str]]:
        """Analyze repository metadata for agent indicators"""
        score = 0.0
        capabilities = []
        
        # Check description
        desc = (repo.get("description") or "").lower()
        name = repo.get("name", "").lower()
        
        agent_keywords = [
            "agent", "autonomous", "ai assistant", "bot framework",
            "llm agent", "ai agent", "automation"
        ]
        
        for keyword in agent_keywords:
            if keyword in desc or keyword in name:
                score += 0.2
                
        # Check topics
        topics = [t.lower() for t in repo.get("topics", [])]
        if "agent" in topics:
            score += 0.3
            capabilities.append("explicit_agent")
        if "autonomous" in topics:
            score += 0.2
            capabilities.append("autonomous_operation")
            
        # Recent activity suggests active development
        if repo.get("pushed_at"):
            last_push = datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00"))
            days_since = (datetime.now().replace(tzinfo=last_push.tzinfo) - last_push).days
            if days_since < 30:
                score += 0.1
                
        return min(score, 1.0), capabilities
    
    async def _analyze_readme(self, repo: dict) -> tuple[float, List[str]]:
        """Analyze README for agent indicators"""
        score = 0.0
        capabilities = []
        
        try:
            url = f"{self.base_url}/repos/{repo['full_name']}/readme"
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return score, capabilities
                    
                data = await resp.json()
                import base64
                content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore").lower()
                
                # Check for agent patterns
                patterns = [
                    ("autonomous", 0.2),
                    ("llm", 0.15),
                    ("openai", 0.1),
                    ("agent framework", 0.25),
                    ("tools", 0.1),
                    ("orchestration", 0.2),
                    ("multi-agent", 0.25),
                ]
                
                for pattern, weight in patterns:
                    if pattern in content:
                        score += weight
                        capabilities.append(pattern)
                        
                # Check for code examples
                if "```" in content:
                    score += 0.1
                    
        except Exception as e:
            pass
            
        return min(score, 1.0), capabilities
    
    async def _analyze_code(self, repo: dict) -> tuple[float, List[str]]:
        """Analyze repository code structure"""
        score = 0.0
        capabilities = []
        
        try:
            # Get repository contents
            url = f"{self.base_url}/repos/{repo['full_name']}/contents"
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return score, capabilities
                    
                contents = await resp.json()
                if not isinstance(contents, list):
                    return score, capabilities
                
                # Check for agent indicator files
                for item in contents:
                    name = item.get("name", "").lower()
                    
                    for indicator_file in self.AGENT_INDICATORS["config_files"]:
                        if indicator_file in name:
                            score += 0.3
                            capabilities.append("configuration_driven")
                            
                # Check for main framework files
                for item in contents:
                    name = item.get("name", "").lower()
                    if name in ["requirements.txt", "package.json", "pyproject.toml"]:
                        # Would analyze dependencies here
                        score += 0.1
                        
        except Exception as e:
            pass
            
        return min(score, 1.0), capabilities
    
    def _classify_agent_type(self, capabilities: List[str]) -> AgentType:
        """Classify the type of agent based on capabilities"""
        caps_lower = [c.lower() for c in capabilities]
        
        if "autonomous_operation" in caps_lower or "autonomous" in caps_lower:
            return AgentType.AUTONOMOUS
        elif "explicit_agent" in caps_lower or "agent" in caps_lower:
            if "orchestration" in caps_lower:
                return AgentType.TOOL
            return AgentType.CODE_AGENT
        elif "multi-agent" in caps_lower:
            return AgentType.TOOL
        else:
            return AgentType.UNKNOWN


class StorageBackend:
    """Simple storage backend for agent data"""
    
    def __init__(self, output_dir: str = "./data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def save(self, agents: List[AgentSignature]):
        """Save agents to JSON file"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"agents_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        data = {
            "collection_timestamp": datetime.utcnow().isoformat(),
            "total_agents": len(agents),
            "agents": [agent.to_dict() for agent in agents]
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
            
        print(f"💾 Saved {len(agents)} agents to {filepath}")
        return filepath


async def main():
    """Main entry point"""
    print("=" * 60)
    print("🤖 GitHub Agent Collector")
    print("=" * 60)
    
    # Initialize collector
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("\n⚠️  Warning: No GITHUB_TOKEN found. Rate limits will be strict.")
        print("   Set GITHUB_TOKEN env var for better results.\n")
    
    async with GitHubAgentCollector(token) as collector:
        agents = await collector.collect(max_repos=50)
    
    # Save results
    storage = StorageBackend()
    filepath = storage.save(agents)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"Total agents discovered: {len(agents)}")
    
    if agents:
        by_type = {}
        for agent in agents:
            by_type[agent.agent_type.value] = by_type.get(agent.agent_type.value, 0) + 1
        
        print("\nBy Type:")
        for agent_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
            print(f"  - {agent_type}: {count}")
            
        print(f"\nTop confidence agents:")
        top_agents = sorted(agents, key=lambda x: -x.confidence_score)[:5]
        for agent in top_agents:
            print(f"  - {agent.name}: {agent.confidence_score:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
