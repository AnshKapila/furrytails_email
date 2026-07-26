import { NextRequest } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const email = body.email;

    if (!email || typeof email !== 'string' || !/^\S+@\S+\.\S+$/.test(email)) {
      return new Response(JSON.stringify({ error: 'Valid email is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const apiKey = process.env.BREVO_API_KEY;
    const listId = process.env.BREVO_LIST_ID;

    if (!apiKey || !listId) {
      console.error('Missing Brevo configuration in environment variables');
      return new Response(JSON.stringify({ error: 'Server misconfigured' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const brevoResponse = await fetch('https://api.brevo.com/v3/contacts', {
      method: 'POST',
      headers: {
        'api-key': apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email,
        listIds: [Number(listId)],
        updateEnabled: true,
      }),
    });

    if (brevoResponse.ok || brevoResponse.status === 201) {
      return new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    } else {
      const errorText = await brevoResponse.text();
      console.error('Brevo API error:', brevoResponse.status, errorText);
      return new Response(JSON.stringify({ error: 'Failed to subscribe' }), {
        status: 502,
        headers: { 'Content-Type': 'application/json' },
      });
    }
  } catch (error) {
    console.error('Subscription error:', error);
    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}
