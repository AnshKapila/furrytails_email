---
description: Orchestrator-only policy for the `images` skill — phase gating, the 3-variation rule, design-spec coherence, modifying-existing image flow, and the post-creation render-and-confirm hand-off to `trigger_coding_agent`. Loaded by `load_skills` only when SKILL.md's `agent_policies.orchestrator` points here.
---

# Image Creation — orchestrator policy

These are the conversation-shaping rules that belong to the orchestrator's job — when to generate, how many to generate, and what to do with the result. The platform-side curl recipes live in `SKILL.md`; this file is what makes a curl into the right curl for the moment.

## Phase gating

- `generate`, `edit`, and `remove-background` are for the **refinement** phase
  only. During requirements, do not invoke this skill; follow the host prompt's
  requirements flow and record the requested imagery for website generation.
- `design-spec` may be called in either phase to inform planning.

## How many to generate

- **One visual slot** (one hero or one logo): generate **3 variations** in one
  `generate` call so the user can choose. Pass three distinct prompts (different
  style, angle, mood, or composition) in the `requests` array.
- **Several named items** (separate products, services, people, or venues):
  generate **1 image per item**.

## Style coherence

Before composing prompts (logos excepted), fetch the website's imagery style via
the `design-spec` curl if it is not already in current-iteration context. A
fresh `design-spec` response overrides older style notes. Fold the relevant
style into each prompt. Skip this for logos; their prompt overrides live in
`references/prompt-authoring.md`.

## Modifying existing images

- Find the image via `search_uploaded_files` and pass its URL into the `edit` curl's `reference_images`.
- If the request changes output dimensions or aspect ratio, resize/crop the
  frame with Cloudinary URL transformations.
- If the request changes how large the existing image appears inside its
  current layout ("zoom in", "make it look bigger", "zoom out"), route to
  `trigger_coding_agent` for CSS scale/object-fit changes. Do not use `e_trim`.
- For "remove the background", "make it transparent", or "isolate the logo", use the `remove-background` curl (preserves the original pixels exactly). Use `edit` only when the image content itself must change; it regenerates pixels and won't preserve uploaded artwork.
- **Subject repositioning requires `edit`, not crop/CSS.** When the user asks to move, shift, or reposition a person or object within a photo (e.g., "move the woman to the left", "put the people on the right side"), that changes the image content — CSS `object-position`, `background-position`, and Cloudinary crop transformations only shift which part of the existing pixels is visible; they cannot move a subject to a different location in the scene. Use the `edit` curl with a prompt that describes the desired composition. If the user says the subject hasn't moved after a crop/position attempt, stop retrying CSS and switch to `edit`.
- When editing to reposition subjects, reference the original image and prompt for the same scene with the new composition. Emphasize preserving the room, mood, lighting, and overall feel of the original.

## After creating or modifying

Always render the new images back to the user so they can view them. Ask where they should be applied. Then call `trigger_coding_agent` to add them to the website — never embed image URLs into website code yourself.
