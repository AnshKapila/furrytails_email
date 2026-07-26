---
name: onboarding
description: >
  Use this skill when a team is being set up for the first time and wants its
  company, its brand, and its search standing captured from scratch — "onboard
  us", "get us set up", "here is our website, take it from here", the first
  working session right after a company is established — or whenever the user
  says to onboard a named company or site ("onboard kite.ai"), which names the
  team's own company. Onboarding always establishes the team's own company;
  studying any other organization is a research delegation, not onboarding.
  It runs the onboarding sequence: confirm and record the company's identity,
  commission its company research, its brand profile, and its SEO/AEO growth
  research to run at the same time, then turn all three into one shareable
  overview styled in the company's own look. For a single research request or
  a one-off report, delegate that on its own instead of running the whole
  sequence.
mode: sandbox
---

# Onboarding

Take the team's own company from nothing to a shareable overview of who they
are, how their brand looks and sounds, and how they show up in search. You
commission the work and relay the result; the specialists do the hands-on
part.

## Use When

- A team is new, or the user asks to be onboarded, set up, or "gotten started" — often handing over just their website.
- The company was just established and no research, brand profile, or search read is on record yet.
- The user asks to onboard a named company or site ("onboard kite.ai") — that names the team's **own** company. Onboarding is always for the self company; never run it as external research on the named site. An explicit onboarding ask is never rerouted to a single research task; a request for only one research stream remains a single-task delegation.
- Not for a single later research ask or a one-off report — delegate those on their own. Not for studying another organization — that is a research delegation to its `research/` page, never this sequence.

## Sequence

Run the steps in order, except within Step 2: commission its three independent tasks in parallel, not sequentially. Step 3 never starts until all three tasks have returned a task id and a result summary (success or failure), even if some finish early.

1. **Confirm and record the identity.** Onboarding establishes the team's own company — there is no external onboarding. Key the sequence off one company and its website URL:
   - **Identity absent, unset, or incomplete, and the ask names a company or site:** the onboarding ask itself is the user naming their company — that is the user confirmation `wiki-management` requires. Use its display name and primary domain as the confirmed identity.
   - **Identity absent, unset, or incomplete, and no site was named:** ask the user for the display name and primary domain per `wiki-management`.
   - **Identity recorded, and the ask names the same company or none:** use the recorded identity.
   - **Identity recorded, but the ask names a different company:** stop and ask the user to confirm the identity change per `wiki-management`. If they actually want that other organization studied, delegate it as a research task instead — never as onboarding.
   - After the display name and primary domain are confirmed, use this recovery order whenever the identity needs creation or repair:
     1. Create or repair `company/identity.md` with the confirmed identity per `wiki-management`.
     2. Run the documented wiki-submit procedure.
     3. If that submit fails, retry it once.
     4. If the retry also fails, continue to Step 2 with the confirmed display name and primary domain. Preserve the intended identity content and submit error in every research task description and later overview task, require each result to repeat the intended identity content and persistence gap, and report that gap to the user.
2. **Commission all three streams in parallel.** In the same turn, per `work-delegation`, create three independent tasks so they run at once:
   - **Company research** — who they are, what they sell, their market, positioning, ideal customer, and closest competitors. Assign `research`.
   - **Brand profile** — the live site's visual identity (logo, colors, fonts, imagery, design style), voice and tone, and brand essence. Assign `research`.
   - **Search standing and growth** — where the live site ranks and how discoverable it is, its SEO and AEO gaps, what its target users are searching for, and the queries it has no page for with the pages worth adding — the organic growth opportunities, grounded in real ranking and search-volume data. Assign `research`, which owns keyword and answer-engine research.
   Create all three tasks together in the same turn, not in sequence, so they run in parallel. Write each task self-contained: the goal, the confirmed company display name and primary domain, that the target is the team's own company, that it is research and analysis to file — not website edits, since there may be no editable site — and what "done" looks like. Findings file to the self-company pages per each specialist's skill: company research to the `company/` pages, the brand profile to `company/brand/` (visual and voice), and search standing to its domain's current and dated snapshot pages — never to an external `research/` page. Say so in each task description. Tell the user all three are underway and what each will produce.
3. **Wait for all three, then commission the overview.** Only after every task has returned a task id and a result summary (success or failure) and none remains in progress, per `work-delegation`, create one task for `generalist`: a single onboarding overview report that combines the company research, the brand profile, and the search findings into one page. A successful summary must name the key findings, sources, and wiki paths; a failed summary must name the blocker. Inline each result summary and point it at the wiki pages the streams filed for the full detail. Instruct it to style the page in the company's own brand — the colors, fonts, and logo the brand stream recorded in `company/brand/` — so the overview looks like the team's company, not a generic template.
4. **Hand back the page.** When the report is live, share its link with a two-line summary of what onboarding surfaced. If identity persistence is still unavailable, name that gap and the identity content that remains to be submitted. That page is the deliverable.

## Verification

- The report was not commissioned while any stream was still in progress — every stream reported first, each with a task id and a result summary. After that gate, a stream that failed after its retry is handled per Failure Handling (a partial overview that names the gap), never silently dropped.
- The report task description carried the brand's colors, fonts, and logo source, so the page is styled in the company's brand rather than a default theme.
- The company and its site were confirmed before any stream was commissioned, and every task description named the same display name and primary domain and stated the target is the team's own company.
- Identity creation or repair followed create or repair → submit → one retry. After a failed retry, the streams still ran with the intended identity content and persistence gap in their task and result context.
- The streams' findings landed on the self-company pages, not on an external `research/` page. The overview and user handoff reported any wiki persistence gap that remained.

## Failure Handling

- When one stream fails, retry it once; if the second attempt returns a failed status or error, build the overview from the streams that finished and note the missing piece in the report rather than withholding the whole page. Report which stream fell short and offer to rerun it.
- When the company or its site cannot be confirmed, stop and ask the user for it — onboarding cannot key off an unknown site.
- Other than an unknown company or primary domain, block only when a required non-wiki system remains inaccessible after its documented recovery or fallback. A wiki submit that still fails after its one retry follows Step 1's continue-and-report path.
