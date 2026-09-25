# Evaluating the skill

This page is for people assessing the **skill and its evidence**: reviewers, maintainers and anyone running agent-evaluation trials. If you just want to try the AI gateway, start with the [README](README.md).

## Evidence levels

Keep these levels separate. A result at one level doesn't establish the next:

1. **Authored:** the agent generated the files.
2. **Locally checked:** structure, references and offline tests pass.
3. **User-reported working:** an operator deployed it and reports passing tests.
4. **Independently live-verified:** someone else confirmed it against the acceptance cases.

Current status belongs in [feature status](references/capability-status.md#current-status); [what the statuses mean](references/capability-status.md#what-the-statuses-mean) defines each level. The labs don't establish comprehensive testing, production readiness or feature parity.

## Operating boundaries

These apply to every lab and to the combined build:

- **Division of work.** The agent authors artifacts. The operator performs cloud setup, import, deployment and live tests from an authenticated workstation.
- **Approvals.** Setup writes, deployment and billable probes each need approval. Nothing is cleaned up or published automatically.
- **Private storage.** Keep configuration, generated bundles and masked evidence outside this repository. Never commit keys, customer prompts, private endpoints or raw traces.
- **Remote agents.** Send only the non-secret inputs they need, never `.env`, keys or cloud credentials. Use container-side paths for agent file locations, and agree how the operator retrieves the ZIP.
- **Placeholders and regions.** Never execute unresolved placeholders. CLI defaults and runtime region don't establish an approved processing location.
- **Resumed sessions.** Restate the manual-only boundary, and supply the previous source directory (or ZIP), exact revision, contract and masked results.

## Pre-import review

Before importing any new ZIP:

- review the minimal diff, policy XML and flow attachments against the linked capability reference
- check that `apiproxy/` is at the ZIP root
- check that references resolve and no placeholders or secrets remain
- check the local validation results

This review shows the policies are present. Only live tests show they execute.

| Lab | Expected implementation |
|---|---|
| 2 — Token quota | `LLMTokenQuota` enforcement and counting. |
| 3 — Spending budget | A separate enforce/count `LLMTokenQuota` pair counting cost, plus cost-calculation JavaScript. |
| 4 — Model Armor | `SanitizeUserPrompt` and `SanitizeModelResponse`. |
| 5 — Burst protection | `PromptTokenLimit`. |
| 6 — Enabled cache trial | `SemanticCacheLookup` and `SemanticCachePopulate`. |

## Evidence handoff for each lab

Keep a private record of:

- the bundle path and source revision
- the deployed environment, revision and identity
- the approved test bounds
- masked results
- remaining gaps
- retained resources and cost exposure

If the agent can't inspect operator evidence, say so. Record a manually reported pass as user-reported, not independently live-verified.

Keep the original failed bundle and evidence, and record any later repair as a separate attempt. If you continue despite a defect, name it and list which later cases it blocks.

## Readiness observations (Lab 0)

During [Lab 0](labs/lab-0-readiness.md), record these as findings:

- any cloud commands the agent runs
- any external documentation it browses
- any proxy it generates

Installing the skills shows they're available. Record the installed source revisions of both skills.

## Fresh-agent evaluation

For an unassisted trial:

- Don't name the skills, prescribe policies or coach missed decisions. Record omissions as findings.
- Observe actual reference reads before authoring, not just claimed reads or a handoff mapping.
- Record agent evaluation separately from proxy acceptance.

| Case | Required evidence |
|---|---|
| Fresh-agent execution | A fresh session discovers and loads the skills and authors artifacts. The operator performs cloud setup, deployment and live tests under approvals. Coaching and retries are recorded separately. |

Keep:

- the skill version
- the non-secret configuration references supplied
- the approval record
- observable skill and reference loads

Distinguish observed tool actions from inferred reference use. A repaired run is not an unassisted success, and a working proxy alone doesn't establish fresh-agent execution.

## Offline checks

From a clone of this repository, with Python 3:

```bash
python3 -B -m unittest discover -s tests -v
```

The [tests](tests/test_examples.py) check:

- XML structure and example consistency
- synthetic rendering
- selected source and step ordering
- documentation links and anchors

They don't execute Apigee policies, validate live IAM or test filter behaviour. The lab acceptance cases cover those.
