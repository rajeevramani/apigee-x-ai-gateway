# Vertex AI gateway — Lab 1 configuration example

Copy this file to a private location outside the repository, replace the placeholders, and give your agent the private file's path. Never put credentials or populated configuration in Git or paste secrets into chat.

`eval`, `global`, the resource names and output allowance below are evaluation choices, not verified resources or model availability. Confirm the environment and processing location before using them. The service-account name is proposed; reuse a suitable existing account instead when available. Choose two exact model IDs permitted by your project's policy and supported at the approved location. See [Vertex setup](references/vertex-target.md) for prerequisites and [general configuration](lab-config.example.md) for later labs.

```text
# Apigee AI Gateway — Vertex AI evaluation configuration

## Apigee environment
Apigee project ID / organization: __APIGEE_PROJECT_ID__
Environment: eval
Proxy: ai-gateway
Base path: /ai-gateway
Operation: POST /chat/completions

## Vertex AI backend
Backend type: vertex-openai
Vertex project ID: __VERTEX_PROJECT_ID__
Vertex location: global
Deployment service account: apigee-vertex-lab@__APIGEE_PROJECT_ID__.iam.gserviceaccount.com
Backend authentication: native GoogleAccessToken
OAuth scope: https://www.googleapis.com/auth/cloud-platform

Models:
  fast → google/__APPROVED_FAST_MODEL_ID__
  smart → google/__APPROVED_SMART_MODEL_ID__

Derive the complete Vertex chat completions URL from the project
and location above. No backend API key or KVM is required.

## Caller authentication and request handling
Caller authentication: x-api-key
Missing, invalid or unapproved model alias: sanitized HTTP 400
Automatic fallback: disabled
Streaming requests (stream: true): sanitized HTTP 400
Supported requests: non-streaming, text-only chat completions

## API Product and developer app
API Product internal name: ai-gateway-product
API Product access: private
Key approval: auto
Developer email: __TEST_DEVELOPER_EMAIL__
Developer app name: ai-gateway-test-app
Setup guide format: Apigee Console UI for product/app and deployment;
gcloud commands for API enablement and service-account/IAM setup.

Scope the product to this proxy and environment, allowing
POST /chat/completions. Keep caller keys out of chat and generated files.

## Setup and deployment
Provide commands to enable aiplatform.googleapis.com in the Vertex
project and verify it is enabled.

Check whether the deployment service account already exists using
operator-supplied readback. Reuse it if suitable; otherwise provide
creation instructions. Provide the required Vertex invocation,
deployer actAs and Apigee token-creation grants, with readback commands.

Do not create service-account JSON keys.
Explain how to select the service account when deploying the proxy.
Importing the ZIP alone does not attach the deployment identity.

## Build and test scope
Build model routing and authentication only.
Do not add token quotas, spending budgets, Model Armor or caching yet.

Output directory: ./ai-gateway/lab-1
Deliver source, an importable ZIP, setup instructions and a manual test plan.
Do not overwrite existing artifacts or deployments without approval.

Use short "hello" requests, stream: false and max_tokens: 256.
Test both aliases, an unknown alias, a missing alias, stream: true
and an invalid caller key. Do not retry automatically.
Check finish_reason; "length" means the answer was truncated.

## Operator boundary
I will perform all cloud setup, import, deployment and live testing.
Do not access my cloud account or make live calls.
Never ask me to paste secrets.

Preserve supplied identifiers exactly. Ask only about essential
unresolved placeholders or conflicting settings.
```
