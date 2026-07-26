import type { MetadataRoute } from 'next';
import { getBaseUrl } from '../lib/site-url';

// Next.js serves this at `/robots.txt` automatically. Emitted from code so
// the `Sitemap:` directive can be an absolute URL — sitemaps.org and Google
// both silently ignore relative `Sitemap:` lines, so a static
// `public/robots.txt` saying `Sitemap: /sitemap.xml` would not actually
// register the sitemap with crawlers.

// Major AI crawlers and agent user-agents, named explicitly so the site
// declares an AI-bot policy instead of leaving agents to infer one from `*`
// (the "AI bot rules" agent-readiness check). Same policy as `*` — these
// sites want AI visibility. Adjust only when the user asks to restrict AI
// access (see the `website-agent-readiness` skill).
const AI_CRAWLERS = [
  'GPTBot',
  'OAI-SearchBot',
  'ChatGPT-User',
  'ClaudeBot',
  'Claude-User',
  'Claude-SearchBot',
  'PerplexityBot',
  'Perplexity-User',
  'Google-Extended',
  'Applebot-Extended',
  'Meta-ExternalAgent',
  'Amazonbot',
  'DuckAssistBot',
  'CCBot',
];

export default function robots(): MetadataRoute.Robots {
  const baseUrl = getBaseUrl();
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: '/api/',
      },
      {
        userAgent: AI_CRAWLERS,
        allow: '/',
        disallow: '/api/',
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
