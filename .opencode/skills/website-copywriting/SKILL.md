---
name: website-copywriting
description: "Use this skill when writing or rewriting visible text on a generated website, including conversion copy, hero headlines, about/bio sections, section copy, benefits, proof, FAQs, objection handling, articles, blogs, case studies, legal pages, calls to action, or testimonials. Covers clear value propositions, stronger CTAs, website-type voice variation, content-type-specific tone, human-sounding wording, believable proof, and avoiding generic or fabricated claims. Triggers any time you produce site copy, even when the user says 'fix the wording', 'less generic', 'make it convert', 'make it sound human', or 'sell me better'."
mode: both
---

If the user supplied the exact text to use (e.g. "change the headline to 'Welcome to Acme'"), apply it verbatim and skip the rules below. These rules govern copy you generate, not text the user dictated.

Every other piece of copy must also pass the rules in the `copy-humanization` skill — apply them on top of the rules below.

Use these rules whenever generating or editing visible website copy. The sitemap and section order come from `website-structure-planning`; this skill owns the words inside those sections.

## Choose The Writing Mode First

- **Marketing copy / conversion copy**: Use for home, landing, pricing, services, product, proof, FAQ, and CTA sections. Optimize for clarity, desire, proof, objection handling, and the next action.
- **Editorial/content copy**: Use for blogs, articles, guides, resources, newsletters, and knowledge pages. Optimize for useful explanation, concrete detail, natural rhythm, and trust. Do not force a sales pitch into every paragraph.
- **Case studies**: Write like reported evidence, not like a disguised testimonial. Cover the problem, context, action, result, and constraints using only supplied facts.
- **Legal/formal copy**: Protect. Precision over flow; every sentence should mean exactly one thing. Use plain language where possible, organize by topic or numbered sections, and avoid privacy/legal marketing fluff such as "we're committed to your privacy."

## Website-Type Voice Variation

Infer the voice from the business type, audience, user requirements, brand context, and visual specification. Do not use the same copy texture for every website. Adjust these knobs:

- **Trust level**: High-stakes, regulated, expensive, or professional services need calmer copy, more proof, and less flourish. Casual, low-risk, or lifestyle offers can be warmer and lighter.
- **Audience expertise**: Expert buyers tolerate precise domain language; general consumers need plain language and fewer assumptions.
- **Decision speed**: Urgent or transactional sites should make the next step obvious fast. Considered, high-value purchases should slow down for process, proof, fit, and reassurance.
- **Sensory warmth**: Keep this low for technical, legal, financial, and professional sites. Increase it for food, hospitality, wellness, events, creative work, retail, and spaces people physically experience.
- **Playfulness**: Off by default for serious or high-stakes categories. Allow it when the user asks for wit/fun or when the brand context safely supports it.

Examples:

- **Architecture/interiors**: Refined, spatial, proof-led, and process-aware. Talk about light, materials, constraints, flow, and how decisions feel in a lived space. Avoid jokey copy.
- **Dev tools/software**: Precise, technical, and outcome-led. Use developer language when it clarifies; avoid buzzwords and fake enterprise gravitas.
- **Bakery/restaurant**: Warm, sensory, and concrete. Mention texture, freshness, ritual, service, ordering, reservations, hours, and the reasons someone would visit today.
- **Law/health/finance**: Calm, restrained, and authority-led. Prioritize clarity, credentials, confidentiality, process, and risk reduction. Avoid wit unless explicitly requested, and keep it minimal.

## Wit And Fun

- Use wit only when the user requests it or the business type safely supports it.
- Keep jokes small: a headline twist, a menu or product name, a microcopy moment, or one playful sentence.
- Never let wit obscure the offer, CTA, price, compliance, legal meaning, safety information, or service details.
- Avoid puns for high-stakes services unless the user explicitly asks.

## Core Conversion Principles

- Prefer clarity over cleverness. If a line can be clear or creative, choose clear.
- Translate features into customer benefits: what changes for the visitor, what gets easier, what risk drops, what outcome becomes possible.
- Be specific without fabricating. Concrete nouns, customer situations, and operational details beat broad claims like "streamline," "optimize," "innovative," or "world-class."
- Use customer language over company language. Mirror the audience's likely pains, goals, objections, and buying context.
- Keep one main idea per section. Each section should advance one argument in the page narrative, not repeat the hero in different words.
- Do not repeat the same value proposition across sections unless each repetition serves a distinct job.
- Match copy length to stakes. High-trust or expensive decisions earn more explanation; simple or low-friction actions need less.

## Fact Grounding

- Preserve exact user-provided names, product names, locations, CTAs, prices, testimonials, URLs, and factual claims unless the user asks for a rewrite.
- If a section needs a detail that was not provided, write around it with honest, specific-but-safe language instead of inventing numbers, credentials, clients, awards, locations, dates, guarantees, or outcomes.
- Populate ClientLogos, TrustBadges, SocialProof, "Trusted By", and similar sections only with names and logos provided in the user requirements or extracted assets. If no real social proof data is available, omit the section entirely or use an obviously-placeholder label such as "Your Client Logo Here". Never use real third-party brand names such as "OpenAI", "SpaceX", or "Google" as fabricated social proof.
- **Regulated compliance claims require provenance.** Only include named compliance certifications (SOC 2, HIPAA, GDPR, ISO 27001, PCI DSS, FedRAMP, CCPA) when the exact certification is explicitly stated in the user requirements or extracted source text. If trust or security language is needed without provenance, use neutral alternatives such as "secure workflows," "protected data," or factual operational claims that were supplied.
- If compliance badge images are present from asset extraction but no supporting text confirms the certification, render them as unlabeled trust icons or omit them.

## Section Copy Jobs

- **Hero**: State the core value proposition above the fold. Use an outcome, audience, problem, or differentiator; pair it with a subheadline that adds specificity and a primary CTA.
- **Social proof**: Build trust with supplied logos, metrics, customer names, ratings, testimonials, credentials, or recognizable context. Prefer one verified proof point over a row of generic claims, and never fabricate third-party names or logos.
- **Problem/Pain**: Show the visitor you understand their situation. Name the specific frustration, cost, delay, risk, or missed opportunity without exaggerating.
- **Benefits/Solution**: Use 3-5 benefits, not a feature dump. For each benefit, write a short outcome-led headline plus a sentence explaining how the offer creates that outcome.
- **How It Works/Process**: Reduce perceived complexity. Use 3-4 simple steps with verb-led labels and the result of each step.
- **Objection Handling/FAQ**: Answer real buying questions directly: price, timing, fit, safety, process, support, logistics, cancellation, or what happens next. No preamble.
- **Testimonials**: Make each quote sound like a real person. Use full name plus role, company, or location only when supplied; never invent testimonial identity. Include a concrete detail, specific moment, result, number, or mild imperfection when source facts support it. Never generate vague praise like "Great service! Highly recommend." If no testimonial facts exist, use a proof section without fabricated quotes.
- **About / Bio**: Sell the person or company through operational specifics and earned authority — not through comparison to competitors. Never frame the value as "unlike others" or "compared to typical [role]"; instead, state what this person does, how they do it, and what that means for the client. Ground every claim in a concrete detail: a credential, a workflow step, a tool, a result, or a domain fact only an insider would know. For personal/freelancer About sections, write as the person would confidently describe their own work to a prospective client — direct, specific, and outcome-oriented. Avoid journey narratives ("my journey began…"), vague mission statements, and multi-paragraph buildup before the value lands. Lead with the strongest operational differentiator in the first sentence.
- **Final CTA**: Recap the main value in one line, repeat the primary action, and include only supplied or safe risk reducers such as "free consultation," "no obligation," "cancel anytime," or "reply within one business day."

## Long-Form And Proof Content

- **Articles and blogs**: Lead with the useful point, not a throat-clearing intro. Explain what the reader came to understand, using concrete examples and short sections.
- **Guides and resource pages**: Teach directly. Prefer steps, examples, and tradeoffs over broad claims about importance or transformation.
- **Case studies**: State the customer's situation, the constraint, what changed, and the result. If metrics are missing, describe the qualitative outcome without inventing a number.
- **Content previews**: Summarize the actual article, post, guide, or case study. Do not use generic teaser copy like "discover insights" or "learn more about our approach."
- **Conclusions**: End with a concrete next step, takeaway, or factual close. Avoid generic positive endings like "the future looks bright" or "exciting times lie ahead."

## Headlines And CTAs

- Hero headlines should be 3-8 words when possible. Section headlines should be 4-10 words. Subheadlines should be one short sentence unless the stakes require more context.
- Useful headline patterns: "{Outcome} without {pain}", "The {category} for {audience}", "Turn {input} into {outcome}", "Never {unpleasant event} again", or "The {category} that {differentiator}". Use these as patterns, not fill-in-the-blank templates.
- Avoid headline patterns that feel hollow: "Welcome to...", "Introducing...", "Ready to transform your business?", stacked adjectives, or abstract nouns without stakes.
- CTAs should be verb-first and say what the visitor gets. Prefer "Book a consultation," "Get the estimate," "See available rooms," "Start a free trial," or "Download the guide" over "Submit," "Click here," "Sign up," "Learn more," or generic "Get started."
- Keep CTA urgency proportional to the offer. Use urgency only when the requirement supplies a real deadline, launch, scarcity, or event date.

## Human-Sounding Writing

- Vary sentence length and paragraph rhythm. Avoid a page where every sentence has the same shape.
- Use plain constructions when they are clearer: "is," "are," "has," and "can" are often better than "serves as," "stands as," "boasts," "features," or "represents."
- Avoid fake depth from trailing "-ing" phrases such as "highlighting," "showcasing," "underscoring," "fostering," "reflecting," and "contributing to."
- Avoid formulaic patterns: rule-of-three padding, synonym cycling, false "from X to Y" ranges, "not only...but also," and clipped tailing negations like "no guesswork" tacked onto the end of a sentence.
- Do not use chatbot artifacts in website copy: "Of course," "I hope this helps," "let me know," "here is a...", knowledge-cutoff disclaimers, or praise for the user's question.
- Avoid mechanical styling tells: emojis, excessive boldface, title-case headings for articles/blog posts, and em dash overuse. Prefer commas, periods, parentheses, or shorter sentences.
- After a heading, do not add a one-line warm-up that merely restates the heading. Start with the useful sentence.

## Voice And Readability

- Use simple words, active voice, and short sentences. Use "use" instead of "utilize," "help" instead of "facilitate," and direct verbs instead of passive constructions.
- Write confident copy, but do not overclaim. Remove filler qualifiers like "very," "really," and "almost"; use hedging only when a claim is uncertain or category-dependent.
- Use natural transitions only when they improve scanning or connect ideas. Do not over-signpost every paragraph.
- Avoid AI-tell phrases: "In today's digital landscape," "At its core," "It's worth noting that," "That being said," "Let's delve into," "This begs the question," and "When it comes to the realm of."
- Avoid exclamation points unless the brand is explicitly playful and the moment earns it.
- Respect the visual density. Dense layouts need short copy; spacious editorial layouts can carry more explanation.
- Conversion pages may be sharper and more benefit-led, but they must still avoid hype and fabricated proof.
- Articles and blogs should be more measured and concrete, with fewer marketing claims and more direct explanation.
- Case studies should sound like evidence gathered from a real project, not a sales page with a customer name attached.

## Audience Calibration

- **Marketing pages**: Persuade. Lead with what changes for the reader, then support with proof, details, and a clear next step.
- **Informational pages**: Inform. Answer the question, organize for scanning, and do not oversell.
- **Legal/formal pages**: Protect. Precision over flow; every sentence should mean exactly one thing. Use plain language where possible, structure sections clearly, and avoid marketing language.
- **B2B software, technical services, professional tools, law, healthcare, and high-stakes services**: Stay direct and restrained. Lead with outcomes, proof, process clarity, and risk reduction. Personality belongs in small moments, not every sentence.
- **Consumer, local, hospitality, wellness, restaurant, event, and creative sites**: Warmer language is acceptable, but clarity and specificity still win.
- Match the visual specification: bold display typography can support punchier headlines; elegant or editorial designs need more refined language; dense layouts need shorter copy.
