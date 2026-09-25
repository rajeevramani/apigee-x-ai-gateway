# Cost budget — spending limit per caller

Limit how much each caller can spend on model calls. Use two native LLMTokenQuota policies that count **cost in micro-US-dollars** (1 USD = 1,000,000) instead of tokens. The budget and each model's prices live in the **API Product** as custom attributes, so changing a price or budget needs no proxy redeploy. See [capability status](capability-status.md).

This builds on the [token quota workflow](token-quota.md): the same enforce-then-count pattern, overshoot and counter-scope questions apply. It is not a hard spending ceiling.

## Ask these questions first, then wait

Before writing any file, ask every question below that the user or existing configuration hasn't already answered. **Stop and wait for the answers.** Only continue without an answer if the user explicitly says to use your recommendation.

| Decision | Question to ask | Recommendation |
|---|---|---|
| Cost source | Does the backend return a cost for each call, or should cost be worked out from token counts and prices? | Tokens × prices, unless a trusted backend cost field is confirmed from a real response. |
| Prices | What are the input and output prices per 1 million tokens for each caller alias, and in which currency? | Ask the user. Never invent or look up prices yourself. |
| Budget and window | How much may a caller spend, over what period (minute, hour, day, week, month)? | Small test budget (for example $0.01 per hour) for the lab. |
| Who shares a budget | Per verified caller (app/API key), or shared? | Per verified caller. |
| Models | One budget across all aliases, or separate per alias? | One shared budget; verify it live (see acceptance). |
| Token quota | Keep the Lab 2 token quota as well, or replace it? | Keep both, with separate counter names. |
| Token limit size | The existing token quota allows N tokens per window (read N and the window from the API Product, including applicable operation-level overrides). Using up the budget needs up to M tokens (see [the check](#check-the-token-quota-against-the-budget)). If N is lower than M, what higher API Product token limit should the user set? | Provide instructions for the user to raise it above M on the API Product, so the budget is reached first during testing. |
| Missing cost | If usage or a price is missing, block the response, allow it without counting, or something else? | Ask; never count it as zero silently. |
| Over budget | Which error should callers get? | Sanitized 429 with its own error code. |
| Test bounds | How many test calls and what output limit? | Few calls, small output limit. |

If an answer is still missing when you build, leave the matching `__PLACEHOLDER__` visible and say plainly in the handoff that the bundle is **not ready to import**.

## How it works

1. **Request:** VerifyAPIKey verifies the caller and exposes the API Product's custom attributes. A guard rejects the call if the budget attributes are missing. `LTQ-CostEnforce` checks whether this caller's spending so far is already over budget.
2. **Response:** `JS-CalculateCost` reads `usage.prompt_tokens` and `usage.completion_tokens` from the OpenAI-compatible response and the alias's prices from the product, and sets `cost.microusd` (rounded up) and `cost.valid`.
3. `LTQ-CostCount` adds `cost.microusd` to the same counter.

Prices are stored as **USD per 1 million tokens**, which is numerically the same as **micro-USD per token**. So cost in micro-USD = prompt tokens × input price + completion tokens × output price.

## Check the token quota against the budget

When the bundle already has a token quota, both limits apply to every call, and the smaller one rejects first. A Lab 2 limit of 100 tokens is used up in one or two calls, so the caller gets the token quota's 429 and the budget is never reached.

1. Read the token limit and window from the caller's API Product (`llmQuota`, `llmQuotaInterval`, `llmQuotaTimeUnit`), including any applicable `llmOperationGroup` operation-level `llmTokenQuota` overrides. If the product configuration is unavailable, ask the user for it.
2. Work out the most tokens the budget can pay for: budget in micro-USD ÷ the lowest price per token among the aliases. Example: `10000` ÷ `3.00` ≈ 3,334 tokens.
3. If the token limit is lower than that, explain that the token quota will reject calls first. Give the user instructions to raise the API Product's `llmQuota` to the agreed value, plus any operation-level `llmTokenQuota.limit` overrides, keeping the agreed window. Follow [API product setup](api-product-setup.md): read back the saved configuration and wait about 3 minutes for the product cache before testing. No policy edit or redeploy is needed, and the agent doesn't change the product itself.
4. If the user keeps the lower limit, build anyway and put the warning in the handoff.

## API Product configuration

Set these as custom attributes on the API Product the caller's app uses. The proxy reads them after VerifyAPIKey as `verifyapikey.<VerifyAPIKey policy name>.apiproduct.<attribute name>` ([API product custom attributes][products]).

| Attribute | Value | Example |
|---|---|---|
| `cost_budget_microusd` | Budget per window, whole micro-USD | `10000` ($0.01) |
| `cost_budget_interval` | Whole number of time units | `1` |
| `cost_budget_timeunit` | `minute`, `hour`, `day`, `week` or `month` | `hour` |
| `price_input_per_1m_<alias>` | USD per 1 million input tokens for that caller alias | `price_input_per_1m_sonnet` = `3.00` |
| `price_output_per_1m_<alias>` | USD per 1 million output tokens for that caller alias | `price_output_per_1m_sonnet` = `15.00` |

- An API product can have **at most 18 custom attributes in total**, including attributes set on operations. Three budget attributes plus two per alias allows up to 7 aliases.
- Different products (for example tiers) can carry different budgets and prices.
- Use the exact caller alias names from routing. Prices keyed by alias stay valid if the alias is repointed, but the user must update them when the upstream model or its price changes.
- The cost policies are LLMTokenQuota policies, so the product needs the same `llmOperationGroup` entries as the token quota (see [API product setup](api-product-setup.md#things-that-go-wrong)).
- The operator sets these attributes using [API product setup](api-product-setup.md): check existing attributes, send the full merged list (saving replaces it), read back, and wait about 3 minutes for the product cache before testing. The agent never changes API Products itself.

## Policies

Files: [budget guard](../assets/examples/cost-budget/RF-CostConfigMissing.xml), [enforcement](../assets/examples/cost-budget/LTQ-CostEnforce.xml), [cost calculation policy](../assets/examples/cost-budget/JS-CalculateCost.xml) and [script](../assets/examples/cost-budget/calculate-cost.js), [counting](../assets/examples/cost-budget/LTQ-CostCount.xml), [flow attachments](../assets/examples/cost-budget/proxy-flow-fragment.xml), [fault rule](../assets/examples/cost-budget/cost-budget-fault-fragment.xml), [over-budget response](../assets/examples/cost-budget/AM-CostBudgetExceeded.xml).

Before writing each file, open its development-skill reference and list it in the reference list: [VerifyAPIKey](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/policies_security.md#verifyapikey), [JavaScript policy](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/javascript_development.md#javascript-policy-configuration), [RaiseFault](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/fault_handling.md#raisefault-for-custom-errors), [FaultRules](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/fault_handling.md#faultrules) and [conditions](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/flow_variables_and_conditions.md#condition-syntax). Use the [token quota](token-quota.md#non-streaming-token-quota) reference for LLMTokenQuota.

| Placeholder | Required input |
|---|---|
| `__VERIFY_API_KEY_POLICY__` | Exact name of the existing VerifyAPIKey policy, which must run before these steps. |
| `__VERIFIED_CALLER_VARIABLE__` | Verified caller identity, for example `verifyapikey.<policy name>.client_id`. |
| `__COST_COUNTER_NAME__` | Same counter name in both cost policies; different from the token quota counter. |
| `__SYNCHRONOUS__` | Approved `true`/`false`; recommend `true` for the lab. |
| `__UPSTREAM_MODEL_VARIABLE__` | The same backend-model variable the token quota policies use, set during alias translation. Both cost policies key on it; see [the model key](token-quota.md#both-halves-key-on-the-request-model). |
| `__MODEL_ALIAS_VARIABLE__` | Flow variable holding the caller's alias, set by routing before the response flow (for example the routing ExtractVariables output). |
| `__CALLER_AUTH_POLICY__`, `__REQUEST_VALIDATION_POLICY__` | The existing steps from earlier labs; merge, don't duplicate. |

Example source: `../assets/examples/cost-budget/LTQ-CostEnforce.xml`

```xml
<LLMTokenQuota name="LTQ-CostEnforce">
  <SharedName>__COST_COUNTER_NAME__</SharedName>
  <EnforceOnly>true</EnforceOnly>
  <Allow count="1" countRef="verifyapikey.__VERIFY_API_KEY_POLICY__.apiproduct.cost_budget_microusd"/>
  <Interval ref="verifyapikey.__VERIFY_API_KEY_POLICY__.apiproduct.cost_budget_interval">1</Interval>
  <TimeUnit ref="verifyapikey.__VERIFY_API_KEY_POLICY__.apiproduct.cost_budget_timeunit">month</TimeUnit>
  <Identifier ref="__VERIFIED_CALLER_VARIABLE__"/>
  <Distributed>true</Distributed>
  <Synchronous>__SYNCHRONOUS__</Synchronous>
  <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
  <LLMModelSource>{__UPSTREAM_MODEL_VARIABLE__}</LLMModelSource>
</LLMTokenQuota>
```

The `count="1"`, `1` and `month` literals are fallbacks. The budget guard (`RF-CostConfigMissing`) rejects missing configuration before this policy runs.

Example source: `../assets/examples/cost-budget/JS-CalculateCost.xml`

```xml
<Javascript name="JS-CalculateCost" timeLimit="200" continueOnError="false" enabled="true">
  <Properties>
    <Property name="verifyApiKeyPolicy">__VERIFY_API_KEY_POLICY__</Property>
    <Property name="modelAliasVariable">__MODEL_ALIAS_VARIABLE__</Property>
  </Properties>
  <ResourceURL>jsc://calculate-cost.js</ResourceURL>
</Javascript>
```

The script ([calculate-cost.js](../assets/examples/cost-budget/calculate-cost.js)) goes in `apiproxy/resources/jsc/`. It is ECMAScript 5.1, rounds up to whole micro-USD, and sets `cost.valid` to `false` when the alias, a price or token usage is missing or invalid. It ignores cached-token discounts, so it can over-estimate. Use JavaScript only for this arithmetic.

Example source: `../assets/examples/cost-budget/LTQ-CostCount.xml`

```xml
<LLMTokenQuota name="LTQ-CostCount">
  <SharedName>__COST_COUNTER_NAME__</SharedName>
  <CountOnly>true</CountOnly>
  <Allow count="1" countRef="verifyapikey.__VERIFY_API_KEY_POLICY__.apiproduct.cost_budget_microusd"/>
  <Interval ref="verifyapikey.__VERIFY_API_KEY_POLICY__.apiproduct.cost_budget_interval">1</Interval>
  <TimeUnit ref="verifyapikey.__VERIFY_API_KEY_POLICY__.apiproduct.cost_budget_timeunit">month</TimeUnit>
  <Identifier ref="__VERIFIED_CALLER_VARIABLE__"/>
  <Distributed>true</Distributed>
  <Synchronous>__SYNCHRONOUS__</Synchronous>
  <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
  <LLMTokenUsageSource>{cost.microusd}</LLMTokenUsageSource>
  <LLMModelSource>{__UPSTREAM_MODEL_VARIABLE__}</LLMModelSource>
</LLMTokenQuota>
```

Example source: `../assets/examples/cost-budget/proxy-flow-fragment.xml`

```xml
<!-- Merge guide only. Keep existing routing, auth and token-quota steps. -->
<PreFlow name="PreFlow">
  <Request>
    <Step><Name>__CALLER_AUTH_POLICY__</Name></Step>
    <Step><Name>__REQUEST_VALIDATION_POLICY__</Name></Step>
    <Step>
      <Name>RF-CostConfigMissing</Name>
      <Condition>(verifyapikey.__VERIFY_API_KEY_POLICY__.apiproduct.cost_budget_microusd = null) or (verifyapikey.__VERIFY_API_KEY_POLICY__.apiproduct.cost_budget_interval = null) or (verifyapikey.__VERIFY_API_KEY_POLICY__.apiproduct.cost_budget_timeunit = null)</Condition>
    </Step>
    <Step><Name>LTQ-CostEnforce</Name></Step>
  </Request>
  <Response>
    <Step>
      <Name>JS-CalculateCost</Name>
      <Condition>response.status.code = 200</Condition>
    </Step>
    <Step>
      <Name>LTQ-CostCount</Name>
      <Condition>(response.status.code = 200) and (cost.valid = "true")</Condition>
    </Step>
  </Response>
</PreFlow>
```

## Rules

- **Never invent prices, budgets or attribute values.** Leave them to the operator's product configuration and list exactly what to set.
- **Missing cost is not zero cost.** The fragment only counts when `cost.valid = "true"`. Add the user's agreed handling for `cost.valid = "false"` (for example reject, or allow and report the gap), and say it is an accounting gap.
- **Overshoot is expected.** The budget is checked before a call and counted after it, so in-flight or expensive calls can go over. Say so in the handoff.
- **Budgets are per backend model.** Both cost policies key on the backend model ID, as in [token quota](token-quota.md#both-halves-key-on-the-request-model). Aliases that map to different models get separate budgets; confirm the scope with a live test.
- **Keep counters separate** from the Lab 2 token quota, and keep both working.
- **The smaller limit rejects first.** Run [the token quota check](#check-the-token-quota-against-the-budget) and state the result in the handoff.
- **Order with later labs:** count cost before any response inspection that could block output, because the backend already charged for it.

## Errors and fault handling

- Over budget: native fault `LLMTokenQuotaViolation` (429). Map it with the [fault rule](../assets/examples/cost-budget/cost-budget-fault-fragment.xml), which also checks `ratelimit.LTQ-CostEnforce.failed`, to the [over-budget response](../assets/examples/cost-budget/AM-CostBudgetExceeded.xml). Keep it separate from the token quota's 429 and from upstream 429s.
- Missing budget attributes: `RF-CostConfigMissing` returns a sanitized 500. Its payload must not reveal attribute names or prices.
- `FailedToResolveTokenUsageCount` (500) means `cost.microusd` didn't resolve; the count condition should prevent it. Don't convert it to 429.
- Use only these documented fault names ([LLMTokenQuota runtime errors][ltq]).

## Completion checks

- Every placeholder resolved or explicitly listed as not ready. XML parses; the script is in `resources/jsc/` and listed in the proxy.
- VerifyAPIKey runs before the guard and enforcement; both cost policies share counter name, identity, budget references and window.
- Token quota policies and earlier labs unchanged; any agreed token limit increase is documented as an operator-applied API Product change. The reference list covers every new file.
- The [token quota check](#check-the-token-quota-against-the-budget) is done and its result is in the handoff.
- Exact API Product attribute instructions for the operator, with a small test budget.

## Live acceptance

| Test | Evidence required |
|---|---|
| Below budget | A cheap call succeeds; `cost.microusd` matches tokens × prices from the product. |
| Budget used up | With a tiny budget and a token limit high enough not to reject first, a few cheap calls later get the agreed over-budget 429 before the backend is called (policy attribution, not status alone). |
| Price change | Change a price attribute (operator), wait about 3 minutes for the product cache, repeat one call, and see the new cost used without redeploying. |
| Shared across aliases | Alternate both aliases under one caller and show they drain the same budget; otherwise mark unverified. |
| Missing configuration | A product without budget attributes gets the sanitized 500; no backend call. |
| Missing usage or price | Agreed behaviour; never a silent zero. |
| Regression | Routing, auth, token quota and earlier checks still pass. |

Stop at the agreed call and output limits; if the budget isn't reached, report inconclusive rather than sending more traffic.

## Handoff

Report what is written, checked offline and verified live, including overshoot, missing-cost handling, model-scope status and the exact product attributes the operator must set. Show the token quota's limit and window next to the budget. If the token limit is lower than the tokens the budget can pay for, start the handoff with this warning: the token quota will reject calls before the budget is reached, so the budget can't be tested until the user raises the token limit. Include the raise-the-limit instructions from [the check](#check-the-token-quota-against-the-budget). Streaming is out of scope.

## Sources

[ltq]: https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/llm-token-quota-policy
[products]: https://docs.cloud.google.com/apigee/docs/api-platform/publish/create-api-products#customattributes
[js]: https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/javascript-policy

- [LLMTokenQuota policy][ltq]: enforce/count pattern, `countRef`, `Interval`/`TimeUnit` references, `LLMTokenUsageSource` as a message template, runtime errors.
- [API product custom attributes][products]: up to 18 including operations; `verifyapikey.POLICY_NAME.apiproduct.ATTRIBUTE_NAME`.
- [JavaScript policy][js]: `<Properties>` read in script as `properties.<name>`.
