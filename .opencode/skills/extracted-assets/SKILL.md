---
name: extracted-assets
description: >
  Use this skill when choosing imagery after the user imported a reference
  website. Before adding, generating, or replacing an image, check the curated
  products, team photos, work samples, customer logos, and visual identity
  assets already extracted from that source, even when the user does not
  mention it again.
mode: both
---

## On-disk source

When `docs/extracted_media.json` exists at the app root, treat it as the source of curated images for this site. It is the persisted output of the orchestrator's `extract_assets` tool — real images observed on a reference URL the user asked to reuse.

## Schema

```
{
  "url": "https://reference-site.example",
  "extracted_at": "ISO-8601 timestamp",
  "images": [
    { "url": "https://...", "role": "hero|product|team|customer-logo|...", "context": "one-sentence description" }
  ]
}
```

## How to use

- Select an extracted image only when its `role` matches the slot type and its
  `context` describes the same subject or business entity as the section. A
  generic hero photo does not replace a product image merely because both are
  wide.
- The user's explicit request for a new or generated image overrides the
  extracted-image preference. Otherwise prefer a matching extracted image. If
  none matches, do not modify `docs/extracted_media.json`; use the normal upload
  or generation flow for that slot.
- Embed each chosen image by its `url` directly. Never fabricate URLs and never modify the URL string.
- If the file is missing, empty, or unreadable, fall back to the normal image flow (uploads, generation).

The selection is complete when every requested image slot either has a matching
extracted URL or has been explicitly handed to the normal image flow.
