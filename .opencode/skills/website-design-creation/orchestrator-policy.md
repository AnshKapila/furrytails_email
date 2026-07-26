# Design generation — orchestrator tools

You generate designs through the `generate_designs` tool (not the
`kite-websites` CLI, which is the sandbox surface).

- A slot is an entry in the `designs` array, shaped
  `{"user_requirements": "…", "remix": false, "contexts": []}`.
- Passing `null` for a slot means "do not generate it"; never pass all 3 as
  null.
- Selection uses the `select_design` tool; edits after selection go through
  `trigger_coding_agent`.
