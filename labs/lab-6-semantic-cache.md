# Lab 6 — Reuse answers to similar FAQ questions (optional)

Trial semantic caching for one test app and one fixed model, so repeated or reworded FAQ questions can reuse an earlier answer. Caching stays **disabled by default** until the trial gate below passes.

## Before you start

- A working bundle that includes [Lab 4](lab-4-model-armor.md) Model Armor. This workflow relies on its prompt and response safeguards.
- Answers must be non-sensitive and safe to share with **every** eligible caller. A short cache lifetime doesn't make confidential answers safe.
- **New costs and a new processing location:** Vertex AI embeddings, plus a Vector Search index and endpoint. You don't need any of these to start planning; the agent can guide the [Vertex setup from zero](../references/semantic-cache-vertex-setup.md).
- Agree the region and data residency before running any setup commands. There's no default region.

## Prompt

```text
Add caching so the gateway can reuse answers to similar FAQ-style
questions and save cost.

Save the proposed changes in ./ai-gateway/lab-6, with deployment
steps and a small test plan.
```

## What you get

- A disabled-by-default trial proposal
- A prerequisite handoff
- A test plan

Similarity thresholds such as `0.90` or `0.95` are candidate cutoffs to test, not accuracy guarantees.

## Deploy

1. **Complete the [pre-import handoff](../references/semantic-cache.md#manual-pre-import-handoff).** If you have no Vertex resources yet, set them up one approved step at a time with the agent.
2. **Review the diff.** Keep the previous bundle.
3. **Import and deploy** the new revision with the chosen service account, but only once the deployment and trial are approved. Set up masking before any test calls.
4. **Agree a cost cap, a cleanup owner and a rollback.** Disabling cache lookup and population rolls back traffic, but doesn't stop the index's ongoing charges.

## Smoke test (the trial gate)

- A new question is a miss and calls the backend.
- The exact repeat is a hit and doesn't call the backend.
- A paraphrase is a hit.
- A near-but-wrong question is a miss.

**Go/no-go:** on a hit, the answer still gets its safety inspection, nothing new is cached, and the caller's quota isn't charged for the cached answer. If any of these fail, leave caching disabled.

## Full checks

See the [cache trial and enablement checklist](../references/semantic-cache.md#cache-trial-and-enablement-checklist).

## If it fails

| Symptom | Likely cause |
|---|---|
| Close match found but no answer returned | The vector matched but the cached answer expired or is missing. |
| Lookup or populate errors | Check the runtime service account, the exact index/endpoint/deployment IDs, and the embedding model and dimensions. |
| Wrong answer served | Revisit eligibility and the threshold, not just the cache lifetime. |
| Charges after rollback | The index keeps charging until you clean it up, with approval. |

**Back to:** [README](../README.md)
