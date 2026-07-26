'use client';

/**
 * Dev-only error overlay for the preview. Next has no API to disable its dev
 * error overlay, so we hide it and show the shared friendly overlay instead —
 * the Next.js analog of the Vite build-error-overlay. Both compile and runtime
 * errors surface through Next's <nextjs-portal>; we poll for it, reveal the
 * custom overlay, and wire "Fix with AI" to the parent editor.
 *
 * Errors are attributed to the app vs. external sources (browser extensions,
 * injected scripts) before mirroring — see APP_FRAME_RE below. Hydration
 * mismatches never mirror at all — see HYDRATION_RE.
 */
import { useEffect, useRef } from 'react';
import {
  ERROR_STYLES,
  ERROR_CONTAINER_HTML,
  APP_RUNTIME_ERROR_EVENT,
  APP_ERROR_DEBUG_EVENT,
  buildErrorDetails,
} from '@appsmithorg/template-frontend/error-page';

const HIDE_NEXT_OVERLAY = `nextjs-portal { display: none !important; }`;
// Marks an error portal (vs. other nextjs-portal uses) inside its shadow root.
const ERROR_MARKER = '[data-nextjs-dialog-overlay], [data-nextjs-dialog]';

// Next's dev overlay opens for ANY uncaught error or console.error on the
// page, including ones thrown by browser extensions (React DevTools, Arc
// boosts, …). Mirroring those as "Whoops, fix with AI" tells the user their
// site broke when it didn't. App code in `next dev` always executes from
// same-origin /_next/ chunks, so an error whose stack has no app frame
// cannot come from the app. Classification fails open: only positively
// external errors are suppressed.
const APP_FRAME_RE = /\/_next\/|webpack-internal:|rsc:\/\//;
// How long a classified error vouches for (or against) a portal appearance.
const ATTRIBUTION_WINDOW_MS = 3000;

// Hydration mismatches are recoverable by design: React discards the server
// HTML and re-renders on the client, so the site still works. In the preview
// they are almost always browser extensions or the iframe host mutating the
// DOM before React hydrates (Grammarly, dark-mode, translators) — stack
// attribution can't catch them because React throws from /_next/ chunks.
// Never mirror them; genuine generation-time hydration bugs are caught by
// the verify pipeline in a clean browser. Patterns cover React 18/19 dev
// messages plus minified codes (#418/#423/#425).
const HYDRATION_RE =
  /hydration failed|error while hydrating|error occurred during hydration|tree hydrated but|server rendered html didn't match|minified react error #(?:418|423|425)/i;

type ErrorSource = 'app' | 'external' | 'unknown';

function classifyFrames(stack: string, dropFirstFrame: boolean): ErrorSource {
  const frames = stack
    .split('\n')
    .filter((l) => /^\s*at |@/.test(l))
    .slice(dropFirstFrame ? 1 : 0);
  if (frames.length === 0) return 'unknown';
  return frames.some((f) => APP_FRAME_RE.test(f)) ? 'app' : 'external';
}

export default function DevErrorOverlay() {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const overlay = rootRef.current?.querySelector(
      '#custom-vite-error-overlay',
    );
    const debugButton = rootRef.current?.querySelector('#debug-button');
    if (!overlay) return;

    let latest = { message: '', location: '', frame: '' };
    let shown = false;
    let lastAppErrorAt = 0;
    let lastExternalErrorAt = 0;

    const recordError = (source: ErrorSource) => {
      if (source === 'app') lastAppErrorAt = Date.now();
      else if (source === 'external') lastExternalErrorAt = Date.now();
    };

    // Classify at the source, before Next's interceptors: full unfiltered
    // stacks here vs. the truncated, ignore-listed ones in the portal DOM.
    const onWindowError = (e: ErrorEvent) => {
      // React reports recoverable hydration errors via reportError → window
      // 'error'; don't let them vouch for an unrelated portal as app errors.
      if (HYDRATION_RE.test(`${e.message || ''} ${e.error?.message || ''}`))
        return;
      recordError(
        classifyFrames(`${e.filename || ''}\n${e.error?.stack || ''}`, false),
      );
    };
    const onRejection = (e: PromiseRejectionEvent) =>
      recordError(
        classifyFrames(String((e.reason as Error)?.stack || ''), false),
      );
    window.addEventListener('error', onWindowError);
    window.addEventListener('unhandledrejection', onRejection);

    const originalConsoleError = console.error;
    console.error = (...args: unknown[]) => {
      originalConsoleError.apply(console, args);
      try {
        const text = args
          .map((a) => (a instanceof Error ? a.message : String(a)))
          .join(' ');
        if (HYDRATION_RE.test(text)) return;
        const errorArg = args.find((a): a is Error => a instanceof Error);
        // Prefer the logged Error's own stack; otherwise probe the caller,
        // dropping the first frame — it is this wrapper, which itself lives
        // in a /_next/ chunk.
        recordError(
          errorArg?.stack
            ? classifyFrames(errorArg.stack, false)
            : classifyFrames(new Error().stack || '', true),
        );
      } catch {
        // Classification must never break console.error.
      }
    };

    const onDebug = () =>
      window.parent?.postMessage(
        { type: APP_ERROR_DEBUG_EVENT, payload: latest },
        '*',
      );
    debugButton?.addEventListener('click', onDebug);

    const findErrorPortal = (): Element | null => {
      for (const p of Array.from(document.querySelectorAll('nextjs-portal'))) {
        if ((p as HTMLElement).shadowRoot?.querySelector(ERROR_MARKER))
          return p;
      }
      return null;
    };

    const extract = (portal: Element) => {
      const sr = (portal as HTMLElement).shadowRoot;
      const message =
        sr?.querySelector('[data-nextjs-dialog-header]')?.textContent?.trim() ||
        sr?.querySelector('h1, h2')?.textContent?.trim() ||
        'Application error';
      return buildErrorDetails({ message: message.slice(0, 300) });
    };

    // Decide whether the portal's error deserves the friendly overlay.
    // Build errors come from the compiler and are always ours. Otherwise:
    // a recent app-attributed error, or no attribution at all, shows the
    // overlay (fail open); only a positively external attribution skips it.
    const shouldMirror = (portal: Element) => {
      const sr = (portal as HTMLElement).shadowRoot;
      const header =
        sr?.querySelector('[data-nextjs-dialog-header]')?.textContent || '';
      if (header.includes('Build Error')) return true;
      const now = Date.now();
      if (now - lastAppErrorAt < ATTRIBUTION_WINDOW_MS) return true;
      return now - lastExternalErrorAt >= ATTRIBUTION_WINDOW_MS;
    };

    // Next reuses one portal and toggles its shadow content, so poll rather
    // than rely on light-DOM mutations (which miss shadow-root changes).
    let suppressed = false;
    const sync = () => {
      const portal = findErrorPortal();
      if (!portal) {
        suppressed = false;
        if (shown) {
          shown = false;
          overlay.classList.remove('visible');
        }
        return;
      }
      if (shown) return;
      // A hydration dialog never mirrors — React already recovered (see
      // HYDRATION_RE). Re-checked every tick rather than latched: Next
      // reuses the portal, so a real error replacing the dialog content
      // re-enters the normal flow below.
      if (
        HYDRATION_RE.test((portal as HTMLElement).shadowRoot?.textContent || '')
      )
        return;
      if (suppressed) {
        // Suppression is sticky for this portal appearance, but a later
        // app-attributed error can still claim the open dialog.
        if (Date.now() - lastAppErrorAt >= ATTRIBUTION_WINDOW_MS) return;
        suppressed = false;
      } else if (!shouldMirror(portal)) {
        suppressed = true;
        return;
      }
      shown = true;
      const details = extract(portal);
      latest = {
        message: details.message,
        location: details.location,
        frame: details.frame,
      };
      window.parent?.postMessage(
        { type: APP_RUNTIME_ERROR_EVENT, payload: details },
        '*',
      );
      overlay.classList.add('visible');
    };

    const interval = window.setInterval(sync, 400);
    sync();

    return () => {
      window.clearInterval(interval);
      debugButton?.removeEventListener('click', onDebug);
      window.removeEventListener('error', onWindowError);
      window.removeEventListener('unhandledrejection', onRejection);
      console.error = originalConsoleError;
    };
  }, []);

  return (
    <>
      <style
        dangerouslySetInnerHTML={{ __html: ERROR_STYLES + HIDE_NEXT_OVERLAY }}
      />
      <div
        ref={rootRef}
        dangerouslySetInnerHTML={{ __html: ERROR_CONTAINER_HTML }}
      />
    </>
  );
}
