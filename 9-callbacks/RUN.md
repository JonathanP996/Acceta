# Running the AccentCoachAgent (ADK)

## Quick Start

```bash
cd /Users/jsmat/gaTech/AI@GT/agent-development-kit-crash-course/9-callbacks
source ../.venv/bin/activate
adk web . --port 8001
```

Then open: **http://localhost:8001**

## If Port 8000 is Busy

The default port is 8000. If it's in use, use a different port:

```bash
adk web . --port 8001
# or
adk web . --port 8080
```

## Using the Web UI

1. Open http://localhost:8001 in your browser
2. Select `before_after_model` from the agent dropdown
3. Test the agent with sample queries

## Current Agent

The `before_after_model` agent demonstrates:
- **before_model_callback**: Processes requests before LLM
- **after_model_callback**: Transforms responses after LLM

This is perfect for AccentCoachAgent because we can:
1. Process pronunciation JSON in `before_model_callback`
2. Transform feedback into structured JSON in `after_model_callback`

