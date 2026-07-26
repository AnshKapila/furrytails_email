---
name: competitor-discovery
description: Use this skill when the task is to identify who a business competes with — "who are our competitors", "build a competitor list", "what are the alternatives to X", "map our market landscape", "who else does what we do". Produces a tiered, evidence-backed competitor list that covers direct rivals and also the indirect players, substitutes, and adjacent threats a naive search misses, with every entry verified from independent sources. For tracking changes at competitors you already know, use `competitor-monitoring` instead; for turning competitor standing into keyword or content moves, use `keyword-research`.
mode: sandbox
---

# Competitor Discovery

Build a competitor list the business can act on: complete across lenses, verified per entry, tiered by threat. A list of five obvious direct rivals from one search is the failure mode this skill exists to prevent.

## Inputs

Before sourcing, establish: what the business sells, to whom, at what price point; the job the customer hires it for, in the customer's words; and geography or segment boundaries, if any. Sources, in order: wiki `company/identity.md` (what the business is and sells), `icp/` (who buys), `positioning/` (how it competes and prices) — then the task description for anything the wiki lacks.

If none of this is derivable, ask the delegating agent — a competitor list against a guessed positioning is worthless.

## The five lenses

Sweep every lens; state explicitly when a lens turns up nothing. Each lens is a membership test a candidate must pass:

1. **Direct** — same offering, same buyer. The customer compares them head-to-head.
2. **Indirect** — different offering, same job-to-be-done. (For a website builder: a design agency.)
3. **Substitute** — how the buyer solves the job without buying anything in the category: DIY, spreadsheets, an intern, doing nothing. Name the dominant substitute even when it isn't a company.
4. **Adjacent** — companies serving the same buyer with a neighboring product that could expand into the category, or that buyers mistake for the category.
5. **Budget** — competes for the same budget line even with an unrelated product, when the task or positioning makes budget rivalry material (skip this lens for most SMB tasks; say so).

## Sourcing protocol

Use `web-research` commands. For each lens, source candidates from at least two independent angles. Angles 1–2 generate candidates; angles 3–5 corroborate, extend, and validate them — when angles disagree about a candidate, resolve it in Verify and tier rather than picking a favorite angle.

1. **Entity discovery** (generates lens candidates, each pre-verified with citations): `kite-research findall` with the lens's membership test as the objective — e.g. `"companies offering AI-powered website builders for small businesses"` (direct), `"services small businesses use to get a website without building it themselves"` (indirect/substitute). One findall run per lens, `match_limit` 10–20.
2. **Alternatives language** (generates the candidates buyers actually compare): `kite-research search` for `"<company or category leader> alternatives"`, `"<company> vs"`, `"best <category> for <ICP>"` — the comparison pages and listicles buyers read.
3. **Community evidence** (corroborates; surfaces substitutes vendors don't name): `kite-research mentions "<company or category>"` plus a `search` scoped to Reddit and review sites for "switched from", "instead of", "cheaper than" phrasings.
4. **Search-overlap** (extends, when keyword standing matters to the business): the DataForSEO catalog via `tool-discovery-execution` — who ranks for the business's money keywords.
5. **Firmographic screen** (validates; fills headcount/funding for B2B lists): `native:crustdata-company-search` (execute pattern in `tool-discovery-execution`; filters DSL: one `{field, type, value}` condition or `{op: and|or, conditions: [...]}` — e.g. `{"field": "taxonomy.categories", "type": "(.)", "value": "website builder"}`).

## Verify and tier

Every candidate must pass all four checks before it enters the output table; drop the ones that fail:

1. **Two independent sources** (a findall citation counts as one). Record both URLs.
2. **Alive**: the product exists and its site is up — `extract` its homepage when in doubt.
3. **Serves the ICP**: check pricing/positioning; for an SMB list, drop enterprise-only players (note them in one line instead of listing them).
4. **Tier assigned by evidence**: **Tier 1** — appears in buyer comparisons ("alternatives" pages, review threads) against this business, or targets the same ICP with the same offering; **Tier 2** — passes the lens test but rarely shows up in buyer comparisons, or overlaps only part of the ICP or offering. Substitutes and adjacents are listed with their lens explanation instead of a tier.

When evidence conflicts, the company's own current site wins for *what they sell*; buyer reviews and community threads win for *who actually buys and why*.

## Output

- A table, one row per competitor:

  | Name | URL | Lens | Tier | Why they compete | Evidence |
  |------|-----|------|------|------------------|----------|
  | [company] | [url] | direct | 1 | [one line] | [url1], [url2] |

- The dominant substitute, even when it's "do nothing", with a one-line explanation.
- Lenses that came up empty, stated as findings.
- File the result to the wiki's competitor pages (per `wiki-management`) so `competitor-monitoring` can track changes against it, and deliver the summary in the task result.

## Failure handling

- Sparse category (fewer real competitors than expected): deliver the short verified list and say why — do not pad with weak matches.
- Conflicting positioning evidence (site says one ICP, reviews say another): list the candidate under the lens the evidence supports and flag the conflict.
