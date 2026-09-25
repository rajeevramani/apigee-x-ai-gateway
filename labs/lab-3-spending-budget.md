# Lab 3 — Add a spending budget

Limit how much each caller can spend on model calls, using prices and a budget kept on the API product. Routing doesn't change. The Lab 2 token quota stays, with a higher limit.


## Before you start

- Lab 2 working, plus its source folder, deployed revision and test results.
- Input and output prices per million tokens for each alias. Use real contract prices, or clearly labelled **synthetic** test prices.
- Permission to set custom attributes on the API product your test app uses.

## Prompt

```text
Limit how much each caller can spend on model calls through the gateway.

The Lab 2 limit of 100 tokens per caller would reject test calls before
the spending budget is reached. Give me instructions to raise the token limit
on the API Product enough for the budget to be tested, including any applicable
operation-level overrides. Do not change the token quota policies.

Save a new source bundle and ZIP in ./ai-gateway/lab-3, with
deployment steps and a small test plan.
```

## What you get

- A new bundle and a cost contract:
  - price source and currency
  - budget and window
  - caller and model scope
  - behaviour when prices or usage are missing
- The list of API product attributes to set
- Instructions to raise the token limit

Cost is counted after each call, so this is **not a hard spending ceiling**. Synthetic prices are never your real bill.

## Deploy

1. **Pick a tiny test budget,** for example $0.01 per hour (`10000` micro-USD).
2. **Set the product custom attributes** the agent lists ([API product setup](../references/api-product-setup.md)):
   - `cost_budget_microusd`, `cost_budget_interval`, `cost_budget_timeunit`
   - `price_input_per_1m_<alias>` and `price_output_per_1m_<alias>` for each alias

   Saving the attribute list **replaces** it, so merge with the existing attributes. A product allows at most 18 custom attributes.
3. **Raise the product's token quota,** including any operation-level overrides, so it doesn't trip before the budget. No redeploy is needed. Read the values back and wait about 3 minutes for the product cache.
4. **Review the diff.**
   - The token quota policies are unchanged.
   - VerifyAPIKey runs before the budget check.
   - Cost is counted once, on successful responses.
5. **Import and deploy** the new revision.

## Smoke test

- A cheap call succeeds, and its cost matches tokens × the product's prices.
- Keep calling until the budget runs out. The next call is rejected before the backend, with a different error from the token quota's.
- Change a price attribute. Calls made about 3 minutes later cost the new amount, with no redeploy.

## Full checks

See the [cost budget acceptance cases](../references/cost-budget.md#live-acceptance).

## If it fails

| Symptom | Likely cause |
|---|---|
| Token-quota error after one or two calls | The Lab 2 token limit is still too low. Raise it on the product, including operation-level overrides. |
| Budget never runs out | Check the attribute names and values, that VerifyAPIKey runs first, that `cost.valid` is true and that the count step runs. |
| Every call rejected at once | A budget attribute didn't resolve. |
| Costs look wrong | Prices must be per 1 million tokens, and alias names must match exactly. |

**Next:** [Lab 4 — Add Model Armor inspection](lab-4-model-armor.md)

[Back to the README](../README.md)
