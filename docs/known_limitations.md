# Known Limitations

These are deliberate non-critical flaws. They make the harness useful for HALO analysis without making the demo unusable.

## Source Quality Is Heuristic

`assess_source` scores domains with simple rules. It can overrate weak pages on institutional domains and underrate high-quality independent research.

## Scratchpad State Is Loose

The scratchpad stores plain text notes. There is no schema for evidence, claims, source IDs, or confidence. This makes it easy for stale or vague notes to influence the final answer.

## Final Output Is Not Enforced

The prompt asks for sections, sources, and uncertainty, but there is no structured output schema or validator. This can produce inconsistent final answers.

## Date Handling Is Weak

The agent is told to be careful with current information, but there is no dedicated date normalization tool. Current or relative-date questions can still be answered with stale evidence.

## Search Deduplication Is Minimal

The harness does not canonicalize URLs or cluster near-duplicate sources. Repeated results can waste tool calls and bias the synthesis.

## Claim Comparison Is Shallow

`compare_claims` only compares lexical overlap. It can miss contradiction, implication, or agreement when two claims use different wording.

## Extraction Is Truncated

`extract_page` caps content to control cost and context size. Important evidence can be outside the returned slice.
