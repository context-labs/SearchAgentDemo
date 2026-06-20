# HALO Search Agent Example

This repo is a compact public demo for collecting OpenTelemetry traces from a search agent and reviewing those traces with HALO.

The agent uses the OpenAI Agents SDK, a LiteLLM-compatible model endpoint, Tavily search, and Inference.net tracing. It is intentionally smaller than a deep research harness, but it still has enough tool use, scratchpad state, source extraction, and prompt surface area to make trace analysis useful.

## What This Demonstrates

- A single OpenAI Agents SDK agent with multi-turn tool calling.
- Inference.net tracing with `setup()`, an outer `agent_span()`, and manual child spans inside search tools.
- Tavily web search and page extraction behind low default result caps.
- A deterministic mock search mode for local testing without Tavily usage.
- A 50-query starter dataset for collecting comparable traces.
- Documented non-critical flaws that HALO should be able to critique.

## Repository Layout

```text
src/search_agent_example/
  agent.py          Agent definition and instructions
  tools.py          Scratchpad, search, extract, source scoring, and claim comparison tools
  search_clients.py Tavily and mock search clients
  cli.py            Single-query traced runner
  batch.py          Dataset traced runner
data/queries.jsonl  50 starter queries
docs/               HALO notes and known limitations
tests/              Unit tests that avoid network and model calls
```

## Setup

Install dependencies with uv:

```bash
uv sync --extra dev
```

Create `.env` from `.env.example` and set:

```bash
LITELLM_BASE_URL=https://lllm.inference.net/v1
LITELLM_API_KEY=...
LITELLM_MODEL_ID=openai/gpt-5.4-mini
TAVILY_API_KEY=...
INFERENCE_NET_API_KEY=...
```

`INFERENCE_NET_API_KEY` is copied into `CATALYST_OTLP_TOKEN` at startup if `CATALYST_OTLP_TOKEN` is not already set. The default trace endpoint is `https://telemetry.inference.net`.

## Run One Query

Use real Tavily search:

```bash
uv run search-agent "What are the latest CISA recommendations for defending against ransomware?"
```

Use mock search for a cheap smoke test:

```bash
uv run search-agent "What changed in the latest Python release?" --mock-search
```

The command prints the final answer and the trace `session_id`. The same `session_id` appears in Inference.net so runs can be grouped in the dashboard.

## Run The Dataset

Start with a small limit to control model and search spend:

```bash
uv run search-agent-batch --limit 3
```

Use mock search when testing the runner shape:

```bash
uv run search-agent-batch --limit 3 --mock-search
```

Each dataset row gets a stable session ID like `dataset-q001` and trace attributes for `demo.query_id`, `demo.category`, and `demo.dataset`.

## Agent Tools

- `scratchpad_write`: stores short planning notes and observations.
- `scratchpad_read`: reads recent notes for final synthesis.
- `web_search`: calls Tavily search with capped results and a retriever span.
- `extract_page`: calls Tavily extract with a character cap and a retriever span.
- `assess_source`: applies a simple source-quality heuristic.
- `compare_claims`: does a deliberately shallow lexical comparison between two claims.

## Trace Shape

The CLI initializes Inference.net tracing, builds the agent, and wraps each run in an `agent_span()` with stable metadata. The OpenAI Agents SDK instrumentation captures agent runs, model calls, and tool calls. The Tavily calls inside tools add manual retriever spans so the dashboard shows both the tool invocation and the downstream search or extract step.

The example removes the OpenAI Agents SDK default trace exporter after Inference.net instrumentation is installed. That keeps the demo from trying to export traces to OpenAI's hosted trace backend when it is using a LiteLLM-compatible gateway.

## Tests

Tests avoid network and model calls:

```bash
uv run pytest
uv run ruff check .
```

## Cost Controls

- Default Tavily search depth is `basic`.
- Search results are capped at five by default.
- Extracted page content is capped at 6000 characters.
- Dataset runs default to three queries.
- Mock search is available for smoke tests and CI.

## HALO Usage

1. Run a representative sample from `data/queries.jsonl`.
2. Inspect grouped traces in the Inference.net dashboard.
3. Export or point HALO at the trace set.
4. Let HALO identify repeated failure modes in planning, search choice, source quality, or final synthesis.
5. Apply harness changes, collect another trace batch, and compare reports.

See `docs/halo.md` and `docs/known_limitations.md` for more detail.
