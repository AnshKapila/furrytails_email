---
name: manage-workflows
description: >
  Use this skill when the user wants recurring work, scheduled edits,
  automation, or periodic checks, such as "update my site every Monday",
  "send me a weekly report", "schedule this task", or "show my scheduled
  automations". Skip this skill for one-time edits the user wants done now.
mode: both
agent_policies:
  orchestrator: orchestrator-policy.md
---

# Manage Workflows

Use this skill to create, list, update, or remove recurring workflows for the current team.

## Hard requirements

- These requirements take precedence over the supporting rules below.
- Before creating a workflow, first list existing workflows, then verify every required third-party app is connected. Do not create it until both checks pass.
- When the recurring work signs in to a website the run drives through a browser (not a connectable app), set up that login before the workflow can fire — follow "Workflows that need a browser login".
- Change an existing workflow in place when the user's request refers to its current purpose or cadence. Preserve its id and every field the user did not ask to change.
- Never create a second workflow to override or replace an existing workflow.
- Verify the returned id, prompt, timing, assignee, and enabled state before reporting success.

## Rules

- Capture what should happen and when in plain language, then translate the timing into cron yourself; never surface cron syntax or ask for it.
- When the timing is ambiguous and you are in a live conversation, ask one plain-language clarifying question ("Which timezone should I use?"); when running non-interactively from a task, pick the most reasonable interpretation and state the assumption. Never guess time zones or dates silently.
- Describe a workflow by what it will do and when ("Every Monday morning, check traffic and send a summary"), not by its prompt, cron, or plumbing.
- Each workflow run executes unattended as a fresh team task with no prior context, so a missing app connection makes every run fail. List the third-party apps the recurring work needs and verify each connection; when one is missing, follow `tool-discovery-execution`'s connect recipe and wait until the connection is completed.
- Workflows belong to the team.
- Write the prompt as a self-contained instruction because each run starts a fresh team task — name the apps and data the run needs. Where the result is reported is the `delivery` setting (see "Where each run reports"), not something to restate in the prompt.
- If the list of workflows is empty, report that no workflows are currently active and offer to create one.
- To change, replace, reschedule, pause, or resume recurring work that already exists, update that workflow in place so its id and run history remain intact.

## Cron grammar

- Five space-separated fields, in order: `minute hour day_of_month month day_of_week`, all UTC.
- Each field is `*`, a number, a list (`1,15`), a range (`1-5`), or a step (`*/15`).
- `day_of_week` is `0`–`6` with `0` = Sunday.
- Examples: `0 9 * * 1` = Mondays 09:00 UTC; `*/30 * * * *` = every 30 minutes; `0 0 1 * *` = first of each month 00:00 UTC.

## Where each run reports (`delivery`)

Every run reports its result somewhere. Pick it from what the user asks; it is a
real setting (the `delivery` tool argument, or the `--delivery` CLI flag),
separate from the prompt text.

- **`default_channel` (default)** — post the result to the team's main Slack
  channel. Use this whenever the user does not say where results should go.
- **`thread`** — reply in this conversation. Use this when the user says to
  answer here ("reply in this thread", "message me back here", "let me know in
  this chat"). Creating with `thread` requires a conversational source; task
  agents must use `default_channel` or `none` when creating a workflow.
- **`none`** — report only to the Tasks page, with no Slack message. Use this
  only when the user asks to keep the result off Slack.

To change where an existing workflow reports ("post to the thread instead of the
channel"), update it in place with the new `delivery` — do not recreate it.

## Workflows that need a browser login

Some recurring work signs in to a website the run drives through a browser rather
than a connectable app — for example "every morning, log in to `<site>` and export
the report". Each run executes unattended, so the login must already be saved to
the workflow's browser profile before the first run fires; otherwise every run
stalls at a login wall no one is watching.

Resolve the login **up front, in this conversation**, while the person is here to
complete it. Use this flow only when the work needs a site login that no connected
app already covers.

1. **Create the workflow disabled** with `kite-workflows create "<cron>" "<prompt>" "<title>" --disabled`. It is saved but does not fire. Read `id` and `browser_profile` from the response.
2. **Delegate a one-off login-setup task** (see `work-delegation`): `kite-tasks create` a task that opens the site's login page in a cloud browser **on the workflow's profile** — `kite-browser create --profile "<browser_profile>" "<login-url>"` — runs `kite-browser handoff`, puts the handoff URL in its task result, and stops without waiting (the handoff and profile mechanics are in `browser-session`, "Human handoff"). Pass the exact `browser_profile` from step 1 so the captured login persists where later runs reuse it.
3. **Relay the link and ask them to log in.** When the setup task reports back with the handoff URL, give that URL to the person and ask them to log in and tell you when they are done. The link expires with the browser session (minutes) — pass along the deadline and ask them to act promptly.
4. **On their confirmation, resume the setup task to save the login** with `kite-comments create "<task_id>" "logged in — verify the page and close the session"`. The task resumes in the same session, confirms the logged-in state, and closes so the login is written back to the profile.
5. **Enable the workflow** with `kite-workflows update "<id>" --enable`. Later triggers reuse the saved login automatically.

Keep the workflow disabled until the login is confirmed saved. If the browser
session expires before they finish, delegate a fresh setup task (step 2) — the
saved profile is unaffected.

## Sandbox — `kite-workflows` CLI

In the sandbox, manage workflows with the `kite-workflows` CLI. The team is resolved from your session token; you do not pass it.

- Create: `kite-workflows create "<cron_expression>" "<prompt>" "<title>" [--delivery thread|default_channel|none] [--disabled]` — prints the created workflow as JSON (with its `id` and `browser_profile`) on success. The title is required: a short display name (at most 6 words, e.g. `Daily Pokemon Poem`) shown in the workflows UI. `--delivery` is optional; omitting it defaults to `default_channel` (see "Where each run reports"). `--disabled` creates the workflow without arming its schedule — use it only for the browser-login setup below, then enable with `update --enable`.
- List: `kite-workflows list` — prints all team workflows, including paused ones, as JSON.
- Update: `kite-workflows update "<workflow_id>" [--cron "<cron_expression>"] [--prompt "<prompt>"] [--title "<title>"] [--assignee "<agent-name>"] [--delivery thread|default_channel|none] [--enable|--disable]` — changes only the supplied fields and prints the updated workflow as JSON. Copy the id from `list`; preserve fields the user did not ask to change.
- Delete: `kite-workflows delete "<workflow_id>"` — removes one workflow (exit 0 on success).
- Webhook: `kite-workflows webhook "<workflow_id>" --enable | --disable` — turns the workflow's webhook trigger on or off and prints the workflow as JSON. Enabling returns a `webhook_url`; disabling clears it. See "Trigger the same workflow from an external event".

Confirm the create or update response contains the expected `id`, prompt, timing, assignee, and enabled state before telling the user it changed. For deletion, confirm the command exits successfully. On failure, follow the shared single-retry rule and never claim the workflow changed without the expected result.

## Trigger the same workflow from an external event (webhook)

A workflow always has a cron schedule, and can additionally fire from an
external event. Enable its webhook to get a public URL that another system (for
example Segment, Zapier, or a form backend) POSTs to; each POST runs the
workflow's prompt as a fresh team task, exactly as a scheduled run does.

Use this when the user wants the recurring work to also run "when X happens"
rather than only on a clock — an event-driven trigger layered on the schedule.

- Enable it with `kite-workflows webhook "<workflow_id>" --enable`, then read
  `webhook_url` from the response and give that URL to the user (or the external
  system) as the POST target. The workflow keeps its cron schedule; the webhook
  is an additional trigger, not a replacement.
- Disable it with `--disable` when the event trigger is no longer wanted; the
  cron schedule keeps running.
- The webhook POST body is handed to the run: it is appended under the stored
  prompt as `Webhook payload: <raw body>` (capped at 64 KB) when the caller
  sends one. So the prompt does not need to restate the per-event data the body
  carries — but still write it to be self-contained for the parts that do not
  vary per event (which apps and data each run should touch), the same as any
  scheduled workflow.
- The URL is a credential: report it once to the user and never post it to a
  shared channel.
