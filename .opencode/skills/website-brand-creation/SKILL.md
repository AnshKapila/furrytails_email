---
name: website-brand-creation
description: "Use this skill when assembling or adjusting a website's brand identity — choosing colors and fonts for backgrounds, headings, body text, navigation, and call-to-action elements, applying a logo's palette, honouring user-supplied colors, or producing a dark-mode variant. Triggers any time you make color or typography decisions for a generated site, even when the user just says 'pick colors', 'use my logo', 'match my brand', or 'make it darker'."
mode: both
---

## Brand Source

When the user prompt contains a `## Brand` section, its `color_palette` and `typography_palette` are the source of truth for the website's palette and fonts. The `## Visual Specification` describes layout, motion, and structure; any colors or fonts it mentions are illustrative of layout intent and are replaced by the values from `## Brand`.

## On-disk source (refinement editor only)

A `## Brand` block in the prompt is always the primary source — see `## Brand Source` above. This on-disk fallback only applies when no `## Brand` block is present (the refinement editor's case).

When the prompt has no `## Brand` block AND `docs/brand.json` exists at the app root, treat that file as the equivalent source of truth (it is the persisted output of `extract_brand_guidelines`). Read it via the filesystem and let `colors`, `typography`, `tone`, and `personality` outrank values inferred from the visual specification or the existing prototype.

Do NOT read `docs/brand.json` when a `## Brand` block is already in the prompt — the block is filtered for the current iteration and overrides the master file. Do NOT read per-iteration `docs/<iter>/brand.json` files; those exist for first-gen prompt injection and are not authoritative outside that flow.

## Logo Analysis

Use the following priority order when deriving the Color and Typography palettes:

1. **`## Brand` block** — when present in the user prompt, its `color_palette` and `typography_palette` outrank every source below. See `## Brand Source` above. Missing role keys (e.g. `nav_background_color`, `alternative_background_color`) fall back to the rules below.
2. **Logo Info** — if provided, derive both palettes primarily from the logo's colors, fonts, and visual style.
3. **User-provided colors** — if the user has explicitly specified brand colors (e.g. "our brand color is #1A73E8"), use them as the foundation even if no logo is provided.
4. **Generated palette** — if neither is available, generate a palette that fits the website purpose and visual specification.

Apply the highest-priority source available. When multiple sources are available, the higher-priority source wins on conflicts (e.g. logo color overrides user-specified color unless the user explicitly says "ignore the logo colors").

## Color palette

Define a hex code value for each of the following roles based on the user requirements. If they are not explicitly provided, select colors that would match the website purpose.

- `background_color` → default page background color.
- `alternative_background_color` → optional secondary background color, which can be used to contrast sections or in some pages to break monotony.
- `primary_cta_color` → primary CTA fills and high-contrast accent text. Must have strong contrast against both backgrounds.
- `accent_color` → highlights, chips, small UI accents, link accents. Must not compete with the primary CTA.
- `nav_background_color` → Check if the visual specification has a transparent or solid navigation bar. If it’s transparent, then set this to transparent `#00000000` .
    - If the navbar is solid, then check if logo info is provided and if the logo background color is not transparent, then this value must match the logo background color.
    - If the navbar is solid and the logo info is provided but the logo background is transparent, then `nav_background_color` must contrast with the primary colors inside the logo.
- `body_text_color` → main text color to use. Must have high contrast against `background_color` for readability.
- `alternate_body_text_color` → text color to use in sections with `alternative_background_color` so that it contrasts with it.

## Typography palette

Use fonts from the `Available Fonts` that would match the `Visual Specification`. Pick the right fonts for each of these values:

- `hero`: font name string
- `heading`: font name string
- `sub_heading`: font name string
- `body`: font name string

## Dark Mode

If the `Visual Specification` references a dark theme, dark mode, or dark background:
- Set `background_color` to a dark value (e.g. `#0D0D0D`, `#111827`, `#1A1A2E`)
- Set `body_text_color` to a light value with high contrast (e.g. `#F5F5F5`, `#E5E7EB`)
- Set `alternative_background_color` to a slightly lighter dark (e.g. `#1A1A1A`, `#1F2937`)
- Set `alternate_body_text_color` to a slightly muted light (e.g. `#D1D5DB`)
- Ensure `primary_cta_color` has strong contrast against both dark backgrounds
- Do not use near-black for `primary_cta_color` unless it is a high-contrast color like white or neon
