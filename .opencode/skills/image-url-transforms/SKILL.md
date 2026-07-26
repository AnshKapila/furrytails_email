---
name: image-url-transforms
description: >
  Use this skill when code must embed or transform a hosted image URL — for
  example "resize this image", "crop the hero", "trim the logo", "zoom in on
  this photo", or "serve a smaller format". Use `images` when the asset must
  first be found, created, or uploaded from a local file.
mode: sandbox
---

# Hosted image URL transforms

Insert transformation segments between `/upload/` and the asset path:

```text
https://static.kite.ai/image/upload/<segments>/<asset>.<ext>
```

Apply these rules in order:

1. Preserve the original host, asset path, and extension.
2. Add `f_auto,q_auto` once to every transformed Cloudinary URL. It negotiates
   WebP/AVIF and automatic quality while preserving alpha. The platform also
   injects it as a fallback, but author it explicitly so the URL is correct
   before post-processing.
3. Classify the asset from its role in the page, not its filename:
   - A **logo** is a brand mark used as identity chrome. Put `e_trim` in its own
     first segment, then sizing/format transforms:
     `.../upload/e_trim/f_auto,q_auto,h_80/<asset>.png`.
   - A **content image** is photography, illustration, a product shot, or any
     image whose surrounding frame is intentional. Never apply `e_trim`; use
     CSS `object-fit`, `object-position`, container sizing, or `transform:
     scale()` for framing changes.
4. Add `w_<integer>` to content images only when the display width in pixels
   is specified in the markup or CSS.
   Add `c_fill,g_auto` only when the image is cropped to a fixed aspect ratio.
5. Use `g_face` only with an anchoring crop such as `c_fill`, `c_thumb`,
   `c_crop`, `c_lfill`, `c_fill_pad`, `c_auto`, or `c_auto_pad`.

Combine compatible transforms with commas inside one segment. If an existing
URL comma-joins `e_trim` with other transforms (e.g. `e_trim,h_80`), rewrite
it per rule 3: `e_trim/f_auto,q_auto,h_80`. If the user explicitly asks to trim a non-logo,
explain that trim removes intentional edge space and use a framing transform
instead unless they confirm pixel-edge trimming is the intended result.

## Zoom and reframe requests

Zoom requests always resolve through CSS, never through URL transforms — this
overrides every rule above. When the user asks to zoom in or out on a content
or product image ("zoom in a bit", "make it bigger", "zoom out"):

1. **Use CSS, not URL transforms.** Apply `transform: scale(<factor>)` on the
   image's container or adjust `object-fit` / `object-position` on the image
   element. This preserves the original framing the user uploaded.
2. **Keep increments small.** "A bit" or "a little" means ~5–10%
   (`scale(1.05)` to `scale(1.1)`). Never exceed 15% in a single step.
3. **Never use `e_trim`, `c_fit`, or `c_pad` pipelines for zoom.** These strip
   whitespace, re-fit, and re-pad the image, changing the framing far more
   than the user expects.
4. To zoom in, wrap the image in an `overflow-hidden` container and apply
   `scale(>1)`. To zoom out, reduce the container width or apply `scale(<1)`.

## Overlay a hosted asset (exact logo placement)

To place the exact brand logo (or any hosted asset) onto another hosted image
— e.g. a generated social visual that must carry the real logo — compose the
two with a layer transform instead of asking an image model to draw the mark.
Two chained segments: the layer (with its sizing), then `fl_layer_apply` with
the position:

```text
.../upload/l_<layer_public_id>,w_220/fl_layer_apply,g_north_west,x_60,y_60/<base-asset>.png
```

- `l_<layer_public_id>` — the overlay's public ID with every `/` replaced by
  `:` (e.g. `app/<app_id>/brand-logo` → `l_app:<app_id>:brand-logo`).
- Size the layer in its own segment: `w_220` (pixels) or `fl_relative,w_0.2`
  (fraction of the base image's width — prefer this when base sizes vary).
- Position on the `fl_layer_apply` segment: `g_<gravity>` (`north_west`,
  `south_east`, `center`, …) plus optional `x_`/`y_` pixel offsets from that
  corner.
- The composed URL is a normal delivery URL — embed it directly, or re-upload
  the result via the `images` skill's `upload` route if a flat file is needed.
- A wrong layer ID returns `400` — validate the URL responds `200 image/*`
  before embedding, like any other transform.

## Validate before embedding

Before returning or embedding the URL, validate that it contains exactly one
`/upload/`, includes `f_auto,q_auto`, and preserves the original asset path. Do
not use the transformed URL until all three checks pass. A validator ships
with this skill at `scripts/check_urls.py` — run it against a file or
`--url <url>` to confirm a URL is canonical.
