---
name: website-structure-planning
description: "Use this skill when planning the structure of a generated website — choosing the conversion strategy, deciding which pages the site needs, and ordering the sections on each page. Covers business-type defaults across restaurants, software, agencies, fitness, real estate, hotels, law, beauty and wellness, events, newsletters, portfolios, and more, with fallback logic for unlisted categories, plus the rule that user-named pages or sections always take priority over category defaults. Triggers any time you build or restructure the site's page list or section flow."
mode: both
---

Build the website structure from conversion intent, not from a fixed component checklist.

## Precedence

User requirements override these defaults. If the user explicitly names a page, section, content item, route, CTA, or list item, include it unless it conflicts with safety, accessibility, factuality, or render correctness.

## Conversion Strategy

| Category | Strategy | Primary action |
| --- | --- | --- |
| Architecture & Interior Studios | Consideration-Decision + Authority/Social proof | Consultation request |
| Bakeries | AIDA + Fogg | Order or visit |
| Beauty & Wellness Outlets | AIDA + Fogg | Appointment booking |
| Consumer Brands & Products | AIDA + Social proof | Purchase or learn more |
| Digital Creative Agencies | Consideration-Decision + Authority/Social proof | Project inquiry |
| Event Planning Services | Consideration-Decision + AIDCAS | Consultation request |
| Events | AIDA + Urgency | Ticket purchase |
| Fitness Programs & Studios | BAB + AIDCAS | Trial or membership signup |
| Home Services | PAS + AIDCAS | Quote request |
| Hotels & Short Stays | AIDA + Fogg + Urgency | Booking |
| Law Services | Consideration-Decision + Authority/Social proof | Free consultation |
| Newsletter | Value-first + Low friction | Email subscription |
| Personal & Portfolio Websites | Authority/Social proof + Story | Contact or hire |
| Real Estate Agency | Consideration-Decision + Authority/Social proof | Property inquiry |
| Restaurants & Bars | AIDA + Fogg | Reservation or visit |
| Software Websites & Apps | PAS + AIDCAS + Social proof | Signup or demo request |

Fallback: urgent/problem-now -> PAS; transformation -> BAB; high-trust/high-stakes -> Consideration-Decision; simple low-friction consumer choice -> AIDA + Fogg; product-led self-serve software -> PAS + Social proof.

## Pages

| Category | Default pages |
| --- | --- |
| Architecture & Interior Studios | Home, Portfolio, Services, About, Contact |
| Bakeries | Home, Menu, About, Contact |
| Beauty & Wellness Outlets | Home, Services, Gallery, About, Contact |
| Consumer Brands & Products | Home, Products, About, Contact |
| Digital Creative Agencies | Home, Work, Services, About, Contact |
| Event Planning Services | Home, Services, Portfolio, About, Contact |
| Events | Home, Lineup, Schedule, Tickets, About |
| Fitness Programs & Studios | Home, Programs, Schedule, About, Contact |
| Home Services | Home, Services, ServiceAreas, About, Contact |
| Hotels & Short Stays | Home, Rooms, Amenities, About, Contact |
| Law Services | Home, PracticeAreas, CaseResults, About, Contact |
| Newsletter | Home |
| Personal & Portfolio Websites | Home, Work, About, Contact |
| Real Estate Agency | Home, Listings, Services, About, Contact |
| Restaurants & Bars | Home, Menu, About, Contact |
| Software Websites & Apps | Home, Features, Pricing, About, Contact |

Page rules:

- Include Home, About, and Contact at minimum except for single-page newsletter sites.
- Add Services, Products, Menu, Portfolio/Work, Pricing, Features, Schedule, Gallery, FAQ, Locations/ServiceAreas, Testimonials, or CaseStudies only when they serve distinct user intent.
- Legal pages belong in the footer, not the main navigation.
- Default page counts: simple local or solo operator 3-5; multi-service, premium studio, or agency 5-7; software, marketplace, or larger high-trust business 5-8.

Functional page selection:

- Treat each page as a routable user workflow with a unique PascalCase page name and unique path; Home uses `/`.
- Add pages by behavior: Services for custom work, Products/Menu for browsable goods, Features/Pricing for software, Schedule/Tickets/Booking for time-based conversion, Portfolio/Work/Gallery/Listings for proof or inventory, and Locations/ServiceAreas when geography affects conversion.
- Keep main navigation to primary visitor workflows; footer or hide utility routes such as legal, admin, support, and policy pages.

## Homepage Narrative

The homepage is the main story surface. Do not treat a category default as an exact homepage section list. Compose the homepage from narrative beats, splitting or merging beats into sections based on the offer.

Required beats:

1. Orient the visitor: what this is, who it is for, and the primary action.
2. Dramatize the offer: problem, desire, transformation, atmosphere, occasion, or opportunity.
3. Reveal the offer: product, service, menu, rooms, listings, features, programs, or work.
4. Make the result imaginable: scenarios, use cases, transformations, day-in-the-life moments, comparisons, editorial story, process detail, proof narrative, gallery, or examples.
5. Explain how it works: booking, buying, onboarding, visiting, delivery, project process, schedule, or workflow.
6. Prove credibility with verified proof only.
7. Handle objections: pricing, logistics, fit, safety, guarantees, policies, availability, FAQ, or risk reversal.
8. Close with the strongest action path.

Homepage depth targets:

- Simple local business or solo operator: 7-9 sections.
- Portfolio or personal website: 7-10 sections.
- Standard service, premium studio, agency, real estate, hospitality, law, or other high-trust business: 9-12 sections.
- SaaS, software, AI, developer tools, marketplaces, product-led tech, and larger high-consideration websites: 12-16 sections.
- Newsletter: 6-8 focused sections.

Software/tech homepage minimum: include at least one section for each of product walkthrough, use cases or workflows, integrations/ecosystem, security or reliability, pricing or packaging, and proof or outcomes. If verified proof is unavailable, use neutral product proof such as sample workflows, metrics explained as product capabilities, implementation path, or comparison against the old way.

Imagination sections:

- Add at least two when the offer benefits from being pictured, compared, experienced, or trusted before action. For SaaS/software/tech, add at least three.
- Good examples: UseCases, Scenarios, BeforeAfter, DayInTheLife, ProductWalkthrough, ProjectStory, MenuStory, NeighborhoodGuide, GuestExperience, FounderPointOfView, ComparisonBlock, OutcomeHighlights, ProcessDeepDive.
- Skip them only when the requirements are extremely narrow or intentionally tiny.

Anti-bloat:

- Every homepage section must reveal the offer, make the result easier to imagine, reduce a real objection, deepen trust, or drive conversion.
- Merge sections with the same job.
- Avoid repeating heavy CTA, proof, FAQ, team, or gallery sections across pages; use previews when needed.
- Omit proof sections when no real proof is available.

## Non-Home Page Templates

Adapt these templates to the business and user requirements:

- Services: Hero, ServicesList, ServiceDetails, ProcessSteps or HowItWorks, PricingApproach or PricingTable, FAQ, CTA.
- Products/Menu/Catalog: Hero, Categories, ProductGrid or MenuItems, Filters or CollectionGroups, TrustSignals, CTA.
- Portfolio/Work/Listings/Gallery: Hero, GridSection, Filters or Categories, FeaturedCaseStudy or HighlightedItems, CTA.
- About: Hero, StorySection, Values or Philosophy, Team or FounderProfile, CredibilityBlock, CTA.
- Contact: Hero, ContactForm or BookingForm, ContactInfo, LocationMap or ServiceAreaSummary, Hours or Availability, FAQ or NextSteps.
- Pricing: Hero, PricingTable, PlanComparison, FAQ, RiskReversal, CTA.
- Features: Hero, FeaturesList, UseCases, Integrations, FAQ, CTA.
- Schedule/Events/Booking: Hero, ScheduleList or BookingOptions, AvailabilityInfo, Pricing or TicketTiers, FAQ, CTA.

Modifiers:

- High-trust or high-stakes: Testimonials, Credentials, Certifications, Awards, CaseStudies, ClientLogos, MediaMentions.
- Visual or aesthetic: Gallery, PortfolioHighlights, BeforeAfter, ImageGrid, StyleCategories.
- Local or location-based: LocationMap, Hours, Directions, ServiceAreas, NeighborhoodGuide, ParkingInfo.
- Booking-led: BookingCTA, AvailabilityInfo, PricingAnchors, FAQ, CancellationPolicy.
- Product-led: FeaturedProducts, ProductCategories, ReviewsPreview, ShippingInfo, ReturnsPolicy.
- Software or digital product: ProblemSolution, FeaturesOverview, UseCases, IntegrationsList, PricingPreview, SecurityTrust, SignupCTA.
- Transformation offer: TransformationProof, BeforeAfter, OutcomeHighlights, ExpertProfile, Testimonials, FAQ.

Non-home section counts:

- Simple pages: 4-6 sections.
- Standard service or evaluation pages: 5-8 sections.
- Specialized deep-dive pages: 4-7 sections.

## Ordering

Unless user requirements say otherwise, order sections by conversion priority:

1. Clarify the offer.
2. Show what is sold.
3. Explain how it works.
4. Build trust.
5. Handle objections.
6. Close with action.

## Social Proof And Compliance

- Populate ClientLogos, TrustBadges, SocialProof, CredentialsBar, Investors, Sponsors, and Testimonials only with names, logos, quotes, certifications, or affiliations present in user requirements or extracted assets.
- If no real proof exists, omit the section or use neutral trust language such as years in business, satisfaction guarantees, secure checkout, transparent pricing, or professional memberships.
- Never fabricate third-party brand names, endorsements, investors, sponsors, certifications, or quotes.
- Name compliance certifications such as SOC 2, HIPAA, GDPR, ISO 27001, PCI DSS, FedRAMP, or CCPA only when explicitly stated in user requirements or verified source text.
