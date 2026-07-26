---
name: cms-management
description: >
  Use this skill when authoring or editing content, fields, collections, or
  reusable blocks for a generated Next.js site with an embedded CMS — for
  example "change the CMS seed", "add a block type", "add a collection", or
  "fix a field validation error". Also load `nextjs-code-writing` for component
  implementation and `website-visual-design` for styling decisions. Do not use
  it for file-based or single-file HTML sites.
mode: both
---

# cms-management

Generated sites store content in **Payload CMS**, not in route files or
`src/data/*`. Content is authored as one `seed.json` manifest, loaded into the
per-iter Payload schema, and rendered by a baked server component that reads the
Payload Local API and maps each page's `layout` blocks to React components.

Payload is the **single source of truth**. The schema (`src/payload/**`), the
content (`seed.json`), and the components (`src/components/blocks/**`) must agree.
When they drift, the admin rejects the doc, silently drops fields, or the page
crashes. This skill defines the grammar that keeps them in sync and a validator
that **proves** it before the content ships.

## The seed manifest

`seed.json` lives at the iteration root and has this shape:

```json
{
  "siteSettings": { "...": "matches the SiteSettings global" },
  "pages": [{ "slug": "home", "title": "Home", "layout": [ /* blocks */ ] }],
  "collections": { "posts": [{ "slug": "blog/my-post", "title": "My Post" }] }
}
```

- **`siteSettings`** — one object matching the `site-settings` global
  (`src/payload/globals/SiteSettings.ts`): brand, colors, fonts, nav, footer,
  social, contact, default SEO.
- **`pages`** — one entry per route matching the `pages` collection
  (`src/payload/collections/Pages.ts`): `title`, `slug`, `seo`, and an
  ordered `layout` array of blocks.
- **`collections`** (optional) — items for repeating-content collections, keyed
  by collection slug (`{ "<slug>": [docs] }`). Present only when the site
  registers content collections (see **Collections — repeating content** below);
  omit it entirely for sites that don't.

Every field name in the manifest **must** be a field name in the schema. The
admin only renders fields it knows; an unknown key is silently dropped and
uneditable.

## Field grammar

Author values that match each Payload field's type exactly. The library uses:

| Field type | Seed value |
|---|---|
| `text`, `textarea`, `email` | a string |
| `number` | a number |
| `checkbox` | a boolean |
| `select` / `radio` | a string that is one of the field's `options` |
| `group` | an object with the group's sub-fields |
| `array` | an array of objects with the row's sub-fields |
| `blocks` | an array of `{ "blockType": "<slug>", ...fields }` |
| `richText` | a **lexical document** or a **markdown string** (see below) |
| `json` | any JSON value |

### Image and asset fields are text URLs

Images, logos, avatars, and og-images are **plain `text` URL fields holding a
Cloudinary URL** — not Payload uploads. Field names ending in `Url`/`ImageUrl`
carry the resolved CDN URL from the image manifest verbatim. Never invent URLs.

### richText is a lexical document or a markdown string

A `richText` value is either a lexical JSON document shaped `{ "root": { ... } }`
or a **markdown string**. The seed converts a markdown string to lexical at write
time (`markdownDoc`), so the admin still stores and edits real rich text — the
string is a convenience for authoring, not a different storage format.

- For **long-form bodies** (article/podcast bodies with headings, lists, quotes,
  links, bold) author a markdown **string**. `lexicalDoc()` only carries
  plain-text paragraphs and silently drops every other construct, so it is the
  wrong tool for long-form content.
- For short, plain richText, the literal lexical object is fine — see the
  `richText` block in `fixtures/seed.golden.json`.

In TypeScript (a field's `defaultValue`, or any code that builds richText) use
the baked helper rather than hand-writing the node tree:

```ts
import { lexicalDoc } from '@/payload/lexical';
// lexicalDoc('First paragraph.', 'Second paragraph.')
```

### Slug rules

`slug` is the route path without a leading slash. The home page is `home`
(rendered at `/`); every other slug is the URL path (`pricing`, `blog`,
`blog/my-post`). Slugs are unique, lowercase, hyphenated.

## Governed, extensible blocks — the triple

Blocks are the composition primitive and the library is **open**: prefer the
blessed library, but you MAY add a new block type when no existing block fits a
design. A block is a validated **triple** authored as one matched set:

> **block = field schema (`src/payload/blocks/<name>.ts`) + component
> (`src/components/blocks/<Name>.tsx`) + registry entry
> (`RenderBlocks.tsx` `blockComponents` map)** — with identical field and prop
> names.

To add a block, ship all three legs as one matched set:

1. Add the `Block` field schema. In the generation pipeline, custom blocks go in
   `src/payload/blocks/generated.ts` (`generatedBlocks`), with a slug unique from
   the library; elsewhere, under `src/payload/blocks/` included in the relevant
   `blocks` list.
2. Add the React component under `src/components/blocks/`, named `<Pascal(slug)>`
   (slug `storyScroller` → `StoryScroller.tsx`); its props are the block's field
   names exactly (the renderer spreads the stored block onto it).
3. The registry entry in `RenderBlocks.tsx`'s `blockComponents` map. In the
   generation and migration pipelines this leg is written **for you** by a
   deterministic injector (between the sentinel markers in `RenderBlocks.tsx`),
   so you author only the schema + component and never hand-edit the literal map.
   The validator still checks the leg is present (`block-triple`).

The validator checks both halves mechanically: schema↔registry
(`block-triple` errors) and component↔schema prop names (`component-props`
errors — every prop a registered component destructures must be a field of its
block, because the renderer spreads the stored block onto the component and a
drifted prop name renders an empty section). `tsc` against `payload-types.ts`
additionally checks prop types. A schema with no registry entry renders
nothing — that is a blocking error, not a warning.

### Rich fields inside blocks

Blocks may use `group`, `array`, and `richText` fields for real editor
ergonomics (e.g. an array of features, a grouped CTA, a richText body) — not
only flat scalars. Nest them freely; the validator recurses through groups,
arrays, and nested blocks, and the generic renderer handles them.

## Collections — repeating content

`Pages` model singleton page content. **Collections** model repeating items —
blog posts, case studies, testimonials, galleries, changelogs, FAQs, team bios.

**Generation-driven — the template ships none.** A site only gets content
collections when its content is genuinely repeating. A single landing page, a
cafe, a brochure site has no collections — its CMS admin shows just Pages /
Users / Site Settings. Add a collection **only** when the site needs a list of
like items (a blog index, a case-study library, a menu, an events list). When in
doubt, model it as Pages.

**Registering a collection.** Author `src/payload/collections/generated.ts`,
which exports `generatedCollections: CollectionConfig[]`. `payload.config.ts`
spreads this array into `collections`, so every entry becomes a real Payload
collection. Build each entry with the `makeCollection(slug, { fields })` factory
(`src/payload/collectionMeta.ts`); it prepends the standard metadata and applies
consistent admin defaults. Example:

```ts
import type { CollectionConfig } from 'payload';
import { makeCollection } from '../collectionMeta';

export const generatedCollections: CollectionConfig[] = [
  makeCollection('posts', {
    labelSingular: 'Post',
    labelPlural: 'Posts',
    fields: [
      { name: 'excerpt', type: 'textarea' },
      { name: 'body', type: 'richText' },
    ],
  }),
];
```

The generation pipeline regenerates the Payload types from this file, so block
components and the seed are typed against the collections you declare.

**Standard metadata (inference targets).** `makeCollection` gives every item a
stable metadata set so the Collections product's import / metadata-inference /
monitoring engines have a consistent schema to write to — users rarely fill
these by hand: `title`, `slug`, `author`, `publishDate`, `status`
(`draft`/`published`/`needs-attention`), `topicCluster`, `intent`
(`seo`/`conversion`/`awareness`), `seoTitle`, `metaDescription`, `featuredImage`
(URL), `canonicalUrl` (override the self-referential canonical),
`ogImageUrl` (social-share image when it differs from `featuredImage`),
`noindex` (hide the item from search + the sitemap), plus the type-specific
`fields` you pass (e.g. a post's `excerpt` + `body`). This set lives in
`src/payload/collectionMeta.ts` (`collectionMetaFields`).

**Item SEO is handled for you.** The baked catch-all route reads these fields to
emit the item's canonical, og/twitter tags, `noindex`, and Article JSON-LD; the
baked `sitemap.ts` lists every published, non-`noindex` item. Populate
`seoTitle`/`metaDescription`/`featuredImage` (and `canonicalUrl`/`ogImageUrl`
when they should differ); never author per-item `<head>` markup.

**Seeding items.** Seed each collection's docs under the `collections` key of
`seed.json` (`{ "<slug>": [docs] }`), keyed by the same slug you registered.
Items are validated exactly like pages (structural + Local-API).

**Listing + item primitives.**
- The `collectionList` block renders a live grid of a collection's published
  items (newest first). Bind it by setting its `collection` field to the
  collection's slug — that slug **must** match a collection you registered in
  `generated.ts`, or the validator fails (`unknown-collection`). It queries
  Payload at render time, so the listing never duplicates item content in the
  seed. It also **facets**: set `filterByTag` to restrict the grid to one
  `topicCluster`, `showTagFilter` to render a server-rendered tag bar (visitors
  filter via `?tag=` links, no client JS), and `sortBy`
  (`publishDate`/`title`).
- The `relatedItems` block renders items from a collection sharing a reference
  item's `topicCluster` — set `collection` and `fromSlug` (the reference item's
  slug). Used for "related posts"/"more episodes" surfaces.
- The baked catch-all route renders each published item via the per-collection
  **item registry** at `/<slug>` (e.g. a post with slug `blog/my-post` renders at
  `/blog/my-post`). A collection without a custom layout uses the neutral
  `DefaultItemLayout` (article-shaped: `title`, `publishDate`, `featuredImage`,
  `body`); non-article collections still render the fields they have.

**Rich-media library blocks.** Beyond the layout blocks, the library includes
`audioEmbed` (an audio/track player from a provider `embedUrl`) and `peopleList`
(a people grid — team members, speakers, guests, contributors). Prefer these for
audio and people-listing content rather than authoring a custom block.

**Custom per-collection item layouts — the item triple.** This is the block
triple's pattern applied to a collection's detail page: the same author-the-leaves,
injected-registry mechanism, keyed by collection instead of blockType. When a
content type needs a bespoke detail page (an article layout with an author block
and a related sidebar, a podcast layout with an audio player and guests), author a
custom layout as a matched triple:

> **item layout = collection schema (`generated.ts`) + component
> (`src/components/collections/<Pascal(slug)>Layout.tsx`) + RenderItem entry** —
> with the component's prop names equal to the collection's field names.

1. Register the collection in `generated.ts` with the fields the layout needs.
2. Author `src/components/collections/<Pascal(slug)>Layout.tsx` (slug `posts` →
   `PostsLayout.tsx`). Its props are the collection's field names exactly, plus
   two renderer-injected props: `collection` (the slug) and `related` (an array
   of same-`topicCluster` items, for a sidebar). Type props against the
   collection's generated interface (`import type { Post } from '@/payload-types'`).
3. The `RenderItem.tsx` registry entry is written **for you** by the deterministic
   injector — never hand-edit it. The validator checks the layout's props match
   the collection's fields (`item-triple`).

Reach for a custom layout when a type's detail page is genuinely bespoke;
otherwise the default layout and a `collectionList` index are enough.

Only the data-model + schema standards live here. Import pipelines, the metadata
inference engine, AI search, related-content, and performance monitoring are
separate tracks this schema targets but does not implement.

## Admin ergonomics standards

The admin panel is the editing surface, so author schemas that are pleasant to
edit:

- **Image fields use `imageUrlField()`** (`src/payload/fields.ts`), which wires
  the `ImagePreview` thumbnail (`src/admin/ImagePreview.tsx`) via
  `admin.components.afterInput`. Use it for every logo/avatar/og-image/image URL
  so editors see the image, not just a string. After adding a custom admin
  component, run `pnpm generate:importmap`.
- **`admin.hideAPIURL: true`** on collections and globals — the API URL is noise
  for content editors.
- **Labels** via the field's `label` for any name whose role is not obvious
  (e.g. `OG Image URL`), and `group` fields to cluster related fields.
- **richText `defaultValue`** via `lexicalDoc()` so a new richText field opens to
  a valid empty document, not a broken/null editor.
- **Live Preview** is configured (`admin.livePreview`, `collections: ['pages']`)
  with responsive breakpoints; it renders the page same-origin in the admin.

## The three fit invariants

Generated content is proven to fit the admin when all three hold. The validator
checks them mechanically:

1. **Schema is valid** — `@payload-config` loads. The admin can render it.
2. **Content is structural** — every seed value matches the field shape *derived
   from the live config* (types, required, select options, block discrimination),
   plus a bidirectional orphan-key check: no content key is missing from the
   schema, and no required field is missing from the content.
3. **Content is semantic** — each doc is accepted by Payload's Local API in a
   rolled-back transaction (the same write-time validation the admin runs). This
   layer runs only when `APP_DATABASE_URL` is set; it is skipped, not failed,
   otherwise.

## Run the validator before finishing

From the iteration directory (the one holding `src/payload.config.ts` and
`seed.json`) — the skill tree is staged under this run dir, not the app root:

```bash
pnpm exec tsx .opencode/skills/cms-management/scripts/validate_cms.mjs seed.json
```

It prints one line of JSON and exits non-zero on any blocking fit error:

```json
{ "ok": false, "invariants": { "schema": "pass", "structure": "fail", "semantic": "skipped" },
  "errors": [ { "path": "pages[0].layout[0].heading", "kind": "missing-required",
                "hint": "required field \"heading\" is missing from the content." } ] }
```

Read `errors[].path` and `errors[].hint`, repair `seed.json` (or the block
schema/component/registry), and re-run until `ok` is `true`. Error kinds:
`missing-required`, `orphan-key`, `type-mismatch`, `unknown-block`,
`block-triple`, `component-props`, `item-triple` (a custom item layout's props
drift from its collection's fields, or it is registered for an unregistered
collection), `unknown-global`/`unknown-collection`, `no-raw-html` (a route was
dumped into a raw-HTML field instead of decomposed into blocks — replace it with
editable blocks), `config-load`, `semantic`.

A worked example of a valid manifest is `fixtures/seed.golden.json`.
