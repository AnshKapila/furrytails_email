---
description: Orchestrator-only policy for the `tool-discovery-execution` skill — when to reach for the tool gateway, confirmation rules for side-effecting actions, and how to handle unconnected providers in conversation. Loaded by `load_skills` only when SKILL.md's `agent_policies.orchestrator` points here.
---

# tool-discovery-execution — orchestrator policy

The `kite-integrations` recipes live in `SKILL.md`; these rules shape when and how the
orchestrator uses them in conversation.

## When to use

- Use this skill when the user asks to act on a third-party integration (send a
  Slack message, read Notion pages, add a sheet row) or asks what integrations
  are available.
- Image generation, editing, and background removal belong to the `images`
  skill — use its recipes even though the catalog lists `native:images-*`
  tools.

## Choosing the source

- Understand the whole task first — it may need tools from several
  integrations, each covering only part of it.
- For each need, prefer in order: a relevant **connected** integration (the
  team's own account and data), then a **platform** integration (Kite-managed,
  nothing to connect), and only then offer to connect a new one — doing the
  parts you already can, with every missing connection batched into one offer.

## Confirmation boundary

- Read-only actions (search, list, fetch) may run as soon as they are useful.
- Side-effecting actions (sending messages, creating or updating records)
  require explicit user intent for that specific action. When the user's
  request implies a write but leaves the target or content open ("let the
  team know"), state what you are about to send and where, and get
  confirmation first.
- A succeeded write is final — report it; never re-run it to verify.

## Handling outcomes

- `provider_not_connected`: run a bare `search` to see what is connected and
  serve the request through a connected sibling app when one covers it (per
  SKILL.md's recipes) — only after that, name the missing app and point the
  user to the Integrations page to connect it.
- Report results in user terms ("Posted to #general") with at most a short
  relevant excerpt of the returned data — never raw JSON dumps.
