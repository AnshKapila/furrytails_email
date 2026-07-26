---
name: conference-research
description: >
  Use this skill when asked to find, rank, or report on conferences, summits,
  trade shows, industry events, sponsorships, exhibitor packages, or speaking
  opportunities for go-to-market — "which conferences should we sponsor",
  "find events where our buyers will be", "is this event worth attending".
  For market or competitor research with no event angle, use `web-research`;
  for building the full invite or prospect list for a chosen event, use
  `prospect-research`.
mode: sandbox
---

# Conference Research

Produce an evidence-backed shortlist and a readable decision report. Optimize
for GTM usefulness, not travel planning or generic event discovery.

## Inputs

Capture or infer these before researching:

- Company name and domain.
- Market/category.
- ICP and buyer personas.
- Geography and travel constraints when known.
- Time window, usually the next 6-12 months.
- Goal: customer acquisition, partner development, analyst visibility, hiring,
  fundraising, community, or sponsorship.
- Delivery context from the delegating agent, including `slackChannel` and
  `slackThread` when supplied.

If the request names a company but omits ICP, stage, geography, or goal, read
the wiki and public context first. Ask the delegating agent for missing
constraints only when the answer materially changes the shortlist.

Extract the working GTM thesis:

- Primary buyer and user.
- Trigger pains and category alternatives.
- Regions with sales capacity or strategic importance.
- Current acquisition channels and gaps.
- Positioning wedge to test at events.

If wiki context is missing or stale for volatile facts, verify with current web
sources and write the synthesis back to the wiki before final delivery.

## Conference Discovery

Build the candidate universe from multiple source types:

- Official conference, summit, expo, trade show, and industry calendar pages.
- Competitor, customer, partner, analyst, and investor event pages.
- Sponsor, exhibitor, and media-kit pages for adjacent products.
- Speaker pages for relevant executives, practitioners, analysts, and community
  leaders.
- LinkedIn or event-platform pages when accessible.
- Search queries combining buyer persona, use case, category, region, and year.

Use queries like:

- `"<category>" conference 2026 sponsorship`
- `"<buyer persona>" summit 2026 agenda`
- `"<competitor>" sponsor conference 2026`
- `"<use case>" expo exhibitors 2026`
- `"<region>" "<category>" summit 2026`

Prefer official event pages for dates, venue, agenda, sponsorship,
registration, and pricing. Use secondary sources only to discover candidates or
corroborate audience claims.

## Source Requirements

For every recommended conference, collect sources for:

- Official event homepage.
- Dates and location or virtual format.
- Registration or attendee link. Use the direct attend/register URL when public.
- Agenda, tracks, speaker list, or call-for-speakers page.
- Relevant speaker names, roles, companies, sessions, and professional emails
  when available.
- Sponsorship, exhibitor, media kit, partner prospectus, or sponsor contact
  link. Use the direct sponsor/exhibit URL when public.
- Audience profile, attendee roles, exhibitor list, or past attendee statistics.
- Public pricing, sponsorship tiers, deadlines, or contact path when available.

Treat conference pages as volatile. Check the page year and avoid stale event
pages. If only a prior-year sponsorship prospectus exists, label it clearly and
reduce confidence.

Do not invent attendee counts, sponsorship prices, speaker names, or deadlines.
If a field is not public, write `Not public` and include the best contact path.

## Speaker Research

Speaker research is mandatory for every recommended event. A conference report
that ranks events without researching who is speaking is incomplete and must not
be returned as `succeeded`.

After ranking the shortlist, for each recommended event:

1. Pull the published speaker lineup, keynote list, agenda, and session pages.
   Identify speakers most relevant to the target company by role, company,
   session topic, buyer perspective, partner motion, investor market, or
   sponsorship goal.
2. Research each relevant speaker's background from public sources. Capture
   name, title, company, the team/product/domain they work on, session or track,
   topic, why they matter to the target company, and a profile/source URL.
3. Aim for the most relevant 5-10 speakers per recommended event. Use fewer only
   when the lineup is genuinely small. Cover highest-fit buyer, decision-maker,
   and partner profiles first.
4. If the lineup is not yet published, say
   `Speakers not yet announced as of <date>, source: <url>`, then list confirmed
   past-edition speakers or the organizer/CFP contact as a proxy.
5. Never write `Not researched` when a public lineup exists. Mark uncertainty
   and link the source instead.

## Speaker And Contact Enrichment

Contact enrichment is mandatory when the platform enrichment catalog is
available. It is a layer on top of completed public speaker research, not a
replacement for it. Enrichment mechanics — the tool calls, email data-point
request shape, confidence marks, and privacy rules — are owned by
`prospect-research`; follow it.

Event-specific rules:

1. Enrich after selecting the relevant speakers: only the 5-10 highest-fit
   speakers per event, plus needed organizer, sponsor, or partner contacts —
   never an entire conference roster.
2. For each enriched contact, capture why the person matters to the GTM motion
   alongside the `prospect-research` contact fields.
3. If enrichment is unavailable after one retry, continue with public sources,
   mark affected fields `enrichment unavailable: <exact error>`, and return
   `partial` with the blocker named. Enrichment failure does not excuse
   missing public speaker research.

## Fit Scoring

Score each candidate from 1-5 on:

- Strategic fit: category, wedge, and GTM priority alignment.
- Buyer density: likelihood target buyers or strong influencers attend.
- Intent level: evaluation intent versus general networking.
- Sponsorship value: booth, speaking, lead capture, meetings, or partner options.
- Speaker/partner potential: realistic chance to speak, host, sponsor,
  co-market, or meet partners.
- Timing: launch cycles, sales capacity, and registration/sponsorship deadlines.
- Geography/logistics: travel and operational load.
- Cost/effort: likely spend and team bandwidth.
- Evidence confidence: source freshness and quality.

Assign one recommendation tier:

- `Must attend`: high buyer density, clear GTM fit, actionable
  sponsorship/speaking path, and workable timing.
- `Sponsor selectively`: strong audience, but value depends on package,
  speaking slot, or meeting plan.
- `Attend only`: useful networking or learning, but sponsorship likely weak or
  overpriced.
- `Monitor`: plausible future fit but missing evidence, wrong timing, or low
  confidence.
- `Skip`: poor ICP fit, weak evidence, wrong region/timing, or vanity
  visibility.

Explain the tier in plain English. The justification matters more than the
numeric score.

## Per-Conference Fields

For each shortlisted conference, include:

- Name.
- Official URL.
- Dates.
- Location or format.
- Registration/attend link.
- Target audience and buyer/persona fit.
- Relevant agenda tracks, themes, sessions, or speaker categories.
- Speaker lineup: table of relevant speakers with researched backgrounds,
  professional email, email confidence, enriched/public background, why they
  matter, and sources.
- Other relevant companies, sponsors, or exhibitors.
- Sponsorship/exhibitor options and direct sponsor link, prospectus link, or
  contact path.
- Public price or sponsorship cost when available.
- Deadlines for registration, sponsorship, CFP, or speaking when available.
- Why this organization should attend.
- Recommended action: attend, sponsor, speak, host side event, book meetings,
  monitor, or skip.
- Risks and unknowns.
- Source links with access date.
- Confidence level.

## Output Artifact

Create a single dated Markdown conference research file in the company wiki. If
the wiki is unavailable, write the Markdown report as the task result and name
the wiki blocker.

Use this report structure:

1. Executive take: the 2-4 events worth action and the biggest non-obvious call.
2. Recommended shortlist: ranked table with tier, date, location, audience fit,
   recommended action, attend link, sponsor link/contact path, estimated cost
   confidence, and why.
3. Event deep dives: one section per recommended event using the required
   per-conference fields, including the required speaker lineup with researched
   backgrounds and enriched professional emails/background confidence.
4. Sponsorship strategy: where to spend, where to avoid booths, and how to use
   speaking, side events, and meeting setting.
5. 30/60/90-day action plan: outreach, sponsorship deadlines, speaker
   submissions, meeting campaigns, and owner suggestions. Use researched
   speakers as named meeting or outreach targets.
6. Skips and watchlist: credible events that do not justify action now, with the
   reason and trigger for reconsidering.
7. Sources and access dates.

Return `succeeded` only when public conference discovery, ranked fit scoring,
mandatory public speaker research, and the report artifact are complete. Return
`partial` when Clay enrichment, wiki write-back, or another non-public-source
layer is blocked, and name the exact blocker.
