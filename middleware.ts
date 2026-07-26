import { NextResponse } from 'next/server';

// Pass-through middleware. Previously re-exported
// ``@appsmithorg/template-shared/middleware`` (a prerender-for-bots
// helper), but that file uses ``return fetch(req)`` for the pass-through
// case, which loops back through Vercel's edge into middleware again →
// 508 INFINITE_LOOP_DETECTED on the Next.js pipeline. Legacy apps were
// rescued by ``next.config.js``'s rewrite to ``/prototype.html`` (a
// static file that bypasses middleware re-entry); the Next.js pipeline
// has no such rewrite.
//
// Re-enable prerender once the upstream package is fixed to use
// ``NextResponse.next()`` for pass-through.
export default function middleware() {
  return NextResponse.next();
}
