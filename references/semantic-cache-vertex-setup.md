# Vertex prerequisites from zero (operator-run)

Use this before the [pre-import handoff](semantic-cache.md#manual-pre-import-handoff) when Vertex resources are missing. Explain components and collect choices rather than demanding finished IDs. Render one selected missing step, have the operator run it, then interpret its sanitized readback. Discover unknown existing resources through supplied evidence or separately approved read-only checks, not automatic creation.

Commands are **manual patterns**, not a top-to-bottom script. Replace every placeholder with an agreed value; stop on failure. Obtain separate approvals through the [trial checklist](semantic-cache.md#cache-trial-and-enablement-checklist). Do not run a full tutorial, change global gcloud configuration, import/deploy or send prompts during setup.

## 1. Explain and approve the proposed path

Explain the three components, not a generic “Vertex instance”:

- **Publisher embedding model:** managed Google `publishers/google/models/MODEL_ID:predict` converts text to vectors, separately from answer generation. Select an available regional model/API; this path needs no custom-model upload or endpoint deployment.
- **Vector Search index:** stores vectors, while Apigee stores answers. Start empty with **STREAM_UPDATE** so Populate can add entries; no initial embeddings file or Cloud Storage bucket is needed.
- **Index endpoint/deployment:** the endpoint exposes search; deployment reserves serving capacity. Index ID, endpoint ID and operator-chosen deployed-index ID differ. An undeployed index is not searchable.

Propose public REST for simplicity, but obtain approval: it is publicly reachable with required OAuth, not anonymous access. Never grant `allUsers` or `allAuthenticatedUsers`. Organization policy/VPC Service Controls may forbid it. For private search, stop public commands and plan network/allowlist, service attachment, Apigee attachment and reachability through the separately approved [PSC tutorial](https://docs.cloud.google.com/apigee/docs/api-platform/tutorials/using-semantic-caching-policies-psc). PSC search does not make embeddings/upserts private.

Agree region and residency **before rendering commands**. Keep `__APPROVED_REGION__` until then; there is no default region, and the tutorial's `us-central1` is only an example.

| Choice | Explain and obtain approval |
|---|---|
| Project and region | Select a billed project; never implicitly create a project/billing account. Agree residency and processing destinations for embeddings, vectors and Apigee answers. Separately check the exact model in [Generative AI model locations](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations) and the **Vector Search** column in [Vertex AI locations](https://docs.cloud.google.com/vertex-ai/docs/general/locations). Verify regional quota, shard/machine capacity, public/PSC reachability and organization/network restrictions through evidence or approved discovery. Index and endpoint must share a region. Co-locating with the embedding model and Apigee is recommended. The helper in step 5 assumes one Vertex project and region; review any other layout explicitly. Keep regional hostnames, not `global`. Check cross-project constraints; stop and redesign if no approved location intersection exists. |
| Model and dimensions | Candidates: `gemini-embedding-001` / default **3072**, or supported-table `text-embedding-005` and `text-multilingual-embedding-002` / default **768**. Obtain a choice. Native XML cannot set `outputDimensionality`, task type or truncation; do not reduce dimensions for cost. Recheck native compatibility and verify actual output dimensions during the approved trial. Never mix versions/dimensions in one index. |
| Metric and quality | Example `DOT_PRODUCT_DISTANCE` / `UNIT_L2_NORM` follows Vertex cosine-like ranking advice. Direct `COSINE_DISTANCE` is an alternative with a different threshold. Vertex dot-product distance is negative dot product; Apigee matches dot product **>=** and cosine **<=**. Never infer Apigee signs from raw Vertex distances or reuse cosine thresholds. Match native `DistanceMeasureType` to the index and verify applied measure/direction on runtime 1-18-0-apigee-4 or later. Treat `0.90` and `0.95` as candidate thresholds. Evaluate them with representative paraphrases and near-but-wrong questions, within the approved test limits; they are not confidence scores. |
| Capacity and retained costs | Approve shard size, machine, replica bounds, tuning, quota and corpus/QPS. Verify [shard/machine compatibility](https://docs.cloud.google.com/vertex-ai/docs/vector-search/create-manage-index) for illustrative `SHARD_SIZE_SMALL` / `e2-standard-2`. One replica is acceptable for a non-HA test, not for production; fewer than two per shard is excluded from the SLA, and Google recommends at least two. Set both replica bounds explicitly; they apply per shard, not as a spend cap. |
| Authorization and cost limits | Separately approve inventory, setup and IAM, import and deploy, test probes and destructive cleanup. Record owner, retained-spend/duration limits, cleanup deadline and failure/timeout plan. Alerts do not stop charges. Include idle serving, embeddings, inserts/build/compaction, networking and Apigee/Armor/backend costs using [Vector Search pricing](https://cloud.google.com/vertex-ai/pricing) and [embedding pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing). |

## 2. Operator preparation, APIs and identity

Use operator-managed authenticated gcloud and private files outside Git. Approved existing user sessions, workload identity federation or impersonation can supply credentials; interactive login is not required. Manual execution is this workflow, not a CLI requirement or agent authorization. Use existing credentials without printing/exporting tokens, `set -x`, `--log-http` or embedded secrets. Keep tokens, keys, credential files, raw IAM/logs out of chat; provide sanitized summaries and keep exact resources privately for rendering.

The creator needs reviewed index/endpoint create/deploy/read permissions; API enablement needs `serviceusage.services.enable`, and IAM changes need policy read/write access. Administrators scope access to selected resources/operations, using approved custom roles where appropriate. Never grant Owner, Editor, Vertex AI Admin or project-wide actAs merely for setup. Keep the runtime service account separate from infrastructure operation.

After read-only approval, list enabled APIs in the selected project:

```bash
export VERTEX_PROJECT_ID='__VERTEX_PROJECT_ID__'
export VERTEX_REGION='__APPROVED_REGION__'
export EMBEDDING_MODEL_ID='__EMBEDDING_MODEL_ID__'
gcloud services list --enabled --project="$VERTEX_PROJECT_ID" --format=json
```

Verify billing in the project console. The Apigee public tutorial lists Vertex AI (`aiplatform.googleapis.com`), Compute Engine (`compute.googleapis.com`) and Cloud Storage (`storage.googleapis.com`). Enable only approved missing services, one per invocation. This creates no bucket, network or VM:

```bash
gcloud services enable __APPROVED_MISSING_API_SERVICE_NAME__ --project="$VERTEX_PROJECT_ID"
gcloud services list --enabled --project="$VERTEX_PROJECT_ID" --format=json
```

Read back enabled services; preserve existing Apigee/Armor APIs/IAM. Prefer the current proxy deployment service account, inspecting the exact deployment in Apigee UI if unknown. Create an account only after separate identity/naming/lifecycle approval through its administrator.

The native tutorial documents runtime `roles/aiplatform.user`, not index-only least privilege. Explain its scope; obtain specific approval for it or for an administrator-reviewed custom equivalent. Render approved missing bindings in the [IAM handoff](semantic-cache.md#manual-pre-import-handoff): the runtime project `roles/aiplatform.user` binding and the human deployer's account-scoped `roles/iam.serviceAccountUser` binding. Runtime needs no self-grant of actAs; explicitly render another deployer principal type rather than using the human template.

Read back each exact target after a grant (private operator inspection):

```bash
gcloud projects get-iam-policy "$VERTEX_PROJECT_ID" --format=json
gcloud iam service-accounts get-iam-policy __PROXY_SERVICE_ACCOUNT_EMAIL__ \
  --project=__SERVICE_ACCOUNT_PROJECT_ID__ --format=json
```

Check exact member/role/resource/conditions and administrator-confirmed effective access, including inheritance, deny policies and cross-project constraints. Preserve Armor/backend access; keep import/deploy permissions separate and keys out of policy XML.

## 3. Render metadata and create the streaming index

Provide a rendered private `index-metadata.json` for operator inspection. This template is the contents of `metadata`, as required by `--metadata-file`, not a request with an outer `metadata` field. Numeric placeholders are quoted only for template JSON validity. Replace entire quoted numeric placeholders with JSON numbers; leave no placeholders or numeric strings.

```json
{
  "config": {
    "dimensions": "__DIMENSIONS_INTEGER__",
    "approximateNeighborsCount": "__NEIGHBORS_INTEGER__",
    "distanceMeasureType": "__DISTANCE_MEASURE__",
    "featureNormType": "__FEATURE_NORM_TYPE__",
    "shardSize": "__SHARD_SIZE__",
    "algorithmConfig": {
      "treeAhConfig": {
        "leafNodeEmbeddingCount": "__LEAF_EMBEDDINGS_INTEGER__",
        "fractionLeafNodesToSearch": "__SEARCH_FRACTION_NUMBER__"
      }
    }
  }
}
```

Propose, then obtain approval for: dimensions `3072`, neighbors `150`, metric `DOT_PRODUCT_DISTANCE`, normalization `UNIT_L2_NORM`, shard `SHARD_SIZE_SMALL`, leaf embeddings `1000`, search fraction `0.05`. These are unmeasured tuning choices; fraction must be strictly between zero and one ([configuration fields](https://docs.cloud.google.com/vertex-ai/docs/vector-search/configuring-indexes)). Omit `contentsDeltaUri` for an [empty streaming index](https://docs.cloud.google.com/vertex-ai/docs/vector-search/create-manage-index); never upload synthetic FAQs merely for creation.

After rendering and setup approval, the operator validates JSON syntax and creates the index:

```bash
python3 -m json.tool index-metadata.json
gcloud ai indexes create --project="$VERTEX_PROJECT_ID" --region="$VERTEX_REGION" \
  --display-name=__APPROVED_INDEX_DISPLAY_NAME__ \
  --metadata-file=index-metadata.json --index-update-method=stream-update
```

Record the long-running operation/resource names privately. On timeout, inspect the original operation in the console or below; never repeat create. After successful completion, extract `INDEX_ID` from the resource name `projects/.../locations/.../indexes/INDEX_ID`, not the operation ID or display name.

```bash
gcloud ai operations describe __RETURNED_OPERATION_RESOURCE_NAME__ \
  --project="$VERTEX_PROJECT_ID" --region="$VERTEX_REGION" --format=json
export INDEX_ID='__CREATED_INDEX_ID__'
gcloud ai indexes describe "$INDEX_ID" \
  --project="$VERTEX_PROJECT_ID" --region="$VERTEX_REGION" --format=json > index-readback.json
```

Pass the full returned operation name, preserving index/endpoint parents; for a short operation ID, CLI help also supports `--index` / `--index-endpoint`. Require `done: true` without `error`; a done operation can have failed. Inspect `index-readback.json` for exact project/location/name, `indexUpdateMethod: STREAM_UPDATE`, and `metadata.config` dimensions, metric, normalization, shard and algorithm. Stop if any field differs.

## 4. Create the approved public endpoint and deploy the index

**Only if public REST exposure was explicitly approved**, render and run:

```bash
gcloud ai index-endpoints create --project="$VERTEX_PROJECT_ID" --region="$VERTEX_REGION" \
  --display-name=__APPROVED_ENDPOINT_DISPLAY_NAME__ --public-endpoint-enabled
```

Wait for successful operation completion as above. Extract `INDEX_ENDPOINT_ID` from the returned endpoint resource name, never display-name substrings or the first listed item. Read back the exact endpoint and require `publicEndpointEnabled: true`:

```bash
export INDEX_ENDPOINT_ID='__CREATED_INDEX_ENDPOINT_ID__'
gcloud ai index-endpoints describe "$INDEX_ENDPOINT_ID" \
  --project="$VERTEX_PROJECT_ID" --region="$VERTEX_REGION" --format=json > endpoint-readback.json
```

Choose and record a deployed-index ID unique on this endpoint, beginning with a letter and containing only letters/digits/underscores, such as `faq_cache_v1`; this is your label, not a generated numeric ID. Obtain separate capacity/cost approval before deployment:

```bash
export DEPLOYED_INDEX_ID='__APPROVED_DEPLOYED_INDEX_ID__'
gcloud ai index-endpoints deploy-index "$INDEX_ENDPOINT_ID" \
  --project="$VERTEX_PROJECT_ID" --region="$VERTEX_REGION" \
  --index="$INDEX_ID" --deployed-index-id="$DEPLOYED_INDEX_ID" \
  --display-name=__APPROVED_DEPLOYMENT_DISPLAY_NAME__ \
  --machine-type=__APPROVED_MACHINE_TYPE__ \
  --min-replica-count=__APPROVED_MIN_REPLICAS__ \
  --max-replica-count=__APPROVED_MAX_REPLICAS__
```

Follow the [public deployment guide](https://docs.cloud.google.com/vertex-ai/docs/vector-search/deploy-index-public) for OAuth/capacity/domain readback; private JWT issuer/audience flags do not belong here. This recipe does not select storage-optimized deployment. Deployment may take tens of minutes: inspect the original operation and console status rather than redeploying on timeout. Require completion without error, then refresh exact readbacks:

```bash
gcloud ai indexes describe "$INDEX_ID" \
  --project="$VERTEX_PROJECT_ID" --region="$VERTEX_REGION" --format=json > index-readback.json
gcloud ai index-endpoints describe "$INDEX_ENDPOINT_ID" \
  --project="$VERTEX_PROJECT_ID" --region="$VERTEX_REGION" --format=json > endpoint-readback.json
```

Require the selected `deployedIndexes` entry to match this exact index, approved machine/replicas and nonempty `publicEndpointDomainName`. Inspect readiness/synchronization (`indexSyncTime` when present); a domain/entry is not a successful query, and an empty index has no answer. Never invent endpoint `READY` fields or send unapproved embedding/search checks. If values, status or errors are unclear, stop and inspect them with the operator.

## 5. Derive policy values from exact readbacks, then hand off

This helper assumes the index and endpoint share one approved project and region. A separately approved multi-region design needs its own URL and residency checks.

The local-only helper checks saved JSON mapping and prints rendering URLs/ID without cloud calls. Use canonical index/endpoint resource names intact in their URLs: Vertex may return project numbers rather than IDs, so never reconstruct those paths. Confirm project identity with the operator; never guess public domains.

```bash
python3 - <<'PY'
import json, os, re
from urllib.parse import urlsplit
index = json.load(open('index-readback.json'))
endpoint = json.load(open('endpoint-readback.json'))
i = re.fullmatch(r'projects/([^/]+)/locations/([^/]+)/indexes/([^/]+)', index['name'])
e = re.fullmatch(r'projects/([^/]+)/locations/([^/]+)/indexEndpoints/([^/]+)', endpoint['name'])
assert i and e, 'Unexpected resource-name format'
assert i.group(1, 2) == e.group(1, 2), 'Different project or region'
assert i.group(2) == os.environ['VERTEX_REGION']
assert i.group(3) == os.environ['INDEX_ID']
assert e.group(3) == os.environ['INDEX_ENDPOINT_ID']
assert index['indexUpdateMethod'] == 'STREAM_UPDATE'
assert endpoint.get('publicEndpointEnabled') is True
selected = [d for d in endpoint.get('deployedIndexes', [])
            if d['id'] == os.environ['DEPLOYED_INDEX_ID']]
assert len(selected) == 1 and selected[0]['index'] == index['name'], 'Deployment mapping mismatch'
domain = endpoint['publicEndpointDomainName']
assert re.fullmatch(r'[A-Za-z0-9.-]+', domain) and domain.endswith('.vdb.vertexai.goog')
assert urlsplit('https://' + domain).hostname == domain.lower()
project, region, model = (os.environ[k] for k in
                         ('VERTEX_PROJECT_ID', 'VERTEX_REGION', 'EMBEDDING_MODEL_ID'))
assert all(re.fullmatch(r'[A-Za-z0-9-]+', s) and '__' not in s for s in (project, region, model))
print('INDEX_ID=' + i.group(3))
print('INDEX_ENDPOINT_ID=' + e.group(3))
print('__DEPLOYED_INDEX_ID__=' + selected[0]['id'])
print('__EMBEDDING_URL__=' + f'https://{region}-aiplatform.googleapis.com/v1/projects/{project}/locations/{region}/publishers/google/models/{model}:predict')
print('__UPSERT_URL__=' + f'https://{region}-aiplatform.googleapis.com/v1/{index["name"]}:upsertDatapoints')
print('__FIND_NEIGHBORS_URL__=' + f'https://{domain}/v1/{endpoint["name"]}:findNeighbors')
PY
```

Never execute printed output as shell commands or normalize IDs after assertions fail; stop for human inspection. Separately check IAM, dimensions, readiness and native schema. Before a ZIP, report verified/missing/unknown prerequisites, exact owned mapping, runtime identity, approved metric/model/capacity and retained-cost deadline. Share only approved private configuration summaries, not credentials. Return to [render/review and manual import](semantic-cache.md#manual-pre-import-handoff); the operator uploads/deploys. Apply [PREP, BOUNDS and HIT](semantic-cache.md#cache-trial-and-enablement-checklist) for trial authorization/evidence.

## 6. Stop charges and clean up deliberately

Apply the [retention/rollback requirements](semantic-cache.md#retention-rollback-and-cost); disabling both cache operations leaves reserved capacity and stored data. Notify the owner on setup failure/deadline, even without a deployed proxy. Under separate exact-resource cleanup approval, first disable both cache operations and verify protected uncached traffic, then undeploy only this deployment:

```bash
gcloud ai index-endpoints undeploy-index "$INDEX_ENDPOINT_ID" \
  --project="$VERTEX_PROJECT_ID" --region="$VERTEX_REGION" \
  --deployed-index-id="$DEPLOYED_INDEX_ID"
gcloud ai index-endpoints describe "$INDEX_ENDPOINT_ID" \
  --project="$VERTEX_PROJECT_ID" --region="$VERTEX_REGION" --format=json
```

Wait for successful operation completion and verify the selected deployment is absent. Do not delete shared endpoints/indexes. If separately approved and exclusively owned, delete the now-unused endpoint and index:

```bash
gcloud ai index-endpoints delete "$INDEX_ENDPOINT_ID" \
  --project="$VERTEX_PROJECT_ID" --region="$VERTEX_REGION"
gcloud ai indexes delete "$INDEX_ID" \
  --project="$VERTEX_PROJECT_ID" --region="$VERTEX_REGION"
```

Verify deletion with exact `describe`: authenticated `NOT_FOUND` after successful deletion counts, not permission/network errors or unfinished operations. Review billing with the owner, allowing for lag. Administrators remove only approved unnecessary IAM bindings. Never disable shared APIs or delete shared accounts/the existing project. Exclude sample cleanup; index teardown leaves [native answer-store and cross-store retention gaps](semantic-cache.md#retention-rollback-and-cost).

## Source and validation boundary

Before rendering, check installed gcloud `--help` for create/deploy/describe/operations/services/IAM/undeploy/delete and check fields/behavior against current official documentation, including the [Apigee public tutorial](https://docs.cloud.google.com/apigee/docs/api-platform/tutorials/using-semantic-caching-policies). Confirm native schema acceptance and runtime behavior in the approved trial. See [capability status](capability-status.md) and the [trial checklist](semantic-cache.md#cache-trial-and-enablement-checklist).
