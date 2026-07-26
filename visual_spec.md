# Visual Design Spec

## 1. Global Visual System
The visual language is highly editorial, heavily print-inspired, and driven by massive typography and rigorous structural linework. The aesthetic relies on an extremely disciplined, high-contrast two-color primary palette: a warm off-white canvas and a deep red used exclusively for all text, UI elements, and dividing lines. It balances dense, oversized letterforms with stark, open negative space. Imagery provides the only real color variance, introducing muted pastels and warm, high-contrast photography that breaks up the monochromatic shell. The overall feel is premium, confident, static, and structural, prioritizing layout rhythm over kinetic motion.

## 2. Global Layout and Rhythm
The entire site is bound by an invisible macro-grid, made visible through the continuous use of 1px horizontal borders that run edge-to-edge, capping almost every vertical section. 
*   **Vertical Dividers:** Rarely used. Structure is implied by alignment, proximity, and horizontal rules.
*   **Containers:** The main layout operates on a fluid edge-to-edge grid with consistent, generous lateral padding (approx. 24px-40px depending on viewport).
*   **Split Layouts:** Heavy use of 50/50 split-screen compositions on desktop for editorial content, alternating left/right alignment as the user scrolls. These reliably stack on mobile.
*   **Section Pacing:** Governed almost entirely by the full-width horizontal rules and standard utility headers that introduce new structural blocks.

## 3. Global Typography System
The design rests heavily on two drastically different typefaces, creating extreme scale and style contrast.
*   **Primary Display (Serif):** A high-contrast modern serif (thin hairlines, prominent ball terminals). Used at overwhelmingly massive scales (often filling the viewport width or dominating half the screen). It features extremely tight line heights (leading) and tight tracking. It acts as the primary graphic element on the page, with organic word breaks permitted.
*   **Secondary/Body (Sans-serif):** A clean, neutral, highly legible neo-grotesque. Used at standard, small sizes (approx. 14px-16px) for body paragraphs, product labels, utility links, and fine print. 
*   **Text Color:** 100% of the typography on the site (excluding inverted promo blocks) is rendered in the primary deep red. There are no gray scales for secondary text.

## 4. Global Color, Surface, and Effects
A strict, uncompromising color limitation rules the system.
*   **Canvas:** A warm off-white/cream is universally applied as the page background.
*   **Ink:** A single deep red/tomato color is used as the exclusive "ink" for all typography, 1px borders, UI outlines, and icons.
*   **Accents (Product Cards Only):** Soft, flat pastels (pink, yellow, mint, light blue) and a light neutral gray are used strictly as background box fills for isolated product shots.
*   **Inversion:** Specific promotional sections completely invert the palette (deep red background, white text) for high impact.
*   **Surface Effects:** Flat and matte. No glassmorphism, no blurs, no gradients. Shadows are restricted entirely to realistic drop shadows baked into the product photography.

## 5. Global Motion Language
The site is fundamentally and deliberately **static**. This is a core defining trait of the design system. The premium, editorial feel is derived from structural rigidity, dramatic scale, and graphic composition, not from kinetic movement. 
*   **Scrolling:** Standard, untethered, native scrolling. 
*   **Reveals:** There are no staged entrance animations, fade-ups, or scroll-scrubbed typography effects. Elements exist natively in the document flow.
*   **Hover States:** Minimal and standard UI shifts (e.g., cursor changes, likely subtle opacity dips on links), prioritizing a print-like stability over digital reactivity.

## 6. Motion Adaptation Rules
Because the site is static, adaptation rules focus on layout reflow rather than animation timing.
*   **Carousel Reflow:** Desktop multi-column product grids must convert to native horizontal scrolling tracks (`overflow-x: auto`, `scroll-snap-type: x mandatory`) on mobile. The carousel must allow the next card to visually peek into the right side of the viewport to afford swiping.
*   **Typographic Scaling:** Massive display serif headings must scale down fluidly on mobile viewports to prevent horizontal overflow, but they must remain disproportionately large relative to body text to maintain their dense, graphic weight.

## 7. Global Imagery and Iconography
*   **Editorial Photography:** Bright, high-contrast lifestyle and atmospheric photography. Often warm-toned with strong directional lighting. Placed with sharp, 0px border-radius corners. No visible CSS borders.
*   **Product Photography:** Studio-isolated products (e.g., bags) floating cleanly inside unbordered pastel rectangles. The products feature realistic, soft drop shadows grounded within the colored box.
*   **Custom Graphics:** Replaces typography in specific instances (like the Blog index header). Heavy, filled vector shapes utilizing the negative space of the off-white background.
*   **Infographics/Icons:** Custom line-art illustrations (e.g., botanical motifs) rendered purely in the primary red ink with a consistent, uniform stroke weight.

## 8. Persistent Interface Layers
*   **Top Navigation:** A sticky top bar that remains visible during scroll. Solid background matching the page body (off-white) with a distinct 1px deep red bottom border.
    *   *Desktop:* Logo (left), secondary contextual links (center), utility links like Cart/Menu (right).
    *   *Mobile:* Simplified. Logo (left), utility links (right).

## 9. Section Inventory
1.  **Split Hero** (Editorial intro)
2.  **Product Carousel** (Horizontal scroll product cards)
3.  **Editorial Block** (Alternating 50/50 text/image splits)
4.  **Inverted Promo Block** (Full-bleed color inversion)
5.  **Oversized Form Block** (Newsletter signup)
6.  **Blog Index Header** (Graphic typography hero)
7.  **Blog Grid** (Dense article cards)
8.  **Article Detail** (Standard reading column with inline graphics)
9.  **Global Footer** (Minimal text grid)

## 10. Section-by-Section Detailed Spec

### Split Hero
*   **Purpose:** Initial brand impression and primary entrance.
*   **Layout:** 50/50 split on desktop.
*   **Typography:** The left half is dominated by the massive display serif. Word breaks are acceptable and expected.
*   **Imagery:** The right half contains a single, sharp-cornered editorial image floating within the grid constraints.
*   **Mobile:** Image stacks above the massive text.

### Product Carousel
*   **Purpose:** Browsable product discovery without vertical page bloat.
*   **Structure:** Preceded by a standard Utility Header (see Reusable Patterns).
*   **Layout:** 4-up horizontal row on desktop.
*   **Card Composition:** A colored, sharp-cornered (or slightly rounded) rectangle. An isolated product image with a drop shadow is centered inside. 
*   **Typography:** Product name and sub-labels are positioned completely *outside* and below the colored box, left-aligned in the small sans-serif.
*   **Mobile:** Converts to a native horizontal swipe carousel. Cards take up ~80-85% of the viewport width, allowing the next card to peek.

### Editorial Block
*   **Purpose:** Feature highlighting and storytelling.
*   **Layout:** 50/50 split on desktop, alternating left/right alignment per section to create a zigzag reading rhythm.
*   **Typography:** One half contains a multi-line, massive display serif heading paired with a short paragraph of small sans-serif body copy.
*   **Imagery:** The other half contains a full-bleed (within the padded container), sharp-cornered photograph.
*   **Mobile:** Sections stack vertically. To avoid uninterrupted walls of text, the stacking order typically prioritizes Image on top, Text on bottom.

### Inverted Promo Block
*   **Layout:** Full-width, full-bleed container.
*   **Color:** Deep red background. Text is inverted to the off-white canvas color.
*   **Typography:** Massive display serif on one side, small sans-serif body copy.
*   **Imagery:** Often incorporates an isolated product or packaging shot, deeply integrated into the layout.

### Oversized Form Block
*   **Purpose:** Newsletter or broad data capture.
*   **Layout:** Full-width.
*   **Typography:** Features a massive display serif headline.
*   **UI Components:** Utilizes the "UI Pill" pattern (see Reusable Patterns). The input field spans the majority of the width, with a corresponding pill-shaped submit button alongside it.
*   **Mobile:** The input pill and the submit pill stack vertically, both expanding to 100% of the available width.

### Blog Index Header
*   **Layout:** Full-bleed container within lateral padding.
*   **Imagery/Typography:** Instead of a standard text node, this utilizes a massive custom vector graphic of overlapping, heavy, bubble-like letterforms spelling the section title. The graphic fills the container edge-to-edge. Counters (inner spaces) are filled with the off-white background color.

### Blog Grid
*   **Layout:** Dense, multi-column grid (e.g., 4-up on desktop) of article cards.
*   **Card Composition:** Top-aligned, sharp-cornered image. Immediately followed below by a multi-line display serif title (scaled down significantly from hero sizes) and a small sans-serif metadata label.
*   **Mobile:** Reflows to a strict 2-column grid.

### Article Detail
*   **Layout:** Standard, centered single-column reading width for optimal line lengths.
*   **Typography:** Large display serif for primary article headings. Standard sans-serif for body copy.
*   **Infographics:** Specific data visualization patterns. Uses uniform stroke-weight line-art (in red ink) paired with scaled-down versions of the UI Pill pattern for data labels. Data volume is sometimes represented by a dense, repeating grid of tiny icon units.

### Global Footer
*   **Layout:** Minimalist, text-only grid. 4 columns on desktop.
*   **Typography:** Exclusively uses the small sans-serif. Left-aligned within columns. 
*   **Color:** Standard canvas and red ink. No distinct background color block separates the footer; it relies on a 1px top border.

## 11. Reusable Patterns and Motifs

*   **The 1px Divider:** The universal pacing element. A 1px solid red horizontal line spanning 100% of the viewport width. It caps almost every section.
*   **The Utility Header:** A strict architectural stack used to introduce grids or carousels.
    *   `[1px horizontal rule]`
    *   `[Left-aligned Category Text (Sans-serif)] — [Right-aligned CTA (Sans-serif) + Thin Line Arrow]`
*   **The Thin Line Arrow:** `->` A bespoke, thin-stroke, right-pointing arrow used consistently alongside CTAs in the utility headers.
*   **The UI Pill:** A large container with fully rounded ends (pill shape) and a 1px solid red outline. The background is transparent. Used for all text inputs, major submit buttons, and small infographic data labels. Placeholder text within the input is large and acts as a dominant visual element.
*   **The Floating Product Card:** Colored background box, transparent-background product image with baked-in drop shadow, text strictly placed outside and below.

## 12. Essential Traits to Preserve
1.  **Strict Two-Color Palette:** The absolute reliance on the off-white canvas and deep red ink for all typography and lines.
2.  **Typographic Extremes:** The pairing of exceptionally large, tightly packed Serif headings with small, highly legible Sans-serif body copy.
3.  **Structural Linework:** The pacing of the page using 1px horizontal borders rather than colored backgrounds or drop-shadowed containers.
4.  **Static Rigidity:** The absence of scroll-triggered motion or complex animations, favoring a print-layout aesthetic.
5.  **Pill Inputs:** The distinct, oversized, outlined pill shapes for forms and buttons.

## 13. Build Guardrails and Anti-Simplification Warnings
*   **Do not dilute the color system:** Do not default to `#333`, `#000`, or standard blue for text, links, or body copy. *Every* text node and border must be the primary red.
*   **Do not soften the typography:** Do not normalize heading sizes to standard web defaults (h1=3em, etc.). The display serif must be uncomfortably large and tightly leaded to achieve the editorial look. 
*   **Do not use standard form inputs:** Default browser inputs with background fills or simple bottom borders will instantly break the design language. Forms must use the outlined UI Pill pattern.
*   **Do not add unprompted animation:** Resist the urge to add "fade-up on scroll" intersection observers. The design depends on immediate, static layout stability.
*   **Do not wrap product cards in borders:** The colored backgrounds of the product items define their edges; adding a 1px border or box-shadow to the outer card container will ruin the clean aesthetic.

## 14. Redaction and Abstraction Notes
*   Specific brand names, product titles, and precise geographical locations have been generalized.
*   The exact wording of massive typographic headlines (e.g., the introductory hero phrase, specific editorial callouts) has been abstracted to describe their structural role rather than their literal content. 
*   Visible email addresses and location data in the footer have been ignored in favor of describing the layout structure.