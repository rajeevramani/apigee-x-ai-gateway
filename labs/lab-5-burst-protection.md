# Lab 5 — Protect against prompt-token bursts (optional)

Rate-limit how many prompt tokens callers can send over time, using the native PromptTokenLimit policy. Routing, the token quota and Model Armor (if you added it) stay as they are.


## Before you start

- A working bundle from an earlier lab, plus its source folder, deployed revision and test results. Model Armor isn't required.
- Check that PromptTokenLimit is available to you, and the licence and cost implications of Extensible policies.
- You don't need to arrive with a rate. The agent helps you choose one.

## Prompt

```text
Stop callers from sending big bursts of prompt tokens through the gateway.

Save a new source bundle and ZIP in ./ai-gateway/lab-5, with
deployment steps and a small test plan.
```

## What you get

- A new bundle and a burst contract:
  - the rate (tokens per second or minute)
  - per-caller or shared
  - which prompt text is counted
  - how invalid input is handled
- Your existing chat contract, unchanged. The agent shouldn't quietly count only the last message.

On Apigee X this uses a sliding window within a region. The policy's count isn't guaranteed to match the provider's token usage. It isn't a per-request context-window limit or a hard spend limit, so keep the Lab 2 quota.

## Deploy

1. **Agree the rate, scope and test bounds.** Keep test traffic away from production counters.
2. **Review the diff.** Check the policy order relative to quota and Model Armor ([workflow](../references/prompt-token-limit.md)). A later rejection can still use up burst allowance.
3. **Import and deploy** the new revision.
4. **Mask sensitive variables** before capturing traces, including `ratelimit.PTL-ProtectPromptBurst.resolvedUserPrompt`.

## Smoke test

- Normal traffic below the rate passes.
- A bounded burst is rejected by the gateway's rate limit (`PromptTokenLimitViolation`) without reaching the backend. A quota, Model Armor or upstream `429` doesn't count.
- Calls recover as the window slides. Don't expect a fixed-minute reset.

Stop at your agreed budget even if you don't reach the rejection. Mark it unverified instead of sending more traffic.

## Full checks

See the [live acceptance cases](../references/prompt-token-limit.md#check-the-bundle-then-test-live).

## If it fails

| Symptom | Likely cause |
|---|---|
| Never rejected | Check the policy attachment, which text is counted, and the caller grouping. Provider usage isn't the policy's count. |
| Wrong `429` | Check the native fault and error-rule precedence, not the status code alone. |
| Calculation errors | Missing text or calculation failures aren't rate exhaustion. |

**Next:** [Lab 6 — Reuse answers to similar FAQ questions](lab-6-semantic-cache.md) (optional)

[Back to the README](../README.md)
