# API product, developer and app setup (operator-run)

Use this when a lab needs API-key callers (routing with VerifyAPIKey) or configuration stored on an API Product (the [token quota](token-quota.md) limit, cost budget attributes). **The operator runs every step.** The agent explains the choices, fills in the values the user agreed, and gives exact instructions and readback checks. It never creates or changes products, developers or apps itself, and never asks for or prints API keys.

## Ask these questions first, then wait

| Decision | Question to ask | Recommendation |
|---|---|---|
| Existing product | Is there already an API product (and developer app) for this proxy? What is its **internal name** (not the display name)? | Reuse a dedicated test product if one exists; don't change a shared one. |
| Scope | Which proxy and environment should the product allow? | Only the lab proxy and the test environment. |
| Key approval | Should new keys work immediately (`auto`) or wait for approval (`manual`)? | `auto` for a test product. |
| Developer and app | Which developer (email) and app name should hold the test key? | A dedicated test developer and app. |
| LLM token quota | Does this lab read the token limit from the product, and what limit, interval and time unit? | [Lab 2](../labs/lab-2-token-quota.md) does. Set it product-wide unless the lab asks for a per-operation limit. |
| Attributes | Which custom attributes does this lab need, and what values? | Only what the workflow lists (for example [cost budget](cost-budget.md#api-product-configuration)). |
| Method | Console or management API? | Console for a one-off lab; API when repeatable steps are wanted. |

If something is unknown, leave the placeholder visible and say the setup is not ready.

## Things that go wrong

- **No proxy or environment on the product = too much access.** A product created without API proxies lets its apps call *any* API in the organization; without environments it allows *all* environments. Always set both.
- **Saving the attribute list replaces it.** `POST …/apiproducts/<product>/attributes` replaces all attributes; any you leave out are deleted. Always read the current list first and send the full merged list.
- **At most 18 custom attributes per product**, including attributes on operations. Count existing ones before adding more.
- **Changes aren't instant.** Products and their custom attributes are cached at runtime for at least 180 seconds. Wait about 3 minutes after a change before testing it.
- **Use the internal product name** in API calls and in the app. It can differ from the display name if the product was made in the UI.
- **The LLM token quota is a product field, not a custom attribute.** It is `llmQuota` / `llmQuotaInterval` / `llmQuotaTimeUnit` on the product, separate from the request-count `quota` fields and from the attribute list. The quota policies read it as `verifyapikey.POLICY.apiproduct.developer.llmQuota.limit` / `.interval` / `.timeunit`, so the product field `llmQuota` supplies `llmQuota.limit`; don't go looking for a product field called `limit`.
- **`LLMTokenQuota` also needs `llmOperationGroup`.** With the token quota set only at product level, `VerifyAPIKey` matches the product and `…llmQuota.limit` resolves, but the quota policy finds no LLM operation and fails with `UnAuthorizedException: Invalid API call as no apiproduct match found`, usually surfacing as an opaque 500. If you see this, check for a missing LLM operation before suspecting quota exhaustion.
- **`llmOperations[].model` is the backend model ID the gateway sends upstream.** Both quota policies read it from the same request-side variable, and it also scopes the counter. Don't use the caller's alias or the model name in the response. See [the model key](token-quota.md#both-halves-key-on-the-request-model).
- **List each model explicitly.** A wildcard `"model": "*"` is accepted when saved but never matches, so every call fails as if the product had no LLM operation.
- **One resource/method/model mapping per `llmOperations` array.** More than one is rejected with `Operations must contain exactly one entity but found N entities`. Use a separate `operationConfig` per proxy/model pair, each with its own `llmTokenQuota`.
- **`apiResources` and `proxies` cannot coexist with an operation group.** Adding `proxies` alongside `operationGroup` is rejected with `Invalid Operation Group: API resources or proxies should not be set`.
- **Don't name an attribute `access`.** Apigee reserves it.
- **Developer email must be lowercase.**

## Generated-proxy handoff

After creating the proxy bundle, include a **Set up the API product** section in the delivered instructions. Fill in the selected product name, environment, proxy, resource paths, methods, approval mode and applicable quota limit/window. Explain how to associate the product with the developer app and verify approval without exposing its key. These are operator-run steps, not permission to change cloud resources.

For token quotas, give one row per route showing **caller alias → API product LLM operation model**. The product model is the backend model ID the alias translates to, which both quota policies read. Explain that callers keep using aliases while the product uses backend model IDs.

For example:

| Caller sends | Product LLM operation model |
|---|---|
| `fast` | `provider/model-a` |
| `smart` | `provider/model-b` |

Use the actual generated mappings. In the console, add a separate **LLM operation** for each model, selecting the generated proxy, resource path and method. A product-wide token limit does not replace these entries. Leave operation-level limits unset when inheriting the product-wide limit; otherwise disclose the override. Finish with the readback checks below and allow for runtime cache propagation before testing.

## Option A — Apigee console

1. **API product:** Distribution → API products → create (or open the existing one). Set a name, the test **environment**, key approval, and an operation for the lab **proxy** (path `/`, or the agreed path; method as agreed). Leave the request-count quota empty.
2. **LLM token quota:** when a lab reads the limit from the product ([Lab 2](../labs/lab-2-token-quota.md) does), set **LLM token quota limit** with its interval and time unit in the product details. A per-operation **LLM Token Quota** on an LLM operation overrides the product-wide value for that operation; use one or the other deliberately, and tell the agent which.
   Add the **LLM operations** listed in the generated-proxy handoff, using its exact model names, proxy, paths and methods.
3. **Custom attributes:** in the same product, add each attribute name and value exactly as listed by the workflow. Save.
4. **Developer:** Distribution → Developers → add (email, first name, last name, username).
5. **App:** Distribution → Apps → create, choose the developer, add the API product. The console shows the key; copy it into your own secret store, never into chat.

Menu names can change between console versions; follow the product and app pages in [Manage API products][products] if they differ.

## Option B — management API

Keep the access token out of command arguments. Replace every `__PLACEHOLDER__` first; don't run commands that still contain one.

```bash
ORG=__ORG__
PRODUCT=__PRODUCT_INTERNAL_NAME__
API=https://apigee.googleapis.com/v1/organizations/$ORG
auth() { printf 'Authorization: Bearer %s' "$(gcloud auth print-access-token)"; }

# 1. Check what already exists (read-only).
curl -sS -H @<(auth) "$API/apiproducts/$PRODUCT"
curl -sS -H @<(auth) "$API/apiproducts/$PRODUCT/attributes"
```

Create a product only if it doesn't exist. `product.json` names the proxy and environment so access stays narrow:

```json
{
  "name": "__PRODUCT_INTERNAL_NAME__",
  "displayName": "__PRODUCT_DISPLAY_NAME__",
  "approvalType": "auto",
  "environments": ["__ENVIRONMENT__"],
  "llmQuota": "__LLM_TOKEN_LIMIT__",
  "llmQuotaInterval": "__LLM_QUOTA_INTERVAL__",
  "llmQuotaTimeUnit": "__LLM_QUOTA_TIME_UNIT__",
  "operationGroup": {
    "operationConfigs": [
      {
        "apiSource": "__PROXY_NAME__",
        "operations": [{ "resource": "/", "methods": ["POST"] }]
      }
    ],
    "operationConfigType": "proxy"
  },
  "llmOperationGroup": {
    "operationConfigs": [
      {
        "apiSource": "__PROXY_NAME__",
        "llmOperations": [
          { "resource": "/**", "model": "__QUOTA_MODEL_ID__", "methods": ["POST"] }
        ],
        "llmTokenQuota": {
          "limit": "__LLM_TOKEN_LIMIT__",
          "interval": "__LLM_QUOTA_INTERVAL__",
          "timeUnit": "__LLM_QUOTA_TIME_UNIT__"
        }
      }
    ]
  }
}
```

```bash
# 2. Create the product (skip if it exists).
curl -sS -X POST -H @<(auth) -H 'Content-Type: application/json' \
  --data @product.json "$API/apiproducts"
```

Omit the three `llmQuota*` fields when the lab doesn't use a product-sourced token quota. `__LLM_QUOTA_TIME_UNIT__` is `minute`, `hour`, `day` or `month`; all three values are JSON strings, including the numeric limit.

To change the token quota on an **existing** product, read the product back, edit only those fields and send the complete body — an update replaces the resource, so any field you omit is lost. Confirm the method and body against [ApiProduct REST][rest-products] before running it:

```bash
# Read, edit the llmQuota* fields in product-current.json, then send the whole body back.
curl -sS -H @<(auth) "$API/apiproducts/$PRODUCT" > product-current.json
curl -sS -X PUT -H @<(auth) -H 'Content-Type: application/json' \
  --data @product-current.json "$API/apiproducts/$PRODUCT"
```

For attributes, build `attributes.json` from the **current list plus the new entries** (never only the new ones):

```json
{
  "attribute": [
    { "name": "__EXISTING_ATTRIBUTE__", "value": "__EXISTING_VALUE__" },
    { "name": "__NEW_ATTRIBUTE__", "value": "__NEW_VALUE__" }
  ]
}
```

```bash
# 3. Save the full merged attribute list (this REPLACES the whole list).
curl -sS -X POST -H @<(auth) -H 'Content-Type: application/json' \
  --data @attributes.json "$API/apiproducts/$PRODUCT/attributes"

# Later: change one existing attribute's value only (for example a price).
curl -sS -X POST -H @<(auth) -H 'Content-Type: application/json' \
  --data '{"name":"__ATTRIBUTE__","value":"__VALUE__"}' \
  "$API/apiproducts/$PRODUCT/attributes/__ATTRIBUTE__"
```

Create the developer and app only if they don't exist:

```bash
# 4. Developer (email lowercase).
curl -sS -X POST -H @<(auth) -H 'Content-Type: application/json' \
  --data '{"email":"__DEVELOPER_EMAIL__","firstName":"__FIRST__","lastName":"__LAST__","userName":"__USERNAME__"}' \
  "$API/developers"

# 5. App linked to the product. The response contains the key: save the output
#    straight to a private file and don't paste it anywhere.
curl -sS -X POST -H @<(auth) -H 'Content-Type: application/json' \
  --data '{"name":"__APP_NAME__","apiProducts":["__PRODUCT_INTERNAL_NAME__"]}' \
  "$API/developers/__DEVELOPER_EMAIL__/apps" > __PRIVATE_APP_RESPONSE_FILE__
```

Permissions the operator needs: `apigee.apiproducts.create` / `apigee.apiproducts.update`, `apigee.apiproductattributes.createOrUpdateAll` (replace list), `apigee.apiproductattributes.update` (one attribute), `apigee.developers.create`, `apigee.developerapps.create`.

## Readback before testing

- Product: `GET $API/apiproducts/$PRODUCT` shows the expected environment, proxy, approval type and attributes, with exact names and values.
- When a lab uses a product-sourced token quota, that same response shows `llmQuota`, `llmQuotaInterval` and `llmQuotaTimeUnit` with the agreed values. Set and verify the product quota before testing; don’t assume a missing quota blocks requests.
- It also shows an `llmOperationGroup.operationConfigs` entry for every proxy/model pair the lab exercises, with applicable `llmTokenQuota` overrides or the intended product-wide limit. In the console these appear under **LLM operations**; an empty table there means token accounting will fail even though the product-level **LLM token quota** is populated.
- Each `llmOperations[].model` equals the model ID both quota policies key on, as listed in the generated-proxy handoff. Confirm the resolved identities in a debug trace when testing is authorized.
- Attribute count is 18 or fewer.
- App: lists the product and its credential status is approved (check without printing the key).
- Wait about 3 minutes after any product or attribute change, then run the lab tests.

## Sources

[products]: https://docs.cloud.google.com/apigee/docs/api-platform/publish/create-api-products
[rest-products]: https://docs.cloud.google.com/apigee/docs/reference/apis/apigee/rest/v1/organizations.apiproducts
[rest-attributes]: https://docs.cloud.google.com/apigee/docs/reference/apis/apigee/rest/v1/organizations.apiproducts/attributes
[rest-developers]: https://docs.cloud.google.com/apigee/docs/reference/apis/apigee/rest/v1/organizations.developers
[rest-apps]: https://docs.cloud.google.com/apigee/docs/reference/apis/apigee/rest/v1/organizations.developers.apps

- [Manage API products][products]: operations, custom attributes (max 18 including operations; reserved `access`), `verifyapikey.POLICY_NAME.apiproduct.ATTRIBUTE_NAME`, product-level **LLM token quota limit** and per-operation **LLM Token Quota**.
- [ApiProduct REST][rest-products]: `llmQuota`, `llmQuotaInterval`, `llmQuotaTimeUnit` (strings; time unit `minute`/`hour`/`day`/`month`) at product level, and the nested `llmTokenQuota` object (`limit`, `interval`, `timeUnit`) on an LLM operation config.
- [ApiProduct REST][rest-products]: create warnings (no proxy = any API; no environment = all), `approvalType`, `operationGroup`, internal name.
- [Attributes REST][rest-attributes]: replace-all behaviour and the 180-second cache note; single attribute update.
- [Developers REST][rest-developers] and [Apps REST][rest-apps]: required developer fields (lowercase email), app `apiProducts`, credentials in the response.
