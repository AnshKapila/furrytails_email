---
name: prompt-writing
description: >
  Use this skill when drafting, reviewing, or tightening reusable instructions
  for a team skill, custom agent, or scheduled workflow — for example "write
  the agent prompt", "improve these instructions", "make this skill trigger
  reliably", or "remove duplication from this prompt". Use the relevant
  management skill to save or delete the finished artifact; this skill owns its
  wording, structure, and validation.
mode: sandbox
---

# Prompt Writing

Write the smallest reusable instruction set that routes correctly, executes
reliably, and can be verified.

## Inputs

Establish these from the conversation before drafting:

1. The single outcome the artifact owns.
2. The situations or user phrases that should activate it.
3. The inputs and tools available at runtime.
4. The expected output and its downstream consumer.
5. The target model and any hard safety or format constraints.

Ask one concise question only when a missing answer would materially change the
artifact. Otherwise state the assumption and continue.

## Choose the artifact shape

### Custom agent prompt

Use three sections:

1. **Role** — one sentence defining the bounded responsibility.
2. **Context** — static facts, runtime inputs, available tools, and downstream
   consumers. Keep behavior out of this section.
3. **Instructions** — ordered, independently actionable rules. Put the most
   important decisions and constraints first.

If the role needs an unrelated "and also" responsibility, split it into another
agent or delegate that work.

### Skill

Treat the skill description as routing metadata and the body as execution
instructions.

- Start the description with `Use this skill when ...`.
- Name two or three realistic trigger phrasings and the boundary with the
  nearest overlapping skill. State a non-trigger only when it prevents a likely
  routing collision.
- Describe user intent, not implementation. Keep tool names, commands, internal
  paths, vendors, schemas, and environment details in the body.
- Keep one task family per skill. Extend an existing skill when the new behavior
  shares the same trigger and mechanics.
- Put exact workflow steps, tool calls, gates, verification, and failure handling
  in the body. Follow the management interface's rule for whether frontmatter is
  stored separately.
- For a repository-backed `SKILL.md`, preserve one YAML block with `name`,
  `description`, and the runtime's required fields; keep the directory and
  hyphen-case name aligned. For a managed team skill, send those fields through
  its interface and keep frontmatter out of the body.
- Prefer `Purpose`, `Inputs`, `Workflow`, `Verification`, and `Failure handling`
  as the body order, omitting sections that add no instruction.

### Scheduled workflow prompt

Write a self-contained instruction for a fresh session. Include the objective,
required integrations or data sources, timing context, destination, success
criteria, and what to report when a dependency is unavailable. Do not rely on
the current conversation being present later.

## Authoring workflow

1. Trace what the runtime receives and what consumes the output. Preserve any
   parsed output shape, delimiter, schema, or side-effect boundary.
2. Assign each rule to its narrowest durable owner. Replace repeated rules with
   one canonical instruction and a short reference when the runtime can load it.
3. Draft in imperative, declarative sentences. Use one term per concept and
   state exceptions next to the rule they qualify.
4. Prefer positive directions that name the desired action. Pair necessary
   prohibitions with the safe alternative.
5. Specify tool-dependent actions exactly: tool or command, required arguments,
   ordering gate, success signal, and failure path.
6. Add examples only when they disambiguate a likely mistake. Keep one minimal
   example per pattern.
7. When revising, cut or merge before adding. Grow the artifact only for a new
   instruction that has no existing owner.
8. Remove filler, restatements, exhaustive tutorials, speculative flexibility,
   and rules already supplied by the parent prompt or another loaded skill.
9. Match detail to the model. Give standard models explicit gates for fragile
   workflows; give reasoning models goals, constraints, and validation without
   prescribing hidden reasoning or redundant step-by-step thought.

## Verification

Before saving, check that:

- The artifact has one coherent responsibility and no contradictory rules.
- A skill description would trigger on the user's real phrasing and excludes
  the nearest neighboring concern.
- Every workflow step names an action, target, and expected result.
- Required tools, commands, and output formats are exact and available in the
  target runtime.
- Safety, confirmation, and side-effect boundaries match the surrounding system.
- The downstream consumer still receives the required shape.
- Each rule appears once, in the correct owner.
- The artifact contains no secrets, credentials, user-specific preferences, or
  one-off task details.

Run the project's prompt-review and validation checks when they are available.
Apply every material finding or record a specific reason for declining it, then
review the final text again.

## Failure handling

- Narrow an unclear task family before drafting.
- Resolve overlap by choosing one owner and sharpening both routing boundaries.
- Stop before saving when a required tool, output contract, or side-effect rule
  is unknown and would change the result.
- Report an unavailable review or validation tool instead of claiming the
  artifact passed it.
