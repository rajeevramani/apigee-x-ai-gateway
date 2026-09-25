# Combined build — Labs 1–4 in one go

Build routing, token quotas, spending budgets and Model Armor as one fresh gateway, instead of four separate steps. Best if you've already been through the labs once.

## Before you start

- Complete the [Model Armor setup](../README.md#model-armor-setup-lab-4). The template readback, approved location and deployment service account are required, not optional.
- Use a proxy name, base path and output folder that don't collide with your lab builds. Don't give the agent earlier lab bundles.
- Optional: run [Lab 0](lab-0-readiness.md) first to check the agent found both skills.

## Prompt

Replace the placeholders with your non-secret values. For Apigee X, the project ID is also the organization ID.

```text
I’m evaluating Apigee AI gateway. Build one gateway with model routing,
per-caller token quotas, spending budgets, and Model Armor inspection
of both prompts and responses.

Apigee project ID: __PROJECT_ID__
Environment: __ENVIRONMENT__
Proxy: __PROXY_NAME__
Base path: __BASE_PATH__
Operation: POST /chat/completions

Backend: __FULL_BACKEND_CHAT_COMPLETIONS_URL__
Models:
  __CALLER_ALIAS_1__ → __EXACT_BACKEND_MODEL_ID_1__
  __CALLER_ALIAS_2__ → __EXACT_BACKEND_MODEL_ID_2__

Caller authentication: x-api-key
Backend authentication: Bearer token from encrypted environment KVM
KVM name: __EXISTING_KVM_NAME__
KVM entry: __EXACT_EXISTING_ENTRY_NAME__

Model Armor template: __FULL_TEMPLATE_RESOURCE_NAME__
Deployment service account: __SERVICE_ACCOUNT_EMAIL__
Model Armor template readback file: __AGENT_READABLE_PATH__
Approved Model Armor processing location: __APPROVED_LOCATION__

Preserve supplied values exactly. Choose and explain sensible evaluation
defaults for everything else. Use clearly labelled synthetic prices if
actual model prices are missing; these are not billing rates. Make the token and spending limits
compatible so I can test each feature. Ask only for essential facts you
cannot safely infer. Read the supplied template/filter configuration and
verify the supplied deployment prerequisites before generation. Preserve
legitimate upstream metadata; protect credentials and authentication secrets.
Explain your choices and report selected settings, sources and overrides.

Save fresh source, an importable ZIP, setup instructions and a small
manual test plan in ./ai-gateway/lab-combined. Include API Product setup
with the exact LLM operation model names, plus prerequisite readiness and exact deployment
service-account selection/readback instructions. Keep test requests short and inexpensive.
Do not copy earlier lab bundles or overwrite existing artifacts.

I will perform all cloud setup, import, deployment and live testing.
Do not access my cloud account, make live calls or include secrets.
```

The same settings live in [`lab-config.example.md`](../lab-config.example.md) if you'd rather keep them in a file.

## Deploy and test

Follow the agent's setup steps, then run the deploy and smoke-test steps from each of Labs [1](lab-1-routing.md), [2](lab-2-token-quota.md), [3](lab-3-spending-budget.md) and [4](lab-4-model-armor.md) against the combined gateway. One ZIP that imports isn't proof that all four capabilities work.

Burst protection and semantic caching aren't part of this build. Add them afterwards with [Lab 5](lab-5-burst-protection.md) and [Lab 6](lab-6-semantic-cache.md).
