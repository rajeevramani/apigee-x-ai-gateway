# Lab 0 — Check the agent is ready (optional)

Confirm your agent found both skills and understands the job before you build anything. Nothing is built or deployed in this lab.

## Before you start

- Install both skills ([Quickstart step 1](../README.md#1-install-the-two-skills)) and start a **new** agent session.
- If the agent runs remotely or in a container, make sure it can read the skill files there. Copy only the skill folders, never `.git`, cloud credentials or private files.

## Prompt

```text
I want to build an AI gateway on my existing Apigee X setup, one step
at a time. Before we start, tell me what you can help with and what
you will need from me. Don't build anything yet.

I will do all cloud setup, import, deployment and live tests myself.
You have no access to my cloud account. Never ask me to paste secrets.
Save each step's work in its own directory under ./ai-gateway.
```

## What to expect

- The agent reads both `SKILL.md` files and the [feature status](../references/capability-status.md), and reports gateway skill version `1.0.0`.
- It lists routing, token quotas, spending budgets, Model Armor, burst protection and semantic caching, and says streaming and format conversion aren't supported.
- It asks for missing details (environment, backend, authentication) without inventing values, and agrees where it will save files.
- It doesn't run cloud commands or generate a proxy yet.

If a skill is missing, the agent should say so and ask where it is, not pretend it loaded it.

## If it fails

| Symptom | What to check |
|---|---|
| Skill not found | Each skill folder has `SKILL.md` at its top level; start a new session after installing. |
| Reference or example missing | Copy the complete skill folders, including `references/` and `assets/`. |
| Agent can't reach GitHub (for example, a sandboxed container) | Clone both repos on your machine and copy the skill folders in. |

**Next:** [Lab 1 — Route between models](lab-1-routing.md)
