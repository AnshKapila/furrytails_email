---
name: website-content-management
description: >
  Use this skill when editing website text, metadata, image URLs, or structured
  values stored in content or data files rather than directly in components —
  for example "change this copy everywhere", "add an item to the list", or
  "replace the image from the data file". Use `cms-management` when an embedded
  CMS owns the content.
mode: sandbox
---

# Content data vs. template code

Trace the rendered value to its authoritative source before editing. When a
template maps or reads a content/data file, edit that file only; the template is
the rendering layer. Never append replacement data in the component with
`.concat()`, `.push()`, or spread merely to avoid changing the source.

When an image URL in the rendered page comes from a JSON content file passed through an image-transformation helper (e.g. `optimizeImg(item.image, width)`, `resizeImg(item.src, opts)`), the actual source URL is in the JSON file without the image-service transforms (e.g. `w_100,c_limit`). Use the raw URL stored in the JSON file as the match target. The runtime-transformed URL visible in the DOM (e.g. with `w_100,c_limit` transforms) is derived and should not be used for matching.

# Where a value lives

Distinguish derived occurrences from independent duplicates:

- First edit the authoritative source. A component expression that references
  the imported object, prop, or mapped item is derived; do not edit it.
- Then search for literal copies of the old user-facing value. Those are
  independent duplicates; update each literal whose meaning should remain
  consistent with the source.
- Treat `alt`, `title`, and metadata as separate semantic fields. Update them
  only when the requested change makes their existing meaning inaccurate.

# Content file conventions

Next.js stores site content in `src/data/*.ts` modules (e.g. `content.ts`, or per-page `home.ts`, `services.ts`). HTML apps use flat JSON files under `src/content/` (e.g. `projects.json`, `services.json`). Use descriptive names, not generic ones like `data`, `main`, or `items`.
