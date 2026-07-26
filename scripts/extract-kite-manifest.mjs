/**
 * Kite analytics manifest extractor (generation-time, deterministic, real AST).
 *
 * Replaces the deploy-time Python regex over JSX. The generation/edit agent
 * authors `data-kite-*` stamps onto the components it writes (see the
 * `nextjs-code-writing` skill); this script parses those .tsx with the
 * TypeScript compiler API (a REAL JSX AST, not a regex) and emits the analytics
 * manifest the backend persists into `site_event_catalog`.
 *
 * Why an AST and not a regex: a `>` inside an attribute value (a Tailwind class
 * `[&>svg]`, an `aria-label`, an href query, a `{x > 1 ? ...}` expression, a
 * nested-brace expression) is just attribute text to a real parser and can never
 * truncate a tag — the entire class of "stamp silently dropped" bugs disappears.
 * (The MANIFEST is AST-derived; a few warn-only detectors — spread stamps, the
 * hook-call pairing, non-.tsx stamp mentions — are deliberate substring
 * heuristics over source text, not AST analyses.)
 * The tree also gives true page->surface->cta nesting (vs the old source-order
 * guess) and exposes `{expression}` values so a dynamic stamp becomes a
 * repairable diagnostic instead of a silent omission.
 *
 * Plain ESM JavaScript (not TypeScript) run with `node` — no tsx/ts-node needed,
 * so it works from a frozen `pnpm install` in the sandbox. Its only dependency is
 * the `typescript` compiler package (a pinned devDependency of this template),
 * loaded at runtime via createRequire; the script itself ships no types.
 *
 * Contract (mirrors cms-content/validate_cms.mjs so generate_files.py can run it
 * the same way): prints exactly ONE line of JSON to stdout and exits
 *   0  -> ok, manifest emitted
 *   1  -> blocking stamp defect(s) the agent must repair
 *   2  -> usage error (bad args)
 * Resolves `typescript` from process.cwd() (the iteration dir), so it works
 * wherever the script file physically lives.
 *
 * Usage:  node scripts/extract-kite-manifest.mjs <src-dir> [--out <file>]
 *   <src-dir>   directory to scan recursively for *.tsx (e.g. "src")
 *   --out FILE  also write the manifest JSON to FILE (e.g. kite-manifest.json)
 *
 * KEEP IN SYNC with public/kite-analytics.js: the event NAME this records for
 * each stamp must equal what that SDK fires at runtime, so the catalog and the
 * live events agree.
 *
 * Structure: main() is CLI wiring around two top-level engines —
 * scanSourceTree() (walks files, fills a Collector via recordStamp()'s named
 * per-concern steps) and assembleManifest() (turns a defect-free scan into the
 * manifest JSON).
 */
import { createRequire } from 'node:module';
import * as fs from 'node:fs';
import * as path from 'node:path';

// Resolve the TS compiler from the iteration dir's node_modules (cwd), not from
// wherever this script lives — same resolution strategy as validate_cms.mjs.
const require = createRequire(path.join(process.cwd(), 'noop.js'));
const ts = require('typescript');

const SCHEMA_VERSION = '2.1';

// ---- event naming -----------------------------------------------------------

/**
 * The event NAME the runtime SDK fires when an element has no explicit
 * `data-kite-event` — its kind/conversion machine fallback. MUST mirror
 * public/kite-analytics.js: conversions fire `<goalType>_completed` when a goal
 * type is known (else the literal `goal_completed` no-goal-type fallback);
 * otherwise nav -> `nav_clicked`, form -> `form_submitted`, expand ->
 * `content_expanded`, cta -> `cta_clicked`. (`data-kite-event` is required by
 * the prompt, so this is the out-of-grammar fallback; recording the SDK's value
 * keeps the catalog truthful.)
 */
function machineEvent(kind, isConversion, goalType) {
  if (isConversion)
    return goalType ? `${goalType}_completed` : 'goal_completed';
  switch (kind) {
    case 'nav':
      return 'nav_clicked';
    case 'form':
      return 'form_submitted';
    case 'expand':
      return 'content_expanded';
    default:
      return 'cta_clicked';
  }
}

/**
 * The event name recorded for a stamp: the authored `data-kite-event` when
 * present, else the kind's machine fallback. Nav links fire a fixed
 * `nav_clicked` at runtime (the SDK uses the nav id as a property, not the
 * event name) — record that so the catalog matches what actually lands in
 * PostHog. Conversion outranks nav: the SDK's onClick fires the goal event for
 * a non-form conversion element and RETURNS before the nav handler
 * (kite-analytics.js onClick), so a nav link that is also a conversion (e.g. a
 * footer mailto stamped data-kite-conversion) never emits nav_clicked at
 * runtime — record the goal's name, not nav_clicked.
 */
function resolveEventName(kind, isConversion, goalType, eventAttr) {
  const authored = eventAttr && eventAttr.value ? eventAttr.value : null;
  if (isConversion) return authored ?? machineEvent(kind, true, goalType);
  if (kind === 'nav') return 'nav_clicked';
  return authored ?? machineEvent(kind, false, goalType);
}

// ---- AST attribute reading ---------------------------------------------------

/** Iterate an element's plain JSX attributes as [name, prop] pairs — the one
 * shared guard (skip spreads and nameless nodes) every attribute reader builds
 * on. */
function* jsxAttrs(el, sf) {
  for (const prop of el.attributes.properties) {
    if (ts.isJsxAttribute(prop) && prop.name) {
      yield [prop.name.getText(sf), prop];
    }
  }
}

/** Read a JSX attribute as a static string literal. dynamic=true for {expr}.
 * Returns { value, dynamic } or null when the attribute is absent. */
function readAttr(el, name, sf) {
  for (const [attrName, prop] of jsxAttrs(el, sf)) {
    if (attrName !== name) continue;
    const init = prop.initializer;
    if (init === undefined) return { value: '', dynamic: false }; // bare attr: name only
    if (ts.isStringLiteral(init)) return { value: init.text, dynamic: false };
    if (ts.isJsxExpression(init)) {
      const e = init.expression;
      // A string-literal or no-substitution template inside {} is still static.
      if (
        e &&
        (ts.isStringLiteral(e) || ts.isNoSubstitutionTemplateLiteral(e))
      ) {
        return { value: e.text, dynamic: false };
      }
      return { value: null, dynamic: true };
    }
    return { value: null, dynamic: true };
  }
  return null;
}

/** Raw initializer text of a JSX attribute (any form — string, expression,
 * template literal), or null when absent. Used where the VALUE may be dynamic
 * but its text still carries signal (e.g. an href template containing
 * "mailto:"). */
function readAttrRawText(el, name, sf) {
  for (const [attrName, prop] of jsxAttrs(el, sf)) {
    if (attrName !== name) continue;
    return prop.initializer ? prop.initializer.getText(sf) : '';
  }
  return null;
}

// The success-hook call the SDK contract requires when an element is stamped
// data-kite-conversion-hook (the SDK skips goal emission on submit AND click
// and waits for this call). Text-level signature on purpose: the taught form is
// `window.__kite && window.__kite.conversion('...')` — but agents legitimately
// write the optional-chained `window.__kite?.conversion('...')` too, so the
// pattern accepts both. Missing the call here raises a BLOCKING
// unpaired_conversion_hook, so a false negative would fail a correct site.
const CONVERSION_CALL_PATTERN = /__kite\??\.conversion\(/;

// Event names follow `{object}_{past-tense verb}` (signup_completed,
// plan_selected) — the convention of the whole closed vocabulary and standard
// instrumentation guides. Heuristic: the final segment ends in "ed" or is a
// common irregular past form. A rough lint, not grammar: it false-accepts
// present-tense "-ed" words (proceed, feed, embed) — acceptable because the
// check is warn-only and those rarely end an event name.  Imperative names
// (contact_us, inquire_purchase) still work at runtime but read as commands.
const IRREGULAR_PAST = new Set([
  'sent',
  'done',
  'made',
  'given',
  'shown',
  'seen',
  'met',
  'left',
  'paid',
  'sold',
  'bought',
  'built',
  'found',
  'won',
  'kept',
  'begun',
  'chosen',
  'set',
  'put',
]);
function isPastTenseName(name) {
  const last = name.split('_').pop();
  return last.length > 2 && (last.endsWith('ed') || IRREGULAR_PAST.has(last));
}

function hasAnyKiteAttr(el, sf) {
  for (const [attrName] of jsxAttrs(el, sf)) {
    if (attrName.startsWith('data-kite-')) return true;
  }
  return false;
}

// ---- shared shapes and helpers -------------------------------------------------
//
// Shapes (plain objects, documented for readers — no static types):
//   Cta     { cta_id, kind: 'cta'|'nav'|'form'|'expand', role?, event,
//             is_conversion, goal_type?, href?, page_id|null, surface_id|null }
//   Surface { surface_id, surface_type?, position, page_id|null }
//   PageMeta{ page_id, page_type? }
//   Diag    { path, line, kind, hint }
//   Ctx     { page: string|null, surface: string|null, form: Cta|null }

function lineOf(node, sf) {
  return sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1;
}

// Only .tsx is AST-extracted; the other extensions are text-scanned for the
// conversion-call signature (a form's success handler may live in a lib file)
// and for stray data-kite- stamps the AST pass would silently miss.
const SOURCE_EXTS = ['.tsx', '.ts', '.jsx', '.js'];

/** Recursively list source files under `dir`, sorted for deterministic order. */
function sourceFiles(dir) {
  const out = [];
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const e of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...sourceFiles(full));
    else if (e.isFile() && SOURCE_EXTS.some((ext) => e.name.endsWith(ext)))
      out.push(full);
  }
  return out;
}

/** Project a collected CTA down to the manifest's public shape (drops nulls). */
function publicCta(c) {
  const o = {
    cta_id: c.cta_id,
    kind: c.kind,
    event: c.event,
    is_conversion: c.is_conversion,
    surface_id: c.surface_id,
  };
  if (c.role !== undefined) o.role = c.role;
  if (c.href !== undefined) o.href = c.href;
  if (c.goal_type !== undefined) o.goal_type = c.goal_type;
  if (c.conversion_medium !== undefined)
    o.conversion_medium = c.conversion_medium;
  return o;
}

/** A surface entry with its in-scope CTAs nested. Every registered surface is
 * emitted (it fires section_viewed/section_engaged on its own), not only those
 * that contain a CTA. */
function surfaceEntry(s, scopeCtas) {
  const e = { surface_id: s.surface_id, position: s.position };
  if (s.surface_type !== undefined) e.surface_type = s.surface_type;
  e.ctas = scopeCtas
    .filter((c) => c.surface_id === s.surface_id)
    .map(publicCta);
  return e;
}

// ---- collection engine ---------------------------------------------------------
//
// scanSourceTree() walks every source file and fills a Collector — the single
// mutable state of the scan. recordStamp() is the per-element orchestration;
// each concern is a named step below it, a plain function of (collector,
// element, context) so a new rule gets its own home instead of growing an
// inline block.

function newCollector() {
  return {
    surfaces: new Map(), // surface_id -> Surface (dedupe, ordered)
    pages: new Map(), // page_id -> PageMeta (ordered)
    ctas: [],
    errors: [],
    warnings: [], // non-blocking Diags, surfaced in generation output
    conversionHooks: [], // {path, line} of data-kite-conversion-hook stamps
    sawHookedConversionForm: false, // hook + conversion + form-type on one element
    sawConversionCall: false, // any scanned file contains __kite.conversion(
    namingWarned: new Set(), // event names already warned (dedupe loop renders)
    // Dedupe identical stamps (loop-rendered) by page+surface+kind+id+event;
    // flag same kind+id with a DIFFERENT event as an ambiguous-identity defect.
    seen: new Set(),
    idToEvent: new Map(), // `${kind}:${id}` -> first event
  };
}

/** Any dynamic data-kite-* value is a blocking defect (the catalog needs a
 * stable literal; the SDK fires the literal too). Scans the element's ACTUAL
 * attributes by prefix — not a hand-maintained name list, which silently
 * exempts any newly added attribute from this gate. `data-kite-item` is the
 * one deliberate exception (a per-item property that MUST be dynamic). */
function checkDynamicStamps(col, el, sf, relPath) {
  for (const [attrName] of jsxAttrs(el, sf)) {
    if (!attrName.startsWith('data-kite-') || attrName === 'data-kite-item')
      continue;
    const a = readAttr(el, attrName, sf);
    if (a && a.dynamic) {
      col.errors.push({
        path: relPath,
        line: lineOf(el, sf),
        kind: 'dynamic_stamp',
        hint: `${attrName} must be a static string literal (e.g. ${attrName}="value"), not a {expression}, so the analytics catalog and the runtime SDK agree on a stable value.`,
      });
    }
  }
}

/** Conversion-hook stamp: the SDK will NOT fire the goal on submit for this
 * element — record it so the hook/call pairing can be verified site-wide. */
function recordConversionHook(col, el, sf, relPath) {
  if (readAttr(el, 'data-kite-conversion-hook', sf) === null) return;
  col.conversionHooks.push({ path: relPath, line: lineOf(el, sf) });
  // The SDK's form_submitted ATTEMPT fires only when a submitted
  // data-kite-form-type form resolves a conversion element (onSubmit); a
  // hook on a non-form conversion (a JS widget button) never produces a
  // submit, so cataloging form_submitted for it would be a phantom event.
  // Detect the canonical stamped shape: hook + conversion + form-type on
  // ONE element (the grammar puts all three on the <form>).
  if (
    readAttr(el, 'data-kite-conversion', sf) !== null &&
    readAttr(el, 'data-kite-form-type', sf) !== null
  ) {
    col.sawHookedConversionForm = true;
  }
}

/** Page root. Returns the attribute read so recordStamp derives `own.page`
 * from the same single read. */
function registerPage(col, el, sf) {
  const pageId = readAttr(el, 'data-kite-page-id', sf);
  if (pageId && pageId.value && !col.pages.has(pageId.value)) {
    const meta = { page_id: pageId.value };
    const pt = readAttr(el, 'data-kite-page-type', sf);
    if (pt && pt.value) meta.page_type = pt.value;
    col.pages.set(pageId.value, meta);
  }
  return pageId;
}

/** Surface. Returns the attribute read (same single-read rule as
 * registerPage). */
function registerSurface(col, el, sf, ctx) {
  const surfaceId = readAttr(el, 'data-kite-surface', sf);
  if (surfaceId && surfaceId.value && !col.surfaces.has(surfaceId.value)) {
    const entry = {
      surface_id: surfaceId.value,
      position: col.surfaces.size,
      // A surface fires section_viewed/section_engaged on its own; record the
      // page it lives under so it is emitted even when it holds no CTA.
      page_id: ctx.page,
    };
    const stype = readAttr(el, 'data-kite-surface-type', sf);
    if (stype && stype.value) entry.surface_type = stype.value;
    col.surfaces.set(surfaceId.value, entry);
  }
  return surfaceId;
}

/** Interaction identity (CTA / nav / form / expand), or null when the element
 * carries no interaction stamp. */
function resolveKindAndId(el, sf) {
  const ctaId = readAttr(el, 'data-kite-cta-id', sf);
  if (ctaId && ctaId.value) return { kind: 'cta', id: ctaId.value };
  const navId = readAttr(el, 'data-kite-nav', sf);
  if (navId && navId.value) return { kind: 'nav', id: navId.value };
  const formType = readAttr(el, 'data-kite-form-type', sf);
  if (formType && formType.value) return { kind: 'form', id: formType.value };
  const expandId = readAttr(el, 'data-kite-expand', sf);
  if (expandId && expandId.value) return { kind: 'expand', id: expandId.value };
  return null;
}

/** Conversion marking. Empty data-kite-conversion="" is a defect, not a
 * conversion. */
function resolveConversion(col, el, sf, relPath) {
  const conversion = readAttr(el, 'data-kite-conversion', sf);
  if (!conversion) return { isConversion: false, goalType: undefined };
  if (!conversion.value) {
    col.errors.push({
      path: relPath,
      line: lineOf(el, sf),
      kind: 'empty_conversion',
      hint: 'data-kite-conversion must name the goal (e.g. data-kite-conversion="signup"); remove it if this element is not the conversion.',
    });
    return { isConversion: false, goalType: undefined };
  }
  return { isConversion: true, goalType: conversion.value };
}

/** Warn-only naming lint on authored (non-nav) event names. */
function lintEventName(col, el, sf, relPath, kind, eventAttr) {
  if (kind === 'nav' || !eventAttr || !eventAttr.value) return;
  if (isPastTenseName(eventAttr.value) || col.namingWarned.has(eventAttr.value))
    return;
  col.namingWarned.add(eventAttr.value);
  col.warnings.push({
    path: relPath,
    line: lineOf(el, sf),
    kind: 'event_name_not_past_tense',
    hint: `data-kite-event "${eventAttr.value}" is not {object}_{past-tense verb}. Name what HAPPENED, not the button label: e.g. "contact_us" -> "contact_requested", "inquire_purchase" -> "purchase_inquiry_sent".`,
  });
}

/** Dedup + global identity uniqueness. Returns false when the stamp must not
 * be recorded (an identical loop-rendered repeat, or a defect just reported).
 *
 * Dedup is scoped to page+surface: identical stamps in the SAME slot are a
 * loop render (collapse to one); the SAME id+event legitimately placed on a
 * different page/surface is a distinct placement and is kept under each.
 * Identity is global: one kind+id must map to exactly one event name across
 * the whole site, regardless of where it is placed. */
function validateIdentity(col, el, sf, relPath, facts) {
  const { kind, id, name, elPage, elSurface } = facts;
  const dedupeKey = `${elPage ?? ''}:${elSurface ?? ''}:${kind}:${id}:${name}`;
  if (col.seen.has(dedupeKey)) return false; // identical stamp repeated (loop render)
  const idKey = `${kind}:${id}`;
  const prior = col.idToEvent.get(idKey);
  if (prior !== undefined && prior !== name) {
    col.errors.push({
      path: relPath,
      line: lineOf(el, sf),
      kind: 'duplicate_identity',
      hint: `${kind} id "${id}" is used for two different events ("${prior}" and "${name}"); give each distinct action a distinct id.`,
    });
    return false;
  }
  col.seen.add(dedupeKey);
  col.idToEvent.set(idKey, name);
  return true;
}

/** How the goal completes. A form submit is a verifiable OUTCOME; a
 * mailto:/tel: click is only INTENT (nothing observable happens after) —
 * the read side splits conversion numbers on this. The href value is
 * often a dynamic template (`mailto:${brand.email}`), so classify from
 * the RAW attribute text, not just the static value. */
function classifyConversionMedium(el, sf, kind) {
  if (kind === 'form') return 'form';
  const hrefRaw = readAttrRawText(el, 'href', sf);
  if (hrefRaw === null) return 'button';
  if (hrefRaw.indexOf('mailto:') !== -1) return 'mailto';
  if (hrefRaw.indexOf('tel:') !== -1) return 'tel';
  return 'link';
}

/** Conversion containment (SDK onSubmit parity): the SDK resolves a
 * submitted form's conversion element via form.querySelector — a
 * conversion stamped on an INNER control belongs to the enclosing form,
 * and the form itself then never fires its own form_submitted. Same-file
 * lexical containment only (a form and its controls live in one
 * component); a conversion in a child component file is invisible here,
 * the same accepted limit as cross-file page attribution.
 *
 * Returns false when the entry must be dropped (the enclosing
 * conversion-form's own stamp wins at submit, so this one can never fire). */
function resolveContainment(col, entry, el, sf, relPath, ctx, facts) {
  const { kind, isConversion, id } = facts;
  if (!isConversion || kind === 'form' || !ctx.form) return true;
  if (ctx.form.is_conversion) {
    // The form's own stamp wins at submit (hasAttribute is checked before
    // querySelector) — this inner stamp can never fire. Don't catalog it.
    col.warnings.push({
      path: relPath,
      line: lineOf(el, sf),
      kind: 'conversion_inside_form',
      hint: `This element and its enclosing form both carry data-kite-conversion; the form's stamp wins at submit and this one never fires. Remove data-kite-conversion from "${id}".`,
    });
    return false;
  }
  ctx.form._containsConversion = true;
  // The goal completes via the form's submit — a verifiable outcome, not
  // click-intent. KEEP IN SYNC with kite-analytics.js fireGoal.
  entry.conversion_medium = 'form';
  col.warnings.push({
    path: relPath,
    line: lineOf(el, sf),
    kind: 'conversion_inside_form',
    hint: `data-kite-conversion sits on "${id}" inside form "${ctx.form.cta_id}"; the goal fires on the form's submit. Prefer stamping the <form> itself (conversion + form-type + hook on one element).`,
  });
  // The SDK fires the form_submitted ATTEMPT when the resolved conversion
  // element or the form carries the hook — containment equivalent of the
  // one-element rule in recordConversionHook.
  if (
    readAttr(el, 'data-kite-conversion-hook', sf) !== null ||
    ctx.form._hasHook
  ) {
    col.sawHookedConversionForm = true;
  }
  return true;
}

/** Per-element orchestration over the named steps above. Returns the element's
 * OWN page/surface/form declarations so walk() derives the subtree context
 * from the same single read — page/surface resolution must not exist in two
 * places, or containment and stamp records can disagree on which page/surface
 * a descendant belongs to. */
function recordStamp(col, el, sf, relPath, ctx) {
  checkDynamicStamps(col, el, sf, relPath);
  recordConversionHook(col, el, sf, relPath);
  const pageId = registerPage(col, el, sf);
  const surfaceId = registerSurface(col, el, sf, ctx);

  const own = {
    page: pageId && pageId.value ? pageId.value : null,
    surface: surfaceId && surfaceId.value ? surfaceId.value : null,
    // Set below when this element is a stamped form: descendants resolve
    // conversion containment against it (SDK onSubmit parity).
    form: null,
  };

  // Interaction stamp (CTA / nav / form / expand). The element's enclosing
  // surface is ctx.surface (the nearest surface ANCESTOR — true containment,
  // not source order), unless the element itself carries the surface stamp.
  const kindId = resolveKindAndId(el, sf);
  if (!kindId) return own;
  const { kind, id } = kindId;

  const { isConversion, goalType } = resolveConversion(col, el, sf, relPath);
  const eventAttr = readAttr(el, 'data-kite-event', sf);
  const name = resolveEventName(kind, isConversion, goalType, eventAttr);
  lintEventName(col, el, sf, relPath, kind, eventAttr);

  // The element's resolved page/surface (its own surface stamp, else ancestor).
  const elPage = ctx.page;
  const elSurface =
    surfaceId && surfaceId.value ? surfaceId.value : ctx.surface;

  if (
    !validateIdentity(col, el, sf, relPath, {
      kind,
      id,
      name,
      elPage,
      elSurface,
    })
  ) {
    return own;
  }

  const entry = {
    cta_id: id,
    kind,
    event: name,
    is_conversion: isConversion,
    // A CTA's page is always its ancestor page; its surface is its own when it
    // carries a surface stamp (a clickable card is both), else its ancestor.
    page_id: elPage,
    surface_id: elSurface,
  };
  const role = readAttr(el, 'data-kite-role', sf);
  if (role && role.value) entry.role = role.value;
  const href = readAttr(el, 'href', sf);
  if (href && href.value) entry.href = href.value;
  if (isConversion && goalType) entry.goal_type = goalType;
  if (isConversion)
    entry.conversion_medium = classifyConversionMedium(el, sf, kind);

  if (
    !resolveContainment(col, entry, el, sf, relPath, ctx, {
      kind,
      isConversion,
      id,
    })
  ) {
    return own;
  }

  if (kind === 'form') {
    entry._hasHook = readAttr(el, 'data-kite-conversion-hook', sf) !== null;
    own.form = entry;
  }
  col.ctas.push(entry);
  return own;
}

function walk(col, node, sf, relPath, ctx) {
  let childCtx = ctx;
  let opening = null;
  if (ts.isJsxElement(node)) opening = node.openingElement;
  else if (ts.isJsxSelfClosingElement(node)) opening = node;

  // Stamps hidden inside a spread ({...attrs} whose inline object mentions
  // data-kite-) are invisible to the attribute reader below: the catalog would
  // silently miss them. Warn (non-blocking); indirect spreads (a variable
  // defined elsewhere) stay invisible — accepted limit of a static scan.
  if (opening) {
    for (const prop of opening.attributes.properties) {
      if (
        ts.isJsxSpreadAttribute(prop) &&
        prop.expression.getText(sf).includes('data-kite-')
      ) {
        col.warnings.push({
          path: relPath,
          line: lineOf(prop, sf),
          kind: 'spread_stamp',
          hint: 'data-kite-* attributes inside a {...spread} are not extracted into the analytics catalog; write them as literal JSX attributes on the element instead.',
        });
      }
    }
  }

  if (opening && hasAnyKiteAttr(opening, sf)) {
    // recordStamp returns the element's OWN page/surface (single source of
    // the resolution rule): a page-id / surface set here contains its
    // descendants, so it becomes the subtree ctx.
    const own = recordStamp(col, opening, sf, relPath, ctx);
    childCtx = {
      page: own.page !== null ? own.page : ctx.page,
      surface: own.surface !== null ? own.surface : ctx.surface,
      form: own.form !== null ? own.form : ctx.form,
    };
  }
  ts.forEachChild(node, (c) => walk(col, c, sf, relPath, childCtx));
}

/** Walk every source file under `srcDir` and return the fully collected scan
 * state, blocking defects included. Only .tsx is AST-extracted; the other
 * extensions are text-scanned for the conversion-call signature (a form's
 * success handler may live in a lib file) and for stray data-kite- stamps the
 * extractor would silently miss. */
function scanSourceTree(srcDir) {
  const col = newCollector();
  for (const file of sourceFiles(srcDir)) {
    let text;
    try {
      text = fs.readFileSync(file, 'utf8');
    } catch {
      continue; // unreadable file: skip, never fail the whole extract
    }
    const rel = path.relative(srcDir, file);
    // The template's own analytics plumbing (src/lib/analytics/) ships with
    // EVERY site and mentions data-kite-* / the hook API in comments — it is
    // not site code, so it must neither warn nor satisfy the hook-call check.
    if (rel.startsWith('lib/analytics/')) continue;
    if (CONVERSION_CALL_PATTERN.test(text)) col.sawConversionCall = true;
    if (!file.endsWith('.tsx')) {
      // Manifest extraction stays .tsx-only (the template's component grammar);
      // a stamp in any other extension would never reach the catalog — warn.
      if (text.includes('data-kite-')) {
        col.warnings.push({
          path: rel,
          line: 0,
          kind: 'unscanned_file_stamp',
          hint: 'data-kite- appears in a non-.tsx file; only .tsx under src/ is extracted into the analytics catalog. Move the stamped JSX into a .tsx component.',
        });
      }
      continue;
    }
    const sf = ts.createSourceFile(
      file,
      text,
      ts.ScriptTarget.Latest,
      /*setParentNodes*/ true,
      ts.ScriptKind.TSX,
    );
    walk(col, sf, sf, rel, { page: null, surface: null, form: null });
  }

  // Hook/call pairing (site-wide, so it runs after every file is scanned): a
  // data-kite-conversion-hook form suppresses the SDK's submit-time goal
  // emission and relies on the site calling window.__kite.conversion(...) from
  // its success handler. A hook with no such call ANYWHERE means the conversion
  // silently never fires — a blocking defect of the same deterministic class as
  // dynamic_stamp.
  if (col.conversionHooks.length > 0 && !col.sawConversionCall) {
    for (const h of col.conversionHooks) {
      col.errors.push({
        path: h.path,
        line: h.line,
        kind: 'unpaired_conversion_hook',
        hint: "data-kite-conversion-hook is stamped but no source file calls window.__kite.conversion(...). Either call it in the form's success handler (after the submission succeeds), or remove data-kite-conversion-hook so the SDK fires the goal on native submit.",
      });
    }
  }
  return col;
}

// ---- manifest assembly ---------------------------------------------------------

/** Build the manifest from a defect-free scan. Assembly-time warnings
 * (no_stamps, no_conversion, multiple_conversions, intent_conversion,
 * hero_without_cta) are pushed onto state.warnings — one warnings channel end
 * to end. `srcArg` is the user-facing src path for the no_stamps hint. */
function assembleManifest(state, srcArg) {
  const { ctas, surfaces, pages } = state;

  // A non-conversion form whose conversion sits on an INNER control never
  // fires its own event: the SDK resolves the inner conversion at submit and
  // fires the goal instead (kite-analytics.js onSubmit), so the form's
  // form_submitted entry would be a phantom with a permanent zero count.
  for (let i = ctas.length - 1; i >= 0; i--) {
    const c = ctas[i];
    if (c.kind === 'form' && !c.is_conversion && c._containsConversion) {
      ctas.splice(i, 1);
    }
  }

  // Assemble the manifest: events (deduped, ordered), pages with nested
  // surfaces+ctas, a shared bucket for stamps with no page ancestor (chrome),
  // and the home-first primary conversion.
  const events = [];
  const eventSeen = new Set();
  for (const c of ctas) {
    if (!eventSeen.has(c.event)) {
      eventSeen.add(c.event);
      events.push(c.event);
    }
  }
  // A hook-marked conversion form fires a literal `form_submitted` ATTEMPT
  // (conversion_attempt: true) on every native submit, BEFORE the success hook
  // fires the goal — guaranteed live traffic, so the catalog must list it.
  // Keyed on the shapes that actually submit — hook + conversion + form-type
  // on one element, or a hooked conversion contained in a stamped form (see
  // recordConversionHook / resolveContainment) — not just any hook stamp, or a
  // hook on a non-form widget conversion would catalog an event that can never
  // fire.
  // KEEP IN SYNC with public/kite-analytics.js onSubmit.
  if (state.sawHookedConversionForm && !eventSeen.has('form_submitted')) {
    eventSeen.add('form_submitted');
    events.push('form_submitted');
  }

  const surfaceList = [...surfaces.values()];
  const pageOrder = [...pages.keys()];

  // Cross-file page attribution recovery. Section components live in separate
  // files, so their AST never sees the `<main data-kite-page-id>` in page.tsx and
  // `page_id` comes back null — otherwise every surface/CTA files as page-less
  // chrome and per-page metrics + experiment surfaces are impossible (the runtime
  // SDK, which reads page_id live from the DOM, would disagree with the catalog).
  // The surface_id encodes the page (`<page>.<section>`), so recover the page from
  // that prefix when it matches a known page id.
  const pageIdSet = new Set(pageOrder);
  const recoverPage = (id) => {
    if (typeof id !== 'string' || !id.includes('.')) return null;
    const prefix = id.slice(0, id.indexOf('.'));
    return pageIdSet.has(prefix) ? prefix : null;
  };
  for (const s of surfaces.values()) {
    if (s.page_id == null) {
      const p = recoverPage(s.surface_id);
      if (p) s.page_id = p;
    }
  }
  for (const c of ctas) {
    if (c.page_id == null) {
      const p = recoverPage(c.surface_id);
      if (p) c.page_id = p;
    }
  }

  // One assembly rule for both page buckets and the shared/chrome bucket
  // (pageId === null): the two must never diverge in shape, or the deploy-seam
  // consumer has to special-case the chrome (Header/Footer — the highest-traffic
  // events, rendered on every route).
  function bucketFor(pageId) {
    const scopeCtas = ctas.filter((c) => c.page_id === pageId);
    return {
      surfaces: surfaceList
        .filter((s) => s.page_id === pageId)
        .map((s) => surfaceEntry(s, scopeCtas)),
      ctas: scopeCtas.filter((c) => !c.surface_id).map(publicCta),
    };
  }

  const pageEntries = pageOrder.map((pid) => {
    const meta = pages.get(pid);
    const entry = { page_id: pid, ...bucketFor(pid) };
    if (meta.page_type !== undefined) entry.page_type = meta.page_type;
    return entry;
  });

  // Chrome (Header/Footer): surfaces and CTAs with no page ancestor, rendered on
  // every route. Surfaces are kept (with metadata) even when they hold no CTA.
  const sharedBucket = bucketFor(null);
  const sharedSurfaces = sharedBucket.surfaces;
  const shared = sharedBucket.ctas;

  // Home-first primary conversion, else first conversion in scan order.
  const conversions = ctas.filter((c) => c.is_conversion);
  const homeConv = conversions.find((c) => c.page_id === 'home');
  const primary = homeConv ?? conversions[0] ?? null;

  // A scan that found NOTHING is the worst silent failure — the generation
  // ignored the stamping grammar entirely (or scanned the wrong tree) and the
  // site ships with an empty catalog. Warn loudly; the previous gating on
  // ctas.length > 0 made exactly this case the only one with no diagnostic.
  if (pages.size === 0 && surfaces.size === 0 && ctas.length === 0) {
    state.warnings.push({
      kind: 'no_stamps',
      hint:
        `No data-kite-* stamps found anywhere under ${srcArg}. The site will have ` +
        'an empty analytics catalog: stamp the page root, sections, CTAs, and the ' +
        'primary conversion per the authoring grammar.',
    });
  }
  // Zero-conversion is otherwise a silent failure: the site ships with a null
  // primary_conversion and no goal ever fires, and nothing alerts. Surface it as a
  // non-blocking warning so it shows up in generation output.
  if (ctas.length > 0 && conversions.length === 0) {
    state.warnings.push({
      kind: 'no_conversion',
      hint: 'No element carries data-kite-conversion, so no conversion/goal is tracked. Stamp the primary CTA or form with data-kite-conversion="<goal_type>".',
    });
  }
  // Exactly one conversion is the contract; more than one is accepted (warn-only)
  // with the home-first winner nominated as primary_conversion.
  if (conversions.length > 1) {
    state.warnings.push({
      kind: 'multiple_conversions',
      hint: `${conversions.length} elements carry data-kite-conversion; expected exactly one. "${primary.cta_id}" (home-first) was nominated as the primary conversion — remove data-kite-conversion from the others.`,
    });
  }
  // A mailto:/tel: conversion counts INTENT (the click), not a verifiable
  // outcome — conversion numbers will overstate. Non-blocking by decision.
  if (
    primary &&
    (primary.conversion_medium === 'mailto' ||
      primary.conversion_medium === 'tel')
  ) {
    state.warnings.push({
      kind: 'intent_conversion',
      hint: `The primary conversion "${primary.cta_id}" completes via ${primary.conversion_medium}: — a click counts as the goal even when no message/call ever happens. Prefer a real form (verifiable completion) when the goal is purchase/lead/inquiry/booking.`,
    });
  }
  // A hero with no stamped CTA means the most-viewed surface offers no
  // measurable action and no hero->conversion funnel leg can exist.
  const allSurfaceEntries = pageEntries
    .flatMap((p) => p.surfaces)
    .concat(sharedSurfaces);
  for (const s of allSurfaceEntries) {
    if (s.surface_type === 'hero' && s.ctas.length === 0) {
      state.warnings.push({
        kind: 'hero_without_cta',
        hint: `Hero surface "${s.surface_id}" contains no stamped CTA. The hero should usually carry at least one data-kite-cta-id action (primary or secondary).`,
      });
    }
  }

  return {
    schema_version: SCHEMA_VERSION,
    primary_conversion: primary ? (primary.goal_type ?? null) : null,
    primary_conversion_event: primary ? primary.event : null,
    primary_conversion_medium: primary
      ? (primary.conversion_medium ?? null)
      : null,
    events,
    pages: pageEntries,
    shared,
    shared_surfaces: sharedSurfaces,
  };
}

// ---- CLI -----------------------------------------------------------------------

function usageError(hint) {
  process.stdout.write(
    JSON.stringify({
      ok: false,
      manifest: null,
      errors: [{ path: '', line: 0, kind: 'usage', hint }],
    }) + '\n',
  );
  return 2;
}

function main(argv) {
  // Parse flags first so a flag's VALUE (e.g. the file after --out) is never
  // mistaken for the positional src dir — `--out kite-manifest.json` with src
  // omitted must be a usage error, not a scan of the out-file path.
  const outIdx = argv.indexOf('--out');
  const outFile = outIdx >= 0 ? (argv[outIdx + 1] ?? null) : null;
  const outValueIdx = outIdx >= 0 ? outIdx + 1 : -1;
  const positional = argv.filter(
    (a, i) => !a.startsWith('--') && i !== outValueIdx,
  );
  const srcArg = positional[0];
  if (!srcArg || (outIdx >= 0 && !outFile)) {
    return usageError(
      'usage: extract-kite-manifest.mjs <src-dir> [--out <file>]',
    );
  }
  const srcDir = path.resolve(process.cwd(), srcArg);
  // A missing src dir is tooling trouble (wrong cwd, layout drift), not "the
  // site has zero stamps" — exit 2 so callers classify it as a skip, instead
  // of writing an empty manifest over a previously valid one.
  if (!fs.existsSync(srcDir) || !fs.statSync(srcDir).isDirectory()) {
    return usageError(`src dir not found: ${srcDir}`);
  }

  const state = scanSourceTree(srcDir);

  if (state.errors.length > 0) {
    process.stdout.write(
      JSON.stringify({
        ok: false,
        manifest: null,
        errors: state.errors,
        warnings: state.warnings,
      }) + '\n',
    );
    return 1;
  }

  const manifest = assembleManifest(state, srcArg);

  if (outFile) {
    try {
      fs.writeFileSync(
        path.resolve(process.cwd(), outFile),
        JSON.stringify(manifest, null, 2) + '\n',
        'utf8',
      );
    } catch (e) {
      // Writing the artifact failed — tooling trouble, not a stamp defect.
      // Surface it through the SAME warnings channel as every other diagnostic
      // (a divergent one-off key here would be dropped by consumers that read
      // only `warnings`, silently shipping without a manifest on disk) and
      // fall through to the single emit below so collected stamp warnings
      // survive too.
      state.warnings.push({
        path: outFile,
        line: 0,
        kind: 'out_write_failed',
        hint: `could not write ${outFile}: ${String(e)} — kite-manifest.json on disk is missing or stale; the manifest on stdout is still valid.`,
      });
    }
  }

  process.stdout.write(
    JSON.stringify({
      ok: true,
      manifest,
      errors: [],
      warnings: state.warnings,
    }) + '\n',
  );
  return 0;
}

// Set exitCode rather than process.exit(): the script is synchronous, so letting
// the process exit naturally guarantees the JSON line on stdout is fully flushed
// to the (async) pipe before we exit — process.exit() can truncate a buffered
// write and silently drop the manifest.
process.exitCode = main(process.argv.slice(2));
