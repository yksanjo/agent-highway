# 🛣️ Agent Highway

> The unified superhighway for AI agent discovery, monitoring, and intelligence

```
╔══════════════════════════════════════════════════════════════════════════╗
║                           🛣️ AGENT HIGHWAY 🛣️                            ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║   All roads lead to agent intelligence                                   ║
║                                                                          ║
║   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ║
║   │  GitHub  │  │ OpenClaw │  │ Discord  │  │ Telegram │  │   Web    │  ║
║   │ Collector│  │ Scanner  │  │  Agent   │  │   Bot    │  │  Crawler │  ║
║   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  ║
║        │             │             │             │             │        ║
║        └─────────────┴─────────────┴──────┬──────┴─────────────┘        ║
║                                           ▼                              ║
║   ╔══════════════════════════════════════════════════════════════════╗   ║
║   ║                         THE HIGHWAY                              ║   ║
║   ║    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            ║   ║
║   ║    │   Stream    │  │   Agent     │  │  Behavior   │            ║   ║
║   ║    │  Processor  │  │  Detector   │  │  Analyzer   │            ║   ║
║   ║    └─────────────┘  └─────────────┘  └─────────────┘            ║   ║
║   ╚════════════════════════════════════════┬────────────────═════════╝   ║
║                                            ▼                             ║
║   ╔══════════════════════════════════════════════════════════════════╗   ║
║   ║                      INTELLIGENCE LAYER                          ║   ║
║   ║   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   ║   ║
║   ║   │ Network │ │  Trend  │ │ Identity│ │Predictor│ │  Swarm  │   ║   ║
║   ║   │  Graph  │ │Analyzer │ │Resolver │ │  Model  │ │Detector │   ║   ║
║   ║   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   ║   ║
║   ╚════════════════════════════════════════┬────────────────═════════╝   ║
║                                            ▼                             ║
║   ╔══════════════════════════════════════════════════════════════════╗   ║
║   ║                    VISUALIZATION & API                           ║   ║
║   ║           Dashboard ◄────► REST API ◄────► Alerts               ║   ║
║   ╚══════════════════════════════════════════════════════════════════╝   ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

## ⚠️ Project Status: MVP (Functional Prototype)

**What Works Today:**
- ✅ **GitHub Collector** - Scans repos and detects AI agents with confidence scoring
- ✅ **Agent Detection** - Multi-factor analysis (metadata, README, code patterns)
- ✅ **Terminal Dashboard** - Live visualization with Rich
- ✅ **JSON Storage** - Export and query discovered agents
- ✅ **OpenClaw Scanner** - Track agent deployments

**In Development:**
- 🚧 Discord/Telegram collectors
- 🚧 Web dashboard (FastAPI-based)
- 🚧 ML-based detection models

## 🎬 See It In Action

### Real Test Run (2025-02-10)

```bash
$ python -m collectors.github
🔍 Starting GitHub agent discovery (max 20 repos)...
📦 Found 20 potential repositories
  ✅ Found agent: Best-of-the-Best (confidence: 0.53)
  ✅ Found agent: inkrypt (confidence: 0.55)
  ✅ Found agent: genuine-axel (confidence: 0.55)
  ✅ Found agent: MemMachine (confidence: 0.63)
  ✅ Found agent: wunderland-sol (confidence: 0.53)

🎯 Total agents discovered: 5
💾 Saved 5 agents to ./data/agents_20260211_025405.json
```

**Recent Discoveries:**
| Agent | Type | Confidence | Stars |
|-------|------|------------|-------|
| [MemMachine](https://github.com/MemMachine/MemMachine) | Autonomous | 0.63 | 4,481 |
| [inkrypt](https://github.com/0xDexFi/inkrypt) | Autonomous | 0.55 | 0 |
| [genuine-axel](https://github.com/NorthProt-Inc/genuine-axel) | Autonomous | 0.55 | 1 |
| [Best-of-the-Best](https://github.com/ruslanmv/Best-of-the-Best) | Autonomous | 0.53 | 3 |
| [wunderland-sol](https://github.com/manicinc/wunderland-sol) | Autonomous | 0.53 | 0 |

*[View full results](data/agents_20260211_025405.json)*

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- (Optional) GitHub token for higher rate limits

### Installation

```bash
# Clone the repository
git clone https://github.com/yourname/agent-highway.git
cd agent-highway

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure GitHub token for better rate limits
export GITHUB_TOKEN="your_token_here"
```

### Run the Collector

```bash
# Run GitHub collector (works without API token!)
python -m collectors.github

# Or use the unified runner
python -m highway.collect --source github
```

### Launch Dashboard

```bash
# Terminal dashboard
python -m highway.dashboard

# Or use run.py
python run.py dashboard
```

## 📊 Capabilities

### Working Collectors

| Collector | Status | Rate Limit | Auth Required |
|-----------|--------|------------|---------------|
| GitHub | ✅ Production | 60/hr (5000/hr w/ token) | Optional |
| OpenClaw | ✅ Production | N/A | No |
| Discord | 🚧 Planned | N/A | Yes |
| Telegram | 🚧 Planned | N/A | Yes |

### Detection Methodology

Agent Highway uses multi-factor confidence scoring:

1. **Metadata Analysis** (20%) - Description, topics, keywords
2. **README Analysis** (40%) - Content patterns, framework mentions
3. **Code Analysis** (40%) - Config files, dependencies, patterns

**Confidence Threshold:** 0.5+ for agent classification

## 📁 Project Structure

```
agent-highway/
├── README.md                 # This file
├── requirements.txt          # Dependencies
├── run.py                    # CLI entry point
├── highway/                  # Core system
│   ├── collect.py           # Unified collector runner
│   ├── process.py           # Stream processing
│   ├── detect.py            # Agent detection
│   ├── dashboard.py         # Terminal dashboard
│   ├── core.py              # Main orchestrator
│   └── storage.py           # Data persistence
├── collectors/              # Data collectors
│   ├── github.py           # GitHub agent collector ⭐
│   └── openclaw.py         # OpenClaw scanner ⭐
├── insights/                # Intelligence layer
│   ├── network.py          # Network analysis
│   ├── trends.py           # Trend analysis
│   └── swarms.py           # Swarm detection
├── data/                    # Discovered agents
│   └── agents_*.json       # Collection outputs
└── tests/                   # Test suite
```

## 🔧 Configuration

```yaml
# config/highway.yaml
highway:
  name: "Agent Highway"
  version: "1.0.0"
  
collectors:
  github:
    enabled: true
    rate_limit: 5000/hour
    search_queries:
      - "AI agent autonomous"
      - "LLM agent framework"
      - "langchain agent"
      - "autogen agent"
      
  openclaw:
    enabled: true
    scan_github: true

detection:
  confidence_threshold: 0.6
  min_signals: 3
  
storage:
  type: "json"
  path: "./data"
```

## 🎮 Commands

```bash
# Collection
python run.py collect --source github
python run.py collect --source openclaw
python run.py collect --all

# Analysis
python run.py analyze --network
python run.py analyze --trends

# Dashboard
python run.py dashboard

# Full status
python run.py status
```

## 🔌 Integration Example

```python
from highway import AgentHighway

# Initialize
highway = AgentHighway()

# Collect from GitHub
await highway.collect(source="github")

# Query agents
agents = highway.query(
    min_confidence=0.6,
    agent_type="autonomous_agent"
)

print(f"Found {len(agents)} high-confidence agents")
```

## 🧪 Testing

See [TESTING.md](TESTING.md) for verification steps and test procedures.

```bash
# Run all tests
pytest tests/

# Run specific collector test
pytest tests/test_github_collector.py -v

# Live test (actually queries GitHub)
pytest tests/test_github_collector.py::test_live_collection -v
```

## 🗺️ Roadmap

### Phase 1: Foundation ✅ 
- [x] GitHub collector with confidence scoring
- [x] OpenClaw scanner
- [x] Terminal dashboard
- [x] JSON storage
- [x] Basic test suite

### Phase 2: Expansion (Current)
- [ ] Discord collector
- [ ] Telegram collector
- [ ] Web-based dashboard
- [ ] SQLite storage option

### Phase 3: Intelligence (Planned)
- [ ] ML-based detection models
- [ ] Network analysis
- [ ] Trend prediction
- [ ] Swarm detection

### Phase 4: Scale (Future)
- [ ] Distributed collectors
- [ ] Real-time streaming
- [ ] Public API
- [ ] Community submissions

## 🤝 Contributing

Contributions welcome! Areas we need help:

1. **New Collectors** - Discord, Telegram, PyPI, npm
2. **Detection Improvements** - Better ML models, more signals
3. **Dashboard** - Web UI improvements
4. **Documentation** - Tutorials, examples

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 🛡️ Security & Ethics

- **Passive Only**: No active exploitation or unauthorized access
- **Public Data**: Only collect publicly available information
- **Rate Limited**: Respect API limits and service terms
- **Privacy First**: Anonymize where possible
- **Transparent**: Open source methodology

## 📜 License

MIT - See [LICENSE](LICENSE)

---

**Last Verified:** 2025-02-10 | [View Test Results](data/agents_20260211_025405.json)

*Mapping the autonomous future, one agent at a time.* 🛣️🤖
