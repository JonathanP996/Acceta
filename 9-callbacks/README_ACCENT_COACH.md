# AccentCoachAgent - Using ADK Model Callbacks

## Why `before_after_model` is Perfect for AccentCoachAgent

The `before_after_model` example is the best fit for AccentCoachAgent because:

### 1. **before_model_callback** - Process Input Data
- Intercepts requests **before** they reach the LLM
- Perfect for processing the pronunciation JSON payload:
  - Extract phoneme deviations
  - Analyze acoustic features
  - Build comprehensive prompt with context
  - Add user history to the request

### 2. **after_model_callback** - Transform Output
- Intercepts responses **after** the LLM generates them
- Perfect for transforming natural language feedback into structured JSON:
  - Parse the model's text response
  - Extract feedback points
  - Structure into the required output format
  - Add exercise recommendations
  - Generate TTS-ready text

## How It Works for AccentCoachAgent

```
User Input (JSON) 
  ↓
before_model_callback:
  - Parse JSON payload
  - Analyze phoneme deviations
  - Build detailed prompt
  - Add context to request
  ↓
LLM (Gemini)
  ↓
after_model_callback:
  - Extract feedback from response
  - Structure into JSON
  - Add exercises
  - Generate TTS text
  ↓
Structured Output (JSON)
```

## Running the Agent

```bash
cd /Users/jsmat/gaTech/AI@GT/agent-development-kit-crash-course/9-callbacks
source ../.venv/bin/activate
adk web .
```

Then open the web UI and select `before_after_model` agent.

## Next Steps

We'll modify `before_after_model/agent.py` to:
1. Accept pronunciation JSON in `before_model_callback`
2. Process phoneme deviations and build prompt
3. Transform LLM response to structured JSON in `after_model_callback`

