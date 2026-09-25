# Prompt-token burst protection

Add native **PromptTokenLimit** (PTL) to an existing Apigee X gateway to absorb prompt-token bursts. See [capability status](capability-status.md) and the [shared gates](../SKILL.md#shared-gates). Read the current [PTL reference][1] first. PTL is an Extensible policy for Apigee X, not hybrid; confirm availability and cost. The [rate-limiting overview][2] contrasts traffic protection with quotas.

## How PromptTokenLimit works

- On Apigee X, set `UseEffectiveCount` to `true` ([1], [3]). Counting then uses a regional, distributed sliding window. It allows bursts within the rate rather than smoothing traffic. Set the full rate; do not divide it by the number of message processors.
- Valid elements are `UserPromptSource`, `Identifier`, `Rate` (such as `20ps` or `100pm`), `UseEffectiveCount` and `IgnoreUnresolvedVariables`.
- `UserPromptSource` takes one text value: the validated `{private.ptl.prompt}`, not the whole body.
- The count, `ratelimit.PTL-ProtectPromptBurst.userPromptTokenCount`, is Apigee's estimate. It may differ from provider token usage.
- PTL is not a per-request context-window limit or a spend limit. Keep the Lab 2 [token quota](token-quota.md) for that.
- `Identifier` groups the count by its value. Omit it for one shared proxy-wide rate.
- Detect rate exhaustion with `fault.name = "PromptTokenLimitViolation"`. The policy's `.failed` variable signals an internal failure, not an exhausted rate.
- Under high load the policy can fail open. This is a documented limitation that `continueOnError` cannot prevent.

## Agree the missing choices

Inspect the bundle and keep its routing, auth, quota and Model Armor. Ask only about undecided choices:

| Choice | What to agree |
|---|---|
| Rate | Tokens per second or minute. Callers never set it. |
| Scope | Per verified app, per developer, or shared. Per-caller rates do not cap total backend load. Never group by raw credentials or the URL. Keep `client_id` out of logs and responses. |
| Text coverage | `$.messages[0].content` suits single-turn requests only. For multi-turn, system, tool or multimodal input, agree which text counts and add an extraction step. Never truncate silently. |
| Invalid input | Missing, empty, non-string or oversized text and missing identity. Recommend rejecting before PTL. |
| Integration | A sanitized 429, and order relative to quota and Model Armor. |
| Live test plan | Scope, identities, request sizes, wait and cost, under the [execution approvals](../SKILL.md#procedure). Never stress production. |

## Add the policies to the bundle

Copy the policies into the existing bundle. The fragments are not a complete proxy. When rendering, check the rate matches `[1-9][0-9]*(ps|pm)` and escape values. Leave single-brace runtime templates in place.

| Placeholder | Value |
|---|---|
| `__PROMPT_TOKEN_RATE__` | The agreed rate. |
| `__VERIFIED_CALLER_VARIABLE__` | A variable set by existing auth, such as `verifyapikey.VAK-VerifyCallerKey.client_id` when that policy runs first. For shared scope, remove `Identifier`. |
| `__PROMPT_TEXT_JSONPATH__` | A scalar path that meets the agreed [text coverage](#agree-the-missing-choices). |
| `__CALLER_AUTH_POLICY__` | The existing auth policy. |
| `__REQUEST_VALIDATION_POLICY__` | A validator for method, content type, size, text coverage, identity, model allowlist and streaming. |

With an aggregation step, point `UserPromptSource` at its variable and drop `EV-BurstPrompt`. Reuse Model Armor's prompt variable only if it covers the agreed text.

Example source: `../assets/examples/prompt-token-limit/EV-BurstPrompt.xml`

```xml
<ExtractVariables name="EV-BurstPrompt" continueOnError="false" enabled="true">
  <Source clearPayload="false">request</Source>
  <JSONPayload>
    <Variable name="prompt" type="string">
      <JSONPath>__PROMPT_TEXT_JSONPATH__</JSONPath>
    </Variable>
  </JSONPayload>
  <VariablePrefix>private.ptl</VariablePrefix>
  <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
</ExtractVariables>
```

Example source: `../assets/examples/prompt-token-limit/PTL-ProtectPromptBurst.xml`

```xml
<PromptTokenLimit name="PTL-ProtectPromptBurst" continueOnError="false" enabled="true">
  <UserPromptSource>{private.ptl.prompt}</UserPromptSource>
  <Identifier ref="__VERIFIED_CALLER_VARIABLE__"/>
  <Rate>__PROMPT_TOKEN_RATE__</Rate>
  <UseEffectiveCount>true</UseEffectiveCount>
  <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
</PromptTokenLimit>
```

Example source: `../assets/examples/prompt-token-limit/proxy-flow-fragment.xml`

```xml
<!-- Merge guide: retain existing routing, quota and Model Armor steps. -->
<PreFlow name="PreFlow">
  <Request>
    <Step><Name>__CALLER_AUTH_POLICY__</Name></Step>
    <Step><Name>__REQUEST_VALIDATION_POLICY__</Name></Step>
    <Step><Name>EV-BurstPrompt</Name></Step>
    <Step><Name>PTL-ProtectPromptBurst</Name></Step>
  </Request>
  <Response/>
</PreFlow>
```

Merge the Steps into each operation's request flow, after auth and validation and before dispatch. Every applicable route runs PTL exactly once.

If token quota and Model Armor are already present, propose `LTQ-Enforce`, then `EV-BurstPrompt` and PTL, then the Model Armor prompt check. PTL rejections then save a scan and a model call. Trade-off: PTL first uses allowance on requests Model Armor later blocks; Model Armor first spends scans on requests PTL later blocks. Keep `LTQ-Count` exactly once.

## Optional sanitized rejection

Reuse existing error handling if it fits. The fault `policies.prompttokenlimit.PromptTokenLimitViolation` returns 429. `fault.name` names the fault type, not the PTL instance. Never map upstream 429s here. Handle `FailedToExtractUserPrompt` (400), `FailedToCalculateUserPromptTokens` (500) and ExtractVariables failures as errors, not rate exhaustion.

Example source: `../assets/examples/prompt-token-limit/prompt-limit-fault-fragment.xml`

```xml
<!-- Merge into ProxyEndpoint FaultRules; this identifies PTL violations, not a specific policy instance. -->
<FaultRule name="prompt-token-rate-exceeded">
  <Step><Name>AM-PromptBurstExceeded</Name></Step>
  <Condition>(fault.name = "PromptTokenLimitViolation")</Condition>
</FaultRule>
```

Example source: `../assets/examples/prompt-token-limit/AM-PromptBurstExceeded.xml`

```xml
<AssignMessage name="AM-PromptBurstExceeded" continueOnError="false" enabled="true">
  <Set>
    <Payload contentType="application/json">{"error":"prompt_token_rate_exceeded"}</Payload>
    <StatusCode>429</StatusCode>
    <ReasonPhrase>Too Many Requests</ReasonPhrase>
  </Set>
  <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
  <AssignTo createNew="false" transport="http" type="response"/>
</AssignMessage>
```

FaultRules are evaluated bottom to top. Check that no catch-all rule, `DefaultFaultRule` or `AlwaysEnforce` step overwrites this response or leaks data. Omit `Retry-After`; the policy gives no reliable retry time.

## Check the bundle, then test live

Check the bundle locally:

- Every changed XML file parses.
- No placeholder remains and every referenced name exists.
- Each route runs the steps in the agreed order.
- No other fault rule shadows the PTL rule.

The operator deploys under the [execution approvals](../SKILL.md#procedure). Before tracing, confirm masking of bodies, auth, identity and `ratelimit.PTL-ProtectPromptBurst.resolvedUserPrompt`. The `private.` prefix does not mask PTL's prompt copy. Keep evidence outside Git.

| Case | Pass when |
|---|---|
| Below rate | Requests reach the backend and `userPromptTokenCount` looks plausible. |
| Burst | Within agreed limits, `PromptTokenLimitViolation` rejects the request before the backend. A 429 alone is not enough. If PTL does not trigger, stop; do not raise traffic. |
| Recovery | Requests pass again after the agreed wait as the window slides. |
| Scope | A second identity shows the agreed isolation or sharing. |
| Invalid input | Bad text and missing identity are rejected before dispatch. Never overload to test fail-open. |
| Regressions | Routing, auth, target path, token quota and Model Armor behave as before. |

Report each case as pass, fail or unverified.

## References

1. [PromptTokenLimit policy][1]
2. [Rate-limiting overview][2]
3. [SpikeArrest policy][3] (`UseEffectiveCount` on Apigee X)

[1]: https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/prompt-token-limit-policy
[2]: https://docs.cloud.google.com/apigee/docs/api-platform/develop/rate-limiting
[3]: https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/spike-arrest-policy
