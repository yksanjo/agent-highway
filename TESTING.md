# Testing Agent Highway

This document describes how to verify that Agent Highway works correctly.

## Quick Verification (30 seconds)

```bash
# 1. Clone and enter
cd agent-highway

# 2. Install deps
pip install -r requirements.txt

# 3. Run GitHub collector (no API key needed!)
python -m collectors.github
```

**Expected output:**
```
🔍 Starting GitHub agent discovery (max 20 repos)...
📦 Found 20 potential repositories
  ✅ Found agent: [name] (confidence: X.XX)
  ...
🎯 Total agents discovered: N
```

## Full Test Suite

### Unit Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=highway --cov=collectors
```

### Collector Tests

#### GitHub Collector

```bash
# Basic functionality test
python -c "
import asyncio
from collectors.github import GitHubAgentCollector

async def test():
    async with GitHubAgentCollector() as collector:
        agents = await collector.collect(max_repos=5)
        assert len(agents) >= 0, 'Should complete without error'
        print(f'✅ Found {len(agents)} agents')

asyncio.run(test())
"
```

#### With GitHub Token (Optional)

```bash
export GITHUB_TOKEN="your_token"
python -m collectors.github
# Should have higher rate limit (5000/hr vs 60/hr)
```

### Dashboard Test

```bash
# Terminal dashboard
python -m highway.dashboard

# Expected: Rich terminal UI with stats and recent agents
# Press Ctrl+C to exit
```

## Manual Verification Checklist

- [ ] `pip install -r requirements.txt` completes without errors
- [ ] `python -m collectors.github` finds at least 1 agent
- [ ] `python -m highway.dashboard` shows terminal UI
- [ ] Data files created in `./data/` directory
- [ ] JSON output is valid and contains agent data

## Troubleshooting

### Rate Limit Errors

```
⚠️  Rate limit hit, waiting...
```

**Solution:** Set `GITHUB_TOKEN` environment variable for 5000 requests/hour.

### Import Errors

```
ModuleNotFoundError: No module named 'highway'
```

**Solution:** Run from project root (`agent-highway/` directory).

### No Agents Found

Check that you have internet connectivity and GitHub is accessible:

```bash
curl https://api.github.com/rate_limit
```

## Performance Benchmarks

Tested on:
- **Scanning 20 repos:** ~30 seconds
- **Scanning 100 repos:** ~2 minutes
- **Memory usage:** <100MB
- **Disk per run:** ~50KB JSON output

## Continuous Integration

Tests run automatically on:
- Every push to `main`
- Every pull request

See `.github/workflows/test.yml` for CI configuration.
