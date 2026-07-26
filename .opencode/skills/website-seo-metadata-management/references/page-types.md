# Page Types → Structured Data

Detailed mapping of page types to recommended schema.org markup. Each entry explains which schemas to use, why, and what edge cases to watch for.

Read this when you need full rationale. For just the quick index, see SKILL.md.

## Table of contents

- [Homepage](#homepage)
- [About page](#about-page)
- [Contact / location page](#contact--location-page)
- [Blog post / long-form article](#blog-post--long-form-article)
- [News article](#news-article)
- [Author / team bio page](#author--team-bio-page)
- [Product detail page](#product-detail-page)
- [Product category / listing page](#product-category--listing-page)
- [Product review / comparison page](#product-review--comparison-page)
- [Recipe page](#recipe-page)
- [Recipe collection / index page](#recipe-collection--index-page)
- [Event detail page](#event-detail-page)
- [Event calendar / listing page](#event-calendar--listing-page)
- [Video page](#video-page)
- [Course detail page](#course-detail-page)
- [Course catalog page](#course-catalog-page)
- [Quiz / flashcard page](#quiz--flashcard-page)
- [Math solver tool page](#math-solver-tool-page)
- [Dataset / research data page](#dataset--research-data-page)
- [Job posting page](#job-posting-page)
- [Employer / company review page](#employer--company-review-page)
- [Forum thread page](#forum-thread-page)
- [Q&A thread page](#qa-thread-page)
- [User profile / creator page](#user-profile--creator-page)
- [FAQ page](#faq-page)
- [Gallery / single image page](#gallery--single-image-page)
- [Software / app listing page](#software--app-listing-page)
- [Movie detail page](#movie-detail-page)
- [Movie list / carousel page](#movie-list--carousel-page)
- [Vacation rental listing page](#vacation-rental-listing-page)
- [Paywalled / subscription content](#paywalled--subscription-content)
- [Text-to-speech-optimized news page](#text-to-speech-optimized-news-page)
- [Search results / category index pages](#search-results--category-index-pages)
- [Universal additions](#universal-additions)

---

## Homepage

**What it is:** The root page of a site. Identifies the brand/site itself rather than describing one piece of content.

**Primary:** `Organization` (or `Person` for a personal site/portfolio)
**Supporting:** `WebSite` with `potentialAction: SearchAction` to unlock the sitelinks searchbox if the site has internal search

**Why:** The homepage is where Google picks up your brand identity — logo, official name, social profiles. Getting this right affects how your brand appears across Knowledge Panels and other rich features.

**Notes:**
- Use a specific `Organization` subtype when applicable: `OnlineStore` for ecommerce, `NewsMediaOrganization` for publishers, `NGO` for nonprofits, `GovernmentOrganization` for government.
- `logo` should be a square image, minimum 112x112px, on a transparent or white background.
- `sameAs` is an array of URLs pointing to the brand's official profiles elsewhere (Facebook, LinkedIn, Wikipedia, etc.). This is one of the highest-leverage fields for entity disambiguation.

---

## About page

**What it is:** The page describing the people or organization behind the site.

**Primary:** `Organization` for companies/groups, `Person` for solo creators/freelancers
**Supporting:** `ProfilePage` wrapping the Person for single-person sites; `ContactPoint` nested inside Organization

**Why:** Often this is where Google looks to confirm entity info it didn't find on the homepage. For personal brands, `Person` on the about page (plus `sameAs` links) establishes the entity.

---

## Contact / location page

**What it is:** A page showing address, phone, hours for a physical presence — even if the main business is online.

**Primary:** `LocalBusiness` (or one of its many subtypes: `Restaurant`, `Store`, `MedicalClinic`, `Plumber`, `LegalService`, etc.)
**Supporting:** `PostalAddress`, `GeoCoordinates`, `OpeningHoursSpecification`, and `Organization` for the parent brand

**Why:** LocalBusiness unlocks Google Business Profile-adjacent features and helps "near me" searches.

**Notes:**
- A business with multiple services can declare multiple types: `"@type": ["Electrician", "Plumber"]`.
- A chain with many locations should have one `LocalBusiness` markup per location page, plus `Organization` for the parent brand on the homepage.
- Include `geo` (latitude/longitude) whenever possible — Google matches this against Maps.

---

## Blog post / long-form article

**What it is:** A single editorial piece — tutorial, opinion, guide, long-form post.

**Primary:** `BlogPosting` for personal/informal blogs, `Article` for more formal editorial content
**Supporting:** `BreadcrumbList`, `Person` (author), `Organization` (publisher), `ImageObject` (hero image), `VideoObject` (if there's embedded video)

**Why:** Article markup contributes to Top Stories eligibility and strengthens how Google understands the authorship and freshness of the page.

**Notes:**
- Always include `datePublished` and `dateModified`. Stale `dateModified` fakery is a known pattern Google watches for — only update it for real changes.
- Author should be a `Person` with a `url` pointing at the author's bio page. The bio page should in turn have `ProfilePage` markup.
- `headline` should be ≤110 characters.
- Include at least one high-resolution image; 16:9, 4:3, and 1:1 aspect ratios as separate URLs is Google's recommendation.

---

## News article

**What it is:** Time-sensitive journalism — breaking news, scheduled reporting, press releases.

**Primary:** `NewsArticle`
**Supporting:** Same as blog post, plus potentially `Speakable` and paywall markup

**Why:** `NewsArticle` specifically signals Top Stories and Google News eligibility.

**Notes:**
- If sections of the article are behind a paywall, add `isAccessibleForFree: false` on the NewsArticle and a `hasPart` array with `WebPageElement` entries pointing to the paywalled CSS selectors. Without this, Google may treat the paywall as cloaking.
- Use `Speakable` only if you're enrolled in Google News and your main markets include the US.

---

## Author / team bio page

**What it is:** A page dedicated to one person — their bio, credentials, articles, social links.

**Primary:** `ProfilePage` with `mainEntity` of type `Person`
**Supporting:** `sameAs` array on the Person pointing to their profiles on Twitter/LinkedIn/GitHub/etc.; `interactionStatistic` for follower counts if publicly visible

**Why:** Profile pages are now a distinct rich result type. For creator-driven sites, this also anchors author authority for E-E-A-T (Experience, Expertise, Authoritativeness, Trust) signals.

---

## Product detail page

**What it is:** A page showing one specific product (or one product with multiple variants/sizes) where price and availability are displayed.

**Primary:** `Product`
**Supporting:** `Offer` (or `AggregateOffer` for a range), `AggregateRating`, `Review`, `Brand`, `BreadcrumbList`

**Two modes — this matters:**
- **Merchant Listing** (user can buy here): MUST include `price`, `priceCurrency`, `availability`, `itemCondition`. STRONGLY recommended: `shippingDetails`, `hasMerchantReturnPolicy`. Eligible for richer features like shipping/returns annotations and price drop callouts.
- **Product Snippet** (page reviews/discusses but doesn't sell): `Product` with `AggregateRating` and/or `Review` is enough. Don't add `Offer` if you're not the seller.

**Notes:**
- Use `sku`, `gtin`, or `mpn` when available — product identifiers meaningfully improve merchant listing eligibility.
- Variants (size/color) → put each in its own `Offer` inside an `offers` array; give each a distinct `url` or fragment.
- Pros/cons → schema has `positiveNotes` and `negativeNotes`.

---

## Product category / listing page

**What it is:** A page showing multiple products (category page, search results, "best X" roundup).

**Primary:** `BreadcrumbList` + `ItemList` containing Product entries (or summary links)
**Supporting:** `CollectionPage` wrapping everything

**Why:** ItemList helps Google render category pages as carousels in certain verticals.

**Notes:**
- Two valid patterns: **summary page** (ItemList entries are just URLs pointing to detail pages) or **all-in-one page** (ItemList entries are full Product objects). Use summary when detail pages exist; use all-in-one when the page itself is the detail.
- Don't mark products as Merchant Listings on a listing page unless each entry is genuinely purchasable there.

---

## Product review / comparison page

**What it is:** A page where the author reviews or compares products they don't sell.

**Primary:** `Review` nested inside `Product` (Product Snippet mode)
**Supporting:** `Person` for the reviewer, `positiveNotes` / `negativeNotes` for pros/cons

**Why:** Review markup unlocks the star rating in search results and signals independent editorial review.

**Notes:**
- Don't mark your own organization's reviews of its own products as `Review` — Google considers this self-serving and may ignore it.
- Each product compared on the page gets its own Product block with its own review.

---

## Recipe page

**What it is:** A page with a single followable recipe: ingredients, steps, cook times.

**Primary:** `Recipe`
**Supporting:** `HowToStep` array inside `recipeInstructions`, `NutritionInformation`, `AggregateRating`, `VideoObject` if there's a video, `BreadcrumbList`

**Why:** Recipes are one of the most feature-rich verticals in Google Search — cooking time callouts, ingredient previews, video previews, ratings all depend on complete Recipe markup.

**Notes:**
- Use ISO 8601 duration format for `prepTime`, `cookTime`, `totalTime`: `PT30M` = 30 minutes, `PT1H30M` = 1 hour 30 minutes.
- `recipeYield` can be a number (servings) or string ("4 servings").
- If the recipe has a video, `VideoObject` should be embedded as a property — not a separate script — so Google links them.

---

## Recipe collection / index page

**What it is:** A page listing many recipes — category ("cookies"), roundup ("30-minute dinners"), or archive.

**Primary:** `ItemList` with each entry either linking to a recipe page (summary form) or containing the full Recipe (all-in-one form)
**Supporting:** `BreadcrumbList`

**Why:** Unlocks Recipe carousels in search.

---

## Event detail page

**What it is:** A page about one specific event at a specific time — concert, workshop, conference session, class, webinar.

**Primary:** `Event`
**Supporting:** `Place` (for in-person) or `VirtualLocation` (for online), `Offer` (tickets), `Person` or `PerformingGroup` (performer), `Organization` (organizer)

**Notes:**
- `eventAttendanceMode` values: `OfflineEventAttendanceMode`, `OnlineEventAttendanceMode`, `MixedEventAttendanceMode`. Set this — Google uses it to filter.
- `eventStatus`: `EventScheduled`, `EventRescheduled`, `EventPostponed`, `EventCancelled`, `EventMovedOnline`. Keep this current — outdated event markup is filtered.
- Recurring events → each occurrence should be its own Event. Schema.org has no good recurrence model that Google indexes.
- For a virtual event, `location` can be a `VirtualLocation` with `url`.

---

## Event calendar / listing page

**What it is:** A page showing multiple upcoming events.

**Primary:** `ItemList` of `Event` entries
**Supporting:** `BreadcrumbList`

---

## Video page

**What it is:** A page where a video is the main content — video player page, tutorial page, embedded interview.

**Primary:** `VideoObject`
**Supporting:** `Clip` array (for chapters/key moments), `SeekToAction` (for deep-linking to timestamps), `BroadcastEvent` (for LIVE badge on livestreams), `Person` or `Organization` for uploader

**Notes:**
- `contentUrl` should be the direct media URL (the .mp4 file). `embedUrl` should be the player URL. Prefer including both.
- `thumbnailUrl` is required. Provide multiple aspect ratios.
- `duration` in ISO 8601: `PT1M33S` = 1 minute 33 seconds.
- For livestreams, add `publication` with `BroadcastEvent` including `isLiveBroadcast: true` and `startDate`/`endDate`.
- `uploadDate` is required.

---

## Course detail page

**What it is:** A page describing one course, class, or training program.

**Primary:** `Course`
**Supporting:** `Organization` (provider), `CourseInstance` (if schedule/format varies), `Offer` (price), `Person` (instructor)

**Important:** The standalone "Course Info" rich result was **deprecated in June 2025**. The `Course` schema still works for the Course list/carousel rich result and still provides semantic value to Google and AI systems, but the dedicated course info panel is gone. Set expectations accordingly.

**Notes:**
- For the course *list* (carousel) rich result, which is still supported, use `hasCourseInstance` with at least one `CourseInstance` including `courseMode` ("Online", "Onsite", "Blended"), `courseWorkload` (ISO 8601 duration), and `instructor`.
- For a single isolated course page with no list context, the markup is still worth adding for entity understanding.

---

## Course catalog page

**What it is:** A page listing multiple courses offered by an institution.

**Primary:** `ItemList` of `Course` entries (minimum 3 for carousel eligibility)
**Supporting:** `BreadcrumbList`

---

## Quiz / flashcard page

**What it is:** A page with educational questions and answers designed for study (flashcards, practice questions).

**Primary:** `Quiz` with `hasPart` array of `Question` entries, each with an `acceptedAnswer`
**Supporting:** Set `eduQuestionType` to `"Flashcard"` for flashcard-style quizzes

**Notes:**
- This is distinct from `QAPage` (community Q&A) and `FAQPage` (authoritative FAQ). Quiz is specifically for study/learning material.

---

## Math solver tool page

**What it is:** A page that accepts math input and returns a solution — an interactive solver, not an article explaining math.

**Primary:** `MathSolver` with `potentialAction: SolveMathAction`
**Supporting:** List supported `eduQuestionType` values (Polynomial, Arithmetic, Algebra, etc.)

---

## Dataset / research data page

**What it is:** A page documenting a dataset — describes the data, its license, how to download it.

**Primary:** `Dataset`
**Supporting:** `DataCatalog` (if part of a larger catalog), `DataDownload` entries inside `distribution` for each file format, `Organization` (creator)

**Important:** As of November 2025, Dataset structured data only surfaces in **Google Dataset Search** (a specialized product), not general Google Search. Still worth implementing for research publishers, government data portals, and scientific institutions — it makes data discoverable to researchers. But don't promise general search rich results.

**Notes:**
- `license` is a URL to the license text (prefer Creative Commons, Open Data Commons, etc.).
- `temporalCoverage` uses ISO 8601 intervals: `"1950-01-01/2013-12-18"`.
- `spatialCoverage` can be a `Place` with `geo`.
- For large datasets with subsets, use `hasPart` with nested Dataset entries.

---

## Job posting page

**What it is:** A page listing one specific open job.

**Primary:** `JobPosting`
**Supporting:** `Organization` (hiringOrganization), `Place` (jobLocation), `MonetaryAmount` (baseSalary), `PostalAddress`

**Why:** Eligibility for the Jobs experience in Google Search.

**Notes:**
- `datePosted` and `validThrough` are both important — expired jobs get deindexed if `validThrough` is past.
- `employmentType`: FULL_TIME, PART_TIME, CONTRACTOR, TEMPORARY, INTERN, VOLUNTEER, PER_DIEM, OTHER.
- For remote jobs, add `jobLocationType: "TELECOMMUTE"` and `applicantLocationRequirements`.
- Salary in `baseSalary.value.unitText`: "HOUR", "DAY", "WEEK", "MONTH", "YEAR".

---

## Employer / company review page

**What it is:** A page showing aggregate employee ratings of a company (think Glassdoor-style pages).

**Primary:** `EmployerAggregateRating` wrapped around an `Organization` as `itemReviewed`
**Supporting:** Individual `Review` entries if displayed

**Notes:**
- `ratingValue`, `bestRating`, `worstRating`, `ratingCount` are all important.
- This is specifically for *employer* ratings by employees, not customer ratings.

---

## Forum thread page

**What it is:** A page showing one forum post with nested comments/replies (Reddit-style, traditional phpBB/Discourse threads).

**Primary:** `DiscussionForumPosting`
**Supporting:** `Comment` array for replies (nested `Comment` for nested replies), `Person` (author), `InteractionCounter` (likes, views)

**Why:** New eligibility for the "Discussions and forums" rich result.

**Notes:**
- This is distinct from `QAPage`. Use DiscussionForumPosting when the primary content is an open-ended post or discussion starter, not a specific question with answers.
- `interactionStatistic` with `InteractionCounter` lets you surface like/upvote counts.

---

## Q&A thread page

**What it is:** A page with one question and multiple user-submitted answers (Stack Overflow-style).

**Primary:** `QAPage` with `mainEntity` of type `Question`
**Supporting:** `acceptedAnswer`, `suggestedAnswer` (array), `Person` for question and answer authors, `upvoteCount`

**Why:** Eligibility for the Q&A-specific rich result.

**Notes:**
- Distinct from `FAQPage`. QAPage = community Q&A with user answers; FAQPage = authoritative answers written by the site owner.
- Each page should have exactly ONE question as `mainEntity`. Don't put multiple unrelated questions in one QAPage.

---

## User profile / creator page

**What it is:** A page for a single user/creator on a platform — their handle, bio, content, follower count.

**Primary:** `ProfilePage` with `mainEntity` of type `Person`
**Supporting:** `interactionStatistic` (followers, posts), `sameAs` (other profiles), `InteractionCounter`

**Why:** Eligibility for the profile rich result.

---

## FAQ page

**What it is:** A page of frequently asked questions with authoritative answers written by the site owner.

**Primary:** `FAQPage` with `mainEntity` array of `Question` entries, each with `acceptedAnswer`

**MAJOR RESTRICTION — mention this before the user invests effort:**

As of Google's 2023 update, FAQ rich results only appear for well-known authoritative government sites and authoritative health information sites. For everyone else, the markup is valid but won't produce rich results. The markup still helps Google *understand* the page, so it's not useless, but don't promise rich snippets.

**Notes:**
- Questions must be genuine and answers must be the same as what's visible on the page.
- Don't duplicate FAQ markup across multiple pages — each question should live on one canonical page.

---

## Gallery / single image page

**What it is:** A page whose main content is a single image or a collection of images (stock photo page, portfolio piece).

**Primary:** `ImageObject` for each image
**Supporting:** `creator` (Person), `copyrightNotice`, `creditText`, `license`, `acquireLicensePage`

**Why:** Image Metadata markup can surface licensing info and credit in Google Images, protecting creators.

---

## Software / app listing page

**What it is:** A page promoting a piece of software, mobile app, web app, or video game with ratings and download info.

**Primary:** `SoftwareApplication` (or subtypes: `MobileApplication`, `WebApplication`, `VideoGame`)
**Supporting:** `AggregateRating` or `Review`, `Offer` (price, even if $0), `operatingSystem`, `applicationCategory`

**Why:** Unlocks the software app rich result with stars and price.

**Notes:**
- `applicationCategory` values include: `GameApplication`, `BusinessApplication`, `EducationalApplication`, `UtilitiesApplication`, `MultimediaApplication`, `DeveloperApplication`, etc.
- For free apps, still include `offers` with `price: "0"` — don't omit it.
- Can be co-typed: `"@type": ["MobileApplication", "VideoGame"]`.

---

## Movie detail page

**What it is:** A page about a single movie — title, director, cast, ratings.

**Primary:** `Movie`
**Supporting:** `Person` (director, actors), `Review`, `AggregateRating`, `dateCreated` (release date), `ImageObject` (poster)

---

## Movie list / carousel page

**What it is:** A page listing multiple movies — "Best movies of 2024", Oscar nominees, a genre collection.

**Primary:** `ItemList` of `Movie` entries
**Supporting:** `BreadcrumbList`

**Notes:**
- This is one of the original carousel-eligible types. Works in both summary and all-in-one patterns.

---

## Vacation rental listing page

**What it is:** A page for one short-term rental property — pricing, amenities, calendar, reviews.

**Primary:** `VacationRental`
**Supporting:** `Accommodation` (via `containsPlace`), `PostalAddress`, `GeoCoordinates`, `AggregateRating`, `Review`, `amenityFeature` array

**MAJOR RESTRICTION — mention this first:**

Vacation Rental rich results require a direct partnership with Google. You need a Google Technical Account Manager and Hotel Center access. This is not self-serve. The markup on its own does nothing without the partnership. Tell the user plainly if they're not already enrolled.

**Notes:**
- Requires a minimum of 8 images.
- `numberOfRooms`, `numberOfBedrooms`, `numberOfBathroomsTotal`, `floorSize`, `occupancy` are all important.
- `amenityFeature` is an array of `LocationFeatureSpecification` entries with `name` and `value: true/false`.

---

## Paywalled / subscription content

**What it is:** An article (or any content page) where parts of the content are hidden behind a paywall or subscription gate.

**Primary:** Whatever the page type normally is (usually `NewsArticle` or `Article`) PLUS paywall markup: `isAccessibleForFree: false` and a `hasPart` array of `WebPageElement` entries with CSS selectors pointing at the paywalled sections.

**Why:** Without this markup, Google may treat paywalled content as cloaking, which hurts rankings. With it, Google knows to treat the Googlebot's view (full content) differently from the user's view (paywalled).

**Notes:**
- The CSS selectors in `hasPart.cssSelector` must match the actual classes/IDs wrapping the paywalled content.
- `isAccessibleForFree: false` at the top level means the page as a whole is gated.
- You can have multiple `WebPageElement` entries if different parts of the page have different access rules.

---

## Text-to-speech-optimized news page

**What it is:** A news article where specific sections (headline, summary) are suitable for voice assistants to read aloud.

**Primary:** Whatever the page normally is (usually `NewsArticle`) PLUS `Speakable` markup with CSS selectors for the speakable sections.

**RESTRICTION:** Google Assistant reads `Speakable` content only for sites enrolled in Google News, and primarily in the US. Don't recommend this broadly — it's a niche feature for established news publishers.

---

## Search results / category index pages

Search results pages don't map cleanly to a single structured data type. Google generally doesn't want its search results competing with a site's search results. For a category index page that functions more like curation than search, use:

- `CollectionPage` wrapping the page
- `BreadcrumbList` for the hierarchy
- `ItemList` for the items if they form a meaningful ordered/unordered list

Don't add markup to purely dynamic search result pages.

---

## Universal additions

Regardless of what type a page is, consider these:

**Every page in a hierarchy:** `BreadcrumbList`. Multiple breadcrumb trails can be declared as an array if a page has several valid paths (e.g., Books > Sci-Fi > Award Winners AND Literature > Award Winners).

**Every brand's homepage or about page:** `Organization` with `logo`, `name`, `url`, `sameAs`, `contactPoint`.

**Pages with user reviews and ratings of anything purchasable or bookable:** `AggregateRating` nested in the item being reviewed.

**Pages with video embeds:** `VideoObject` for the embedded video.

---

## Choosing between similar types — quick decision rules

- **Article vs BlogPosting vs NewsArticle** — Time-sensitive news → `NewsArticle`. Personal blog / informal → `BlogPosting`. Evergreen editorial / formal → `Article`.
- **Product Snippet vs Merchant Listing** — Can the user buy on this exact page? Yes → Merchant Listing. No → Product Snippet.
- **QAPage vs FAQPage vs DiscussionForumPosting** — Authoritative FAQ by site owner → `FAQPage`. One user-asked question with community answers → `QAPage`. Open discussion/post with comments → `DiscussionForumPosting`.
- **Course vs Article tutorial** — Structured offering with enrollment/syllabus → `Course`. One-off tutorial post → `Article`.
- **Recipe vs Article about food** — Has followable ingredient list AND steps → `Recipe`. Just discussing food without instructions → `Article`.
- **Event vs Article about an event** — The page IS the event listing with date/location/tickets → `Event`. The page is a retrospective/write-up → `Article`.
- **Movie vs Article review of a movie** — Page is the movie's canonical info → `Movie`. Page is one reviewer's opinion piece → `Review` nested in `Movie`.
- **VideoObject vs Article containing a video** — Video is the main content → `VideoObject` as primary. Video is illustrative alongside text → `Article` as primary with embedded `VideoObject`.
