# Vertex AI chat target

Use this path for Gemini through Vertex AI's **OpenAI-compatible, non-streaming** chat completions endpoint. Keep caller `x-api-key` authentication and alias routing. Native `generateContent`, partner models and streaming are outside this path. Qualification is recorded in [feature status](capability-status.md).

## Configuration and model selection

Confirm the Vertex project, approved location (`global` or a supported region), deployment service account and two exact `google/<MODEL_ID>` values. The proxy service account belongs to the Apigee project; the Vertex project may differ. Global is a processing-location choice, not a residency guarantee. Check current model availability and organization policy before choosing models.

Use the complete operation URL:

- Global: `https://aiplatform.googleapis.com/v1/projects/<PROJECT>/locations/global/endpoints/openapi/chat/completions`
- Regional: `https://<LOCATION>-aiplatform.googleapis.com/v1/projects/<PROJECT>/locations/<LOCATION>/endpoints/openapi/chat/completions`

Do not use `global-aiplatform.googleapis.com`. Request model values are `google/<MODEL_ID>`, not `publishers/google/models/<MODEL_ID>` or policy values such as `is:publishers/google/models/<MODEL_ID>:predict`. Report malformed supplied identifiers rather than silently repairing them. An allowlist entry does not prove endpoint or location availability.

## Operator setup before the ZIP

The operator runs these commands. They enable services and grant IAM; model calls incur charges. Reuse suitable resources. Stop on unresolved placeholders or permission errors; do not grant Owner/Editor or change organization policy to bypass failures.

Set approved values first. Use the same deployment identity for Vertex and Model Armor when combining labs; retain its existing required permissions. When following the Armor setup, use this same account name as `SA_ID`.

```bash
APIGEE_PROJECT_ID="__APIGEE_PROJECT_ID__"
VERTEX_PROJECT_ID="__VERTEX_PROJECT_ID__"
SA_NAME="__PROXY_SERVICE_ACCOUNT_NAME__"
DEPLOYER_MEMBER="user:__DEPLOYER_EMAIL__" # or serviceAccount:EMAIL
SA_EMAIL="${SA_NAME}@${APIGEE_PROJECT_ID}.iam.gserviceaccount.com"
APIGEE_PROJECT_NUMBER="$(gcloud projects describe "$APIGEE_PROJECT_ID" --format='value(projectNumber)')"

gcloud services enable aiplatform.googleapis.com --project="$VERTEX_PROJECT_ID"
gcloud services enable iam.googleapis.com iamcredentials.googleapis.com --project="$APIGEE_PROJECT_ID"
gcloud services list --enabled --project="$VERTEX_PROJECT_ID" \
  --filter='config.name=aiplatform.googleapis.com' --format='value(config.name)'
gcloud iam service-accounts describe "$SA_EMAIL" --project="$APIGEE_PROJECT_ID"
```

The service list must include `aiplatform.googleapis.com`. Create the account only if `describe` reports `NOT_FOUND`, not `PERMISSION_DENIED`:

```bash
gcloud iam service-accounts create "$SA_NAME" --project="$APIGEE_PROJECT_ID" \
  --display-name="Apigee Vertex AI proxy"
```

Inspect existing bindings first. Run only missing grants. These are unconditional evaluation grants; use administrator-approved conditions if your organization requires them.

```bash
gcloud projects get-iam-policy "$VERTEX_PROJECT_ID" --format=json
gcloud iam service-accounts get-iam-policy "$SA_EMAIL" --project="$APIGEE_PROJECT_ID" --format=json

# Runtime invocation in the Vertex project
gcloud projects add-iam-policy-binding "$VERTEX_PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" --role=roles/aiplatform.user --condition=None
# Deployer can attach the proxy identity
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" --project="$APIGEE_PROJECT_ID" \
  --member="$DEPLOYER_MEMBER" --role=roles/iam.serviceAccountUser --condition=None
# Apigee can mint tokens for that identity
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" --project="$APIGEE_PROJECT_ID" \
  --member="serviceAccount:service-${APIGEE_PROJECT_NUMBER}@gcp-sa-apigee.iam.gserviceaccount.com" \
  --role=roles/iam.serviceAccountTokenCreator --condition=None

# Read back the exact account and bindings after writes
gcloud iam service-accounts describe "$SA_EMAIL" --project="$APIGEE_PROJECT_ID"
gcloud iam service-accounts get-iam-policy "$SA_EMAIL" --project="$APIGEE_PROJECT_ID" --format=json
gcloud projects get-iam-policy "$VERTEX_PROJECT_ID" --format=json
gcloud services list --enabled --project="$APIGEE_PROJECT_ID" \
  --filter='config.name=iam.googleapis.com OR config.name=iamcredentials.googleapis.com' --format='value(config.name)'
```

Verify the account is enabled and bindings name the intended principals. Import permission is separate. Never create a service-account JSON key or store access tokens in a KVM.

If a model is denied by `constraints/vertexai.allowedModels`, inspect the effective policy:

```bash
gcloud org-policies describe vertexai.allowedModels --project="$VERTEX_PROJECT_ID" --effective --format=yaml
```

If this requires `orgpolicy.googleapis.com`, the operator may enable that API with permission; enabling it does not relax model restrictions. Choose an approved compatible model or ask the administrator. More IAM grants cannot override this policy.

## Target composition

Read the [official TargetEndpoint authentication reference](https://cloud.google.com/apigee/docs/api-platform/reference/api-proxy-configuration-reference#authentication-element-usage) before generating XML. Merge this connection into the TargetEndpoint and replace the URL placeholder with the approved full URL.

Example source: `../assets/examples/target/vertex-connection.xml`

```xml
<HTTPTargetConnection>
  <Authentication>
    <GoogleAccessToken>
      <Scopes><Scope>https://www.googleapis.com/auth/cloud-platform</Scope></Scopes>
    </GoogleAccessToken>
  </Authentication>
  <URL>__VERTEX_CHAT_COMPLETIONS_URL__</URL>
</HTTPTargetConnection>
```

In the TargetEndpoint request flow, retain `AM-PrepareTargetRequest` from [routing](model-routing.md#target-request-preparation): it removes caller `Authorization` and `x-api-key` headers and disables suffix copying. Caller verification must already have run. For Vertex, omit the upstream KVM lookup, its missing-key guard and `AM-SetUpstreamAuth`; native authentication inserts the Google access token at dispatch. Never mix static Bearer assignment with native authentication. Keep the external/KVM route unchanged.

Before handing over the ZIP, give the operator the exact service-account email and instructions to select it during deployment in the Apigee UI. Import alone does not attach the identity. For CLI deployment, inspect installed command help before producing flags. Read back the exact revision's deployment, service account and READY state before testing. See [Google authentication deployment](https://docs.cloud.google.com/apigee/docs/api-platform/security/google-auth/overview).

## Usage and bounded acceptance

Preserve upstream response fields, including usage and model metadata. For token quota, use `usage.total_tokens`; do not reconstruct it from visible completion tokens. In the cost calculation, select `usageMode=vertex-total-minus-prompt` only for this text-only Vertex route: output tokens are `total_tokens - prompt_tokens`, including reasoning. Do not add `reasoning_tokens` again. Validate that total is at least prompt plus visible completion; missing or inconsistent usage follows the agreed missing-cost error path. The default external calculation remains unchanged. Use synthetic prices for the lab; this is not billing reconciliation or support for multimodal pricing.

Run the [routing acceptance cases](model-routing.md#acceptance-cases) for both aliases. Use small text requests, `stream: false` and an agreed output allowance (for example 256 tokens). A tiny allowance can be spent on reasoning: HTTP 200 with `finish_reason: "length"` is not a complete answer. Record that outcome rather than retrying automatically. Confirm `finish_reason: "stop"` for a complete-text check.

For later labs, verify quota rejection, reasoning-inclusive cost counting and budget rejection, and Armor benign/block cases independently on the generated Vertex proxy. API Product LLM model names must match the exact resolved `google/<MODEL_ID>`, not caller aliases. See [cost budget](cost-budget.md) and [API product setup](api-product-setup.md).

## Sources

- [Vertex OpenAI compatibility](https://cloud.google.com/vertex-ai/generative-ai/docs/start/openai)
- [Model access policy](https://cloud.google.com/vertex-ai/generative-ai/docs/control-model-access)
- [Apigee Google authentication](https://docs.cloud.google.com/apigee/docs/api-platform/security/google-auth/overview)
