---
name: website-visual-design
description: "Use this skill when laying out or styling a generated website — choosing how sections, navigation, logos, buttons, hero areas, feature blocks, image grids, and product visuals look and behave at desktop and mobile sizes. Covers responsive layout, accessibility, contrast-safe brand-color application, navbar visual behaviour, logo sizing, and the visual treatment of product UI versus illustrative imagery. Triggers whenever you make visual layout or styling decisions for the site, even when the user just says 'fix the design' or 'this section looks off'."
mode: both
---

## Precedence

When a prompt includes a `Visual Specification`, use it as the primary visual source. Apply these rules only as guardrails for accessibility, responsiveness, touch usability, and render correctness.

1. Ensure that every section is designed with mobile responsiveness in mind. These are the bare minimum rules:
    - no horizontal scrolling
    - text wraps safely
    - mobile nav is usable and non-transparent unless explicitly intended
    - the hamburger menu in the navbar must toggle open/closed and include a visible close (✕) button inside the drawer
    - the navbar (including the hamburger/close button) must always render above the mobile nav drawer and its backdrop overlay
    - the mobile nav drawer must include a semi-transparent backdrop overlay that closes the drawer when tapped
2. Use Lucide icons wherever instead of emojis.
3. When adding animations, think through the purpose of the section and decide on the event, speed, and nature of the animation so that it fits the section’s purpose.
    - Use `overflow: clip` (or `overflow-x: clip`) for all clipping near sticky or scroll-linked elements — both when adding new containment and when replacing existing overflow. It clips visually without creating a scroll container, so `position: sticky` continues to work.
    - For sticky + scrolling column layouts (one column pinned via `position: sticky`, the other scrolling past with crossfades or scroll-spy triggers):
        1. The scrolling column’s total height determines how long the sticky element stays pinned. Sticky range = parent container height − sticky element height.
        2. The scrolling column must be tall enough for every scroll-triggered transition (opacity crossfade, text highlight, UI swap) to complete before the sticky element unpins.
        3. If the scrolling content is short, add bottom padding to the scrolling column to extend the sticky range. Compare against any similar working section on the same page to calibrate the required height.
4. Ensure semantic structure and keyboard-friendly interactions.
5. Keep contrast accessible and visual hierarchy clear.
6. Ensure that all interactive elements are obvious and usable on touch devices.
7. When visual instructions conflict, use this precedence: explicit user request first, then required response format and validation steps from the host prompt, then visual/design spec, then current implementation pattern. Follow one coherent visual direction.
8. Apply the minimum visual change that satisfies the request. Do not introduce unrelated styling, animation, layout shifts, or decorative treatments.
9. Transparent/blur nav mechanics are preserved; only the base hue/hex is swapped.
10. Respect the **contrast intent** (e.g., "near-white text on dark hero", "muted supporting text on light sections").
11. If the `Logo Info` mentions that it contains a wordmark, do not add the brand name in the navbar as text.
12. If applying a brand color would create low contrast (e.g., accent text on background, body text on alternative background), do **one** of the following (in this order):
    1. Keep the reference color for that role, or
    2. Use a darker/lighter variant that restores contrast (still expressed with a hex), or
    3. Do not apply that brand color at all.
13. If applying `nav_background_color` reduces legibility, you may adjust **only** nav text/icon/link colors (still with hex) to restore contrast. Do not change nav layout, opacity mechanics, blur strength, stickiness, borders, elevation/shadows, or interactions.
14. If the nav is transparent, semi-transparent, blurred, frosted, or "glass":
    - Keep the described opacity/blur/frosted mechanics unchanged.
    - Apply `nav_background_color` as the **base/nav surface hue** under that mechanic (i.e., swap only the color/hex, not the behavior).
15. If the nav has multiple states (e.g., default vs scrolled, sticky vs non-sticky), apply `nav_background_color` to the **background/surface color** of each state where a background is defined.
16. Render logos in containers that prevent distortion and keep them visually prominent:
    - Navbar logos must be clearly legible: use `h-10` (40px) minimum for wordmarks/icon-wordmarks, `h-8` (32px) minimum for icon-only logos. Never use `h-5` or `h-6` for logos - they become unreadable.
    - Trust/logo-strip logos and employer/institution logos must sit in consistent cards or tiles with enough height for wide wordmarks to read clearly. Prefer containers at least `min-h-[72px]` and increase to `min-h-[88px]` when the section is sparse or premium in tone.
    - For a small set of logos, use a compact wrapped row or grid instead of stretching them edge-to-edge with oversized gaps.
    - Apply `object-fit: contain` with `w-auto` or bounded max-width/max-height values so the logo scales naturally inside the card.
    - Avoid stretching logos to fill mismatched containers.
17. For SaaS/software sections, distinguish between two visual classes before designing the layout:
    1. **Code-rendered product visuals**: dashboards, analytics panels, workflow builders, integration/data-flow maps, architecture/security diagrams, charts, metrics, and admin/product UI. These should usually be built in HTML/CSS/SVG.
    2. **Illustrative/editorial raster images**: brand mood backdrops, portraits, and supporting non-UI imagery. Use these only when the section benefits from atmosphere or human context rather than literal product detail.
18. When rendering product visuals (product previews, app screens, dashboard sections, integration/data-flow sections, and workflow/automation sections, etc.), follow these rules:
    1. Select a visual treatment mode for product visual sections based on narrative intent:
        - Clean Isolated UI (minimal/no background)
        - Soft Ambient (subtle tinted/texture background)
        - Full-Bleed Branded (strong gradient/mesh/wave background)
        - Dark Contextual (dark/cinematic setting for compliance/infrastructure/ops)
        - Annotated Overlay (floating callout cards/labels over base UI)
        - Layered Product Story (multiple UI panes/cards showing flow/state)
    2. Rendered UI blocks can be interactive-looking or schematic/static based on the section's storytelling needs.
    3. Backgrounds are optional for rendered UI visuals. Use whichever best fits the section: none, subtle ambient, or full-bleed branded/contextual.
    4. If the page includes multiple product visual sections, maintain visual variety:
        - Use at least 2 distinct visual treatment modes across those sections.
        - Avoid reusing the same treatment mode in adjacent product visual sections unless explicitly requested.
19. Apply these rules to both images and rendered HTML visuals (dashboards, product previews, workflow diagrams, etc.)
    1. Every visual placement should look intentional, not accidental.
    2. **Hero/background sections**: Images must fill the section edge-to-edge using `object-cover object-center` with `w-full h-full`. Rendered HTML visuals must span the full container width.
    3. **Feature sections (text + visual)**: Either match the container aspect ratio to the visual, or use `object-cover` with the focal point anchored using `object-[position]`. Rendered HTML visuals should be sized to balance with the adjacent text.
    4. **Grid cards**: Use consistent aspect ratios across the grid (e.g., `aspect-video`, `aspect-square`, or `aspect-[4/3]`) with `object-cover` for images. Rendered HTML visuals in grids should use matching fixed heights.
    5. **Floating/accent visuals**: If the visual doesn't fill its container, center it with consistent padding so it looks deliberate.
    6. Every visual - whether an image or a rendered HTML block - must fill its container cleanly with no awkward dead space that looks like a rendering bug.
    7. **Background color matching**: When an image sits on a colored section background, the image's own background (solid or environmental) must be described to match the surrounding section background so the generated image blends seamlessly rather than creating a visible rectangle against the page.
20. Raster-image placement contract for SaaS/software layouts:
    - Do not place a small centered illustration inside a large card unless the layout is intentionally poster-like and the surrounding section supports that treatment.
    - In split sections, make the raster visual feel sized for the live slot, not like a large artwork shrunk down at the last minute.
    - Avoid obvious "card inside card" artifacts where the image background reads as a separate rectangle against the section.
    - If the raster image is contained rather than full-bleed, its internal composition must still occupy the slot with clear visual weight and no accidental dead space.
    - Do not let raster imagery overlap with copy in a way that feels like a rendering bug or makes the image seem misplaced.
21. When a request replaces an entire section's design with a detailed spec (timeline, process flow, showcase, etc.), treat it as a bespoke layout challenge, not a template swap:
    - Avoid uniform grids where every item is the same size and weight. Vary card dimensions, spacing, or visual treatment across steps to create hierarchy and rhythm.
    - Make the spec's focal element (e.g., a Slack mockup, a dashboard preview, a hero image) visually dominant — significantly larger and more detailed than the other items, not just a slightly accented card.
    - Use asymmetrical or staggered layouts (e.g., two-column with one large visual + stacked steps, offset timeline nodes, alternating left/right) rather than equal-width column grids.
    - Establish strong typographic hierarchy: section headline, step titles, and descriptive text should each sit at a distinct size/weight tier.
    - If the spec calls for a linear sequence (timeline, journey, first-day walkthrough), the layout should read as forward motion — left-to-right on desktop, top-to-bottom on mobile — without circular or looping visual metaphors unless the spec requests them.
22. When creating hero sections with overlapping elements (e.g., large text behind or above images, negative margins to create overlap effects):
    - The primary hero text (h1) must remain fully readable - no part of the text should be completely hidden behind overlapping elements. If text overlaps with images or content rows, ensure enough of the text is visible and legible. Do not let overlapping elements fully obscure the hero heading.
    - Do not use `overflow-hidden` on hero section containers - use `overflow-clip` or remove overflow constraints entirely. `overflow-hidden` clips oversized viewport-relative text (`text-[12vw]`, `text-[8vw]`, etc.) at the section boundary.
    - On mobile viewports, reduce or remove negative margin overlaps to prevent text from being obscured. Use responsive variants (e.g., `md:mt-[-5vw]` but no negative margin on mobile) and ensure the text remains fully visible at all breakpoints.
    - Hero text using viewport-relative units (`vw`) must remain fully readable at all screen widths, including narrow design preview frames (~320px). Ensure no letters are clipped or hidden behind other elements at any breakpoint.
