# Feature status

What this skill covers today and how far each capability has been tested. Use it to set expectations, then run each lab's smoke test and full checks against your own Apigee X environment.

## What the statuses mean

- **Tested on Apigee X:** the generated proxy has been deployed and exercised on Apigee X, including the lab's main acceptance cases.
- **Checked offline:** the example XML, scripts and flow fragments pass this repository's tests, but the current design hasn't yet been run end to end on Apigee X.
- **Trial:** ships disabled by default. Enable it only after its trial checklist passes in your environment.
- **Not implemented:** out of scope for this version. Requests that need it are rejected, not silently handled.

Offline checks cover structure and example consistency. They don't run Apigee policies, validate IAM or prove filter behaviour.

## Current status

| Capability | Status | Notes |
|---|---|---|
| Model routing | Tested on Apigee X | Non-streaming, OpenAI-compatible chat completions. Callers choose approved aliases; each maps to a backend model ID. |
| Caller and backend authentication | Tested on Apigee X | API-key callers (VerifyAPIKey); backend credential read at runtime from an encrypted KVM. Other mechanisms need their own design. |
| Accumulated token quota | Tested on Apigee X | Limit, interval and time unit come from the API product. Both quota policies key on the backend model ID. |
| Cost budget | Checked offline | Prices and budget are API product custom attributes. Synthetic test prices demonstrate enforcement, not real billing. |
| Prompt-token burst protection | Tested on Apigee X | PromptTokenLimit sliding window within a region. Not a hard per-request or spend limit. |
| Model Armor | Tested on Apigee X | Prompt and response inspection for text-only, single-turn requests. Blocks matches and incomplete inspection; doesn't redact. |
| FAQ semantic caching | Trial | Disabled by default. Follow the [trial checklist](semantic-cache.md#cache-trial-and-enablement-checklist) before enabling. |
| Anthropic Messages format | Not implemented | Use an OpenAI-compatible backend or gateway. |
| Streaming | Not implemented | Requests with `stream: true` are rejected. |
| Fallback between models | Not implemented | Unknown or unavailable aliases return an error. |
