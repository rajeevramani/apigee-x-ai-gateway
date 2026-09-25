# Token quota — incremental workflow

## Scope and source

Use native LLMTokenQuota, not request-count Quota, to limit accumulated token usage on an existing non-streaming OpenAI-compatible gateway. See [evidence status](capability-status.md).

The limit, interval and time unit live on the caller's **API Product**, not in the policy. Both policies read them through `countRef` and `ref` flow variables, so changing a budget needs no proxy redeploy. VerifyAPIKey (or an OAuthV2 ValidateToken step) must execute before the quota policy so that `apiproduct.developer.llmQuota.*` resolves. The operator sets the product values with [API product setup](api-product-setup.md); the agent never changes an API Product itself.

Take policy syntax from the templates below. Confirm availability, entitlement and permissions in the current [LLMTokenQuota documentation](https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/llm-token-quota-policy), or ask the user. Build the endpoint with [routing's pinned bundle, Step and template mechanics](model-routing.md#implementation-sequence).

## Discover and explain

Inspect the existing source and deployed revision within the approved read scope, and keep the known-good bundle. Ask only for missing choices:

| Choice | Explanation and suggested starting point |
|---|---|
| Caller authentication | Product-sourced quota needs VerifyAPIKey or OAuthV2 ValidateToken first. If callers authenticate another way (JWT, VerifyIAM), stop and agree a different design: this workflow has no hardwired-limit fallback. |
| Limit | Agree the token limit, then have the operator set the product's `llmQuota`, `llmQuotaInterval` and `llmQuotaTimeUnit` through [API product setup](api-product-setup.md). 100 tokens is a small test value, not a production recommendation. Later changes apply without redeploying the proxy. |
| Window and reset | Interval and time unit come from the product. Only the `type` attribute (fixed, calendar, flexi or rollingwindow) stays in the policy. Suggest one minute with the documented fixed-window reset as a simple starting point. A rolling window ages usage out gradually instead of resetting it all at once. |
| Accounting | Input, output or combined? Suggest combined `usage.total_tokens` if that is the desired budget. Don't add `total_tokens` to its input and output components. |
| Identity | Per authenticated client or app, per developer, or shared? Suggest the verified client identity. Use only verified identity for counter isolation, never an arbitrary caller header. Explain whether multiple credentials should share a budget. |
| Model scope | Both policies key on the backend model ID the gateway sends upstream (see [the model key](#both-halves-key-on-the-request-model)). Aliases that map to different backend models get separate counters; aliases that map to the same model share one. Confirm the chosen scope with the isolation test. |
| Missing usage and failures | Decide how missing, invalid or error-response usage is handled. Don't treat missing usage as zero or estimate it with a different tokenizer. Some failed calls still consume backend tokens. |
| Deployment and test limits | Confirm the environment, revision, number of model calls, output limit, budget, permitted negative tests and wait duration. Vague approval does not cover calls or deployment. |

"Add 100 tokens" is not a complete quota contract. Present the proposed contract and its limits before editing. List the exact product values for the operator to apply and read back. Don't change API Products, shared KVMs, credentials or IAM implicitly.

## Both halves key on the request model

When the API Product scopes quotas per model (`llmOperationGroup`), each counter is keyed by
**model** as well as `SharedName` and `Identifier`. If the enforcing and counting policies resolve
different model strings, they read and write different counters: both succeed, neither reports
`failed`, and the limit is never enforced.

Key both halves on the **request model**: the backend model ID the gateway sends upstream after
alias translation.

- **Set one variable during alias translation.** In the request flow, before `LTQ-Enforce`, store
  the resolved backend model ID in a custom variable under a prefix Apigee does not own, for
  example `ai.upstream_model` (see
  [custom flow variables](model-routing.md#custom-flow-variables-never-use-an-apigee-owned-prefix)).
  Custom variables set in the request flow remain readable in the response flow.
- **Point both policies at it.** `LTQ-Enforce` and `LTQ-Count` both set
  `<LLMModelSource>{__UPSTREAM_MODEL_VARIABLE__}</LLMModelSource>`. Don't use the model name
  in the response: providers and upstream gateways often return a different or versioned name,
  and it isn't available when the enforcing policy runs.
- **Use the same ID in the product.** Each API Product `llmOperations[].model` entry is the
  backend model ID, the value of that variable. It is not the caller's alias and not the name in
  the response.
- **Check the halves agree.** In a trace, `ratelimit.LTQ-Enforce.model` and
  `ratelimit.LTQ-Count.model` show the same value, and `ratelimit.LTQ-Enforce.used.count` rises as
  `ratelimit.LTQ-Count` records usage. An `allowed.count` of `9223372036854775807` on the counting
  policy is expected, because `CountOnly` doesn't enforce.

## Sanitized quota errors

A native `LLMTokenQuota` fault can expose the caller's consumer key in `faultstring`, so read the
rejection body, not only its 429 status. Follow
[Sanitized errors](model-routing.md#sanitized-errors-verify-the-body-and-use-the-attribute-form-of-assignto)
for the `AssignTo` form and the body checks. The quota rejection must also be local and
distinguishable from an upstream 429.

## Enforcement semantics

EnforceOnly checks previously accounted usage on each incoming request. CountOnly records response usage under the same SharedName. Actual output usage arrives afterward, so admitted or concurrent calls and synchronization delay can overshoot the limit. Treat the quota as a usage budget, not a hard cost ceiling or an exact token cap. Set generation output limits separately.

Check Distributed and Synchronous support for the chosen counter type in the current documentation. Counter scope includes the proxy and can depend on API Product operation settings and model references. A shared counter is scoped to one proxy unless verified otherwise. Test per-caller and cross-model behavior before asserting it.

Extract the chosen `usage.prompt_tokens`, `usage.completion_tokens` or `usage.total_tokens` through documented LLMTokenUsageSource message templates, and require nonnegative numeric usage. Take LLMModelSource in both policies from the request-side model variable described in [the model key](#both-halves-key-on-the-request-model). Keep the approved scope, and report unsupported semantics rather than inventing policy elements.

## Implementation sequence

Render the [quota policies](#non-streaming-token-quota) and [merge attachments](#merging-attachments-and-optional-fault-handling).

1. Copy the working proxy into a new output directory. Inspect auth policy names, routing conditions, target preparation, fault rules and response transformations.
2. Render separate EnforceOnly=true and CountOnly=true policies with the same approved SharedName, identity, and documented type and reset settings. Both take limit, interval and time unit from the same product variables; never substitute a hardwired limit.
3. Give the operator the exact product values — `llmQuota`, `llmQuotaInterval`, `llmQuotaTimeUnit`, **and** an `llmOperationGroup` entry per proxy and model pair with its own `llmTokenQuota` — and have them applied and read back through [API product setup](api-product-setup.md) before deployment. Product edits take a few minutes to reach the runtime cache. The product field `llmQuota` is what the policy reads as `llmQuota.limit`. A product-level quota needs at least one LLM operation: without one, the policy aborts with `Invalid API call as no apiproduct match found`, usually surfacing as an opaque 500. Each operation's model string is the backend model ID the gateway sends upstream (the value of `__UPSTREAM_MODEL_VARIABLE__`), not the caller's alias or the name in the response. See [API product setup](api-product-setup.md#things-that-go-wrong).
4. Enforce after successful caller authentication and request validation, before invocation. Use the actual verified identity variable, not an invented policy name or the raw `x-api-key`. The VerifyAPIKey policy named in `__VERIFY_API_KEY_POLICY__` must be that same executed step.
5. Count exactly once, before usage or model fields are transformed or removed. Set usage extraction explicitly. Inspect successful responses, provider HTTP errors, transport failures and absent usage separately across normal and fault paths.
6. Explain missing or invalid usage gaps. Ask whether to return without counting, fail the response or use another supported approach. Add guards, rejection or logging only as chosen, without leaking responses. Post-call errors cannot undo consumption or debit unreported usage.
7. Integrate [quota fault handling](#merging-attachments-and-optional-fault-handling).
8. Keep [target preparation and auth order](model-routing.md#target-request-preparation), model mapping, credentials and response sanitization intact. Exclude counter identities and credentials from diagnostic headers.
9. Run the [completion checks](#completion-checks), citing the files and steps behind each claim.
10. Obtain deployment approval, then import, read back and deploy the exact revision. Get separate approval for a limited number of model calls under the [shared procedure](../SKILL.md#procedure). Never reset shared counters, alter limits or wait indefinitely just to pass tests.

## Non-streaming token quota

Files: [enforcement](../assets/examples/token-quota/LTQ-Enforce.xml), [accounting](../assets/examples/token-quota/LTQ-Count.xml), [flow attachments](../assets/examples/token-quota/proxy-flow-fragment.xml), [optional quota fault rule](../assets/examples/token-quota/quota-fault-fragment.xml), [optional sanitized response](../assets/examples/token-quota/AM-QuotaExceeded.xml).

The files omit `type` and use the default window. For an approved rollingwindow, flexi or calendar window, add that type to both root elements. Calendar also needs the same approved UTC StartTime in both policies; add StartTime for no other type. Confirm schema placement, interval, unit and documented reset semantics. Distributed=true does not mean instant synchronization; see [enforcement semantics](#enforcement-semantics).

| Placeholder | Required input |
|---|---|
| __SYNCHRONOUS__ | Approved true or false. Recommend true for sequential live tests after explaining the performance and availability tradeoffs. It does not remove post-response or in-flight overshoot. |
| __COUNTER_NAME__ | Same stable shared counter name in both policies; keep the test apart from existing counters. |
| __VERIFY_API_KEY_POLICY__ | Name of the VerifyAPIKey policy that actually executes before both quota policies; the product variables resolve only under that exact name. |
| __VERIFIED_CALLER_VARIABLE__ | Actual verified identity variable, e.g. verifyapikey.VAK-VerifyCallerKey.client_id only if that named policy exists and executes first. |
| __USAGE_JSONPATH__ | $.usage.total_tokens, $.usage.prompt_tokens or $.usage.completion_tokens according to the approved accounting mode. |
| __UPSTREAM_MODEL_VARIABLE__ | Custom variable holding the backend model ID, set during alias translation before LTQ-Enforce, for example `ai.upstream_model`. Both policies use it; see [the model key](#both-halves-key-on-the-request-model). |

Render with XML-aware editing and validate each value; don't use unrestricted text substitution. Leave the Apigee runtime expressions in single braces unchanged. Confirm every `__PLACEHOLDER__` is gone before import.

The inline `count="1"`, `Interval` `1` and `TimeUnit` `minute` are fallback literals, not a budget. Set the product quota before testing. Agree an explicit missing-configuration guard that rejects the request when the product quota values are absent, and verify it in the [Missing product quota](#live-acceptance) acceptance case.

The accounting template expects the selected usage in `response.content`; the model comes from the request-side variable. Check that usage is valid; HTTP 200 does not guarantee it. Resolve `__APPROVED_COUNT_CONDITION__` only after agreeing which responses are counted and how absent or invalid usage and model values are handled. A status-only condition means accepting native missing-usage failures; see [condition options](#condition-and-window-options). Never skip accounting silently as zero.

Integrate input validation, missing-usage handling, quota faults and API Product scope explicitly.

Example source: `../assets/examples/token-quota/LTQ-Enforce.xml`

```xml
<LLMTokenQuota name="LTQ-Enforce">
  <SharedName>__COUNTER_NAME__</SharedName>
  <EnforceOnly>true</EnforceOnly>
  <Allow count="1" countRef="verifyapikey.__VERIFY_API_KEY_POLICY__.apiproduct.developer.llmQuota.limit"/>
  <Interval ref="verifyapikey.__VERIFY_API_KEY_POLICY__.apiproduct.developer.llmQuota.interval">1</Interval>
  <TimeUnit ref="verifyapikey.__VERIFY_API_KEY_POLICY__.apiproduct.developer.llmQuota.timeunit">minute</TimeUnit>
  <Identifier ref="__VERIFIED_CALLER_VARIABLE__"/>
  <Distributed>true</Distributed>
  <Synchronous>__SYNCHRONOUS__</Synchronous>
  <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
  <LLMModelSource>{__UPSTREAM_MODEL_VARIABLE__}</LLMModelSource>
</LLMTokenQuota>
```

Example source: `../assets/examples/token-quota/LTQ-Count.xml`

```xml
<LLMTokenQuota name="LTQ-Count">
  <SharedName>__COUNTER_NAME__</SharedName>
  <CountOnly>true</CountOnly>
  <Allow count="1" countRef="verifyapikey.__VERIFY_API_KEY_POLICY__.apiproduct.developer.llmQuota.limit"/>
  <Interval ref="verifyapikey.__VERIFY_API_KEY_POLICY__.apiproduct.developer.llmQuota.interval">1</Interval>
  <TimeUnit ref="verifyapikey.__VERIFY_API_KEY_POLICY__.apiproduct.developer.llmQuota.timeunit">minute</TimeUnit>
  <Identifier ref="__VERIFIED_CALLER_VARIABLE__"/>
  <Distributed>true</Distributed>
  <Synchronous>__SYNCHRONOUS__</Synchronous>
  <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
  <LLMTokenUsageSource>{jsonPath('__USAGE_JSONPATH__',response.content,true)}</LLMTokenUsageSource>
  <LLMModelSource>{__UPSTREAM_MODEL_VARIABLE__}</LLMModelSource>
</LLMTokenQuota>
```

Example source: `../assets/examples/token-quota/proxy-flow-fragment.xml`

```xml
<PreFlow name="PreFlow">
  <Request>
    <Step><Name>__CALLER_AUTH_POLICY__</Name></Step>
    <Step><Name>__REQUEST_VALIDATION_POLICY__</Name></Step>
    <Step><Name>LTQ-Enforce</Name></Step>
  </Request>
  <Response>
    <Step>
      <Name>LTQ-Count</Name>
      <Condition>__APPROVED_COUNT_CONDITION__</Condition>
    </Step>
  </Response>
</PreFlow>
```

## Merging attachments and optional fault handling

The proxy flow fragment is a merge guide, not a replacement endpoint.

- Replace the caller-authentication and request-validation Step placeholders with the existing steps, keeping their behavior. Place LTQ-Enforce after both.
- Choose one matching operation flow so enforcement isn't added to unrelated paths.
- Replace `__APPROVED_COUNT_CONDITION__` with the agreed Apigee condition, XML-escaped.
- Insert LTQ-Count before any transformation that removes usage, including transformations in the TargetEndpoint response flow. If that means counting in the TargetEndpoint, move the response Step there and don't keep a second copy in the proxy.

Map documented exhaustion to a sanitized response, normally 429. Make sure DefaultFaultRule cannot replace it with a generic 502 or overwrite its status. Keep upstream 429s distinct from local quota failures. Add Retry-After only when the configured window gives a reliable reset time.

Fault handling is optional. Inspect existing rules first; if they already return the agreed quota error, reuse them. Otherwise propose the supplied quota FaultRule and AM-QuotaExceeded policy and get the user's agreement. For general endpoint evaluation mechanics, use the pinned `apigee-x-proxy-development` skill's [FaultRules](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/fault_handling.md#faultrules) and [DefaultFaultRule](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/fault_handling.md#defaultfaultrule) guidance.

- Merge the rule into ProxyEndpoint FaultRules. They evaluate bottom to top, so account for existing catch-all rules.
- The native exhaustion fault name is LLMTokenQuotaViolation; the rule also checks LTQ-Enforce's `failed` variable. Check current fault-variable behavior and AlwaysEnforce precedence.
- Missing usage or model faults (FailedToResolveTokenUsageCount, FailedToResolveModelName) are not quota exhaustion. Choose their handling separately rather than converting them all to 429.

### Condition and window options

These snippets illustrate choices to add only with the user's agreement. By default, Apigee target success handling sends 4xx and 5xx responses into error flows. Inspect `success.codes` and existing fault routing before deciding where to count error-response usage. Don't change `success.codes` just to use this example.

Option A, if the user accepts native failures for missing usage on 200 responses:

```xml
<Condition>response.status.code = 200</Condition>
```

Option B, only if the user chooses to return successful responses without accounting when usage is missing. Add an approved validation step that sets `quota.usage.valid` to true only for a nonnegative numeric chosen count and a usable model field, then use:

```xml
<Condition>(response.status.code = 200) and (quota.usage.valid = true)</Condition>
```

Option B leaves an accounting gap; it does not record zero tokens. Supply and enable a validation policy only when agreed. If the user chooses rejection instead, generate the agreed guard and error response explicitly. Leave response handling outside the agreed change as it is.

For one-minute quotas with no type, the documentation says the counter resets at the start of the next minute. Check the documented semantics for other intervals and types. A rolling window root adaptation (apply to both policies, keeping their distinct names):

```xml
<LLMTokenQuota name="LTQ-Enforce" type="rollingwindow"/>
```

This root-only snippet is not a complete policy. A calendar window uses `type="calendar"` plus the approved StartTime element, e.g.:

```xml
<StartTime>__APPROVED_START_TIME_UTC__</StartTime>
```

The Identifier reference must resolve after authentication on every relevant route. Both templates set IgnoreUnresolvedVariables=false; keep it. Confirm the documented message-template expression for usage and model extraction, including scalar behavior, during rendering.

Both templates set LLMModelSource with the same message template, `{__UPSTREAM_MODEL_VARIABLE__}`. Keep them identical when rendering.

## Completion checks

- Parse the XML. Validate current policy syntax, policy, resource and endpoint resolution, conditions, step order and usage extraction.
- Check paired settings and identity, resolved placeholders and count-once coverage. Both policies' `LLMModelSource` reference the same request-side model variable, set before `LTQ-Enforce`. Show the exact minimal diff for approval.
- Confirm no hardwired limit survives: both policies' `Allow` carries `countRef` to the product's `llmQuota.limit`, and the VerifyAPIKey policy named in the refs is the step that actually executes first.
- Keep structural checks separate from [live acceptance](#live-acceptance), which covers target URL and authentication, counter changes and rejection attribution.

## Related capabilities

Add separately, keeping working controls intact: [cost budget](cost-budget.md), [Model Armor inspection](model-armor.md), [prompt-token burst protection](prompt-token-limit.md), [limited FAQ caching](semantic-cache.md). Follow each workflow's decisions and acceptance gates.

## Live acceptance

Run these in the existing working test environment. Approve the request count, maximum output, window and budget first. Use synchronous counters (`__SYNCHRONOUS__` true) for sequential tests; with asynchronous counters, the next request can lag, so allow only the approved observation window and report the result as inconclusive if it doesn't settle.

| Test | Evidence required |
|---|---|
| Below budget | Successful real request and observed usage; sanitized policy counter state where available. |
| Accounting | Under sequential controlled calls, compare counter deltas with the chosen usage field. Observe Apigee's counter directly; summing response usage is not the same thing. |
| Exhaustion | Reach or exceed the configured budget within the approved limits, then observe a later request rejected by the local quota policy before backend invocation. Attribute it with a masked policy trace or equivalent, not the 429 status alone. |
| Window | Verify fixed, flexi or calendar reset, or rolling-window expiry, at the documented boundary within approved wait limits. |
| Model key | Send a request whose alias differs from its backend model ID. In a masked trace, `ratelimit.LTQ-Enforce.model` equals `ratelimit.LTQ-Count.model`, and the next enforce step sees the count step's increment. |
| Isolation | If per caller, use a second approved credential, without exposing its value, and confirm it has its own budget. For shared model scope, alternate two approved aliases that map to the same backend model and confirm they draw on one budget. If a second credential or alias is unavailable, record the scope as unverified. |
| Errors and missing usage | Exercise safe controlled cases without breaking shared credentials; verify the agreed behavior and that no zero counts are recorded in place of missing usage. |
| Product-sourced limit | Change only the API Product's LLM token quota, wait out the product cache, and observe the new limit enforced with no import or deployment. An unchanged limit means the ref did not resolve; inspect the VerifyAPIKey policy name and the matched product. |
| Missing product quota | With the product's LLM token quota unset, confirm the agreed missing-configuration guard rejects the request rather than allowing an unlimited budget. |
| Regression | Existing routing, authentication, exact target path and response sanitization still work. |

Stop at the agreed request, token and time limits. Don't change limits or reset shared counters automatically. If exhaustion is not reached, report the result as inconclusive rather than increasing traffic. Record the requested and resolved models, accounting mode, counter scope, test times, usage, status and sanitized fault attribution privately; keep keys, full prompts and raw traces out of Git.

## Handoff

Report what was implemented, what was checked locally and what was verified live, including overshoot, missing-usage gaps and untested cases. Streaming (EventFlow) accounting is a separate increment.
