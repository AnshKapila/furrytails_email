import type { MetadataRoute } from 'next';
import { getBaseUrl } from '../lib/site-url';

// Next.js serves this at `/sitemap.xml` automatically. Agents extend it as
// pages are added: static routes go in `staticRoutes`, data-driven routes
// (blog posts, product pages, anything keyed off a JSON file in
// `public/content/`) are mapped programmatically so they stay in sync with
// the data without a separate edit.

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

  // Dynamic route example — uncomment and adapt when the app gains a
  // data-driven route segment such as `src/app/blog/[slug]/page.tsx`:
  //
  // import posts from '../../public/content/blog.json';
  // const dynamicRoutes: MetadataRoute.Sitemap = posts.map((post) => ({
  //   url: `${baseUrl}/blog/${post.slug}`,
  //   lastModified: new Date(post.updatedAt),
  //   changeFrequency: 'monthly',
  //   priority: 0.6,
  // }));
  // return [...staticRoutes, ...dynamicRoutes];

  return staticRoutes;
}
