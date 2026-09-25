# Semantic caching for FAQ answers (trial)

## Scope and evidence boundary

Use native **SemanticCacheLookup** and **SemanticCachePopulate** on the **existing working proxy** to reuse FAQ answers that are:

- non-sensitive, text-only, single-turn and non-streaming;
- from one approved app with a fixed model, configuration, system prompt and content version;
- safe to share with **every eligible caller**. Approving one app does not make an answer shareable.

Personalized, confidential, multi-tenant, tool, RAG, variable-context and general chat traffic keeps its existing uncached behavior.

Caching is disabled by default. Enable it only after the [cache trial and enablement checklist](#cache-trial-and-enablement-checklist) passes; see [capability status](capability-status.md).

Take policy syntax from the XML below and flow mechanics from the pinned `apigee-x-proxy-development` skill ([dependency map](dependency-map.md#capability-ownership-and-precise-dependency-references)). Check availability, models and regions in the [Lookup][lookup], [Populate][populate], [public tutorial][public] and [PSC tutorial][psc] pages, or ask the user.

### How it works

- **Two stores.** Apigee's cache holds answers; Vertex AI Vector Search holds prompt vectors. Lookup embeds the prompt, finds the nearest vector and fetches its answer.
- **Two hit flags.** `SemanticCacheLookup.SCL-LookupFAQ.is_nearest_neighbor_hit` means a close vector exists; `SemanticCacheLookup.SCL-LookupFAQ.cache_hit` means an answer was returned. Use `cache_hit`.
- **Hits skip the model.** A hit returns the cached response (`Cached-Content: true`) without calling the target ([PSC tutorial][psc]). Add no null RouteRule and no AssignMessage copying `.cached_llm_response`.
- **Prompt source.** The default reads only the last Gemini text part. Set `UserPromptSource` to a validated, complete scalar prompt; OpenAI messages need their own extraction.
- **Fixed context.** Freeze model, system instructions, locale, answer format, generation settings and content version. Bypass the cache and review freshness when any change.

### Prerequisites

- An **Intermediate or Comprehensive** environment with the Extensible-policy entitlement, APIs and billing.
- An embedding model and a deployed **STREAM_UPDATE** index. Create missing resources with the [Vertex setup guide](semantic-cache-vertex-setup.md).
- **Dimensions.** Index dimensions must match the model's output ([model choices](semantic-cache-vertex-setup.md#1-explain-and-approve-the-proposed-path), [supported models][embeddings]). The PSC tutorial uses `gemini-embedding-001` at 3072. The XML has no dimension or task-type setting. Never mix models or dimensions in one index.
- **Metric and threshold.** Match normalization, metric and threshold direction ([metric choices](semantic-cache-vertex-setup.md#1-explain-and-approve-the-proposed-path)). `DistanceMeasureType` needs runtime **1-18-0-apigee-4 or later**; older runtimes ignore it and use dot product. Dot product matches **>=** the threshold; cosine, squared L2 and L1 match **<=**. The default 0.9 and tutorial 0.95 are starting cutoffs, not confidence scores.
- **Size.** Cacheable text is at most **256 KB**; enforce a smaller response limit.

### Limits

- No tenant, app, cache-key or filter selector exists. Separate indexes narrow candidates; a second endpoint on the same index does not.
- Similarity, TTL, Model Armor and identifiers in prompts are not authorization boundaries.
- Cache-key scope, and which Steps, headers and metadata apply on a hit, are undocumented. Confirm them in the HIT check.
- Upstream `Cache-Control` is ignored. Continuous SSE (EventFlows) is unsupported. Hits still pay embedding and search latency.

## Decisions before rendering or setup

Ask only for open decisions; explain tradeoffs.

| Decision | What to agree |
|---|---|
| Eligibility | Authenticated app and operation, fixed model and context version, complete prompt source, non-sensitive corpus, sharing boundary. |
| Accounting | Quota and burst admission stay before Lookup. Each fresh generation counts once; withheld output counts only if the existing contract says so. Hits never debit historical usage but do use burst allowance. Serving hits after quota exhaustion needs a changed contract. |
| Hit response | Current-prompt inspection, privacy, headers, status, IDs, timestamps, model and usage fields. Never replay routing data, label old usage as fresh, or invent zero-token usage. |
| Freshness | A positive TTL (zero does not disable caching), a metric-matched threshold, version-change behavior and acceptable wrong-answer risk. |
| Dependencies | The [Vertex choices](semantic-cache-vertex-setup.md#1-explain-and-approve-the-proposed-path): region and residency first, capacity, transport, model, dimensions and IAM. Keep `__APPROVED_REGION__` until agreed. |
| Outages | Strict failure, or a separately built bypass. `continueOnError="true"` is not a fallback. Auth, quota, Armor and privacy failures never become misses. |
| Approvals | Separate approvals for inventory, setup, deploy and trial. Before writes, agree time, request, token and cost limits, plus a cleanup owner, deadline and budget. |

## Native XML and merge guide

Copy these into a **new private output**, keeping the working bundle. Escape for XML and resolve every `__PLACEHOLDER__` with confirmed values. Single braces are runtime templates.

| Placeholder / variable | Value |
|---|---|
| `__EMBEDDING_URL__` | `https://LOCATION-aiplatform.googleapis.com/v1/projects/PROJECT_ID/locations/LOCATION/publishers/google/models/MODEL_ID:predict`. Always HTTPS. |
| `__FIND_NEIGHBORS_URL__` | Public search: `https://PUBLIC_DOMAIN_NAME/v1/projects/PROJECT_ID/locations/LOCATION/indexEndpoints/INDEX_ENDPOINT_ID:findNeighbors`, using the endpoint's real domain. |
| `__UPSERT_URL__` | `https://LOCATION-aiplatform.googleapis.com/v1/projects/PROJECT_ID/locations/LOCATION/indexes/INDEX_ID:upsertDatapoints`, with the **index** ID. Populate always uses REST. |
| `__DEPLOYED_INDEX_ID__` | Exact deployment ID of the upsert index. Keep index, endpoint and deployment IDs distinct. |
| `__DISTANCE_MEASURE__`, `__THRESHOLD__` | `DOT_PRODUCT_DISTANCE`, `COSINE_DISTANCE`, `SQUARED_L2_DISTANCE` or `L1_DISTANCE`, matching the index; a finite threshold in the right direction. |
| `__TTL_SECONDS__` | Approved positive whole seconds. |
| `__PSC_TARGET_HOST__` | PSC only: the confirmed endpoint-attachment host. `grpc://` is plaintext and relies on network isolation; `grpcs://` is unsupported. PSC covers search only. |
| `private.semantic.enabled`, `.eligible`, `.prompt` | Your own variables. Set `enabled` and `eligible` false at the start of each request. `enabled` comes from trusted server configuration; `eligible` and `prompt` from authenticated eligibility checks. Never from the caller. |
| Policy and group placeholders | Existing policy names, or groups expanded into ordered Steps. |
| `__APPROVED_FRESH_COUNT_CONDITION__` | Existing usage and error conditions plus a verified fresh-generation marker. The hit flag or HTTP success alone is not enough. |
| `__APPROVED_SAFE_POPULATE_CONDITION__` | Lookup missed; fresh generation; approved status, shape and size; all inspections completed and passed; whole-envelope privacy passed. |

The lookup uses **public REST**. For PSC, replace the whole `SimilaritySearch` block with the PSC fragment; never include both. Always include `<Embeddings>`.

Example source: `../assets/examples/semantic-cache/SCL-LookupFAQ.xml`

```xml
<SemanticCacheLookup name="SCL-LookupFAQ" continueOnError="false" enabled="true">
  <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
  <UserPromptSource>{private.semantic.prompt}</UserPromptSource>
  <Embeddings>
    <VertexAI>
      <URL>__EMBEDDING_URL__</URL>
    </VertexAI>
  </Embeddings>
  <SimilaritySearch>
    <VertexAI>
      <URL>__FIND_NEIGHBORS_URL__</URL>
      <Threshold>__THRESHOLD__</Threshold>
      <DeployedIndexID>__DEPLOYED_INDEX_ID__</DeployedIndexID>
      <DistanceMeasureType>__DISTANCE_MEASURE__</DistanceMeasureType>
    </VertexAI>
  </SimilaritySearch>
</SemanticCacheLookup>
```

Example source: `../assets/examples/semantic-cache/SCP-PopulateFAQ.xml`

```xml
<SemanticCachePopulate name="SCP-PopulateFAQ" continueOnError="false" enabled="true">
  <IgnoreUnresolvedVariables>false</IgnoreUnresolvedVariables>
  <SimilaritySearch>
    <VertexAI>
      <URL>__UPSERT_URL__</URL>
    </VertexAI>
  </SimilaritySearch>
  <TTLInSeconds>__TTL_SECONDS__</TTLInSeconds>
</SemanticCachePopulate>
```

Example source: `../assets/examples/semantic-cache/psc-search-fragment.xml`

```xml
<!-- Replace the lookup SimilaritySearch block ONLY after choosing PSC. -->
<SimilaritySearch>
  <VertexAI>
    <PrivateServiceConnect>
      <GrpcEndpoint>grpc://__PSC_TARGET_HOST__:10000</GrpcEndpoint>
    </PrivateServiceConnect>
    <Threshold>__THRESHOLD__</Threshold>
    <DeployedIndexID>__DEPLOYED_INDEX_ID__</DeployedIndexID>
    <DistanceMeasureType>__DISTANCE_MEASURE__</DistanceMeasureType>
  </VertexAI>
</SimilaritySearch>
```

Example source: `../assets/examples/semantic-cache/proxy-flow-fragment.xml`

```xml
<!-- Merge guide, NOT a deployable flow. Expand group placeholders into existing Steps.
     Hit-path execution and fresh-generation provenance MUST pass the runtime trial gate. -->
<PreFlow name="PreFlow">
  <Request>
    <Step><Name>__CALLER_AUTH_POLICY__</Name></Step>
    <Step><Name>__REQUEST_VALIDATION_POLICY__</Name></Step>
    <Step><Name>__CACHE_ELIGIBILITY_AND_PROMPT_POLICY__</Name></Step>
    <Step><Name>__EXISTING_QUOTA_AND_BURST_STEPS__</Name></Step>
    <Step><Name>__PROMPT_ARMOR_AND_COMPLETENESS_STEPS__</Name></Step>
    <Step>
      <Name>SCL-LookupFAQ</Name>
      <Condition>(private.semantic.enabled = true) and (private.semantic.eligible = true)</Condition>
    </Step>
  </Request>
  <Response>
    <Step>
      <Name>LTQ-Count</Name>
      <Condition>!(SemanticCacheLookup.SCL-LookupFAQ.cache_hit = true) and (__APPROVED_FRESH_COUNT_CONDITION__)</Condition>
    </Step>
    <Step><Name>__RESPONSE_ARMOR_VALIDATION_AND_PRIVACY_STEPS__</Name></Step>
    <Step>
      <Name>SCP-PopulateFAQ</Name>
      <Condition>(private.semantic.enabled = true) and (private.semantic.eligible = true) and (SemanticCacheLookup.SCL-LookupFAQ.cache_hit = false) and (__APPROVED_SAFE_POPULATE_CONDITION__)</Condition>
    </Step>
  </Response>
</PreFlow>
```

### Preserve existing flow behavior

Merge into the operation's ProxyEndpoint, keeping existing Steps and their order.

1. **Before Lookup.** Authenticate, validate, set trusted eligibility and prompt, run `LTQ-Enforce` and burst admission, then `SUP-InspectPrompt` with completeness checks for every enabled filter. Nothing reaches embeddings or search before this.
2. **Lookup** runs only when both gates are true. On a miss, routing, path preparation, model mapping and credential handling stay unchanged.
3. **Count.** `LTQ-Count` runs once, only for fresh generations. Embedding and Armor spend stay out of it.
4. **Populate last**, in the **ProxyEndpoint PreFlow Response** ([PSC tutorial][psc]), after `SMR-InspectResponse`, completeness and privacy checks, so it stores the sanitized response.
5. **Hits short-circuit** and may skip later Steps. Pass [HIT](#cache-trial-and-enablement-checklist) before enabling.

A missing or failed Lookup is a failure, not a miss. Check fault rules for leaked payloads or credentials.

## Manual pre-import handoff

Before a ZIP, record each prerequisite as **verified / missing / unknown**, with evidence, IDs and owner. The operator runs commands after approval, leaving global gcloud configuration unchanged.

1. **Scope.** Check the Apigee environment and entitlement, and the [Vertex setup path](semantic-cache-vertex-setup.md). Guide setup for missing resources; look up unknown ones only with approval. Keep Model Armor permissions.
2. **Read-only checks.** With approval, inspect IDs, dimensions, update method, metric and readiness:

```bash
gcloud ai indexes describe __INDEX_ID__ --project=__VECTOR_PROJECT_ID__ --region=__APPROVED_REGION__
gcloud ai index-endpoints describe __INDEX_ENDPOINT_ID__ --project=__VECTOR_PROJECT_ID__ --region=__APPROVED_REGION__
```

For PSC, follow the [tutorial readback][psc]: the endpoint attachment shows `state: ACTIVE`, `connectionState: ACCEPTED` and a reachable `host`.

3. **IAM.** Follow the [setup IAM analysis](semantic-cache-vertex-setup.md#2-operator-preparation-apis-and-identity). The proxy service account needs `roles/aiplatform.user` (or a reviewed equivalent) on Vertex projects; keep [Armor access](model-armor-setup.md#manual-pre-import-handoff). The deployer needs Apigee import and deploy rights and `roles/iam.serviceAccountUser` on that account. Render grants only when missing and approved; keep credentials out of XML.

```bash
gcloud projects add-iam-policy-binding __VERTEX_PROJECT_ID__ \
  --member="serviceAccount:__PROXY_SERVICE_ACCOUNT_EMAIL__" \
  --role="roles/aiplatform.user"
gcloud iam service-accounts add-iam-policy-binding __PROXY_SERVICE_ACCOUNT_EMAIL__ \
  --project=__SERVICE_ACCOUNT_PROJECT_ID__ \
  --member="user:__DEPLOYER_EMAIL__" \
  --role="roles/iam.serviceAccountUser"
```

Use `user:` only for a human deployer. Read back the policies with the [setup readbacks](semantic-cache-vertex-setup.md#2-operator-preparation-apis-and-identity).

4. **Render and review.** Resolve all placeholders. Implement eligibility, fresh-generation tracking, safe population and one switch that disables both policies. Check IDs and URL suffixes, one lookup transport, metric and model agreement, Step order and conditions, no secrets, and a ZIP rooted at `apiproxy/`. Apply [PREP and HIT](#cache-trial-and-enablement-checklist).
5. **Import and deploy.** The operator imports the ZIP in the Apigee UI, deploys that revision with the chosen service account and reads back READY. Keep the previous revision for rollback. Confirm masking before any capture.

## Retention, rollback and cost

`TTLInSeconds` expires answers and marks datapoints for expiry; it does not guarantee vector deletion. There is no cache-key purge or cross-store erase. Use [removeDatapoints][updates] only with known IDs and deletion approval.

Don't use the sample cleanup integration; agree your own retention and deletion. Stop writes if deletion can't meet the data policy.

Roll back by disabling **both Lookup and Populate**, or removing both in an approved revision. This doesn't erase data or stop charges. Tear down resources with [readbacks](semantic-cache-vertex-setup.md#6-stop-charges-and-clean-up-deliberately) under separate approval. Never delete the existing project.

Before provisioning, set a cost cap and cleanup deadline using [cost choices](semantic-cache-vertex-setup.md#1-explain-and-approve-the-proposed-path), [Vector Search pricing][pricing] and [embedding pricing][embedding-pricing]. Idle index nodes still bill and every lookup pays for embedding and search, so low-traffic caching can cost more than it saves.

## Checks and trial gates

Before any debug capture, mask credentials, caller identity, bodies, URLs, `private.*` variables and these native copies by full name:

- `SemanticCacheLookup.SCL-LookupFAQ.user_prompt`, `.embeddings_request`, `.embeddings_response`, `.dense_embeddings`, `.cached_llm_response`
- `SemanticCachePopulate.SCP-PopulateFAQ.upsert_index_request`, `.upsert_index_response`

Extracting to `private.*` doesn't mask these copies. Keep existing Armor and prompt-limit masking. Record sanitized flags and counter changes outside Git, never raw prompts, vectors or answers.

### Cache trial and enablement checklist

Record each gate as **pass / fail / unverified**; only the approved trial satisfies runtime gates, and all must pass before normal traffic. If HIT fails, leave caching disabled; don't build a custom cache.

| ID | When | Evidence |
|---|---|---|
| PREP | Before setup | [Decisions](#decisions-before-rendering-or-setup) and [handoff](#manual-pre-import-handoff) complete and approved. |
| BOUNDS | Before writes | Limits, cleanup owner and masking confirmed. No automatic retries. |
| HIT | First | Miss, then hit: both flags set, target not called, Steps run recorded, current-prompt checks applied, no Populate, no quota debit. A 200 alone is not enough. |
| QUALITY | Matching | Paraphrase hits; near-miss doesn't. Check `semanticcache.lookup.SCL-LookupFAQ.measure_type` and `.nearest_neighbor_measure`. |
| TTL | Expiry | Answer expires after TTL; a stale vector isn't a hit. |
| SAFETY | Safety | Blocked prompts skip embedding; blocked or oversized outputs don't populate. |
| ELIGIBILITY | Eligibility | Ineligible traffic, including chat, tools, streaming and personal content, never touches the cache and keeps its protections. |
| ACCOUNTING | Accounting | Fresh responses count once; hits add nothing; quota and routing unchanged. |
| OUTAGE | Failures | Dependency failures fail safely; disabling both restores uncached traffic. |
| RETENTION | Rollback | [Retention, rollback and cost](#retention-rollback-and-cost) agreed and cleanup approved. |

The two `semanticcache.lookup.*` variables use a different prefix from the other Lookup variables, as named in the [Lookup reference][lookup].

[lookup]: https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/semantic-cache-lookup-policy
[populate]: https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/semantic-cache-populate-policy
[public]: https://docs.cloud.google.com/apigee/docs/api-platform/tutorials/using-semantic-caching-policies
[psc]: https://docs.cloud.google.com/apigee/docs/api-platform/tutorials/using-semantic-caching-policies-psc
[embeddings]: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/text-embeddings-api
[updates]: https://docs.cloud.google.com/vertex-ai/docs/vector-search/update-rebuild-index
[pricing]: https://cloud.google.com/vertex-ai/pricing
[embedding-pricing]: https://cloud.google.com/vertex-ai/generative-ai/pricing
