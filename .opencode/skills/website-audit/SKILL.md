---
name: website-audit
description: Use this skill when the task is to assess how well a website or a page performs — "audit our site", "why isn't our homepage converting", "how do we show up in search and AI answers", "grade this landing page", "what should we fix first on the site". Produces a graded scorecard across message, conversion, pricing, search visibility, AI visibility, and technical foundation, with a short list of evidence-backed verdicts and a first-week plan. Works on the team's own site or a competitor's. For a full company report (history, firmographics, competitors) use `company-deep-dive`; for building the keyword universe itself use `keyword-research`; for diffing a known competitor over time use `competitor-monitoring`.
mode: sandbox
---

# Website Audit

Grade a website the way a growth advisor would: six dimensions, weighted by the business's stage, every verdict tied to evidence you actually collected. This is the same standard the platform's public page-audit report applies — an audit you produce should agree with it.

## Gather before grading

Collect with `web-research` commands; grade nothing you haven't looked at:

- `extract`/`scrape` the homepage and the money pages (pricing, signup, top landing pages); `screenshot` the homepage — the first viewport carries most of the message grade.
- Robots/sitemap: `extract` `<site>/robots.txt` and `/sitemap.xml` for crawlability and AI-crawler access.
- Search standing: the DataForSEO catalog via `tool-discovery-execution` — ranked keywords, top-3 presence, competitor rank overlap.
- Real behavior when it matters: `browser-session` to click the primary CTA and see what actually happens — the one evidence source the crawl can't give you.

## Stage, then weights

Classify the business first — **New** (little traffic or content, pre-traction), **Growth** (ranking and converting some, scaling), **Established** (mature traffic, defending position) — because the same flaw matters differently by stage:

| Dimension | New | Growth | Established |
|---|---:|---:|---:|
| Message & positioning | 35 | 15 | 10 |
| Conversion readiness | 30 | 20 | 15 |
| Pricing & packaging | 5 | 15 | 10 |
| Search visibility | 20 | 20 | 25 |
| AI visibility | 5 | 20 | 25 |
| Technical foundation | 5 | 10 | 15 |

Grade each dimension **Excellent / Strong / Developing / Needs attention**.

## What good looks like, per dimension

- **Message & positioning** — the first viewport makes the product category and buyer clear without scrolling. Flag hero copy built on unproven generics ("best", "fast", "simple", "powerful", "seamless") and copy that could describe any company in the category.
- **Conversion readiness** — one clear primary CTA per page; button copy names a specific action; proof (logos, metrics, reviews, case studies, screenshots) sits near the CTAs, not on a separate page.
- **Pricing & packaging** — pricing is findable and legible; tiers map to identifiable buyer types; the next step from the pricing page is obvious.
- **Search visibility** — top-3 rankings for the queries that matter; winnable keywords have a dedicated page; positions 5–20 with fixable on-page issues are called out as the cheapest wins.
- **AI visibility** — the site answers real buyer questions in a form an answer engine can quote. Favor source clarity over content volume: the goal is not more pages, it is pages answer engines can understand and cite.
- **Technical foundation** — AI crawlers (GPTBot, PerplexityBot, ClaudeBot, Google-Extended) are allowed; main content renders without JavaScript; canonical/robots/sitemap are coherent.

## Evidence discipline

- Never assert a flow is broken from crawl data alone — a CTA href is a hint, not proof. Verify interactively with `browser-session` or label the finding as unverified.
- Every verdict names its grounds: the page, the element or metric, and how you observed it.
- Distinguish "different from taste" from broken — flag the latter, mention the former only when it measurably hurts a graded dimension.

## Output

One markdown report with this skeleton:

```markdown
# Website audit: [site] — [date]
Stage: New | Growth | Established (one line on why)

## Scorecard
| Dimension | Grade | Grounds |
|-----------|-------|---------|   <!-- all six dimensions, one-line evidence each -->

## Verdicts                        <!-- exactly 3: page, element/metric, how observed -->
## Quick wins                      <!-- 2, each shippable in under a day -->
## First-week plan                 <!-- 3 steps -->
```

- **Three verdicts**, not ten: the highest-impact, most site-specific findings, drawn from different dimensions. Prefer the finding specific to this site over the one true of every site in the category.
- File the audit to the wiki (per `wiki-management`) so later audits can diff against it; summary in the task result.

## Before returning

- Every verdict names its page, its element or metric, and how you observed it (crawl, screenshot, interactive check, or search data).
- The report has all five parts: stage, six graded dimensions with grounds, three verdicts, two quick wins, three-step plan — or an "insufficient evidence" note where a part could not be graded.

## Failure handling

- A data source erroring (search data, a page that won't render) drops its dimension to "insufficient evidence" with the reason — never grade on a guess.
- Auditing a competitor's site: same rubric, but skip interactive CTA verification that would create accounts or submit forms; note the limits.
