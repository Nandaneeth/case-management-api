# RAG Failure Log

## Purpose

This log classifies observed failures in the policy RAG pipeline. A failure is
recorded only when an evaluation result, test result, or reproducible runtime
observation provides evidence for it.

## Failure Categories

| Category | Classification guidance |
| --- | --- |
| `ingestion failure` | A policy file cannot be loaded, decoded, or parsed, or required metadata is missing. |
| `preprocessing failure` | Cleaning changes, removes, or corrupts policy content or metadata unexpectedly. |
| `chunking failure` | Chunks are empty, duplicated unexpectedly, lose metadata, or split required evidence in a way that prevents retrieval. |
| `retrieval failure` | Relevant evidence or the expected policy is not returned for a supported question, or irrelevant evidence is ranked as relevant. |
| `context assembly failure` | Retrieved evidence is lost, malformed, duplicated, or incorrectly formatted before generation. |
| `generation failure` | The provider fails, returns unusable output, or produces an answer unsupported by the supplied context. |
| `citation failure` | The answer uses evidence but omits, misstates, or cites the wrong policy source. |
| `refusal failure` | The system answers without sufficient evidence or refuses a question when sufficient evidence is available. |

## Observed Failure Register

No evaluation failure records are currently available. The retrieval evaluator
script exists at `evaluation/evaluate_retrieval.py`, but no generated
`retrieval_results.json` output or recorded failed question is present in the
workspace. Consequently, there are no question IDs, observed behaviors, root
causes, improvements, or post-improvement results to document without inventing
evidence.

| Question ID | Observed behavior | Failure category | Likely root cause | Targeted improvement | Result after improvement |
| --- | --- | --- | --- | --- | --- |
| _No observed failures_ | _Not applicable_ | _Not applicable_ | _Not established_ | _Not applicable_ | _Not measured_ |

## Recording Template

When an evaluation run produces a failure, add one record using this structure:

```text
### <question_id> - <short title>

- Observed behavior: <what the evaluation actually returned>
- Failure category: <one category from the table above>
- Likely root cause: <evidence-based cause; distinguish confirmed from suspected>
- Targeted improvement: <small change aimed at that cause>
- Result after improvement: <measured result, or "not yet rerun">
```

The post-improvement field must remain `not yet rerun` until the same evaluation
question is executed again and its result is recorded.