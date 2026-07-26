import { NextRequest } from 'next/server';

async function handleProxy(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const baseUrl = process.env.PLATFORM_BASE_URL;
  const apiKey = process.env.PLATFORM_API_KEY;

  if (!baseUrl) {
    return new Response(JSON.stringify({ error: 'Missing PLATFORM_BASE_URL' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const resolvedParams = await params;
  const targetPath = (resolvedParams?.path || []).join('/');
  const targetUrl = new URL(`${baseUrl.replace(/\/$/, '')}/${targetPath}`);
  targetUrl.search = req.nextUrl.search;

  try {
    const headers = new Headers();
    req.headers.forEach((value, key) => {
      if (key.toLowerCase() !== 'host') {
        headers.set(key, value);
      }
    });
    
    if (apiKey) {
      headers.set('Authorization', `Bearer ${apiKey}`);
    }

    const fetchOptions: RequestInit = {
      method: req.method,
      headers,
      redirect: 'manual',
    };

    if (req.method !== 'GET' && req.method !== 'HEAD') {
      fetchOptions.body = await req.blob();
    }

    const response = await fetch(targetUrl.toString(), fetchOptions);

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });
  } catch (error) {
    console.error('Proxy error:', error);
    return new Response(JSON.stringify({ error: 'Proxy request failed' }), {
      status: 502,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

export const GET = handleProxy;
export const POST = handleProxy;
