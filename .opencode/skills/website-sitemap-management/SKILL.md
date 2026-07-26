---
name: website-sitemap-management
description: >
  Use this skill when adding, moving, renaming, or deleting a page or route, or
  adding a redirect — for example "add a pricing page", "move /blog to
  /resources", or "remove this route". Update the sitemap and redirects in the
  same change for both Next.js and legacy HTML sites.
mode: sandbox
---

# Detect the layout first

Choose exactly one target before editing:

1. If a root `next.config.js`, `next.config.ts`, or `next.config.mjs` exists, or
   root `package.json` lists `next` in `dependencies`, select **Next.js** and
   edit only `src/app/sitemap.ts` (Step A). This signal wins even if a legacy
   sitemap file is also present.
2. Otherwise, if `frontend/public/sitemap.xml` exists, select **legacy HTML**
   and edit only that file (Step B).
3. If neither signal exists, stop and report that the sitemap layout cannot be
   identified. Do not create both formats.

Next.js serves `src/app/sitemap.ts` at `/sitemap.xml` automatically. A `public/sitemap.xml` alongside it would be dead code that drifts — leave the route file as the single source of truth.

# Step A — Next.js (`src/app/sitemap.ts`)

## A0 — Create the file if it's missing

If `src/app/sitemap.ts` does not exist (older sandbox, partial migration), create it with this canonical shape before editing — it pulls the base URL from the shared helper and ships the homepage entry. If `src/lib/site-url.ts` is also missing, create that too with the contents shown.

```ts
// src/lib/site-url.ts
export function getBaseUrl(): string {
  const vercel =
    process.env.VERCEL_PROJECT_PRODUCTION_URL ?? process.env.VERCEL_URL;
  if (vercel) return `https://${vercel}`;
  return process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:4321';
}
```

```ts
// src/app/sitemap.ts
import type { MetadataRoute } from 'next';
import { getBaseUrl } from '../lib/site-url';

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = getBaseUrl();
  const lastModified = new Date();

  const staticRoutes: MetadataRoute.Sitemap = [
    {
      url: baseUrl,
      lastModified,
      changeFrequency: 'weekly',
      priority: 1.0,
    },
  ];

  return staticRoutes;
}
```

Then continue to the relevant subsection below.

The sitemap is code, so static routes are listed and data-driven routes are mapped from their data source. Both live in the same file.

## Adding a static page

When a new route lives at `src/app/<slug>/page.tsx`, append one entry to the `staticRoutes` array:

```ts
{
  url: `${baseUrl}/<slug>`,
  lastModified,
  changeFrequency: 'monthly',
  priority: 0.8,
}
```

- Use `${baseUrl}/<slug>` — never a hardcoded origin. The `getBaseUrl()` helper resolves the deploy URL at runtime.
- Reuse the shared `lastModified` constant already defined in the file; do not introduce a per-entry literal date.
- `changeFrequency: 'monthly'` and `priority: 0.8` are the defaults for content pages. The homepage stays at `priority: 1.0` and `changeFrequency: 'weekly'`.

## Adding a dynamic route segment

When a new dynamic route lives at `src/app/<segment>/[<param>]/page.tsx` (e.g. `src/app/blog/[slug]/page.tsx`), drive it from its data source instead of listing each entry by hand:

```ts
import posts from '../../public/content/blog.json';

const blogRoutes: MetadataRoute.Sitemap = posts.map((post) => ({
  url: `${baseUrl}/blog/${post.slug}`,
  lastModified: new Date(post.updatedAt ?? post.publishedAt),
  changeFrequency: 'monthly',
  priority: 0.6,
}));

return [...staticRoutes, ...blogRoutes];
```

- Import from the same JSON file the route's `generateStaticParams` reads. One source of truth — adding a blog post to the JSON updates both the route set and the sitemap.
- If the data source has no per-item timestamp, fall back to the shared `lastModified`.
- Concatenate dynamic groups into the returned array; leave `staticRoutes` unchanged.

## Changing a page's URL

Update the matching `url:` value. The shared `lastModified` already reflects "today".

## Deleting a page

Remove the entry, plus any `import` that was the only consumer of its data source.

# Step B — Legacy HTML (`frontend/public/sitemap.xml`)

Keep `frontend/public/sitemap.xml` in sync with the site's pages, matching the domain used in existing entries. Compute today's date at runtime in `YYYY-MM-DD` form (e.g. `date -u +%Y-%m-%d`) — never hardcode it.

- When **adding** a page, add a `<url>` entry with `<loc>`, `<lastmod>` (today's date), `<changefreq>` (monthly), and `<priority>` (0.8).
- When **changing** a page's URL/path, update the corresponding `<loc>` and set `<lastmod>` to today's date.
- When **deleting** a page, remove its `<url>` entry.

# Redirects (both layouts)

When adding redirects, also add them to `redirects.csv` (columns: source, destination, statusCode, caseSensitive, preserveQueryParams).
Use only these redirect status codes: `301`, `302`, `307`, `308`.

# Verify

- Only the sitemap target selected during layout detection was edited.
- Every live route appears exactly once and every removed route is absent.
- Next.js sitemap code type-checks, or legacy XML parses successfully.
- Each redirect row has all five columns and an allowed status code.
