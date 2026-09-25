# Model routing — first increment

## Helpful discovery

Read the available context first. Ask only the questions it leaves open, and explain each recommendation.

| Decision | Helpful question and starting recommendation |
|---|---|
| Existing deployment | Which approved Apigee organization, environment and proxy base path should be used? Check for collisions before proposing writes. |
| Models and formats | Which endpoint, exact model identifiers and request formats are available? Start with one common format; two providers do not necessarily require two formats. |
| Selection | Should callers choose a model alias? Recommend an explicit allowlisted alias mapping for the first increment. |
| Invalid selection | Reject missing or unknown models, or use an explicitly chosen default? Recommend rejection, so cost and behavior never change silently. |
| Caller authentication | How will callers authenticate to Apigee? Treat caller access as its own decision, separate from the upstream key. For API keys, guide product, developer and app setup with [API product setup](api-product-setup.md). |
| Backend authentication | Which header, scheme and private credential reference does each backend need? Ask for the reference or its location, never the secret itself. |
| Streaming | Is streaming required now? Recommend non-streaming for the first test, and reject `stream=true` explicitly until streaming is supported. |
| Test bounds | What endpoint usage is authorized? Propose one small request per model, an agreed output bound and no automatic retries; confirm the provider-supported token-limit field before sending. |

## Configuration contract

Keep a private table that maps each alias to its endpoint, upstream model, API format, auth scheme and secret reference. Resolve only configured destinations, and reject caller-controlled target URLs or credential references. Compare identifiers exactly, without normalization or repair.

Start with non-streaming OpenAI-compatible chat completions, and verify the backend's request and response fields. Anthropic conversion, streaming and fallback are separate increments. Direct provider integrations (provider-specific auth and formats) are separate increments.

Agree the client contract: a POST to the approved path with a JSON object holding a string model alias and a messages array. A missing or unsupported model, or an unsupported streaming request, returns a sanitized 400. If a contract already exists, document and test that one.

## Implementation sequence

Use the [target request preparation](#target-request-preparation) below and inspect its actual flow placement. For general routing mechanics, read the pinned skill's [TargetEndpoint](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/endpoints_and_routing.md#targetendpoint) and [RouteRules](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/endpoints_and_routing.md#routerules); keep the exact local allowlist, path and credential-order checks. For alias and stream checks, read its [JSONPath extraction](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/policies_mediation.md#jsonpath-extraction), [Condition syntax](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/flow_variables_and_conditions.md#condition-syntax) and [RaiseFault](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/fault_handling.md#raisefault-for-custom-errors) before writing them.

1. Inspect any existing proxy. Preserve unrelated behavior and operator revisions.
2. Extract and validate aliases, and select allowlisted targets, with native policies. Use narrow JavaScript only for necessary JSON-safe transformations; never concatenate unescaped user content.
3. Map the exact upstream model, preserving agreed messages. Store the resolved backend model ID in a custom variable such as `ai.upstream_model`; token quota and cost budgets key on it later. Reject unsupported options before backend calls; verify provider token parameters.
4. Apply [target preparation](#target-request-preparation) on every route. Read back the policy and its attached TargetEndpoint Step, including conditions and any later overwrite or removal.
5. Select an approved, documented runtime credential mechanism, with its permissions and masking. Obtain [approval](../SKILL.md#procedure) before any KVM, secret or IAM write, and follow the [privacy gates](../SKILL.md#shared-gates). Files in the agent's container are not visible to the Apigee runtime.
6. Preserve the agreed response fields and any usage data. Strip internal routing metadata, and sanitize both successes and errors. Keep prompt and response logging off by default.
7. Complete the [local checks](#completion-checks). Then obtain deployment approval, import and read back the exact revision, and deploy without overriding existing deployments. Verify readiness before running approved probes.

Use the pinned skill's [bundle layout](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/proxy_bundle_anatomy.md#directory-tree), [Step configuration](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/flows_and_execution.md#step-configuration) and [message templates](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/flow_variables_and_conditions.md#message-templates) for syntax, within the [dependency boundary](dependency-map.md#capability-ownership-and-precise-dependency-references). Merge the examples below into working flows; [feature status](capability-status.md) lists what has been tested.

## Sanitized errors: verify the body, and use the attribute form of AssignTo

Every error contract in this skill promises a sanitized body. Check it in two ways:

- **Write fault responses with the attribute form of AssignTo.** In a fault flow, use
  `<AssignTo createNew="false" transport="http" type="response"/>` (the skill's assets also use it without
  `transport`). The bare `<AssignTo>response</AssignTo>` form can run without replacing Apigee's native fault,
  which may contain a caller identity or policy name.
- **Make every template variable resolve.** An unresolved `{var:default}` reference is emitted verbatim, so the
  caller sees `{ai.error_message:...}` as text.

Test every error path by reading the response body. It must contain no `faultstring`, no `policies.*` code, no
identity or credential, and no leftover `{...}`.

<a id="custom-flow-variables-never-use-an-apigee-owned-prefix"></a>
## Custom flow variables: use a prefix Apigee does not own

Carry every value between policies, or across the request/response boundary, in a custom flow variable. Apigee
owns a set of top-level namespaces. A custom child written under one can fail **silently**: the write appears to
succeed but a later read returns null. For example, a guard that reads `request.reject_reason` sees null and
rejects well-formed requests.

Never create a custom variable under these prefixes:

    request.   response.   message.   route.   target.   proxy.
    client.    system.     fault.     error.   apiproxy. environment.   organization.

This applies to custom names only; set built-in variables such as `target.copy.pathsuffix` normally.

Use a prefix Apigee does not define, such as `ai.`, `custom.` or a project-specific namespace:
`ai.upstream_model`, `ai.alias`, `custom.original_verb`. Reserve `private.` for values that must be masked in
trace sessions. Verify the read at each consuming Step.

Before writing a policy that creates or reads a custom variable, read the pinned skill's
[scope rules and custom variables](dependency-map.md#capability-ownership-and-precise-dependency-references).
Carry any request-phase value you need later in a custom variable, rather than relying on `request.*` in the
response flow.

## Target request preparation

Files: [preparation](../assets/examples/target/AM-PrepareTargetRequest.xml), [upstream authentication](../assets/examples/target/AM-SetUpstreamAuth.xml), [flow fragment](../assets/examples/target/target-request-flow.xml).

Copy the policies into the bundle's policies directory. Merge the request Steps into the existing TargetEndpoint request PreFlow, and keep the existing endpoint and response Steps. Authenticate callers before header removal. Replace `__CREDENTIAL_LOOKUP_POLICY__` with the approved lookup policy, which must set `private.upstream_api_key`, and handle a missing or empty credential before auth insertion. Never render secrets into assets or bundles.

Set the complete approved operation URL separately. Set `target.copy.pathsuffix` to Boolean false in the **TargetEndpoint request flow** (setting it only in the ProxyEndpoint is not enough), and never append `proxy.pathsuffix` again. Use this order on every route:

1. Preparation and header removal.
2. Approved credential lookup.
3. Upstream auth insertion.
4. Dispatch.

The header removal here is a minimum, not a complete security policy.

Example source: `../assets/examples/target/AM-PrepareTargetRequest.xml`

```xml
<AssignMessage name="AM-PrepareTargetRequest">
  <Remove><Headers><Header name="Authorization"/><Header name="x-api-key"/></Headers></Remove>
  <AssignVariable><Name>target.copy.pathsuffix</Name><Value>false</Value></AssignVariable>
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
  <AssignTo createNew="false" transport="http" type="request"/>
</AssignMessage>
```

Example source: `../assets/examples/target/target-request-flow.xml`

```xml
<!-- Fragment: merge into TargetEndpoint, not ProxyEndpoint. -->
<PreFlow name="PreFlow">
  <Request>
    <Step><Name>AM-PrepareTargetRequest</Name></Step>
    <Step><Name>__CREDENTIAL_LOOKUP_POLICY__</Name></Step>
    <Step><Name>AM-SetUpstreamAuth</Name></Step>
  </Request>
  <Response/>
</PreFlow>
```

## Completion checks

- Render with an XML-aware tool. Validate values, preserve single-brace runtime expressions and resolve every `__PLACEHOLDER__`.
- Parse the XML. Check policy syntax and conditions against the references you read. Check that every policy, resource and endpoint resolves, that Steps are in order, and that the ZIP root is `apiproxy/`.
- Include the [reference list](../SKILL.md#procedure): each policy and endpoint file with the development skill reference opened before writing it.
- Show the exact diff for approval. These are structural checks; runtime behavior is covered by [live acceptance](#acceptance-cases).

## Related capabilities

Add separately, preserving working controls: [accumulated token quota](token-quota.md), [Model Armor inspection](model-armor.md), [prompt-token burst protection](prompt-token-limit.md), [limited FAQ caching](semantic-cache.md). Follow each workflow's decisions and acceptance gates.

## Acceptance cases

| Case | Required evidence |
|---|---|
| Exact target path and authentication order | Local inspection identifies the preparation policy, its TargetEndpoint request Step and upstream-auth Step in execution order. Live verification observes the exact expected target path, without a duplicated suffix, and successful upstream authentication without logging credential values. |
| Each configured alias | Sanitized outgoing model mapping plus a successful real response. Routing evidence from a controlled trace or trusted upstream metadata. |
| Unknown or missing alias | Agreed client error, plus trace or upstream evidence that the backend was not invoked. |
| stream=true while unsupported | Explicit rejection before backend invocation. |
| Caller auth failure | Rejected at Apigee without upstream call, under an approved negative test. |
| Backend error | Sanitized response under a safe controlled test; do not rotate or break a shared production credential to generate a failure. |
| Response privacy | Standard response fields behave as agreed. Internal routing and key aliases, and authorization details, are absent from client output. |

Capture only the evidence each case needs. If you need a trace, configure masking before capture, restrict access, and keep only nonsecret routing fields. If routing or non-invocation evidence is unavailable, mark that case unverified.
