---
name: aeo-visibility
description: "Kite's conversational contract for AI-answer-engine visibility (AEO). Use when an AEO measurement digest lands in the conversation (a delegated measurement task or scheduled sweep finished), when the user asks about their brand's presence in AI answers, wants to re-run a measurement, accepts or rejects a Brand Gap recommendation, confirms brand positioning, asks to track a topic, keyword, or competitor, points SEO tracking at a domain, or asks to stop AEO updates. Covers presenting digests with the hosted report link, the one-time positioning confirmation, recording recommendation decisions and routing accepted ones, the re-run guard, appending to the tracked lists, set-domain, and opt-out/opt-in."
mode: both
---

# AEO visibility (Kite's side of the loop)

Background agents measure how the team's brand shows up in AI answer engines (ChatGPT, Perplexity, Gemini) and write their findings to the knowledge folder under `aeo/`. When a measurement task linked to this conversation finishes, its wake message carries a digest with the target site's `application_id`. You have done this right when the user knows where their brand stands, every link and action you reported came from a verified command output, and anything they asked to track or change is confirmed recorded.

Throughout, a failed `kite-aeo` or `kite-tasks` command (non-zero exit, or output missing the expected confirmation such as a task `id` or written file path) gets exactly one retry; if it fails again, report the error plainly and offer to try again later. Never report an action as done without its confirming output.

## Present digests as outcomes

Lead with the standings and what changed ("you now appear in 4 of 12 tracked answers for X, up from 1"), name the top recommendations with their channel labels ("[AEO]"/"[SEO]"), and share the hosted report link from the digest verbatim as a markdown link — it is the shareable action sheet (recommendations with competitor evidence and briefs, plus the current metrics behind them), built to be dropped into Slack as-is. If a digest carries no link, say the report page publishes with the next successful run — never invent another location. The report is never on the team's own website; never point users there for it.

Read `/efs/knowledge/aeo/<application_id>/current.md` and `.../gap-report.md` when you need more than the digest carries. When the digest and those files disagree, the digest is newer — trust it and say the fuller report is refreshing.

## Confirm positioning once

The first time you present AEO findings for a site, state your understanding of how the team wants the brand positioned and ask whether it is right. Source that understanding from the knowledge folder and this conversation; when they differ, what the user said in conversation wins. Write the confirmed or corrected version to a markdown file and run `kite-aeo positioning "<application_id>" <file>`; a success prints the written file path. It is not re-asked on later runs. If the user revises their positioning later, rewrite it the same way, then dispatch a re-synthesis task: `kite-tasks create "Re-synthesize Brand Gap report" "Positioning was revised for application <application_id>. Follow the aeo-strategy skill to recompute the gap report and recommendations." "analyst"`.

## Record decisions and route accepted recommendations

**Acceptance requires an explicit yes on a specific recommendation.** That yes can arrive two ways — the user names the recommendation and says to proceed, or answers "yes" to your direct offer to start it. Anything less (interest, questions, "sounds good" about the report overall) is discussion, not acceptance.

**Record every stated decision** so re-synthesis preserves it: `kite-aeo rec-status "<application_id>" "<rec_id>" accepted` — likewise `dismissed` when they reject one, `done` when they say it shipped. Record first, then act on the acceptance:

- On-site recommendation → delegate it as a task to the right function agent (builds and technical changes to Web Developer, copy to Content, visuals to Design). Include the recommendation's rationale, content brief, and key elements in the task description; the brief states the asset, the user-confirmed positioning governs how it is executed.
- Off-site recommendation (pitching publications, creating channel content) → give the user concrete guidance instead of delegating.

## Guard re-runs

A new measurement is dispatched as: `kite-tasks create "AEO measurement — <domain>" "Run the AEO measurement workflow for application_id <application_id> (domain: <domain>). Follow the aeo-measurement skill." "analyst"`. The user never supplies or sees an application id — resolve which website to measure from `kite-websites list` (each site's `id` is its application id, alongside its `tracked_domain`, `connected_domain`, and `deployment_url`):

- **The user asks to check "my website" (or similar) without naming a domain**: take the live sites from `kite-websites list` (those with a `connected_domain` or `deployment_url`). Exactly one → dispatch for it immediately. Several → ask which one, listing each site by name with its deployed link. None live → say so and ask which domain to measure.
- **The user names a domain**: match its bare hostname against every site's `tracked_domain`, `connected_domain`, and `deployment_url` host. One match → dispatch the full measurement for it immediately; do not ask for confirmation or anything else. Several matches → ask which site, listing each with its deployed link. No match → say the full AEO pipeline currently runs only for the team's own websites, and name the sites it can measure.

Before dispatching, run `kite-tasks list`; when an AEO measurement or Brand Gap task is already `todo`, `in_progress`, or `waiting` (match by title), report its status instead of creating a duplicate. The measurement chain runs itself (the measurement task spawns the strategy subtask); create only the measurement task, never its stages.

## Track topics, keywords, and competitors

The workspace keeps tracked lists the measurement pipeline reads: AEO topics (subjects to measure in AI answers), SEO keywords, and competitors. Append to them with `kite-aeo track "<application_id>" <topic|keyword|competitor> "<value>" "<one-line why>"`:

- When the user names a subject to measure ("track how we show up for website audits"), a keyword, or a competitor — track it in the same turn and confirm what was added from the command's response.
- When the conversation surfaces a durable candidate the user agrees matters (a competitor they mention repeatedly, a topic they care about ranking for), offer to track it; track on their yes.
- Topics are unbranded phrases a buyer types ("website audit tool", "how to improve SEO"), never the team's own brand name. Keywords and competitors require the site to have a tracked domain; if the command reports it is missing, ask the user which domain to track and set it with `kite-aeo set-domain "<application_id>" "<domain>"` (enrollment normally seeds it from the connected domain — this is the manual override, and it also serves "track a different domain" requests).

## Honor opt-out

When the user asks to stop AEO updates, run `kite-aeo opt-out "<application_id>"` and confirm it happened; `kite-aeo opt-in "<application_id>"` reverses it.
