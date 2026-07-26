---
name: brand-research
description: >
  Use this skill when the task is to capture a company's brand identity from its
  live website — "research brand X", "what is their look and feel", "profile our
  brand", "document the brand voice and visual style", or a bare company URL when
  the goal is a brand profile rather than a single fact. Covers the visual
  identity (colors, typography, logo, imagery, layout feel), the writing voice and
  tone taken from real page copy, and the brand personality and positioning cues,
  then files the profile to the team's shared knowledge. For general market,
  competitor, or pricing research, or a quick one-off brand-token pull, use
  `web-research`.
mode: sandbox
---

# Brand Research

Profile a company's brand from its live website — how it looks, how it sounds, and
what it stands for — then record the profile in the team wiki.

## Use When

- A research task asks for a company's brand, look and feel, visual identity, or voice and tone.
- You are about to produce customer-facing work and need the self company's own brand on record first.
- Not for a single brand-token pull or general market and competitor research — use `web-research`. Not for restyling a site from a reference — use `website-design-extraction`.

## Inputs

- The company's website URL, or enough to find it. For the self company, use the site named on `company/identity.md`.
- Whether the subject is the self company or an external one — it decides where the profile is filed.

## Workflow

1. Load context per `wiki-management`. For the self company, re-read `company/brand/` so you extend the existing record. Apply its source precedence:
   - Current verified evidence supersedes older agent-written facts with provenance.
   - `source: user-edit` remains pinned. Preserve and report any conflict with research evidence; do not relabel the user edit as research-verified.
   - A prior fact remains when replacement evidence is unavailable, but is not relabeled as newly verified.
2. Use the platform Firecrawl commands as the extraction source. Start with the canonical homepage URL. Run `kite-research scrape "<url>"` for page content, `kite-research brand "<url>"` for semantic design tokens, and `kite-research assets "<url>"` for page-exposed image and logo candidates. From the scraped homepage, choose one or two same-site primary pages (About, Product, or Services pages linked from the homepage), run the same three commands on each, and retain every input URL beside its evidence. Follow `web-research` for the returned JSON fields and gateway error contract.
3. Classify the evidence before synthesizing it. A newly researched visual fact is `verified` only when every applicable source, role, corroboration, and asset-property rule below is satisfied; otherwise it is `unverified`.
   - **Colors and type** — verify a concrete hex/RGB color or named font in a semantic role in the homepage's `result.brand.color_palette` or `result.brand.typography_palette`. When a primary page exists, confirm the same value and role there. When none is linked from the homepage, homepage evidence is sufficient. Treat declared tokens as global theme inventories only. Promote a WordPress preset or other declared token only if the current page's role-keyed result contains that concrete value.
   - **Logos and imagery** — retain each `result.images` candidate's exact asset URL, source page, and usage context. A canonical logo requires homepage header or navigation usage as the identity link to home. When a primary page exists, confirm the same asset URL or the same wordmark text and symbol geometry in that role there. When none is linked from the homepage, homepage evidence is sufficient. Record color or transparency differences within that family as background variants. Newsroom, docs, partner, and article-only logos remain candidates. Required properties are visible pixel colors, transparency, actual-use background, and light/dark-background suitability. A missing property leaves the candidate `unverified`, leaves the canonical headings unset, and blocks visual-profile completion when logo candidates exist. Describe imagery treatment, layout density, and motion only when Firecrawl page, asset, or screenshot evidence supports them.
   - **Voice and essence** — use quoted scraped copy to assess reading level, sentence length, person, formality, humor, and recurring phrases. Label positioning and personality conclusions as inference.
4. Optionally use `kite-research screenshot "<url>" [viewport]` or `browser-session` after extraction for final rendered verification or fallback observations. Browser availability is not an extraction dependency. Firecrawl evidence retains precedence; rendered observations may corroborate it or fill a gap, but never override it.
5. Record the profile per `wiki-management`, routed by subject: the self company → `company/brand/visual.md` and `company/brand/voice.md`; any other company → its `research/<slug>.md` (set `relationship: competitor` when it is one). Preserve existing frontmatter and facts per step 1. For the self company, add `Primary logo`, `Light-background variant`, and `Dark-background variant` only for verified assets; under each, record asset URL, source page, usage context, pixel colors, transparency, actual-use background, and suitable backgrounds. Put other assets under `Logo candidates (unverified)` with their unresolved properties. Never put another company's brand on the self pages.

## Verification

Before returning, complete every check:

- Confirm each required page returned text in `result.markdown`, at least one concrete color role and one font role in `result.brand`, and `result.images` without a Firecrawl error. An empty image list is valid only when the scraped page exposes no images.
- Confirm every promoted visual fact passes Workflow step 3, and every finding retains its source URL. Unverified logo candidates block `Visual profile: complete`.
- Confirm every voice claim cites a specific scraped line and source URL; label each essence claim as inference.
- Confirm the write landed on the required subject page, no external brand data landed on a self-company page, and the `wiki-management` submission succeeded.

## Failure Handling

- Apply `web-research` retry handling to Firecrawl gateway errors. When a required `scrape`, `brand`, or `assets` call still fails or misses the first verification check, preserve only the prior facts whose replacement evidence is missing and return `Visual profile: incomplete/blocked` with the URL, failed command, and missing evidence. Submit only independently verified updates.
- Rendered observations can corroborate Firecrawl evidence but cannot validate a failed extraction or an unverified logo candidate. Browser capacity failure does not block a Firecrawl-complete profile. When it leaves a required property without evidence, that property stays unverified, no canonical logo is finalized from it, and a profile that needs that evidence cannot be reported as successful or complete.
- When the site is unreachable, report which URL failed and profile only what loaded — do not invent tokens.
