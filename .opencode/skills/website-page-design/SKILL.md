---
name: website-page-design
description: "Use this skill when starting a new page design or redesign and you need a concrete visual foundation to build from — fetches a real design specification (layout structure, typography, color usage, spacing, and component patterns) based on a short description of what the page is about. Triggers when a newly-sitemapped page has no existing layout, the previous specification is not working and you want a different direction, or the build pipeline needs an inspiration source before generating the page — even when the user just says 'give me a fresh look' or 'try a different layout'."
mode: sandbox
---

# website-page-design

Calls the Kite gallery API to return a visual design specification — layout structure, typography, color usage, spacing, and component patterns — for a website page.

## When to reach for this

- A page redesign is starting and you need a design foundation.
- A newly-sitemapped page has no existing layout and you need inspiration.
- A previous spec isn't working and you want to try a different one.

## Call it

```bash
curl -sS -X POST "$GALLERY_API_URL/api/external/visual-specs" \
  -H "Authorization: Bearer $GALLERY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": ["A photography portfolio homepage"], "quantity": 1}'
```

Replace the `data[0]` string with a short description of what the page is about — this steers category selection server-side.

## Read the response

JSON shape:

```json
{
  "category": { "name": "...", "description": "..." },
  "visual_specs": [
    { "inspiration_website_name": "...", "visual_spec": "<design description>" }
  ]
}
```

Use `visual_specs[0].visual_spec` as the design foundation. `visual_specs[0].inspiration_website_name` identifies the source folder if you need to reference it later.

## Env vars

- `$GALLERY_API_URL` — base URL
- `$GALLERY_API_TOKEN` — bearer token (never log or echo this)
