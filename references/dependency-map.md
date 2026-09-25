# Dependency map

This skill depends on the pinned `apigee-x-proxy-development` skill from github.com/carlosmscabral/cabral-skills at commit f1171671874444b42d5a6d7a0e4ac63e80db2fe8, under `skills/apigee-x-proxy-development/`. Read the exact reference before authoring each policy or flow.

- For policy syntax and flow mechanics, the gateway references and the pinned skill are the source of truth. Don't look up syntax in official documentation.
- Availability, entitlement, quotas and pricing change over time. A reference may ask you to check those in current documentation or with the user (see [SKILL.md](../SKILL.md#dependencies-and-tools)).
- Where the pinned skill differs from official sources, follow the [conflict guidance](#official-document-conflict-guidance).
- Gateway workflows own approved composition, safety, accounting and acceptance.
- Read the pinned skill for every proxy mechanic a workflow needs, including conditions, variables and fault responses, even when it is not listed below.
- If neither covers a detail, stop and ask. Never invent XML or weaken safeguards.

## Capability ownership and precise dependency references

| General mechanic in the pinned skill | Gateway owner and constraint |
|---|---|
| [Bundle directory structure](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/proxy_bundle_anatomy.md#directory-tree) | [Routing](model-routing.md#target-request-preparation): real bundle files and resolved references; keep the `apiproxy/` ZIP root. Keep the proxy descriptor filename of a valid existing bundle. |
| [TargetEndpoint mechanics](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/endpoints_and_routing.md#targetendpoint) | [Routing](model-routing.md#target-request-preparation): approved full operation URL, path suppression and credential order on every route. |
| [RouteRules](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/endpoints_and_routing.md#routerules) | [Routing](model-routing.md): exact alias allowlist and mapping. No caller-selected URL or credential reference, and no silent fallback. |
| [Conditional flows](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/flows_and_execution.md#conditional-flows) and [Step configuration](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/flows_and_execution.md#step-configuration) | [Armor](model-armor.md) and [cache](semantic-cache.md): merge into existing Steps. Take AI ordering from the workflow, not from generic security, mediation or traffic ordering. |
| [AssignMessage removal](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/policies_mediation.md#remove-operation) and [AssignVariable sources](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/policies_mediation.md#assignvariable--all-value-sources) | [Routing](model-routing.md#target-request-preparation): parameterized preparation and auth insertion. Leave native runtime expressions unrendered at author time. |
| [JSONPath extraction](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/policies_mediation.md#jsonpath-extraction) | [Armor](model-armor.md) and [quota](token-quota.md): approved complete text and usage sources. Validate cardinality, type and structure separately from scalar extraction. |
| [VerifyAPIKey](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/policies_security.md#verifyapikey) and [VerifyJWT](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/policies_security.md#verifyjwt) | [Routing](model-routing.md): chosen caller contract, verified identity and missing-input handling; upstream auth is separate. |
| [KVM GET](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/policies_integration.md#get-operation) | [Routing](model-routing.md#target-request-preparation): approved runtime credential, a missing-secret guard, and lookup before insertion. Never build the credential key from untrusted input, and ask before seeding a KVM. |
| [FaultRules](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/fault_handling.md#faultrules) and [DefaultFaultRule](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/fault_handling.md#defaultfaultrule) | [Quota](token-quota.md) and [PTL](prompt-token-limit.md): policy-specific attribution and endpoint precedence. No catch-all that erases agreed errors or relabels upstream 429s. |
| [Scope rules and custom variables](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/flow_variables_and_conditions.md#scope-rules-and-custom-variables) | [Routing](model-routing.md#custom-flow-variables-never-use-an-apigee-owned-prefix): read before creating any custom variable. Carry request-phase values into the response phase in a custom variable under a prefix Apigee does not own. The prefix rule is owned by the routing reference. |
| [Condition syntax](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/flow_variables_and_conditions.md#condition-syntax) and [request variables](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/flow_variables_and_conditions.md#request-variables) | [Routing](model-routing.md#implementation-sequence): alias allowlist and stream rejection conditions. |
| [RaiseFault](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/fault_handling.md#raisefault-for-custom-errors) | [Routing](model-routing.md#configuration-contract): agreed 400 errors for missing/unknown alias and unsupported streaming. |
| [Message templates](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/flow_variables_and_conditions.md#message-templates) | [Quota](token-quota.md#non-streaming-token-quota): check exact field support in the reference; retain single braces and XML-aware rendering. |
| [VerifyAPIKey](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/policies_security.md#verifyapikey), [JavaScript policy configuration](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/javascript_development.md#javascript-policy-configuration) and [RaiseFault](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/fault_handling.md#raisefault-for-custom-errors) | [Cost budget](cost-budget.md): API Product custom attributes after VerifyAPIKey; JavaScript only for cost arithmetic; sanitized missing-configuration fault. |
| [JSON parsing/transformation](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/javascript_development.md#json-parsing-and-transformation) | [Routing](model-routing.md): native policies first; minimal JSON-safe transformation; exact mapped model and message semantics. |
| [Private-variable masking concept](https://github.com/carlosmscabral/cabral-skills/blob/f1171671874444b42d5a6d7a0e4ac63e80db2fe8/skills/apigee-x-proxy-development/references/debugging_and_performance.md#private-variable-masking) | [SKILL privacy gate](../SKILL.md#shared-gates): mask native copied values before capture. Ask before using the pinned skill's debug commands. |

Keep these capabilities distinct:

- Use LLMTokenQuota for LLM accounting, not ordinary Quota.
- Use semantic caching policies for semantic caching, not ResponseCache.
- Set up Model Armor as its own step; Google target authentication does not cover it.

Manual pre-import assistance still applies. You may consult existing shared-flow mechanics, but create a new shared flow only with explicit approval.

## Official-document conflict guidance

Don't use the AI snippets in the pinned skill's `advanced_patterns.md` as generation templates. Use the owning gateway reference and these resolutions:

| Topic | Resolution and owner |
|---|---|
| Sanitizer names and inputs | The response policy is named `SanitizeModelResponse`, even though its documentation URL says `sanitize-llm-response`. Use `UserPromptSource`, `LLMResponseSource`, documented fallback sources and nested `ModelArmor/TemplateName`, not generic `Source`. [Armor](model-armor.md) owns the completeness and fallback guards. [1][2] |
| Armor prerequisites | Model Armor API and roles, not generic Vertex setup. [Setup](model-armor-setup.md#known-limitations) owns identity, template, location and permissions. [1][2] |
| Token quota | Official split-counter syntax uses message-template bodies, `Allow count`, `SharedName`, `EnforceOnly` and `CountOnly`; don't use the pinned skill's `ref` and child `Tokens` example. [Quota](token-quota.md) owns paired accounting and the model source for enforce and count. [3] |
| Semantic cache | Use `UserPromptSource`, `Embeddings/VertexAI`, `SimilaritySearch/VertexAI` and populate `TTLInSeconds`. Don't use generic `Source`, `CacheConfig`, `SimilarityThreshold` or other ordinary-cache fields. [Cache](semantic-cache.md) owns transport, IDs, isolation and hit trials. [5][6] |
| Cache placement and cost | Populate only after response Armor and privacy checks. Don't promise savings or assume what runs after a hit. Follow the [trial checklist](semantic-cache.md#cache-trial-and-enablement-checklist) for placement, not the pinned skill's TargetEndpoint population advice. [5][6] |
| PromptTokenLimit | The pinned skill mentions per-request throttling without an implementation. Use [PTL](prompt-token-limit.md#how-prompttokenlimit-works) for the supported configuration. [4] |
| Fault-flow response writing | Write fault responses with the attribute form, `<AssignTo createNew="false" type="response"/>`, as every asset in this skill does, not the bare `<AssignTo>response</AssignTo>` shown in the pinned skill's `fault_handling.md`; the bare form can leave Apigee's native fault on the wire. See [sanitized errors](model-routing.md#sanitized-errors-verify-the-body-and-use-the-attribute-form-of-assignto). |
| Null routing | Use the TargetEndpoint and RouteRule mechanics above, not the advanced-pattern null-route recipe, for routing and cache hits. Routing redesign needs separate approval. |

Don't use the pinned skill's IAM, debug or region examples as-is; ask first.

## Sources

1. [SanitizeUserPrompt policy](https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/sanitize-user-prompt-policy)
2. [SanitizeModelResponse policy](https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/sanitize-llm-response-policy)
3. [LLMTokenQuota policy](https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/llm-token-quota-policy)
4. [PromptTokenLimit policy](https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/prompt-token-limit-policy)
5. [SemanticCacheLookup policy](https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/semantic-cache-lookup-policy)
6. [SemanticCachePopulate policy](https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/semantic-cache-populate-policy)
