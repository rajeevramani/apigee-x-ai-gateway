# Lab 4 — Add Model Armor inspection

Inspect prompts and responses with Model Armor. The gateway blocks matches and incomplete inspection, and keeps its routing and quota behaviour.

## Before you start

- Lab 3 working (or Lab 2 if you skipped the spending budget), plus its source folder, deployed revision and test results.
- Complete the [Model Armor setup](../README.md#model-armor-setup-lab-4) first. You'll have:
  - a template
  - an approved processing location
  - a deployment service account
  - a template readback file for the agent

  Model Armor adds a processing location and usage charges. Details: [Model Armor setup](../references/model-armor-setup.md).

## Prompt

```text
Protect the gateway's prompts and responses with Model Armor.

Save a new source bundle and ZIP in ./ai-gateway/lab-4, with
deployment steps and a small test plan.
```

## What you get

- A new bundle
- A contract for text-only, single-turn, non-streaming traffic, inspected in both directions
- Which filters and thresholds apply, based on your actual template
- Failure responses for matches and incomplete inspection

The gateway blocks matches. It doesn't redact or rewrite text.

## Deploy

1. **Review the diff** against the [Model Armor workflow](../references/model-armor.md).
2. **Import, then select the deployment service account** for the new revision. Importing the ZIP doesn't attach it, and it isn't inherited from the previous revision.
3. **Read back the deployment** and confirm the revision, `serviceAccount` and readiness:
   `GET https://apigee.googleapis.com/v1/organizations/ORG/apis/PROXY/deployments`
4. **Set up masking** for credentials and prompt/response bodies before capturing any debug traces.

## Smoke test

- **Benign prompt:** a normal answer, with evidence that inspection ran for each enabled filter. A `200` alone isn't enough.
- **Prompt your filters should catch:** use an agreed synthetic test prompt. It's rejected before the backend is called.
- **Response your filters should catch:** the output is withheld. The model call still costs, and blocking can't undo that.
- **Earlier labs:** their smoke tests still pass.

## Full checks

See the [Model Armor acceptance cases](../references/model-armor.md#offline-checks-and-live-acceptance).

## If it fails

| Symptom | Likely cause |
|---|---|
| Deploy works but scans fail | Check the deployed service account, its IAM, that the API is enabled, and the exact template name. |
| Inspection skipped or results missing | Check which text is sent and each enabled filter's result. Don't treat unknown as clean. |
| Filter not available in location | Revisit the approved location. Don't change residency settings silently. |

**Next:** [Lab 5 — Protect against prompt-token bursts](lab-5-burst-protection.md) (optional)
