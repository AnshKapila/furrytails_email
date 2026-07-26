---
name: website-aeo-metadata-management
description: >
  Use this skill when creating or updating a website's llms.txt or AI-readable
  site index — for example "add llms.txt", "make the site easier for AI to
  understand", or "update the AI index". Also use it after a new route or a
  material change to site copy, structure, or brand summary. Use
  `website-sitemap-management` for sitemap.xml and
  `website-seo-metadata-management` for structured data.
mode: both
---

# llms.txt Generator

## What this skill does

`llms.txt` is a Markdown file placed at the root of a website (`/llms.txt`) that gives LLMs a concise, curated map of the site. Context windows can't absorb a whole website of HTML, navigation, and ads, so `llms.txt` hands the model a short, expert-level overview plus links to the pages that actually matter.

This skill takes whatever the user provides — a README, a page list, a sitemap, raw notes, a site description — and turns it into a clean, spec-compliant `llms.txt`. The user supplies the material; your job is to organize, curate, and write it well. The end deliverable is a single file named `llms.txt`.

This works for **any** kind of site, not just code documentation. The format is the same; only the section names and emphasis change.

## The format

An `llms.txt` file has these parts, and they must appear **in this order**:

1. **An H1 with the site or project name.** This is the only strictly required element.
2. **A blockquote summary** — a short paragraph (`> ...`) capturing what the site is and any key facts needed to interpret the rest of the file. Strongly recommended; almost always include it.
3. **Optional free-form prose** — zero or more paragraphs or lists giving must-know context. This region may *not* contain any headings.
4. **Zero or more H2 sections**, each a "file list": an H2 heading followed by a Markdown list of links. Each list item is `[name](url)` and may optionally be followed by `: ` and a short description.

The only headings allowed anywhere in the file are the single H1 and the H2 section headers. Don't use H3+ or put headings inside the prose region — parsers and downstream tools rely on this structure.

Skeleton:

```
# Site Name

> One to three sentences on what this site is and the key facts a reader needs.

Optional short paragraph or list of must-know context.

## Section Name

- [Page title](/page): What the reader finds here and why it matters.
- [Another page](/other): Brief, informative note.

## Optional

- [Secondary resource](/extra): Nice-to-have, safe to skip.
```

### The "Optional" section is special

A section literally named `## Optional` has reserved meaning: its links are secondary material that tools may skip when a shorter context is needed. Put supplementary or background resources here — never anything essential. Use it as a pressure valve for context size, and omit it entirely if everything is core.

## Workflow

The site name, brand voice, sitemap (page list with titles and purposes), and any
must-know constraints are already in the surrounding context — visual spec, brand
metadata, sitemap plan, workpad build requirements, and user requirements. Use
them directly; do not pause to ask the user for material they have already
supplied.

1. **Write the H1 and the summary blockquote.** The H1 is the site/brand name as
   a human would say it. The blockquote is the elevator pitch plus any fact a
   model must know to use the rest correctly (what it is, who it's for, notable
   constraints). Keep it to roughly one to three sentences.

2. **Decide whether prose is needed.** Add a short paragraph or list only for
   must-know context that doesn't fit the summary — e.g., a compatibility
   caveat, a usage tip, a policy that governs everything else. Skip it
   otherwise. Brevity is the point.

3. **Curate and group the links into H2 sections.** This is the core of the
   work. `llms.txt` is a *curated* overview, not a sitemap dump — pick the
   pages that genuinely help an LLM understand and use the site, and leave out
   boilerplate (cookie notices, login-only pages, duplicate landing pages).
   Group related pages under H2 headings named for how a knowledgeable person
   would mentally organize the site (see next section).

4. **Write a description for each link.** After each link, add `: ` and a
   concise, informative note — what the reader will find and why it's useful.
   One line each. This is what lets a model decide which link to follow.

5. **Pull secondary material into an `## Optional` section** if there's
   anything that's helpful but skippable.

6. **Self-check against the checklist** at the end of this file before
   finishing.

## Choosing sections for different site types

Section names should describe the site's actual structure. Some starting points — adapt freely, don't force a site into a template:

- **Software / documentation:** `Docs`, `Getting Started`, `API Reference`, `Tutorials`, `Examples`, `Optional`
- **SaaS / business / company site:** `About`, `Products` or `Solutions`, `Pricing`, `Customers`, `Support`, `Policies`
- **Personal site / portfolio:** `About`, `Writing` or `Blog`, `Projects`, `Talks`, `Contact`
- **E-commerce:** `About`, `Product Categories`, `Buying Guides`, `Shipping & Returns`, `FAQ`
- **School / university / nonprofit:** `Programs` or `Courses`, `Admissions`, `Research`, `Resources`, `Contact`

The guiding principle: a reader scanning your H2 headings should immediately grasp what the site offers and where to look. Three to six well-chosen sections usually beats a long list of thin ones. A section can also have just one or two links if that link is important enough.

Include a section only when the site content supports it — never add an empty or speculative one.

Section names that fit most business sites, as further starting points: `Website overview`, `Primary user goals`, `Key pages`, `Products` or `Services`, `Mission and values`, `Team`, `Locations` or `Service areas`, `Pricing` or `Plans`, `Contact`.

### Sections that speak to AI agents directly

`llms.txt` is read mainly by AI agents, so two sections are worth adding to almost any site when the content supports them:

- **`Agent guidance`** — practical, plain instructions for an agent using the site: which page to consult for which kind of question; when to send users to an official contact form, support page, sales page, or other official channel; and what the agent must not infer, estimate, or fabricate.
- **`Common questions`** — the questions users most often ask, each pointing at the page that answers it.

## Writing well

- **Be concise and concrete.** Expert-level but plain. The audience is a model deciding what to read next.
- **Front-load the summary with what matters most** — what the site is, who it serves, and any constraint that changes how everything else should be read.
- **Avoid unexplained jargon and ambiguous terms.** If a term is load-bearing, explain it briefly.
- **Make every link description earn its place.** Say what the page is the source of truth for — what a reader finds there and which questions it answers. "Pricing page" is weak; "Plan tiers, per-seat costs, and what each tier includes" tells a model whether to follow it.
- **Be specific to this site, not generic.** Describe what the site actually is. Avoid filler like "a professional business website" unless the content genuinely is that generic.
- **Curate ruthlessly.** When in doubt, leave a marginal page out or move it to `Optional`.
- **State only what the source supports.** Do not invent services, products, pricing, timelines, client names, awards, office hours, phone numbers, team members, locations, guarantees, or policies. If a fact is missing, omit it or guide agents to say it is not listed on the site — never imply it exists.

## Link targets

Every link target is a **site-relative path** beginning with `/`. Examples:
`/`, `/about`, `/pricing`, `/blog/launch-update`. The site serves `llms.txt`
from its root, so relative paths resolve correctly against whatever origin
the site is deployed at.

- **Every link must point at a route that actually exists on the site.**
  Verify the path against the supplied source — for an HTML SPA, the
  `const routes = { ... }` declaration; for Next.js, the
  `src/app/**/page.tsx` set; for an MPA, the `<a href="/…">` links from
  the home page. If a path is not in that source, leave it out.
- **Never include an absolute URL** (anything starting with `http://`,
  `https://`, or `//`) as a link target. The deployment origin is decided
  later and is not knowable here.
- **An inspiration / source URL in the brief is not the deployment URL.**
  If the user's prompt references a site being remixed, redesigned, or
  scraped (e.g. "build a site like https://example.com"), that origin
  belongs to a third party — using it sends LLMs and agents off this site
  entirely. Strip the origin; keep only the path portion if it matches a
  real route on the generated site.
- Use `.md` variants only when the surrounding context confirms a Markdown
  version of the page exists at that URL.
- Favor content-rich routes over navigation-only or login-gated pages.

BAD: `[Features](https://www.example.com/features)` — absolute URL pointing
at a third-party origin.

GOOD: `[Features](/features)` — site-relative, resolves against the
deployed origin at runtime.

## Where the file lives

The output is a plain UTF-8 Markdown file named exactly `llms.txt`, written at
the site root so it is served from `https://<site>/llms.txt`. Pick the path
based on the surrounding project layout:

- **Kite HTML site (source under `frontend/src/`, served by Vite from
  `frontend/public/`):** `frontend/public/llms.txt`. This is the only path
  Vite serves at `/llms.txt`; the SPA `index.html` and any MPA pages under
  `frontend/src/` all resolve `/llms.txt` here. The initial file is written
  programmatically by the post-selection background task in
  `app/llm/llms_txt/generator.py`; when you load this skill during an edit,
  write here directly.
- **Next.js / Vite / Astro / any other framework with a `public/`
  directory:** `public/llms.txt`.

Don't stall on minor missing details: if a small gap remains (e.g. a
description you cannot confirm from context), write a sensible draft from the
sitemap and brand summary rather than blocking.

## Examples

### Example: a SaaS / business site

```
# Brightpath Analytics

> Brightpath is a cloud analytics platform that turns raw product event data into dashboards and alerts for non-technical teams. It is aimed at product and growth teams; it is not a general-purpose BI tool and does not support custom SQL.

Key things to know:

- Brightpath connects to event sources via prebuilt integrations only — there is no raw database connector.
- All plans include unlimited viewers; pricing scales by tracked monthly events.

## Product

- [How Brightpath works](/product): Overview of event ingestion, dashboards, and alerting.
- [Integrations](/integrations): Full list of supported event sources and how to connect them.

## Pricing

- [Plans and pricing](/pricing): Tier breakdown, event limits, and what each plan includes.

## Support

- [Help center](/help): Setup guides, troubleshooting, and FAQs.

## Optional

- [Company blog](/blog): Product updates and analytics best-practice articles.
```

### Example: a personal site / portfolio

```
# Jordan Lee

> Jordan Lee is a product designer and writer based in Lisbon, focused on accessibility and design systems. This site collects their writing, project case studies, and ways to get in touch.

## About

- [Bio and background](/about): Career history, focus areas, and current work.

## Writing

- [Essays on design systems](/writing): Long-form articles on building and maintaining design systems.

## Projects

- [Case studies](/projects): Detailed write-ups of selected client and personal projects.

## Contact

- [Contact and availability](/contact): How to reach Jordan and current availability for work.
```

Note how the structure is identical across very different sites — only the H1, summary, and section names change.

## Final checklist

Before delivering, confirm:

- [ ] The file starts with a single H1 naming the site.
- [ ] A blockquote summary follows the H1 (present unless the user explicitly declined it).
- [ ] Parts appear in order: H1, summary, optional prose, H2 sections.
- [ ] The only headings are the one H1 and the H2 section headers — no H3+, no headings inside prose.
- [ ] Every H2 section is a Markdown list of `[name](url)` links.
- [ ] Most links have a concise, informative description that says what the page is the source of truth for.
- [ ] Descriptions are specific to this site, not generic filler.
- [ ] No invented facts; missing information is framed as "not listed on the site," not implied to exist.
- [ ] Any `Agent guidance` section is practical — which pages to use, when to point at official channels, what not to fabricate.
- [ ] Links are curated, not an exhaustive sitemap dump.
- [ ] `.md` link targets are used only where confirmed to exist.
- [ ] Any `## Optional` section contains only skippable, secondary material.
- [ ] The file is saved as `llms.txt` at the site root (see "Where the file lives").
