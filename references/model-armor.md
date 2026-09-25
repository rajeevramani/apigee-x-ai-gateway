# Model Armor — approval-gated native inspection

Add native SanitizeUserPrompt and SanitizeModelResponse inspection to the existing gateway. For current status, see [Feature status](capability-status.md).

## Ask these questions first, then wait

Before writing any file, check the working proxy and approved configuration, then ask every question below they don't already answer. **Stop and wait for the answers.** Only continue without an answer if the user explicitly says to use your recommendation.

Explain first that Model Armor sends prompts and responses to another Google service, so it adds a processing location, cost and latency.

| Decision | Question to ask | Recommendation |
|---|---|---|
| Directions | Inspect prompts, responses, or both? | Both. Prompt inspection requires a response policy to be created before the prompt policy is deployed ([prompt prerequisites][sup]); response inspection has no matching requirement ([response prerequisites][smr]). |
| Template | Reuse an existing template (exact `projects/…/locations/…/templates/…` name) or create one? | Reuse if one exists. Never invent a template name. If none exists yet, follow [no template yet](#when-the-template-does-not-exist-yet). |
| Location and residency | Which region holds the template, and is that acceptable for residency? | Never infer a region. Apply the [location gate](model-armor-setup.md#location-gate-before-commands) and check [filter coverage by region][1]. |
| Filters and thresholds | Which filters does the template enable, and at what levels? Ask the user to read them back from the console or API: RAI types, prompt injection and jailbreak, malicious URLs, and basic or advanced SDP. |Needed to set `requiredFilters`. |
| Caller contract | Limit callers to single-turn, text-only, non-streaming OpenAI-compatible requests? Agree the operation and path, input and output sizes, and how unsupported shapes are rejected (400, before any scan or backend call). | Yes, agreed explicitly; never silently restrict an existing chat API. |
| Failure handling | If inspection fails, is skipped or is incomplete: block (fail closed) or allow? | Fail closed. |
| Latency and cost | Accept the added latency and cost? | Check current pricing; measure latency in your own tests. See [limits and cost](#limits-and-cost). |
| Quota semantics | If a response is blocked after the backend generated it, does it still count against the token quota and any cost budget? | Yes (consumption accounting): enforce quota before prompt inspection and count usage before response inspection, including withheld output. Delivery-only accounting needs a redesigned attachment order. Preserve the [quota contract](token-quota.md). |
| Deployment identity | Which Apigee project, organization, environment, proxy and revision, and which deployment service account? Does it have the Model Armor roles? | Ask; never infer. |
| Logging | Is `logSanitizeOperations` enabled on the template? It logs full prompts and responses. | Off unless the user approves. |

The caller contract covers one user message. Full conversations, system instructions, tools, content arrays, multiple choices, attachments and streaming need a different design; inspecting only the last message does not protect a full chat.

If an answer is still missing when you build, leave the matching `__PLACEHOLDER__` visible and say plainly in the handoff that the bundle is **not ready to import**.

## When the template does not exist yet

The user often has no Model Armor template when this step starts. Creating one is their job (see [setup](model-armor-setup.md#reuse-or-create-a-template)); the proxy bundle depends on it. Handle the gap like this:

1. Give the template creation instructions first, and ask whether the user wants to create it **now** (you wait) or **later** (you build with placeholders). Don't decide for them.
2. If building with placeholders: keep `__TEMPLATE_PROJECT__`, `__TEMPLATE_LOCATION__` and `__TEMPLATE_ID__` visible in every file that needs them, set `requiredFilters` from the filters the user *plans* to enable, and state in the handoff that the bundle is **not ready to import**.
3. End the handoff with two explicit requests: "When the template exists, send me its exact resource name and the filter readback (which filters are enabled, at what levels)", and "Tell me whether you want me to regenerate the bundle with those values". Wait for both.
4. When the answers arrive, rebuild in the same step directory, replace only the template values and `requiredFilters`, show the diff from the placeholder version, and re-run the offline checks. Don't regenerate silently, and don't edit a bundle the user has already imported — produce a new one.

The template name is a resource path, not a secret, so it may be pasted into chat. Filter readback is configuration, not content.

## Setup and integration approval checkpoints

1. Before any command, complete the [location gate](model-armor-setup.md#location-gate-before-commands).
2. If the template or deployment identity is missing or unknown, resolve it through the [template setup](model-armor-setup.md#reuse-or-create-a-template).
3. Before integration, apply the [known limitations](model-armor-setup.md#known-limitations).
4. Before presenting a ZIP, supply the [manual pre-import handoff](model-armor-setup.md#manual-pre-import-handoff).

## Completeness guard: which result fields to use

Decide success from the native policy's `invocationResult`, `filterMatchState` and parsed `responseFromModelArmor`. Don't rely on `requestSentToModelArmor` or flattened per-filter flow variables ([policy reference][sup]); they are not a portable success check.

1. Require `invocationResult = "SUCCESS"` and `filterMatchState = "NO_MATCH_FOUND"`. Reject PARTIAL, FAILURE, missing or unexpected values.
2. Parse `responseFromModelArmor` as JSON and require `sanitizationResult.filterMatchState = "NO_MATCH_FOUND"` and `EXECUTION_SUCCESS` for every enabled filter ([SanitizationResult][2]). Missing, malformed, skipped or failed results leave the guard false. Verify this with a masked benign trace before acceptance.
3. Convert Java-backed policy properties and flow-variable strings with `String(...)` before strict comparison in JavaScript. Never use truthiness to decide success.
4. The supplied [validator](../assets/examples/model-armor/validate-armor.js) reads each JavaScript policy's `requiredFilters` property: a comma-separated list of filter keys under `sanitizationResult.filterResults`. Each must report `EXECUTION_SUCCESS`; basic and advanced SDP are both handled. The default, `rai,sdp,pi_and_jailbreak,malicious_uris`, matches the template created by the README setup. **Set `requiredFilters` in both JavaScript policies to the filters in the approved template readback** (for example, add `csam`, or remove `sdp` if it is disabled). Don't edit the script. An empty list, a missing filter or any other state fails closed.
5. A native filter match raises a fault and keeps the content-block mapping. A match that doesn't fault, or an incomplete result, fails the validator and gets the incomplete error. Keep consumption accounting before response inspection.
6. Don't guess a size limit. Use the [quotas page][3], and still check execution states, because an input-size bound doesn't show that every filter ran.

Copy `validate-armor.js` into `apiproxy/resources/jsc/` and both JavaScript policies into `apiproxy/policies/`. Keep native policy names consistent with the validator's variable prefixes. Attach each validator immediately after its native inspection, and require its result before continuing. Run response extraction, inspection, validation and the incomplete guard only when `response.status.code = 200`.

## Errors, fault rules and references

- **Use only these documented fault names** (`fault.name` is the last part of the fault code).

  | `fault.name` | HTTP | Meaning |
  |---|---|---|
  | `FilterMatched` | 400 | The prompt or response failed the template check (a content block). |
  | `SanitizationResponseParsingFailed`, `FailedToExtractUserPrompt`, `FailedToExtractLLMResponse` (response policy only), `InternalError`, `ModelArmorTemplateNameExtractionFailed`, `AuthenticationFailure`, `ModelArmorAPIFailed`, `ModelArmorCalloutError`, `ServiceUnavailable` | 500 | Inspection could not be done (not a content block). |

  Tell which policy failed with `SanitizeUserPrompt.<policy name>.failed = true` or `SanitizeModelResponse.<policy name>.failed = true`.
- **Keep failures and content blocks separate.** A filter match gets the agreed "blocked" response. An outage, skipped filter or incomplete result gets the incomplete response (503 suggested). Never map every Model Armor failure to "blocked by safety filter".
- **Only inspect successful backend responses.** Put `response.status.code = 200` on the response extraction, `SMR-InspectResponse` and its guard, so provider error bodies are never scanned.
- **Error AssignMessage policies used in FaultRules must set the response.** Don't use `<AssignTo … type="request"/>` there.
- **Never suggest breaking shared IAM or credentials** to test failure handling. Use isolated, approved fault injection, or mark the case unverified.
- **Open the pinned `apigee-x-proxy-development` skill reference for the non-Armor policies** you write for this capability, and list it in the reference list: [ExtractVariables](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/policies_mediation.md#jsonpath-extraction), [AssignMessage](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/policies_mediation.md), [RaiseFault](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/fault_handling.md#raisefault-for-custom-errors), [FaultRules](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/fault_handling.md#faultrules) and [conditions](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/flow_variables_and_conditions.md#condition-syntax).

## Basic integration: render and merge into the existing gateway

For users who choose **both directions, reject matches, reject incomplete inspection and outages, and consumption-based accounting**. There is no fail-open path. Explain to the user:

- `continueOnError="false"` raises a fault on any policy failure, not just on a filter match.
- `IgnoreUnresolvedVariables` is `false` here, which overrides the console default of `true`.
- Native policy failures enter the error flow before the completeness guard runs.
- The completeness guard catches incomplete results that don't raise a fault. It also rejects an unexpected match that didn't fault, and reports it as incomplete rather than as a `FilterMatched` block. Verify this behavior at runtime.

### Integration placeholder contract

Resolve every row against the approved gateway; a placeholder name does not implement a policy. Render with XML-aware editing, keep single-brace runtime expressions intact, and keep credentials and account identifiers out of reusable files.

| Placeholder | Required mapping and integration behavior |
|---|---|
| `__TEMPLATE_PROJECT__`, `__TEMPLATE_LOCATION__`, `__TEMPLATE_ID__` / `__APPROVED_TEMPLATE_LOCATION__` | Use the exact readback and alias mapping in the [setup location gate](model-armor-setup.md#location-gate-before-commands). |
| `__REQUEST_VALIDATION_POLICY__` | Check the operation and JSON content type. Require exactly one `messages` entry with role `user` and nonempty string content. `stream` must be absent or false, and `n` absent or 1. Reject tools, `tool_choice`, function calls, content arrays and attachments. Agree extra fields and sizes. Reject unsupported payloads before any scan or backend call. ExtractVariables with `type="string"` may coerce non-strings, so validate the shape separately. |
| `__RESPONSE_VALIDATION_POLICY__` | Validate successful responses: exactly one choice with an assistant message and nonempty string content. Reject tool or function calls, refusal-only payloads, content arrays and unsupported extra output. Agree handling for provider errors, missing usage, empty, refused or truncated output, and overflow. Preserve error paths and `success.codes`. |
| `__CALLER_AUTH_POLICY__`, `__RESPONSE_PRIVACY_POLICY__` | Map to the working policies, adding several Steps if needed. Preserve caller auth and model validation, [target path suppression and credential order](model-routing.md#target-request-preparation), RouteRules and response sanitization. Exclude unrelated paths, but don't silently skip inspection for unsupported payloads. |
| `__APPROVED_COUNT_CONDITION__` | Keep the agreed eligibility and missing-usage handling. Map `LTQ-Enforce` and `LTQ-Count` to the existing policies; never rename or duplicate them to fit. With consumption accounting approved, count once, before inspection and response validation, while the native usage and model fields are still present. Check TargetEndpoint transformations and fault routes, and move steps earlier where needed: a new fault can skip Count, and unavailable usage is not zero. |
| `__INCOMPLETE_STATUS__` | Agree the HTTP error status (503 suggested). Keep separate sanitized responses for match, extraction, service and incomplete errors, without the native faultstring, Model Armor results or custom template errors. Inspect endpoint FaultRules and DefaultFaultRule (including AlwaysEnforce). Merge by the policy's `failed` variable plus verified `fault.name` or error code, and keep unrelated auth, quota and upstream failures intact. `RF-ArmorIncomplete` covers completeness only, not native fault mapping; reuse existing safe mappings where they fit. |

### Capture and merge order

- Capture the prompt before any model or payload transformation, and keep it for response inspection.
- `messages[0]` and `choices[0]` rely on the agreed cardinality checks.
- `FunctionResponseSource` and `FunctionCallSource` point at the same validated text variables as the primary sources. This fills the policies' optional source fields without adding tool content to scope. The validation steps keep these fields from mattering on the normal path; test missing and empty input separately.
- Merge the steps into the selected operation, not blindly into the global PreFlow. Check which conditional flow matches first, and check response and error attachments.
- Show the exact rendered diff and resolve every Step before import. The fragments below provide no deployed proxy, validation, fault mapping or template.

Example source: `../assets/examples/model-armor/EV-ArmorPrompt.xml`

```xml
<ExtractVariables name="EV-ArmorPrompt" continueOnError="false" enabled="true">
  <Source clearPayload="false">request</Source>
  <JSONPayload>
    <Variable name="prompt" type="string"><JSONPath>$.messages[0].content</JSONPath></Variable>
  </JSONPayload>
  <VariablePrefix>private.armor</VariablePrefix>
  <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
</ExtractVariables>
```

Example source: `../assets/examples/model-armor/EV-ArmorResponse.xml`

```xml
<ExtractVariables name="EV-ArmorResponse" continueOnError="false" enabled="true">
  <Source clearPayload="false">response</Source>
  <JSONPayload>
    <Variable name="response" type="string"><JSONPath>$.choices[0].message.content</JSONPath></Variable>
  </JSONPayload>
  <VariablePrefix>private.armor</VariablePrefix>
  <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
</ExtractVariables>
```

Example source: `../assets/examples/model-armor/SUP-InspectPrompt.xml`

```xml
<SanitizeUserPrompt name="SUP-InspectPrompt" continueOnError="false" enabled="true">
  <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
  <ModelArmor>
    <TemplateName>projects/__TEMPLATE_PROJECT__/locations/__TEMPLATE_LOCATION__/templates/__TEMPLATE_ID__</TemplateName>
  </ModelArmor>
  <UserPromptSource>{private.armor.prompt}</UserPromptSource>
  <FunctionResponseSource>{private.armor.prompt}</FunctionResponseSource>
</SanitizeUserPrompt>
```

Example source: `../assets/examples/model-armor/SMR-InspectResponse.xml`

```xml
<SanitizeModelResponse name="SMR-InspectResponse" continueOnError="false" enabled="true">
  <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
  <ModelArmor>
    <TemplateName>projects/__TEMPLATE_PROJECT__/locations/__TEMPLATE_LOCATION__/templates/__TEMPLATE_ID__</TemplateName>
  </ModelArmor>
  <UserPromptSource>{private.armor.prompt}</UserPromptSource>
  <LLMResponseSource>{private.armor.response}</LLMResponseSource>
  <FunctionCallSource>{private.armor.response}</FunctionCallSource>
</SanitizeModelResponse>
```

Example source: `../assets/examples/model-armor/RF-ArmorIncomplete.xml`

```xml
<RaiseFault name="RF-ArmorIncomplete" continueOnError="false" enabled="true">
  <FaultResponse>
    <Set>
      <Payload contentType="application/json">{"error":"inspection_incomplete"}</Payload>
      <StatusCode>__INCOMPLETE_STATUS__</StatusCode>
      <ReasonPhrase>Inspection incomplete</ReasonPhrase>
    </Set>
  </FaultResponse>
  <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
</RaiseFault>
```

Example source: `../assets/examples/model-armor/JS-ValidateArmorPrompt.xml`

```xml
<Javascript name="JS-ValidateArmorPrompt" timeLimit="200"><Properties><Property name="phase">prompt</Property><Property name="requiredFilters">rai,sdp,pi_and_jailbreak,malicious_uris</Property></Properties><ResourceURL>jsc://validate-armor.js</ResourceURL></Javascript>
```

Example source: `../assets/examples/model-armor/JS-ValidateArmorResponse.xml`

```xml
<Javascript name="JS-ValidateArmorResponse" timeLimit="200"><Properties><Property name="phase">response</Property><Property name="requiredFilters">rai,sdp,pi_and_jailbreak,malicious_uris</Property></Properties><ResourceURL>jsc://validate-armor.js</ResourceURL></Javascript>
```

Example source: `../assets/examples/model-armor/proxy-flow-fragment.xml`

```xml
<!-- Merge guide: inspect prompts and responses; count usage before response inspection. -->
<PreFlow name="PreFlow">
  <Request>
    <Step><Name>__CALLER_AUTH_POLICY__</Name></Step>
    <Step><Name>__REQUEST_VALIDATION_POLICY__</Name></Step>
    <Step><Name>LTQ-Enforce</Name></Step>
    <Step><Name>EV-ArmorPrompt</Name></Step>
    <Step><Name>SUP-InspectPrompt</Name></Step>
    <Step><Name>JS-ValidateArmorPrompt</Name></Step>
    <Step>
      <Name>RF-ArmorIncomplete</Name>
      <Condition>(private.armor.prompt_complete != true)</Condition>
    </Step>
  </Request>
  <Response>
    <Step><Name>LTQ-Count</Name><Condition>__APPROVED_COUNT_CONDITION__</Condition></Step>
    <Step><Name>__RESPONSE_VALIDATION_POLICY__</Name><Condition>response.status.code = 200</Condition></Step>
    <Step><Name>EV-ArmorResponse</Name><Condition>response.status.code = 200</Condition></Step>
    <Step><Name>SMR-InspectResponse</Name><Condition>response.status.code = 200</Condition></Step>
    <Step><Name>JS-ValidateArmorResponse</Name><Condition>response.status.code = 200</Condition></Step>
    <Step>
      <Name>RF-ArmorIncomplete</Name>
      <Condition>(response.status.code = 200) and (private.armor.response_complete != true)</Condition>
    </Step>
    <Step><Name>__RESPONSE_PRIVACY_POLICY__</Name></Step>
  </Response>
</PreFlow>
```

## Offline checks and live acceptance

Run `python3 -m unittest discover -s tests -v` in a terminal (Node.js required). It checks XML and source elements, inline/asset parity, synthetic rendering, step order and the JavaScript guard. It doesn't replace live acceptance; apply the [verification boundary](../SKILL.md#verification-boundary).

Before any debug session, configure and verify masking for:

- request and response content, `private.armor.prompt`, `private.armor.response` and credentials;
- native `userPrompt`, `modelResponse`, `requestSentToModelArmor`, `responseFromModelArmor` and `maliciousURIs`;
- custom errors.

Never collect raw traces first. Get approval for which sanitized metadata (template identifier, status, fault details) you keep and for how long, and keep it out of normal client responses.

Once blockers are resolved and the user has approved the deployment, the scans and the model calls, run these cases:

| Case | Required masked evidence |
|---|---|
| Benign prompt and response | The intended sources were inspected. `invocationResult=SUCCESS`, parsed `responseFromModelArmor`, and `EXECUTION_SUCCESS` for every enabled filter, with the match state recorded. HTTP 200 or `NO_MATCH_FOUND` on its own is not enough. |
| Selected synthetic filter match on prompt | Correct policy and filter attribution, the agreed safe error, and no backend call. Use safe, non-sensitive detector fixtures, never real harmful or illegal material. |
| Selected response match | Output is not delivered. With consumption accounting, generated usage is counted exactly once. A block after the backend call cannot undo backend cost. |
| Missing, empty, wrong-type, multiple, tool or streaming input and output | The agreed handling applies. No content passes uninspected, and scope is never narrowed silently. |
| Skipped, partial, failed or missing result, and size limits | Explicit incomplete handling. Exercise the guard with null and absent variables, and check every chosen filter, not just the aggregate match state. |
| Service, auth or parse failure | The sanitized agreed error, and traffic is never allowed through during an outage. Use approved isolated fault injection; never break shared IAM or credentials to force it. |
| Regression | Routing, caller and upstream auth, the exact target URL and path, quota exhaustion, reset, isolation and accounting, and response privacy all still work. |

Stay within the approved request, output, time and cost limits. Don't reset quotas, change filters or widen retries automatically. Report each case as pass, fail or unverified.

### Limits and cost

- [Model Armor limits][3] include project-level query quotas, a 4 MB input limit and per-filter token limits. Text over a limit can be skipped. Agree conservative size limits and still check execution states, because a character limit doesn't guarantee every detector's token limit.
- Model Armor calls, Apigee extensible-policy usage, backend generation and optional Logging are separate costs. Check current [pricing][4] and the billing arrangement; measure latency in your own tests.

## Official sources

See the [complete source catalog](model-armor-setup.md#official-sources) and the [known limitations](model-armor-setup.md#known-limitations).

[sup]: https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/sanitize-user-prompt-policy
[smr]: https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/sanitize-llm-response-policy
[1]: https://docs.cloud.google.com/model-armor/feature-availability-by-region
[2]: https://docs.cloud.google.com/model-armor/reference/rest/v1/SanitizationResult
[3]: https://docs.cloud.google.com/model-armor/quotas
[4]: https://cloud.google.com/security/products/model-armor#pricing
