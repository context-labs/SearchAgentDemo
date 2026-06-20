# HALO Notes

HALO works best when the trace set contains repeated behavior across varied tasks. This repo gives you a small, repeatable search harness that can generate those traces without being a full deep research system.

## Recommended Trace Collection

Run a focused slice first:

```bash
uv run search-agent-batch --limit 5
```

Then run category slices by changing `--start` and `--limit`:

```bash
uv run search-agent-batch --start 20 --limit 5
```

Use at least 20 real-search traces before drawing conclusions. Mock-search traces are useful for verifying instrumentation, but they are too uniform for serious harness analysis.

## What HALO Should See

The trace tree should include:

- An outer `AGENT` span named `traceable-search-agent.run` or `traceable-search-agent.dataset_run`.
- OpenAI Agents SDK spans for the agent loop, model calls, and tool calls.
- Manual `RETRIEVER` spans named `tavily.search` and `tavily.extract`.
- Session grouping through `session_id`.
- Query metadata on dataset runs.

## Useful Questions For HALO

- Does the agent search too broadly before narrowing the task?
- Does it extract pages when snippets are insufficient?
- Does it over-trust the source-quality heuristic?
- Does it use the scratchpad as working memory or just as a ritual step?
- Does it surface uncertainty when sources conflict?
- Does the final answer cite enough concrete source identifiers?

## Expected Iteration Pattern

1. Collect traces.
2. Run HALO over the grouped traces.
3. Feed the HALO report to a coding agent.
4. Apply prompt, tool, or harness changes.
5. Re-run the same dataset slice.
6. Compare failure modes across iterations.
