# Model Armor — template and identity setup

This file covers the cloud side of Model Armor: location, the template, and the proxy's service account. For policy XML and runtime checks, use the [Model Armor workflow](model-armor.md#basic-integration-render-and-merge-into-the-existing-gateway). See [capability status](capability-status.md).

The agent prepares commands; the operator runs them. Every cloud write (API enablement, template creation, IAM grants) needs explicit user approval first.

## Location gate before commands

Agree the template location before writing any concrete command. Never default to a tutorial region, the gcloud default or the Apigee runtime region.

- **Reuse.** With read approval, GET the exact `projects/PROJECT/locations/LOCATION/templates/TEMPLATE`. Check its location, filters, thresholds and residency against requirements and current filter availability [5]. If the name is unknown, ask, or ask for read-only scope to list templates. If it doesn't fit, let the user choose between it and a new template. Never move or edit a shared template.
- **Create.** Agree location, residency, filters and thresholds against [5] first. Keep `__APPROVED_TEMPLATE_LOCATION__` as a placeholder until then. On conflicts the user chooses; never change region, drop residency or weaken filters yourself. Agreeing a location approves nothing else.
- **Endpoint.** Use the management endpoint for the template's location. The Apigee policy reaches the right region through the full TemplateName ([Known limitations](#known-limitations)).
- **Placeholders.** `__TEMPLATE_LOCATION__` equals the approved location. Fill it, `__TEMPLATE_PROJECT__` and `__TEMPLATE_ID__` only from the approved template's readback. Reject unresolved placeholders before running or importing anything.

## Reuse or create a template

1. **Check what exists.** Pass the location gate and confirm the project. Check the Model Armor API is enabled. A disabled API or denied access means "unknown", not "none". Request enablement as its own approval.
2. **Reuse.** List templates in the approved location (follow pagination). GET the chosen one and show filters, thresholds, metadata and `updateTime`. Ask who else uses it. For a shared template, offer a dedicated one instead of editing it.
3. **Create.** Collect the template ID, Responsible AI categories and an explicit confidence for each. `LOW_AND_ABOVE` blocks more (and has more false positives) than `HIGH` [3]. Set jailbreak/prompt-injection confidence if enabled. Basic Sensitive Data Protection (SDP) checks six fixed info-types with no DLP template. Advanced SDP needs separately approved DLP templates and IAM.
4. **Write the full payload.** Include every chosen field or accepted documented default: filters, confidence levels, `ignorePartialInvocationFailures`, `enforcementType`, `dataResidencyCompliant`, modalities, `filterVersionSelector`, `multiLanguageDetection`. Use exact enums from [3] (`MODALITY_TEXT`, `FILTER_VERSION_ALIAS_STABLE`). `STABLE` moves over time; pinning a version is a separate choice. Set thresholds explicitly. Basic and advanced SDP are mutually exclusive. Add custom errors only if the user chose them.
5. **Logging.** Approve `logTemplateOperations` and `logSanitizeOperations` separately. Sanitize logging records **full prompts and responses** [6]. Recommend `false` for both. Raw logging needs agreed access, retention, regional sink and cost. Audit logs and Apigee debug masking are separate controls.
6. **IAM.** The creator needs `modelarmor.templates.create` on the parent [4]. The proxy's deployment service account needs `roles/modelarmor.user` and `roles/modelarmor.viewer` [1,2] on the template's project [7]. Check effective access and propose only missing bindings. Never propose Owner or Editor. A human's access is not runtime access.
7. **Get approval.** Show the exact enablement, payload, name, location, each IAM principal/role/resource, data handling, cost and verification plan. The user may approve a subset. Approving creation does not approve deployment, scans, model calls or IAM.
8. **Run what was approved.** Check installed `gcloud` help, or use REST [3,4] for fields the CLI lacks. Pass endpoints explicitly; don't change global gcloud config. Create with a UUID `requestId` and reuse it for retries within 60 minutes. On timeout or conflict, GET and reconcile before retrying.
9. **Read back.** Recheck the API, the template and changed IAM policies. Compare against the approved payload. For reuse, compare configuration and `updateTime` before and after. On mismatch, stop and report; don't patch or delete automatically. Keep evidence masked and private.
10. **Hand off.** Give the verified template name and the [manual pre-import handoff](#manual-pre-import-handoff) before the ZIP. Check [Known limitations](#known-limitations), then get separate approval to deploy the exact revision and run a small test.

### Manual pre-import handoff

Before sharing the ZIP, label each prerequisite verified, missing or unknown, and give the operator instructions.

With read approval, check the deployment's current `serviceAccount` and reuse it if suitable. Never guess it from the active gcloud account. If unknown, ask whether to reuse or create one. Note that new grants widen access and that changing identity affects other policies. No keys are needed.

| Stage | Principal and scope | Check |
|---|---|---|
| ZIP import | Operator's Apigee import permissions | Separate from runtime roles. |
| Deployment | Operator: `iam.serviceAccounts.actAs`; Apigee service agent: token creation, both on the selected service account [8] | Exact service account in the Apigee project, as in the sample [11,12]. |
| Runtime | Proxy service account: `roles/modelarmor.user` and `roles/modelarmor.viewer` on the template project [1,2,7] | API, template and effective permissions. |

Write commands only for missing setup the user chose. Leave unknown values as placeholders and ask. `__DEPLOYER_MEMBER__` includes its type (`user:EMAIL` or `serviceAccount:EMAIL`). `__APIGEE_PROJECT_NUMBER__` is the numeric project number. Check inherited and conditional access first, and preserve existing bindings.

```bash
# Optional: only when the user chooses a new dedicated SA.
gcloud iam service-accounts create __PROXY_SA_ID__ \
  --project=__APIGEE_PROJECT__ --display-name="Apigee Model Armor proxy"

# Runtime roles granted TO the selected SA ON the template project.
gcloud projects add-iam-policy-binding __TEMPLATE_PROJECT__ \
  --member="serviceAccount:__PROXY_SA_EMAIL__" --role=roles/modelarmor.user
gcloud projects add-iam-policy-binding __TEMPLATE_PROJECT__ \
  --member="serviceAccount:__PROXY_SA_EMAIL__" --role=roles/modelarmor.viewer

# Deployment permissions ON this specific SA, not the whole project.
gcloud iam service-accounts add-iam-policy-binding __PROXY_SA_EMAIL__ \
  --project=__APIGEE_PROJECT__ --member="__DEPLOYER_MEMBER__" \
  --role=roles/iam.serviceAccountUser
gcloud iam service-accounts add-iam-policy-binding __PROXY_SA_EMAIL__ \
  --project=__APIGEE_PROJECT__ \
  --member="serviceAccount:service-__APIGEE_PROJECT_NUMBER__@gcp-sa-apigee.iam.gserviceaccount.com" \
  --role=roles/iam.serviceAccountTokenCreator
```

- Let the user choose conditional or unconditional grants. Never add `--condition=None` silently.
- If the operator lacks IAM authority, an administrator must act. Don't suggest Owner, Editor or broad `modelarmor.admin` grants.
- If the API is disabled, list `gcloud services enable modelarmor.googleapis.com --project=__TEMPLATE_PROJECT__` as its own approved step.

**Verify** with these read-only checks. Inspect members, conditions, disabled status and inherited access.

```bash
gcloud iam service-accounts describe __PROXY_SA_EMAIL__ --project=__APIGEE_PROJECT__
gcloud projects get-iam-policy __TEMPLATE_PROJECT__ --format=json
gcloud iam service-accounts get-iam-policy __PROXY_SA_EMAIL__ \
  --project=__APIGEE_PROJECT__ --format=json
gcloud services list --enabled --project=__TEMPLATE_PROJECT__
```

**Deploy with the identity.** After import, select `__PROXY_SA_EMAIL__` when deploying the exact revision. Import doesn't attach an identity and revisions don't inherit one. If the console lacks the field, use the `serviceAccount` deployment parameter [8] or `apigeecli -s` [11,12].

**Read back the deployment** with `GET https://apigee.googleapis.com/v1/organizations/__ORG__/apis/__PROXY__/deployments`, keeping the token out of shell arguments. Match environment, revision, `serviceAccount` and readiness, then GET the template. Finally run the approved [live acceptance checks](model-armor.md#offline-checks-and-live-acceptance); readback alone doesn't show that inspection works.

### Management API reference

Run only after approval. Check installed `gcloud model-armor templates` help before using flags. Don't change the global account, project or region. The regional base URL is `https://modelarmor.__TEMPLATE_LOCATION__.rep.googleapis.com` [6].

| Operation | Method and path, relative to the regional base |
|---|---|
| List | GET /v1/projects/__TEMPLATE_PROJECT__/locations/__TEMPLATE_LOCATION__/templates; follow nextPageToken |
| Read one | GET /v1/projects/__TEMPLATE_PROJECT__/locations/__TEMPLATE_LOCATION__/templates/__TEMPLATE_ID__ |
| Create (approved only) | POST /v1/projects/__TEMPLATE_PROJECT__/locations/__TEMPLATE_LOCATION__/templates?templateId=__TEMPLATE_ID__&requestId=__REQUEST_UUID__; body is the approved Template JSON [3,4] |

Validate and URL-encode identifiers. Keep tokens in memory and auth headers and raw errors out of logs. Use the regional hostname for the approved location; the global `modelarmor.googleapis.com` host says nothing about residency.

## Known limitations

This skill supports the native SanitizeUserPrompt and SanitizeModelResponse policies with the template and service account in one project. If the user needs any of the following, stop and ask.

- **Same project, one identity.** Cross-project templates, or different service accounts for the proxy and shared flow, are not covered [11,12]. Don't add Authentication XML or reuse target credentials.
- **Block only.** Observe-only (`INSPECT_ONLY`), selective fail-open and `ignorePartialInvocationFailures`-dependent behavior are not covered. The workflow [rejects incomplete results](model-armor.md#basic-integration-render-and-merge-into-the-existing-gateway) explicitly.
- **No redaction.** The policies inspect and block; they don't rewrite payloads.
- **Regional endpoint.** It comes from the full TemplateName. Add no endpoint XML. Confirm hard residency requirements with product documentation or support before sending data.
- **Verify at runtime.** Confirm schema acceptance, fault codes and error mapping with a masked live test.
- **Least privilege.** Use the User and Viewer roles, not the sample's broad grants.

Recheck current documentation before use. Don't substitute REST callouts for an unsupported path.

## Official sources

1. [SanitizeUserPrompt](https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/sanitize-user-prompt-policy) — prompt policy syntax, prerequisites and faults.
2. [SanitizeModelResponse](https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/sanitize-llm-response-policy) — response policy syntax, faults and variables.
3. [Template schema](https://docs.cloud.google.com/model-armor/reference/rest/v1/projects.locations.templates) — filters, thresholds, SDP and enums.
4. [Create template](https://docs.cloud.google.com/model-armor/reference/rest/v1/projects.locations.templates/create) — request body, permission and `requestId`.
5. [Feature availability by region](https://docs.cloud.google.com/model-armor/feature-availability-by-region) — locations, residency and filters.
6. [Configure logging](https://docs.cloud.google.com/model-armor/configure-logging) — regional endpoints and logging.
7. [Model Armor IAM access control](https://docs.cloud.google.com/model-armor/access-control/access-control-iam) — roles and grant scope.
8. [Apigee Google authentication](https://docs.cloud.google.com/apigee/docs/api-platform/security/google-auth/overview) — deployment service account permissions.
9. [Model Armor quotas and limits](https://docs.cloud.google.com/model-armor/quotas) — quotas and over-limit behavior.
10. [Model Armor pricing](https://cloud.google.com/security/products/model-armor#pricing) — current pricing.
11. [Official native-policy sample](https://github.com/GoogleCloudPlatform/apigee-samples/tree/b007d721ace3028dd64e5c7841263ed860720043/llm-security-v2) — native XML, regional setup and deployment.
12. [Sample deployment/IAM helpers](https://github.com/GoogleCloudPlatform/apigee-samples/blob/b007d721ace3028dd64e5c7841263ed860720043/shlib/utils.sh) — service account at deployment and role binding.
