---
name: work-delegation
description: >
  Use this skill when work should be handed to another agent — the task calls
  for a specialist outside your own role (research, website changes, data
  analysis, SEO/AEO, image work), or a piece of work should run as its own
  subtask. Triggers on "ask Kite to research …", "delegate this", "have
  someone build …", and whenever you are about to attempt specialist work
  another agent owns. Keep the work yourself when your own role is the best
  fit — delegation is for routing work, not for doing it.
mode: sandbox
---

# Work Delegation

Use this skill to delegate work to another agent when the task needs a different specialist.

Kite's CMO plans and delegates every deliverable. Other agents keep work in
their own function when it is the best fit.

The _Delegation Rules_ below are the team's only routing map. Agent
descriptions state what each agent owns; who receives a task is decided here.

## Context

Check which of `THREAD_ID` or `TASK_ID` is set — it selects the workflow below and the available `kite-tasks` commands.

- Conversational agents have `THREAD_ID`. They can use `kite-tasks agents`, `kite-tasks create`, `kite-tasks list`, `kite-tasks status`, and `kite-comments create`.
- Task agents have `TASK_ID`. They can use `kite-tasks create` to create subtasks. They cannot use `kite-tasks agents`, `kite-tasks list`, or `kite-tasks status`.
- Task agents also have `set-task-result` and must use it when their own task result changes.

## Conversational Workflow

Use this workflow when `THREAD_ID` is set.

1. Run `kite-tasks agents` to list available agents.
2. Apply the _Delegation Rules_ function map, choose the matching `name`, and pass it verbatim — not a shortened or display form. A bundled request is not "fits no specialist": split it per _Decomposing Work_ so each specialist owns its part.
3. Write the title and description to files with a single-quoted heredoc, then run `kite-tasks create --content-files <title_path> <description_path> "<assignee_agent>"`. This preserves the exact user text; do not put task content in command arguments. If the command fails with an error listing `valid_agents`, the assignee was not recognized: re-run `kite-tasks agents` and retry once with an exact `name` from it.
4. If the task advances an initiative on the board, add `--initiative-id "<initiative_id>"` — `kite-tasks create --content-files <title_path> <description_path> "<assignee_agent>" --initiative-id "<initiative_id>"` — so the platform links the task to it. Use the `id` from the `kite-initiatives create` or `kite-initiatives list` output. Every task you delegate toward an initiative must carry its id.
5. Tag the task per _Tagging the Task_ with `--tags "<keys>"`.
6. Confirm the create output contains a non-empty task identifier, then tell the user what is now underway and when they will hear back, in outcome terms; leave assignee names to the task board unless the user asks. When the output has no task identifier, report that the task was not created.

Use `kite-tasks list`, `kite-tasks status "<task_id>"`, and `kite-comments create "<task_id>" "<markdown>"` only for tasks created from this conversation.

When content has user text, Markdown, dollar amounts, backslashes, or newlines, write it with a single-quoted heredoc so the shell does not interpret it:

```sh
cat > /tmp/task-title.txt <<'EOF'
Approve launch budget
EOF
cat > /tmp/task-description.md <<'EOF'
# Budget

1. Approve $2,500.
EOF
kite-tasks create --content-files /tmp/task-title.txt /tmp/task-description.md "<assignee_agent>"
```

For a task result, use the same file-based transport for both the summary and Markdown body:

```sh
cat > /tmp/task-summary.txt <<'EOF'
Approved the $2,500 launch budget.
EOF
cat > /tmp/task-result.md <<'EOF'
# Budget

1. Approved $2,500.
EOF
set-task-result --summary-file /tmp/task-summary.txt < /tmp/task-result.md
```

For a task comment, write the Markdown to a file first and pass it as `"$(cat notes.md)"`.

## Task Workflow

Use this workflow when `TASK_ID` is set.

1. Delegate only when a specialist should do a separate subtask.
2. Use the assignee named by the task instructions when one is provided, verbatim.
3. If no assignee is named in the instructions, apply the _Delegation Rules_ function map. Do not create a recursive subtask for the agent already running the work. Every create command must include an explicit `<assignee_agent>`; omission is invalid and never selects a default agent.
4. Write the title and description to files with a single-quoted heredoc, then run `kite-tasks create --content-files <title_path> <description_path> "<assignee_agent>"`. If it fails with an error listing `valid_agents` (the assignee was not recognized), retry once with an exact `name` from that list — task agents cannot run `kite-tasks agents`, so the returned `valid_agents` is your source of valid names. Tag the subtask per _Tagging the Task_ with `--tags "<keys>"`.
5. Continue your own task or end your turn so the platform can resume you when the subtask changes.
6. Write the summary and Markdown result to files with a single-quoted heredoc, then run `set-task-result --summary-file <summary_path> < <markdown_path>` when your own task has a final or updated result. The summary is required: a single past-tense sentence stating the outcome; run histories show only that sentence.

Do not call `kite-tasks agents`, `kite-tasks list`, `kite-tasks status`, or `kite-comments create` from a task context.

A task cannot schedule future work. When work must happen later — a follow-up send, a measurement readout, a re-check — put that plan in the task result so the delegating agent can schedule it.

## Decomposing Work

Apply these rules in either context before any `kite-tasks create`.

1. One task, one outcome. When a request needs several distinct deliverables, create one task per deliverable rather than one task listing all of them — each runs with its own specialist and its own result.
2. Independent pieces can be created together and run in parallel. When one piece needs another's output, create the first task alone and create the dependent task after the first result arrives, passing that result in its description.
3. Match each piece to the specialist whose role owns it; split a piece that would straddle two specialists.
4. A request that mixes work listed specialists own with unmatched work is a bundle. Split it into sequenced tasks: each specialist piece goes to its owner, while only the residue that fits no specialist goes to `generalist` or stays with the current non-CMO task.

## Writing the Task

The assignee sees only the title and description you write — no conversation history, no context you had. The description must carry:

1. The goal and why it matters, in one or two sentences.
2. Every input the work needs: source data, URLs, names, prior results, constraints. A reference like "the list from earlier" is invisible to the assignee — inline it.
3. Acceptance criteria: what must be true for the task to count as done, stated so the assignee can check it themselves ("the page is live at /pricing and renders the three tiers", not "improve the page").
4. The expected result shape when it matters — a report, a table, a live URL, a draft.
5. The user's constraints verbatim — numbers, schedules, names, identifiers — never paraphrased. When a fact the work depends on is unknown to you (a table's columns, an event name, a timing window), say it is unknown and instruct the assignee to parameterize it or ask through the task result, never to guess it — a guessed identifier fails silently at integration time and costs a rebuild.
6. Who will apply the deliverable and what they can run. When the requester cannot execute commands, require finished artifacts — complete file contents, a hosted page — plus plain-language apply steps; a CLI runbook is not a deliverable for a non-technical requester.
7. Where the result goes: the assignee returns it through the task result, and you relay it onward. Never instruct the assignee to deliver to a channel (post to a chat thread, send an email) — task agents have no channel access, and such an instruction fails the task.

## Tagging the Task

Tags label a task with the kind of marketing work it is; the team's Activity feed shows and filters tasks by them.

1. Tag every marketing deliverable with the one or two keys that best describe the work, comma-separated (e.g. `--tags "content,seo"`); omit `--tags` when no key fits.
2. Use only these curated keys: `content`, `seo`, `paid-ads`, `social`, `email`, `creative-design`, `web-landing`, `analytics-reporting`, `pr-comms`, `experiment`. An unknown key fails the create and the error names the valid keys — retry with keys from that list.
3. Pass tags as `--tags "<keys>"` after the required arguments, in either context: `kite-tasks create --content-files <title_path> <description_path> "<assignee_agent>" --tags "content,seo"`. Optional flags (`--tags`, and `--initiative-id` in a conversation) work in any order; each one you skip changes nothing about the rest of the command.

## Delegation Rules

1. Delegate when the work matches another agent's primary function and does not match your own.
2. Keep work yourself when your own function covers it and no other function covers it more directly.
3. Route by the requested final artifact: evidence gathering — including keyword, SEO, AEO, search-competitor, and search-opportunity research — to `research`; customer-facing words to `content`; visual work to `design`; the public marketing website — new sites, custom landing pages for conversion, SEO/AEO pages, blog posts, and every other marketing-site change — to `web-developer`, even when a research, audit, or AEO report supplies the inputs; measurement and experiments to `analyst`; and unmatched work — a standalone internal tool, a dashboard aggregating several agents' results — to `generalist`. Keep each specialist inside its function; a subtask for the agent already running the work is invalid.
4. Substantial data reaches users as a hosted page, not a long chat message or wiki file. Structured or tabular results — lead lists, prospect tables, rankings — are always substantial, whatever their row count; so is a prose answer past about 200 words. A user's ask to share results in a channel adds the chat summary alongside the page. The agent whose task produced the findings publishes them with `dashboard-building` in that same task. A dashboard aggregating several tasks' or agents' results is its own deliverable: create the producing tasks first, then one `generalist` task carrying every result and requirement inlined. If an unplanned task returns substantial findings, relay the verified findings rather than waiting on a page that was never delegated.
5. After a delegated website change completes, when the change is user-visible and its result does not show it was verified, delegate an audit-only verification pass to `web-developer`, naming the exact pages and expected states to check.
6. A NEW-website task's deliverable is design options, not a finished site: write the task to generate designs from the approved brief and return each design's screenshot plus the designs link for the user to compare. Give it no acceptance criteria that ask for a finalized, verified, or live site — no "complete page implemented", no "return the live URL", no browser-verification evidence — those apply only after the user picks a design. Only after the user names one of the returned designs, create the follow-up task (or comment on the existing one) stating the exact design number the user chose; that task selects the named design. Build-out beyond selection is a separate ask — include it only when the user's message actually requested it.
   - Before creating a NEW-website task, read the company brand knowledge (`/efs/knowledge/company/brand/`) and run `kite-websites list` (conversational agents get a read-only listing). A site is a match candidate only when its `selected_iteration` is set or it has a `deployment_url` — a site whose designs were generated but never selected has no committed look to match. When at least one candidate exists and you are conversing with the user, ask one question before delegating: match the design of an existing site (name only the candidates) or go with a fresh new direction? Record the answer in the task description — including which source site, when matching. When no candidate exists, skip the question and write the task as a fresh design. As a task agent (no user channel), skip the ask too: apply the preference order below and note the applied choice in your task result. Resolve the preference in this order: the user's current message, then what they stated earlier in the conversation (no re-asking), then — when neither exists and a candidate exists — record "match <most recently updated candidate>" as the default and say so where you report (chat reply or task result).
7. To redirect or clarify running work, comment on the existing task instead of creating a duplicate.
8. Never report delegation as complete unless the command returned task JSON with an `id`.
