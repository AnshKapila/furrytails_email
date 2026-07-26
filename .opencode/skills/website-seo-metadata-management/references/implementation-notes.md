# Implementation Notes

Practical guidance for implementing structured data correctly: format choice, Google-specific restrictions, common mistakes, validation, and maintenance.

## Format

Google supports three formats: **JSON-LD**, **Microdata**, and **RDFa**. Always recommend JSON-LD unless the user has a specific reason not to:

- It lives in one block in `<head>` rather than scattered across HTML attributes
- Keeps content separated from markup, so redesigns don't break structured data
- Easier to generate, read, debug, and maintain
- Supported equally well by Google

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "...",
  ...
}
</script>
```

Place the script in `<head>`; `<body>` also works but `<head>` is cleaner. Multiple `<script>` blocks per page are fine.

## Deprecated types — do not recommend these

Google has been actively pruning low-usage structured data types. As of April 2026, the following **no longer produce rich results** and should not be recommended for new implementations:

| Type | Status | What to use instead |
|---|---|---|
| `HowTo` | Deprecated August 2023 on mobile, later on desktop too | `Recipe` for cooking, `Article` for general tutorials |
| `Course` (info rich result) | Course Info rich result deprecated June 2025 | `Course` markup still works for carousels and semantic value, but the standalone "info" rich result is gone |
| `EstimatedSalary` | Deprecated June 2025 | Use `JobPosting.baseSalary` inside regular JobPosting markup |
| `LearningVideo` | Deprecated June 2025 | Use standard `VideoObject` |
| `SpecialAnnouncement` | Deprecated July 2025 | No direct replacement — put urgent announcements on the page as prominent content |
| `VehicleListing` | Deprecated June 2025 | Use general `Product` markup if selling vehicles |
| `ClaimReview` | Deprecated June 2025 | No direct replacement for general sites; limited tooling remains for registered fact-checkers |
| `PracticeProblem` | Deprecated January 2026 | Use `Quiz` for flashcard-style study material |

Google has also confirmed:
- **`Dataset`** markup works only in Dataset Search (https://datasetsearch.research.google.com), not regular Google Search. Still recommend it for research and data-publishing pages, but set expectations correctly — no rich results in main Search.

Existing markup of these deprecated types doesn't hurt rankings; Google just ignores it. There's no rush to remove, but don't invest in adding it.

This landscape evolves. When in doubt, check Google's live documentation at https://developers.google.com/search/docs/appearance/structured-data/search-gallery before promising rich results for any feature.

## Restrictions and gotchas by type

### FAQPage

- Rich results **gated to well-known government and authoritative health sites only** as of August 2023.
- Markup is still valid, still helps Google understand the page, but no rich result appears for most sites.
- Don't let users spend major effort here expecting stars/expanders unless they run a qualifying site.

### Dataset

- Only serves **Dataset Search** (a specialized Google product), not regular Google Search.
- Still worth implementing for research publishers, government data portals, scientific institutions — it makes datasets discoverable to researchers.
- Don't promise regular search rich results from Dataset markup.

### HowTo

- **Fully deprecated** as of 2023–2024. Don't recommend it at all for new sites.
- For cooking content use `Recipe`. For other instructional content use `Article`.

### Product

- **Merchant Listings** (purchase pages) unlock shipping, returns, and price-drop features but require `price`, `priceCurrency`, `availability`, `itemCondition`, and strongly benefit from `shippingDetails` and `hasMerchantReturnPolicy`.
- **Product Snippets** (editorial/review pages where the item can't be bought here) need only `review` or `aggregateRating`. Don't add `Offer` if you're not the seller — it misleads Google.
- Product identifiers (`sku`, `gtin`, `mpn`) significantly improve merchant listing eligibility. Include whichever the user has.
- Self-serving reviews are filtered: a company can't publish its own "we give ourselves 5 stars" review and expect it to show.

### Review / AggregateRating

- Standalone Review pages are no longer a distinct rich result type. Reviews must be embedded inside the thing being reviewed (`Product`, `Movie`, `Book`, `LocalBusiness`, etc.).
- Ratings must be for a specific item, not the site as a whole.
- Aggregate rating requires `ratingValue` + `reviewCount` or `ratingCount`. Leaving these out silently kills the rich result.

### VacationRental

- Requires direct partnership with Google: a Technical Account Manager and Hotel Center access. Not self-serve.
- Minimum 8 images.
- Markup without partnership produces no rich result.

### Speakable

- Only works for sites enrolled in Google News and primarily in the US.
- Useful only for a narrow slice of publishers. Skip for most users.

### Event

- `eventStatus` must be kept current — outdated markup (events that are marked `EventScheduled` but already happened) gets filtered.
- Recurring events: there is no good recurrence model Google indexes. Each occurrence must be its own `Event` with its own `startDate`.
- For cancelled/rescheduled events, update `eventStatus` to `EventCancelled` or `EventRescheduled` rather than deleting the page.

### JobPosting

- `validThrough` is how Google knows the job is still open. Jobs past `validThrough` are dropped from the Jobs experience.
- Don't mark expired jobs as still valid; Google can cross-check with the page and penalize.
- For remote jobs, include `jobLocationType: "TELECOMMUTE"` AND `applicantLocationRequirements`. Omitting these is a common mistake.

### Course

- Google now requires `hasCourseInstance` with at least one `CourseInstance` for course rich results eligibility.
- `courseMode`, `courseWorkload`, and `instructor` inside the CourseInstance all meaningfully improve eligibility.

### VideoObject

- `thumbnailUrl` and `uploadDate` are often missed — they're required.
- For video-detail pages, make sure the video URL (`contentUrl` or `embedUrl`) is accessible to Googlebot; if the CDN blocks crawlers the video won't be indexed.
- For livestreams, `BroadcastEvent` with `isLiveBroadcast: true` is what triggers the LIVE badge.

### Organization

- `logo` should be a square PNG/SVG on transparent or white background, minimum 112x112px. A wide rectangular logo won't produce the desired Knowledge Panel display.
- `sameAs` is one of the highest-leverage fields. Point to every authoritative profile: official social accounts, Wikipedia, Wikidata, Crunchbase.

### BreadcrumbList

- Use `position` starting at 1, not 0.
- The last item can omit `item` (URL) — it's the current page.
- Multiple breadcrumb trails on one page are valid; emit them as separate script blocks or as an array of BreadcrumbList objects.

## Common mistakes

1. **Marking up invisible content.** Google requires that structured data describe content that's actually visible on the page. Don't put fake reviews, fake FAQs, or phantom ratings in JSON-LD that aren't shown to users.

2. **Stale `dateModified`.** Google watches for sites that update `dateModified` without actually changing content. Only update it when there's a real edit.

3. **Missing images or low-resolution images.** Google recommends multiple aspect ratios (16:9, 4:3, 1:1) at high resolution. One small image often blocks rich result eligibility.

4. **Wrong date format.** Dates must be ISO 8601: `2024-03-10` or `2024-03-10T08:00:00+02:00`. Human-friendly formats ("March 10, 2024") are invalid.

5. **Wrong duration format.** Durations must be ISO 8601: `PT1M30S` (1 min 30 sec), `PT2H` (2 hours), `PT10M` (10 minutes). Not "1:30" or "1 min 30 sec".

6. **Using relative URLs.** All URLs in JSON-LD must be absolute (`https://example.com/page`), not relative (`/page`).

7. **Self-serving reviews.** Sites giving themselves 5 stars via markup get filtered. Reviews should come from genuine third parties.

8. **Currency mismatches.** `priceCurrency` is ISO 4217 (USD, EUR, GBP) — three-letter codes only, not symbols.

9. **Price as string with symbol.** `"price": "$10.99"` is invalid. Use `"price": "10.99"` and set `priceCurrency` separately.

10. **Using `@type` without `@context`.** The `@context` field must be present at the top level: `"@context": "https://schema.org"`.

## Validation workflow

Always walk the user through validation:

1. **Rich Results Test** (https://search.google.com/test/rich-results) — tells them *which* rich results their markup qualifies for, with Google's specific view. Primary tool.

2. **Schema Markup Validator** (https://validator.schema.org) — tells them whether the schema is structurally valid per schema.org, which is broader than Google's view. Useful for catching typos and invalid property names.

3. **Search Console → Enhancements** — after Google crawls the live page, Search Console surfaces which structured data was detected and any errors. This is the source of truth.

Order: validate with the Rich Results Test before deploying, then monitor Search Console after deploying.

## Maintenance

Structured data isn't set-and-forget:

- **Events:** update `eventStatus`, remove or archive past events.
- **Job postings:** ensure `validThrough` is accurate; remove filled roles.
- **Products:** keep price and availability accurate (Google cross-checks against the page).
- **Articles:** `dateModified` should reflect real edits only.
- **Reviews:** add new reviews, don't cap at old ones.

Stale or incorrect markup is worse than no markup — Google can ignore or penalize it.

## Multi-type objects

Sometimes one entity is multiple things. Schema.org supports multi-type declarations via an array:

```json
{ "@type": ["Electrician", "Plumber", "Locksmith"] }
```

```json
{ "@type": ["SoftwareApplication", "MobileApplication", "VideoGame"] }
```

Use this when the single best type doesn't capture the whole picture. Don't overuse — 4+ types usually indicates the markup should be split.

## Images: what Google actually wants

For article, product, and recipe rich results, Google asks for:

- Multiple images per item in different aspect ratios: **16:9, 4:3, 1:1**
- High resolution: at least 1200px on the longest side
- Files Google can crawl (not blocked by robots.txt, not behind login)

Passing an array of URLs for `image` is the standard approach:

```json
"image": [
  "https://example.com/photos/1x1.jpg",
  "https://example.com/photos/4x3.jpg",
  "https://example.com/photos/16x9.jpg"
]
```

## When NOT to add structured data

- **Search results pages of the site itself** — Google generally doesn't want to index those as rich-result eligible.
- **Pages that don't actually display the marked-up content** — markup must match visible content.
- **Thin or low-quality pages** — structured data doesn't rescue bad content.
- **Duplicated content** — don't emit the same structured data from canonical and non-canonical versions.

## Site-wide vs page-specific

Most structured data is **page-specific** — the markup describes that particular page's content. Exceptions that typically appear site-wide:

- **Organization** on the homepage (or one canonical page like /about)
- **WebSite with SearchAction** on the homepage
- **BreadcrumbList** on every non-homepage in a hierarchy

Don't paste Organization markup on every page of the site — duplicate Organization markup is a common and unhelpful pattern.
