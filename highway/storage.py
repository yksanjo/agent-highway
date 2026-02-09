"""
Storage Layer - Data persistence for Agent Highway
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class HighwayStorage:
    """Unified storage for Agent Highway"""
    
    def __init__(self, data_dir: Path, backend: str = "json"):
        self.data_dir = Path(data_dir)
        self.backend = backend
        self.db_path = self.data_dir / "highway.db"
        self._conn: Optional[sqlite3.Connection] = None
        
    async def initialize(self):
        """Initialize storage"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        if self.backend == "sqlite":
            await self._init_sqlite()
        else:
            await self._init_json()
            
        logger.info(f"✅ Storage initialized: {self.backend}")
        
    async def _init_sqlite(self):
        """Initialize SQLite database"""
        self._conn = sqlite3.connect(str(self.db_path))
        cursor = self._conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT,
                agent_type TEXT,
                confidence REAL,
                source TEXT,
                platform TEXT,
                detected_at TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                event_type TEXT,
                timestamp TEXT,
                data TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents (id)
            )
        """)
        
        self._conn.commit()
        
    async def _init_json(self):
        """Initialize JSON storage directories"""
        (self.data_dir / "agents").mkdir(exist_ok=True)
        (self.data_dir / "events").mkdir(exist_ok=True)
        (self.data_dir / "insights").mkdir(exist_ok=True)
        
    async def close(self):
        """Close storage connections"""
        if self._conn:
            self._conn.close()
            
    async def save_agent(self, agent: Dict):
        """Save an agent to storage"""
        if self.backend == "sqlite":
            await self._save_agent_sqlite(agent)
        else:
            await self._save_agent_json(agent)
            
    async def _save_agent_sqlite(self, agent: Dict):
        """Save agent to SQLite"""
        cursor = self._conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO agents 
            (id, name, agent_type, confidence, source, platform, detected_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent.get("agent_id"),
            agent.get("name"),
            agent.get("agent_type"),
            agent.get("confidence_score"),
            agent.get("source"),
            agent.get("platform"),
            agent.get("detected_at"),
            json.dumps(agent.get("metadata", {}))
        ))
        self._conn.commit()
        
    async def _save_agent_json(self, agent: Dict):
        """Save agent to JSON file"""
        agent_id = agent.get("agent_id", "unknown")
        filepath = self.data_dir / "agents" / f"{agent_id}.json"
        
        with open(filepath, "w") as f:
            json.dump(agent, f, indent=2)
            
    async def save_batch(self, items: List[Dict]):
        """Save a batch of items"""
        for item in items:
            await self.save_agent(item)
            
        logger.info(f"💾 Saved {len(items)} items to storage")
        
    def query_agents(self, **filters) -> List[Dict]:
        """Query agents with filters"""
        if self.backend == "sqlite":
            return self._query_agents_sqlite(**filters)
        else:
            return self._query_agents_json(**filters)
            
    def _query_agents_sqlite(self, **filters) -> List[Dict]:
        """Query agents from SQLite"""
        cursor = self._conn.cursor()
        
        query = "SELECT * FROM agents WHERE 1=1"
        params = []
        
        if "agent_type" in filters:
            query += " AND agent_type = ?"
            params.append(filters["agent_type"])
            
        if "source" in filters:
            query += " AND source = ?"
            params.append(filters["source"])
            
        if "min_confidence" in filters:
            query += " AND confidence >= ?"
            params.append(filters["min_confidence"])
            
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "agent_id": row[0],
                "name": row[1],
                "agent_type": row[2],
                "confidence_score": row[3],
                "source": row[4],
                "platform": row[5],
                "detected_at": row[6],
                "metadata": json.loads(row[7]) if row[7] else {},
            })
            
        return results
        
    def _query_agents_json(self, **filters) -> List[Dict]:
        """Query agents from JSON files"""
        results = []
        agents_dir = self.data_dir / "agents"
        
        if not agents_dir.exists():
            return results
            
        for filepath in agents_dir.glob("*.json"):
            try:
                with open(filepath) as f:
                    agent = json.load(f)
                    
                # Apply filters
                if "agent_type" in filters and agent.get("agent_type") != filters["agent_type"]:
                    continue
                    
                if "source" in filters and agent.get("source") != filters["source"]:
                    continue
                    
                if "min_confidence" in filters:
                    if agent.get("confidence_score", 0) < filters["min_confidence"]:
                        continue
                        
                results.append(agent)
                
            except Exception as e:
                logger.warning(f"Error reading {filepath}: {e}")
                
        return results
        
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        if self.backend == "sqlite":
            cursor = self._conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM agents")
            total_agents = cursor.fetchone()[0]
        else:
            agents_dir = self.data_dir / "agents"
            total_agents = len(list(agents_dir.glob("*.json"))) if agents_dir.exists() else 0
            
        return {
            "total_agents": total_agents,
            "backend": self.backend,
            "data_dir": str(self.data_dir),
        }
