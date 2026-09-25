# Lab 2 — Add a token quota

Limit how many tokens each caller can use per time window, without changing routing.

## Before you start

- Lab 1 working, plus its source folder, deployed revision and test results. Give all three to the agent: configuration alone isn't the previous implementation.
- Callers use API keys (VerifyAPIKey). The limit lives on the **API product**, not in the proxy, so you need permission to edit the product.

## Prompt

```text
Add a limit of 100 tokens per caller to the Lab 1 gateway.

Save a new source bundle and ZIP in ./ai-gateway/lab-2, with
deployment steps and a small test plan.
```

## What you get

- A new bundle, with routing unchanged
- The quota contract:
  - window and reset
  - which usage field is counted
  - per-caller or per-model scope
  - what happens when a response has no usage data
- The API product settings to change

Tokens are counted after each call, so a caller can overshoot slightly. This is **not a hard spend ceiling**.

## Deploy

1. **Set the quota on the API product.** Set the LLM token quota limit, interval and time unit on the product your test app uses ([API product setup](../references/api-product-setup.md)). Read the values back, then wait a few minutes for the product cache to refresh.
2. **Review the diff.** Routing and authentication are unchanged, no limit is hardcoded in the proxy, and each call is counted once.
3. **Import and deploy** the new revision. Keep the Lab 1 bundle.

## Smoke test

- A few short calls succeed.
- Keep calling until the tokens run out. The next call is rejected by the gateway (normally `429`) without reaching the backend. Don't confuse this with a `429` from the backend itself.
- After the window resets, calls succeed again.
- Change the limit on the product only. Enforcement changes with no redeploy.

Stop at your agreed call and cost limit, even if the quota hasn't run out.

## Full checks

See the [quota acceptance cases](../references/token-quota.md#live-acceptance) and [quota semantics and limitations](../references/token-quota.md#enforcement-semantics).

## If it fails

| Symptom | Likely cause |
|---|---|
| Product limit ignored | Check three things: the VerifyAPIKey policy name in the quota policies matches the step that runs; you edited the product the app actually uses; the product cache has refreshed. |
| Quota never runs out | Check that usage is extracted from the response and counted, and check the counter scope. Don't just send more traffic. |
| Quota error shows as `502` | Existing error handling is catching the fault. |

**Next:** [Lab 3 — Add a spending budget](lab-3-spending-budget.md)

[Back to the README](../README.md)
