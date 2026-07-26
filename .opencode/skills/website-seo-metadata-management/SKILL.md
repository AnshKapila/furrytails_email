---
name: website-seo-metadata-management
description: >
  Use this skill when adding or updating structured data for search rich
  results — for example "add schema markup", "generate JSON-LD", "why are rich
  results missing", or after a page is added, rewritten, or redesigned. Use
  `website-sitemap-management` for route discovery and
  `website-aeo-metadata-management` for llms.txt.
mode: both
---

# Structured Data Suggester

This skill helps you recommend and generate JSON-LD structured data for any webpage, driven by the **page's type and content** rather than the business behind it. It covers all 27 structured data types that Google Search currently supports.

## Core idea

Google cares about what a given *page* is. A page that shows a single recipe needs `Recipe`. A page that lists many recipes needs `ItemList` + `Recipe`. A page describing one job opening needs `JobPosting`. Once you know the page type, the schema follows.

This skill is organized around that idea. When a user asks for structured data or wants to improve the website's SEO or does major changes to the website, your job is to:

1. Predict the page type (read their HTML, or read the URL if offered) and understand the page's content
2. Look up the recommended schemas for that page type
3. Check for restrictions
4. Generate filled-in JSON-LD using their actual content

## Workflow

### Step 1 — Identify the page type based on the page's content

### Step 2 — Map the page type to schemas

If `references/page-types.md` is available to you, open it and locate the matching page type. That file lists:

- The **primary schema** the page should use
- **Supporting schemas** that strengthen the markup
- **Universal schemas** to add alongside (Organization, Breadcrumb, etc.)
- Any **restrictions or caveats** for that page type

Otherwise, use the quick page-type index in this file and your schema.org knowledge to determine the appropriate schemas.

Most pages need more than one schema. A recipe page, for example, usually wants `Recipe` + `BreadcrumbList` + `VideoObject` (if there's a video) + site-wide `Organization`.

If `references/implementation-notes.md` is available, read it for the full list of caveats.

### Step 3 — Generate the JSON-LD

If `references/schema-templates.md` is available to you, open it and find the template(s) you need. Otherwise, generate the JSON-LD directly using your schema.org knowledge. Fill in values from the user's content. Always:

- Wrap the output in `<script type="application/ld+json"> ... </script>`
- Use absolute URLs, not relative (`https://example.com/page` not `/page`)
- Use ISO 8601 dates (`2024-03-10` or `2024-03-10T08:00:00+02:00`)
- Include all **required** properties Google demands for rich results (the templates are already structured around these)
- Include the most valuable **recommended** properties too — ratings, images, authors — since these meaningfully improve how the result looks in search

### Step 4 — Recommend universal additions

Every site benefits from a small set of site-wide schemas. Unless they have already been added, mention:

- **Organization** on the homepage/about page — the brand's identity: logo, name, sameAs (social profiles), contact
- **BreadcrumbList** on every non-homepage that sits in a hierarchy — significantly helps Google render the path in search
- **WebSite with SearchAction** on the homepage — can unlock the sitelinks searchbox

## Quick page-type index

This is a fast lookup to orient yourself; for details and rationale go to `references/page-types.md`.

| Page type | Primary schema(s) |
|---|---|
| Homepage | Organization, WebSite (+ SearchAction) |
| About page | Organization or Person |
| Contact / location page | LocalBusiness, Organization |
| Blog post / long-form article | Article / BlogPosting |
| News article | NewsArticle (+ Speakable, Paywall if applicable) |
| Author / team bio page | ProfilePage + Person |
| Product detail page | Product (+ AggregateRating, Review, Offer) |
| Product category / listing page | BreadcrumbList + ItemList of Products |
| Product review / comparison page | Review + Product (Product Snippets mode) |
| Recipe page | Recipe |
| Recipe collection / index | ItemList + Recipe |
| Event detail page | Event |
| Event calendar / listing | ItemList + Event |
| Video page | VideoObject (+ Clip for chapters) |
| Course detail page | Course |
| Course catalog | ItemList + Course |
| Dataset / research data page | Dataset |
| Job posting page | JobPosting |
| Employer / company review page | EmployerAggregateRating |
| Forum thread page | DiscussionForumPosting |
| Q&A thread page | QAPage |
| User profile / creator page | ProfilePage + Person |
| FAQ page | FAQPage (gov/health only for rich results) |
| Gallery / single image page | ImageObject |
| Software / app listing page | SoftwareApplication |
| Movie detail page | Movie |
| Movie list / "best of" page | ItemList + Movie |
| Vacation rental listing | VacationRental (partnership required) |
| Any hierarchical page | + BreadcrumbList |
| Paywalled content | + hasPart with isAccessibleForFree:false |

If the page doesn't fit any of these cleanly, see the "Choosing between similar types" section in `references/page-types.md`.

## Choosing between overlapping types

A few cases come up often and trip people up:

- **Article vs BlogPosting vs NewsArticle** — use `NewsArticle` for time-sensitive news, `BlogPosting` for personal/informal blog content, `Article` for evergreen editorial pieces. When in doubt, `Article` is always safe.
- **Product Snippets vs Merchant Listings** — if the user can buy the item on this exact page, it's a Merchant Listing (price, availability, shipping required). If the page is reviewing or discussing the product without a buy button, it's a Product Snippet (ratings optional but valuable, fewer required fields).
- **QAPage vs FAQPage vs DiscussionForumPosting** — `FAQPage` is for authoritative Q&A written *by the site* (e.g., a company's FAQ). `QAPage` is for a community question with user-submitted answers (Stack Overflow style). `DiscussionForumPosting` is for forum-style threads with nested comments (Reddit style).
- **Course vs Article tutorial** — use `Course` when the content is a structured educational offering with a provider, enrollment, or syllabus. Use `Article` for one-off tutorial posts.
- **Recipe vs Article about food** — `Recipe` requires ingredients and steps. An article discussing food without a followable recipe should be `Article`, not `Recipe`.
