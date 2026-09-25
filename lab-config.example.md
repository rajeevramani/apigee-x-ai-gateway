# Apigee AI gateway evaluation configuration

Copy this file to a private location outside the repository. Replace required placeholders with your values; omit optional lines until needed. Never include secrets. Give the agent the path it can read (the container-side path if applicable).

## Core settings — Lab 1 onward

```text
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
```

For Apigee X, the project ID is also the organization ID. This example uses one OpenAI-compatible backend and a KVM-backed Bearer credential; adapt those lines if your approved backend differs. Copy existing KVM map and entry names exactly. If they do not exist, say “setup needed” rather than inventing an existing resource.

## Optional settings — add when needed

Leave these out to let the agent propose evaluation defaults. Keep agreed values in your private copy for later labs.

```text
API Product internal name: __PRODUCT_NAME__

Token quota: __TOKEN_LIMIT__ tokens every __INTERVAL__ __TIME_UNIT__
Spending budget: __USD_AMOUNT__ USD every __INTERVAL__ __TIME_UNIT__
Model prices: use clearly labelled synthetic evaluation prices

Model Armor template: __FULL_TEMPLATE_RESOURCE_NAME__
Deployment service account: __SERVICE_ACCOUNT_EMAIL__
Model Armor template readback file: __AGENT_READABLE_PATH__
```

Token quotas begin in Lab 2; spending budgets and prices in Lab 3; Model Armor in Lab 4. If supplying real prices, give input and output USD per million tokens for each alias. Existing template filters must come from the actual readback, not assumptions. If no template exists, request setup guidance and agree the processing location first.

## Instructions to the agent

Preserve supplied values exactly. Choose and explain sensible evaluation defaults for missing settings. Synthetic prices demonstrate enforcement, not actual billing. Ask only for essential facts you cannot safely infer. I will perform cloud setup, deployment and live tests. Do not access my cloud account, make live calls or include secrets.

## Reuse for later labs

Use this same private configuration for progressive Labs 1–4 or a fresh combined build. For each progressive lab, also supply the previous working source/ZIP, deployed revision and test results, plus a separate output directory. Configuration alone does not contain the previous implementation. Retain the agreed settings unless explicitly changing them.

For Labs 5–6, reuse the common settings and add the burst-protection or semantic-cache inputs requested by those labs. Do not enable those capabilities merely because you are reusing this file. Lab 0 can use it for readiness discussion without building. For a separate combined trial, choose a non-colliding proxy name/base path and fresh output directory; do not pass earlier bundles as build inputs.
