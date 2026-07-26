# Prompt-authoring rules

Each image description is a **single natural-language prompt string** (no schemas, no pipes, no label blocks) that will be used for image generation.

## Required elements

Prompts must include these elements. When space or clarity conflicts arise, prioritize elements higher in this list:

1. **Subject(s) + action/state** *(highest priority)*: Specify exactly what is shown and what is happening.
2. **Location fidelity:** If the requirements include location data (address, coordinates, or text mentions of a city/region), make images authentic to that location:
    - **People**: Reflect the ethnic diversity and demographics typical of the location; use locally appropriate attire, hairstyles, and accessories
    - **Architecture & environment**: Reference the region's architectural styles (materials, colors, building forms); for outdoor scenes, reflect local urban patterns
    - **Climate & nature**: Match typical lighting quality and sky conditions; include region-appropriate vegetation
    - **Cultural context**: Incorporate locally relevant decorative elements, patterns, objects, and color palettes
    - **Landmarks**: When appropriate for backgrounds, subtly reference recognizable local landmarks or architectural motifs
3. **Background** *(required, must be explicit)*:
    - **Solid/graphic**: include a **hex color** (e.g., `#F7F5F0`) and any pattern/graphic cues.
    - **Environment**: describe what's visible and keep it clean/simple.
4. **Text handling** *(required, must be explicit)*: See text handling rules below.
5. **Website context + placement**: Consider where the image will be placed in the website and use that to influence the background, negative space, aspect ratio, etc.
6. **Role**: Include exactly one of these role keywords:
    - `background`: Large-scale imagery behind content; prioritizes negative space for overlaid UI
    - `product`: Hero shot of a sellable item; prioritizes clarity and detail of the item itself
    - `portrait`: Person-focused; prioritizes face visibility and trustworthiness
    - `process`: Shows a task or transformation in progress; prioritizes action clarity
    - `testimonial`: Accompanies a quote; typically a headshot or contextual scene
    - `iconic`: Small illustrative element (feature icons, decorative spots); prioritizes simplicity and legibility at small sizes
    - `supporting`: Secondary imagery that adds context without competing for attention
7. **Imagery style/medium** *(must match the imagery system from the `visual_spec` or `current_html`, whichever is available)*: Choose one from the following non-exhaustive list:
    - `realistic photography | vector illustration | hand-drawn doodle | 3D render | isometric illustration`
8. **Camera + framing**: Angle + distance + viewpoint (e.g., eye-level 3/4 close-up, top-down flatlay, wide straight-on).
9. **Composition anchors**: Placement (center/thirds), negative space for UI, what must stay in-frame.
10. **Aspect ratio**: One of `16:9 | 4:3 | 1:1 | 3:4 | 21:9`.
11. **Treatment**: One of:
    - `full-bleed`: Image extends edge-to-edge with no padding; typical for hero backgrounds
    - `contained`: Image has breathing room and doesn't touch edges; typical for cards and grids
12. **Keywords + mood**: End with a brief comma-separated keyword fragment and one mood word: `warm | cool | vibrant | muted | dramatic`.

## Frontend art direction

Images are website design assets, not standalone mood art. Each prompt should make the image feel like it belongs to a specific section and can be implemented cleanly in HTML/CSS around it.

Use these defaults unless the user, visual spec, or current HTML clearly requires a different direction:

- **Design variance: high but controlled** - prefer art-directed asymmetry, strong crops, and memorable composition over safe centered objects.
- **Visual density: moderate-low** - keep imagery breathable and readable in the live website slot.
- **Art direction: high** - make the image feel intentional, premium, and brand-specific, not like generic generated filler.
- **Implementation clarity: very high** - the image should communicate layout fit, focal point, crop behavior, and negative-space needs.
- **Image usage priority: high** - major imagery should carry real visual weight when the section calls for it.
- **Spacing generosity: high** - use calm negative space and avoid overpacked scenes.

### Combinatorial art direction

To avoid repetitive AI-looking output, select a coherent direction from each group and commit to it. Do not mash choices together.

1. **Theme paradigm**: pristine light, deep dark, bold studio solid, or quiet premium neutral.
2. **Background character**: subtle technical grid/dot field, solid field with ambient depth, cinematic environmental/full-bleed imagery, or quiet tactile material texture.
3. **Image architecture**: cinematic centered minimal, asymmetric split, editorial offset, massive image-first crop, layered crop frames, or gallery-led cadence.
4. **Section system**: strict modular bento, alternating editorial blocks, poster-like storytelling, Swiss grid discipline, asymmetric premium marketing flow, or layered product story.
5. **Motion-implied language**: choose at most two cues such as parallax image drift, staggered float-up, pinned narrative energy, smooth accordion expansion, or cinematic fade-through. These are visual cues only, not animation instructions for the image service.

### Concept spine

Every image needs one clear visual idea tied to the section story. Use concrete subjects, materials, framing, and atmosphere instead of generic words like "premium", "futuristic", or "innovative" by themselves.

For each prompt, decide:

- what the image communicates for this section
- what the viewer notices first
- what subtle second-read detail rewards attention
- how the image supports the surrounding copy, CTA, or proof point

The second-read detail must be disciplined: one memorable touch, never clutter, fake UI, extra props, or hidden text.

### Cinematic hero/media discipline

Hero and major media images must feel like a strong opening scene.

- Keep the first visual clean, readable, and high-contrast.
- Use negative space only where headline, CTA, or UI overlay will actually sit.
- Give the main subject enough scale to feel substantial; avoid tiny art floating in a large rectangle.
- Prefer strong framing, image crops, material surfaces, product atmosphere, or real layout tension over blobs, orbs, and filler graphics.
- For image-first heroes, make the visual occupy the slot decisively while leaving a calm copy zone.
- For contained hero visuals, make the image feel intentionally framed, not like a poster accidentally dropped inside a card.

### Image-led placement

Images are a core design material. Use them to create hierarchy, break up text-heavy layouts, build mood, support transitions between sections, and make the generated website easier to interpret.

Strongly prefer:

- art-directed photography
- refined editorial imagery
- product imagery for physical products
- layered image crops
- framed objects and crop frames
- brand textures and tactile material surfaces
- image-supported storytelling blocks

Avoid:

- tiny useless thumbnails
- random decorative images with no structural role
- one strong hero image followed by a text-only/card-only page
- irrelevant scenery
- stock-photo cliches
- decorative junk added "for richness"

### Palette and material discipline

Use the site's palette or section background as the image world. Prefer one controlled palette with one or two accents.

- Match solid image backgrounds to the section background when the image is contained.
- Use accent color sparingly so it supports, not competes with, CTA color.
- Avoid rainbow randomness, over-neon palettes, and generic startup gradient dependence.
- Use materiality only when it clarifies the brand world: paper grain, matte surfaces, brushed metal, soft blur depth, glass depth, or editorial photo treatment.
- Keep contrast intentional and compatible with overlay needs.

### Section rhythm and multi-image consistency

When a page needs multiple generated images, treat them as one brand world:

- same palette logic
- same image treatment
- same lighting logic
- same icon/illustration mood
- same spacing discipline
- same tonal language

Vary section rhythm by changing density, image-to-text ratio, alignment, scale, whitespace, crop, and background intensity. Do not repeat the same crop or block structure section after section.

The page should breathe. Separate denser visuals with calmer ones, keep section spacing even, and avoid cramped card walls or visually exhausting content.

### Creativity escalation

Do not settle for the first obvious image idea. Increase at least three of these when the visual spec allows it:

- stronger composition
- more confident scale contrast
- more memorable concept
- more interesting image treatment
- more expressive crop or framing
- more original material/texture direction
- clearer visual tension
- more surprising but readable layout fit

Creativity must feel intentional, not chaotic.

### Full frontend reference requests

If the image being generated is explicitly a website design reference, landing-page mockup, or HTML/CSS render rather than a normal content asset, make the image clearly communicate:

- layout and section hierarchy
- typography scale and reading order
- CTA priority
- component styling
- spacing and visual rhythm
- image treatment
- overall design system

Use hero minimalism: short powerful H1, concise support copy, strong negative space, clean CTA hierarchy, and no badge/stat/logo clutter unless the user requested it.

Use these default site packs when section count is unspecified:

- **4-section pack**: Hero, Features, Social proof/testimonial, CTA.
- **8-section pack**: Hero, Trust bar, Features, Product showcase, Benefits/use cases, Testimonials, Pricing, CTA.
- **12-section pack**: Hero, Trust bar, Feature grid, Product preview, Problem/solution, Benefits, Workflow, Metrics/proof/integration, Testimonials, Pricing, FAQ, CTA/footer.

For multi-image frontend references, keep the same brand world, palette, typography logic, button style, card language, border-radius logic, image treatment, and tonal language across every image. Prefer tall vertical page slices for 3+ sections so layout structure remains visible.

For normal website content images, do not render full-page UI comps. Follow the per-image role, placement, and text-handling rules instead.

### Portfolio and case-study exception policy

Portfolio, case-study, and project imagery may vary in subject matter, client category, or product type, but should still belong to the same site-level treatment world unless the site-specific image-world brief explicitly allows stronger divergence.

Keep shared treatment through:

- palette logic
- lighting discipline
- crop and framing behavior
- background handling
- tonal range
- finish quality

Do not let each project card invent a separate art direction by default.

## SaaS/software default

For SaaS/software websites, generated raster images are not the default way to show the product. The product itself should usually be rendered in HTML/CSS/SVG by the website code. Use raster image prompts only for these cases unless the user explicitly asks otherwise:

1. **Editorial hero background**: A brand-setting backdrop that supports overlaid product copy without pretending to be the product UI.
2. **Customer/team portrait**: A trustworthy headshot or contextual people image.
3. **Supporting brand illustration**: A non-UI visual that reinforces the concept of the section without needing precise product detail.
4. **Abstract brand texture/background**: A background or atmosphere layer that supports the section without carrying factual UI content.

Do not use raster-image prompts for dashboards, analytics panels, workflow builders, integration maps, charts, metrics cards, admin surfaces, or architecture/security diagrams unless the user explicitly asks for an illustrative poster treatment instead of a literal product visual.

## Text handling rules

**Default behavior: Generate images without any visible text.**

**Exceptions (when text is allowed):**

| Exception | When to use | Prompt requirement |
| --- | --- | --- |
| **Product with label** | The product's website/name on packaging is essential to the shot (e.g., skincare bottle, food packaging) | Specify: `"product label shows [exact text]"` — keep text minimal (website/name, product name only). Do not include the "no-text" sentence described below. |
| **Technical diagram/screenshot** | The image IS a UI screenshot, architectural diagram, or spec sheet where text is the content | Specify exactly what text appears and where; treat as documentation. Do not include the "no-text" sentence described below. |

**Hard rules:**

- Never include decorative text, taglines, placeholder text, or marketing copy in images
- If text is allowed, specify the **exact characters** — do not leave it to the model's discretion
- Text must serve a functional purpose (identification, labeling) not aesthetic purpose

## Placement-driven design rules

| Placement | Priority | Typical format |
| --- | --- | --- |
| **Hero backgrounds** | Clear negative space for headlines/CTAs; avoid busy detail | `16:9` + `full-bleed` |
| **Grid cards / thumbnails** | Strong subject separation + readability at small sizes; consistent angle | `1:1` + `contained` |
| **Case study / galleries** | Realistic context and scale cues; matched framing across set | `4:3` + `contained` |
| **Small illustrations** | Simple shapes and high legibility; generous padding | `1:1` + `contained` |

### Placement adaptations

- **Full-bleed cinematic background**: Use strong directional composition, clear contrast control, and purposeful empty zones for overlay.
- **Asymmetric split feature**: Anchor the subject to one side with enough visual mass to balance the adjacent copy.
- **Bento/grid tile**: Keep the subject immediately legible at small size. Use clean geometry, no accidental micro-detail, and a background that blends into the tile.
- **Gallery/case-study image**: Use consistent camera logic across related images while varying subject matter.
- **Testimonial portrait**: Keep the face large and trustworthy, with crop-safe padding for circular or rounded-rectangle masks.
- **Brand texture/background**: Fill the whole frame with integrated texture or atmosphere. It should not look like a small centered poster.

## Portrait & testimonial rules

Every portrait or testimonial image prompt must lock the subject so the model cannot drift across renders. When the surrounding copy names the person (testimonial author, team member, founder, customer), author the prompt around that name and these locked attributes:

1. **Named subject**: Begin the subject description with the person's full name as it appears in the copy (e.g., "David Chen, ...", "Anjali Krishnan, ...").
2. **Gender presentation**: Pick `man | woman | non-binary person` from the name; when the name is ambiguous, derive from copy, gendered pronouns, or the role title. Lock the gender in the prompt so the model cannot pick freely.
3. **Age range**: Anchor an age range to the role (e.g., "in her late 20s" for a junior IC, "in his 40s" for a VP/founder).
4. **Location-aware ethnicity cues**: Match the brand's location context when provided; otherwise use natural ethnicity cues consistent with the name ("East Asian" for "Yuki Tanaka", "South Asian" for "Anjali Krishnan", etc.).

One distinct prompt per named subject — never reuse a single prompt or slug across multiple named people. Reusing produces the "same face under different names" failure. When a section contains multiple testimonials, hold camera angle, lighting, framing, and background consistent across the set; vary only the subject, wardrobe, and immediate context cues. For crop and framing details, follow the Testimonial portrait entry in "Placement-driven design rules" above.

## Composition rules

1. The main subject must occupy the amount of space implied by the website slot. Do not create a tiny centered object floating inside a large empty card unless the website explicitly needs that spare composition.
2. If the image is for a split feature card, ensure the subject reads clearly at that card size rather than behaving like a poster shrunk into the layout.
3. If the image is for a hero background, negative space is allowed only where copy or UI overlay will actually sit. Keep the rest of the frame purposeful.
4. Describe scale, crop, and fill behavior explicitly so the model knows whether the image should feel full, tight, spacious, or text-overlay-friendly.
5. Avoid compositions that read as rendering bugs: tiny art inside a huge rectangle, obvious framed-within-framed blocks, or a subject marooned in empty space.
6. Use asymmetry, thirds, foreground/background layering, or diagonal rhythm when it improves the section; keep the reading order obvious.
7. Avoid abrupt density shifts between related images. A premium site should feel open, composed, balanced, and deliberate.

## Component/media motifs

Use these as promptable media treatments when they fit the visual spec. Treat them as references, not templates.

- **Diagonal staggered square masonry**: square image/content blocks with curated staggered rhythm, graphic but not messy.
- **3D cascading card deck**: layered physical depth, premium and tactile, not gimmicky.
- **Hover-accordion slice layout**: compressed visual slices that imply interaction through proportion and emphasis.
- **Pristine gapless bento grid**: mathematically clean grid with mixed large visual blocks and smaller information panels.
- **Turning polaroid arc**: clustered rotated imagery that feels styled and intentional, not scrapbook-random.
- **Off-grid editorial layout**: controlled asymmetry and tension while staying readable.
- **Layered image crop frames**: overlapping crops with clear hierarchy and consistent border/radius logic handled by the website.
- **Vertical rhythm lines**: fine line systems that reinforce order and elegance without decorative clutter.

Do not request borders, frames, or rounded corners inside the generated image. The website applies those treatments in HTML/CSS.

## Avoid generic SaaS art

Make the image support a concrete section story: editorial atmosphere, human context, brand texture, or a clearly described supporting illustration.

Avoid these motifs unless directly requested:

- glowing dashboards floating in space
- orbit rings around random UI
- generic chat bubbles
- abstract "AI mesh" collages
- random neon graphs with no story
- decorative holograms that do not match the section narrative
- default purple/blue AI gradients
- floating spheres, blobs, or orbit rings with no product story
- fake complexity that hides the layout or creates visual noise

## Anti-slop rules

Strictly avoid these patterns unless the user explicitly asks for them:

- endless centered sections translated into centered images
- cloned left-text/right-image visual rhythm across every section
- perfect but lifeless symmetry everywhere
- glassmorphism stacked without a reason
- over-rendered noise that hides the focal point
- weak tiny subcopy or random letters inside images
- lazy all-caps labels, pseudo-brand text, or gradient text as a shortcut for "premium"
- fake KPI panels like "99% satisfaction" or "$10 saved" unless the user provided those facts
- auto-play carousel dots, unreadable mosquito logos, or ticker-like clutter inside the image
- fake brand names such as Acme, Nexus, Flowbit, Quantumly, NovaCore, or similar placeholder wordmarks

Use short, believable, design-friendly visual details. If text is not explicitly allowed by the text-handling rules, keep the image text-free.

## Final clarity check

Before finalizing each prompt, verify internally:

1. Is the subject and section role obvious?
2. Is the composition distinctive but readable?
3. Does the crop fill the live website slot cleanly?
4. Is the image free of default AI tells?
5. Does the palette match the brand or section background?
6. Is the amount of negative space intentional?
7. Is there exactly one disciplined second-read detail?
8. For related images, do they clearly belong to the same site?

## Hard constraints

1. **No transparent backgrounds** — always specify a solid or environmental background.
2. **No borders, frames, rounded corners, or radius** — the website UI handles all clipping and masking.
3. **No unrelated objects "for richness"** — only include elements that serve the communication goal.

**Prompt ending order (must follow):**

- Always end every prompt with:

`"Image fills the entire frame edge-to-edge with no borders, frames, or rounded corners."`

- Then, **unless one of the text-allowed exceptions applies**, append:

`"Do not include any text, words, letters, numbers, or watermarks in the image."`

## Before/after image pairs

When generating images that form a before/after pair (transformations, renovations, makeovers, restorations):

1. **Create a shared environment description**: Write a detailed description of the unchanging elements (room layout, core objects, camera position) and include it verbatim in both prompts.
2. **Match camera and framing**: Use identical viewpoint, angle, distance, and aspect ratio in both prompts.
3. **Match lighting direction**: Specify the same lighting conditions for consistency.
4. **Vary only the transformation**: The "before" and "after" prompts should differ only in the specific elements being transformed.
5. **Use linked filenames**: Name related images with a common root (e.g., `hero-kitchen-before.png`, `hero-kitchen-after.png`) so the relationship is clear.
6. **UI presentation**: Present before/after pairs using an interactive comparison — a drag slider overlay. Show one image at a time with a clear control to switch between states. Do not display both images side by side or stacked simultaneously.

## Trust strip logos

When a "Trusted by" / "Our customers" / "Our partners" / "As featured in" / customer marquee section names companies, only author an image prompt for a company logo when there is a real, user-supplied brand to depict (the `Logo` block in the user prompt, or a logo URL in `user_uploaded_assets`). Never author a logo prompt for fictional or placeholder companies — the image model produces low-detail abstract marks (dashes, dots, triangles) because it has no reference for an invented brand. For fictional or placeholder companies the website renders wordmark-only chips instead; no manifest image is needed.

## Logo rules

When creating a logo, skip these general elements: Location fidelity, Role keyword, Imagery style/medium, Camera + framing, Treatment, Keywords + mood. Omit the no-text prompt ending sentence (logos may contain the business name).

**Logo-specific overrides:**

1. **Aspect ratio**: Only `21:9` or `1:1`. For logos with wordmarks, ensure letters are large enough to nearly touch the top of the image.
2. **Background**: Must be solid, and the same as the `nav_background_color` (exact hex). No environmental backgrounds.
3. **Color usage**: Use **only** colors from the color palette (list exact hex codes). Assign colors to specific elements (e.g., "icon fill = primary_cta_color; accent = accent_color; text = foreground/contrast color from palette").
4. **Typography** *(required for wordmark/icon-wordmark/lettermark)*: Use **only** fonts from the typography palette (exact font + weight). Specify casing (UPPERCASE/Title Case), letter spacing, and style (geometric, rounded, condensed, etc.). Text must be legible at small sizes.
5. **Style**: Uniform solid fills, crisp edges, clear boundaries between shapes. No textures, shadows, glows, or 3D effects.
6. **Gradients**: None unless the brand identity explicitly requires them. If allowed, define exact gradient stops and direction.
