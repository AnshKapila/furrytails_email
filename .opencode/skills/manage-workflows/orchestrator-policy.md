# Workflows — orchestrator tools

You manage workflows through tools (not the `kite-workflows` CLI, which is the sandbox surface).

- Create with `create_workflow` using `cron_expression`, `prompt`, and `title` (required: a short display name of at most 6 words), plus optional `delivery` (`thread` | `default_channel` | `none`; defaults to `default_channel` — see the skill's "Where each run reports" section).
- List with `list_workflows`; set `include_disabled=true` only when the user asks to see disabled workflows too.
- Update with `update_workflow`; provide only fields the user wants changed (including `delivery` to change where results are reported).
- Delete with `delete_workflow` after the user clearly asks to remove a workflow.
- The skill's "Workflows that need a browser login" setup flow is sandbox-only (it needs `kite-tasks`/`kite-browser`) and does not apply to you — your tools cannot create a disabled workflow or drive a login handoff.
