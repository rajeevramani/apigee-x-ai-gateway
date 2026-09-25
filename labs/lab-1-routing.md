# Lab 1 — Route between models

Expose one gateway endpoint where callers pick a model by alias, with separate caller and backend authentication.

The [Quickstart](../README.md#quickstart-your-first-routed-call) walks through this lab step by step. This page adds the options, the full checks and troubleshooting.

## Before you start

- An Apigee X test environment and an approved **non-streaming, OpenAI-compatible** chat completions backend with two exact model IDs.
- The backend key in an **encrypted environment KVM**, or ask the agent for setup steps. Copy the KVM map and entry names exactly, including case. If one doesn't exist yet, tell the agent "setup needed".
- Two terms the agent will use:
  - **Model alias:** the `model` value callers send, such as `fast`.
  - **Backend model ID:** the exact upstream model ID it maps to. Callers can only choose aliases, never arbitrary URLs or credentials.

## Prompt

Use the [Quickstart prompt](../README.md#3-ask-the-agent-to-build-it). You don't need a configuration file: the agent asks for what it needs.

**Shortcut:** copy [`lab-config.example.md`](../lab-config.example.md) to a private location, fill in what you know, give the agent its path, and ask it to confirm it read everything.

## What you get

- The agreed alias → model mapping, and what happens for a missing or unknown alias (rejected, never a silent fallback)
- Proxy source, an importable ZIP and local check results
- Setup steps for the API product and developer app that give you a caller key ([API product setup](../references/api-product-setup.md))
- A short test plan

## Deploy

1. **Review the bundle.** Check that:
   - `apiproxy/` is at the ZIP root
   - no placeholders or secrets are left
   - the backend key is read from the KVM at runtime, not stored in the bundle
2. **Set up.** Store the backend key and create the API product and app, using the agent's steps.
3. **Import and deploy** the exact revision ([Quickstart step 4](../README.md#4-deploy)), then confirm the deployment is ready.

## Smoke test

Run [Quickstart step 5](../README.md#5-smoke-test). Keep the `lab-1` folder, because Lab 2 builds on it.

## Full checks

The [routing acceptance cases](../references/model-routing.md#acceptance-cases) go further than the smoke test:

- **Routing evidence.** For each alias, show the outgoing mapped model and target path. A model describing itself isn't evidence.
- **Rejected before the backend.** Unknown aliases, streaming requests and caller-auth failures are rejected without calling the backend. A status code alone doesn't prove that.
- **Credentials stay separate.** The caller's key is never forwarded to the backend, and the backend credential never appears in responses.

## If it fails

| Symptom | Likely cause |
|---|---|
| Backend `404` | Path is duplicated in the target URL. Check the TargetEndpoint's effective URL. |
| Backend `401/403` | Wrong KVM map or entry name, key not populated, or credential inserted in the wrong order. Don't paste the key into chat. |
| `200`, but you can't tell which model answered | Routing isn't verified yet. See the [routing workflow](../references/model-routing.md). |

**Next:** [Lab 2 — Add a token quota](lab-2-token-quota.md)
