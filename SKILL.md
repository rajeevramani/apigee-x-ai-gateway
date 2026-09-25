---
name: apigee-x-ai-gateway
description: Builds or changes an Apigee X proxy that acts as an AI or LLM gateway. Use it to route between models with aliases, or to add token quotas, spending budgets, Model Armor prompt and response inspection, prompt-token burst limits or FAQ semantic caching.
version: 1.0.0
---

# Apigee X AI gateway

## When to use

- Build, change or inspect an Apigee X AI gateway proxy. Deliver proxy files, operator setup steps and a test plan.
- Help an operator deploy or prepare pre-import steps. Infrastructure changes, including creating an organization, need approval.
- Anthropic-format conversion and streaming are not implemented. Reject streaming requests explicitly.

## Dependencies and tools

- **Use the pinned `apigee-x-proxy-development` skill** throughout proxy work. If it is missing, stop and ask the user to install it.
- **Open the exact reference before writing each policy, flow or condition**, using the [pinned dependency map](references/dependency-map.md#capability-ownership-and-precise-dependency-references). In the handoff, list each file with the reference you opened for it.
- **Take syntax from the references.** The gateway references and the development skill are the source of truth for policy XML, flows, conditions and variables. Availability, entitlement, quotas and pricing change over time: check them in current official documentation or with the user. If the development skill and official documentation disagree, follow the [conflict guidance](references/dependency-map.md#official-document-conflict-guidance).
- **Build only what the selected workflow describes.** Read it in full first. If a request or detail isn't covered, say so and ask.
- **Custom flow variables** must not start with an Apigee-owned prefix (`request.`, `response.`, `message.`, `route.`, `target.`, `proxy.`, `client.`, `system.`, `fault.`, `error.`, `apiproxy.`, `environment.`, `organization.`). See [custom flow variables](references/model-routing.md#custom-flow-variables-never-use-an-apigee-owned-prefix).
- **Tools:** use terminal and file tools. Check `apigeecli` commands with `--help`; never invent flags or API calls.

| Capability | Reference | Output |
|---|---|---|
| Routing | [Routing](references/model-routing.md) | Alias, endpoint and auth mapping; bundle; route checks |
| Accumulated tokens | [LLMTokenQuota](references/token-quota.md) | Product-sourced limit, counter scope, paired policies, counter tests |
| API keys and product configuration | [API product setup](references/api-product-setup.md) | Operator-run product, developer, app and attribute steps with readback |
| Spending budget | [Cost budget](references/cost-budget.md) | Prices and budget on the API Product, cost calculation, paired cost counters, tests |
| Prompt bursts | [PromptTokenLimit](references/prompt-token-limit.md) | Rate, trusted identity, complete prompt sources, failure tests |
| Prompt and response protection | [Model Armor](references/model-armor.md) | Failure contract, template and identity readiness, safety tests |
| FAQ reuse | [Semantic cache](references/semantic-cache.md) and [trial checklist](references/semantic-cache.md#cache-trial-and-enablement-checklist) | Fixed configuration, answers safe for every caller, gated bundle |
| Missing Vertex dependencies | [Operator setup](references/semantic-cache-vertex-setup.md) | Guided creation; exact IDs and URLs before the ZIP |

## Shared gates

**Location before commands**

- Agree processing and storage locations for every regional dependency. Never infer a region; keep `__APPROVED_REGION__` and `__APPROVED_TEMPLATE_LOCATION__` until agreed.
- Check availability of each model, filter, embedding model and Vector Search separately, plus quotas and connectivity. With approved read access, read back exact resource names and locations.
- Never relocate, modify shared resources or weaken residency or filters. For Model Armor, follow the [location mapping](references/model-armor-setup.md#location-gate-before-commands).

**Privacy**

- Keep configuration, credentials, private endpoints and raw test output outside Git.
- Never ask for secrets in chat or embed keys in XML, JavaScript or properties. Keep tokens out of command arguments and verbose traces.
- Mask copied native variables before capture. Never log authorization headers, sensitive prompts or raw responses. Strip internal routing metadata from responses.

## Procedure

1. **Discover.** Read supplied configuration, then ask about all gaps at once, each with a recommendation. Confirm organization, environment, proxy name, base path, endpoints, models, formats, caller and backend authentication, streaming and test budget. Agree aliases and unknown-model errors; recommend explicit rejection, never implicit fallback. Keep existing identifiers.
2. **Approve and baseline.** Confirm the project, ownership, changes, exposure and call limits. Get separate approval for reads, backend calls, setup and IAM, deployment, retained costs and trials. Probe approved backends with a small synthetic call and record the status, resolved model and usage. Resolve authentication failures with the user; never retry blindly.
3. **Build incrementally.**
   - Keep working proxies and operator changes. Write real files, native policies first.
   - Validate the model allowlist and translate aliases before the backend call. Keep caller and upstream authentication separate.
   - For fixed target URLs, set Boolean `target.copy.pathsuffix=false` in the TargetEndpoint request flow.
   - On every route, remove caller credential headers before inserting the backend credential.
   - Mark any file written without its reference as unverified and ask.
   - Check policies, attachment order, XML, references and ZIP structure.
4. **Import and deploy as approved.** Get separate approval for runtime credentials. Before the ZIP, supply the [Model Armor](references/model-armor-setup.md#manual-pre-import-handoff) and [semantic cache](references/semantic-cache.md#manual-pre-import-handoff) handoffs that apply. Never run manual instructions yourself. Deploy only approved revisions, and read back configuration and readiness after each write.
5. **Verify and hand off.**
   - With every API-key proxy, deliver [API product setup](references/api-product-setup.md#generated-proxy-handoff) instructions for the generated proxy. For token quotas, list the product's LLM operation model names and explain that they are backend model IDs, not caller aliases.
   - Run the acceptance cases on the deployed proxy. Report structural checks, direct-backend results and deployed-proxy results separately.
   - Report what was built and tested, retained resources and costs, and gaps.
   - No cleanup or publication without approval.

## Verification boundary

- **Read the error body, not just the status code.** A fault-formatting policy can run and still leave Apigee's native fault on the wire, leaking a caller identity or policy name. See [sanitized errors](references/model-routing.md#sanitized-errors-verify-the-body-and-use-the-attribute-form-of-assignto).
- Known limits ([capability status](references/capability-status.md)): an unchanged passthrough tests upstream routing, not Apigee request mapping; non-streaming results say nothing about streaming; routing alone is not a complete gateway.
