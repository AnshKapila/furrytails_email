'use client';

/**
 * Global error boundary for the generated Next.js site — catches uncaught render
 * errors that escape the root layout, so it emits its own <html>/<body>.
 *
 * - Editor preview (next dev): the shared "Fix with AI" overlay + parent-frame
 *   contract. DevErrorOverlay covers compile errors (layout stays mounted); this
 *   covers runtime errors, where global-error replaces the layout.
 * - Live site (production): a plain Reload page that reports the error to the
 *   site's analytics provider (pinned by __kiteErrorProvider to match the
 *   backend Errors view; PostHog preferred when unpinned).
 */
import { useEffect, useRef } from 'react';
import {
  ERROR_STYLES,
  ERROR_CONTAINER_HTML,
  APP_RUNTIME_ERROR_EVENT,
  APP_ERROR_DEBUG_EVENT,
  buildErrorDetails,
  reportRuntimeErrorToProvider,
} from '@appsmithorg/template-frontend/error-page';

const IS_PREVIEW = process.env.NODE_ENV !== 'production';
const HIDE_NEXT_OVERLAY = `nextjs-portal { display: none !important; }`;

export default function GlobalError({
  error,
}: {
  error: Error & { digest?: string };
}) {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const details = buildErrorDetails({
      message: error.message,
      stack: error.stack,
      id: error.digest,
    });

    if (IS_PREVIEW) {
      // Editor preview: reveal the overlay and wire the "Fix with AI" contract.
      rootRef.current
        ?.querySelector('#custom-vite-error-overlay')
        ?.classList.add('visible');
      window.parent?.postMessage(
        { type: APP_RUNTIME_ERROR_EVENT, payload: details },
        '*',
      );
      const button = rootRef.current?.querySelector('#debug-button');
      const onDebug = () =>
        window.parent?.postMessage(
          {
            type: APP_ERROR_DEBUG_EVENT,
            payload: {
              message: details.message,
              location: details.location,
              frame: details.frame,
            },
          },
          '*',
        );
      button?.addEventListener('click', onDebug);
      return () => button?.removeEventListener('click', onDebug);
    }

    // Live site: report to the site's analytics provider via the persistent
    // window.posthog / window.pirsch (loaded by the layout — script side effects
    // survive the boundary replacing the DOM). Provider selection + the pin
    // (__kiteErrorProvider) live in the shared package so this boundary and the
    // inline capture script apply one rule.
    reportRuntimeErrorToProvider(details);
  }, [error]);

  // Editor preview: the shared "Fix with AI" overlay.
  if (IS_PREVIEW) {
    return (
      <html lang="en" suppressHydrationWarning>
        <body style={{ margin: 0 }}>
          <style
            dangerouslySetInnerHTML={{
              __html: ERROR_STYLES + HIDE_NEXT_OVERLAY,
            }}
          />
          <div
            ref={rootRef}
            dangerouslySetInnerHTML={{ __html: ERROR_CONTAINER_HTML }}
          />
        </body>
      </html>
    );
  }

  // Live site: a plain, friendly error page with a Reload action.
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        style={{
          margin: 0,
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#fff',
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        }}
      >
        <div
          style={{
            display: 'flex',
            width: 343,
            flexDirection: 'column',
            alignItems: 'center',
            gap: 16,
            textAlign: 'center',
          }}
        >
          <h1 style={{ color: '#171717', fontSize: 16, fontWeight: 500 }}>
            Something went wrong
          </h1>
          <p
            style={{
              color: '#737373',
              fontSize: 14,
              lineHeight: 1.5,
              margin: 0,
            }}
          >
            An unexpected error occurred. Please reload the page to continue.
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              minHeight: 36,
              padding: '8px 16px',
              borderRadius: 8,
              background: '#E15615',
              color: '#fff',
              border: 'none',
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: 500,
            }}
          >
            Reload
          </button>
        </div>
      </body>
    </html>
  );
}
