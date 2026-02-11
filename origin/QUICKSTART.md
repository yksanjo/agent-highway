# 🚀 Agent Highway Origin - Quick Start

Get up and running in 5 minutes.

## Prerequisites

- Node.js 18+
- Cloudflare account
- Python 3.9+ (for SDK)

## Step 1: Deploy the Worker (2 minutes)

```bash
cd agent-highway-origin
npm install
npx wrangler login  # If not already authenticated
npx wrangler deploy
```

Your worker is now live at `https://agent-highway-origin.YOUR_SUBDOMAIN.workers.dev`

## Step 2: Test the Endpoint (1 minute)

```bash
curl -X POST https://agent-highway-origin.YOUR_SUBDOMAIN.workers.dev/beacon \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent",
    "agent_type": "test",
    "timestamp": '$(date +%s000)',
    "event_type": "birth",
    "sequence": 1,
    "signature": "test",
    "public_key": "test"
  }'
```

## Step 3: View the Dashboard (1 minute)

Open in browser:
```
https://agent-highway-origin.YOUR_SUBDOMAIN.workers.dev/agents/live
```

## Step 4: Install Python SDK (1 minute)

```bash
cd agent-highway
pip install -r requirements-beacon.txt
```

## Step 5: Run an Example Agent

```python
# test_agent.py
import asyncio
from highway.beacon import AgentBeacon, BeaconConfig

async def main():
    config = BeaconConfig(
        endpoint="https://agent-highway-origin.YOUR_SUBDOMAIN.workers.dev",
        lane="demo"
    )
    
    async with AgentBeacon("my-first-agent", "demo", config=config) as beacon:
        await beacon.start_heartbeat()
        await beacon.task_start("hello-world")
        print("Hello from agent!")
        await asyncio.sleep(2)
        await beacon.task_complete("hello-world")

asyncio.run(main())
```

Run it:
```bash
python test_agent.py
```

Watch the dashboard update in real-time! 🎉

## Next Steps

- Try the [examples](examples/) for more use cases
- Integrate the React dashboard into your AgentChat
- Configure multiple lanes for different protocols

## Troubleshooting

### Worker not responding
Check wrangler logs: `npx wrangler tail`

### Python can't connect
Verify the endpoint URL and check your internet connection

### No data in dashboard
Ensure agents are emitting beacons with correct timestamps (in milliseconds)
