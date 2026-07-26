---
name: act-on-pulse-proposals
description: >
  Use this skill when your turn lists open pulse proposals and the message is
  a reply to them — the team acting on the CMO hourly pulse digest you
  posted in Slack. Records the team's decision (start or skip) on the
  proposal itself, so it stops surfacing as open. Fires whenever
  `open_pulse_proposals` context is present and the reply resolves to a
  go-ahead or a skip for one of them.
mode: sandbox
---

# Act on Pulse Proposals

The pulse digest has no buttons — a reply on its thread is how the team acts. This skill records that decision on the proposal itself; creating the actual task still goes through the work-delegation skill's `kite-tasks create`, as normal.

## Rules

- Match the reply to exactly one proposal from the `open_pulse_proposals` list by its `id`. Treat it as ambiguous — and ask instead of guessing — unless the reply names or clearly points at exactly one proposal (by id, title, or a unique detail that matches only that one).
- A go-ahead ("do it", "start with X", "yes"): first create the task with `kite-tasks create`, using the proposal's own `detail` (what it observed and the plan) as the brief; then run `kite-pulse start "<proposal_id>"` to record it as accepted.
- A skip ("not now", "hold off on X", "skip the analytics one"): run `kite-pulse skip "<proposal_id>"` to record it. Do not create a task.
- A reply asking to connect a tool first is not itself a go-ahead: run the tool-discovery-execution skill's connect flow, and run `kite-pulse start` only after the team explicitly says to proceed — a "start" said mid-connection does not skip the connect step.

## `kite-pulse` CLI

The thread and team are resolved from your thread token; you do not pass them.

- Record a go-ahead: `kite-pulse start "<proposal_id>"`.
- Record a skip: `kite-pulse skip "<proposal_id>"`.

## Confirming success and handling failures

A successful command prints JSON with a `status` of `"accepted"` or `"dismissed"`. If a command fails (non-zero exit, error message, or no JSON) — including a proposal that's already been actioned — the record did NOT change; say so plainly rather than claiming it succeeded.
