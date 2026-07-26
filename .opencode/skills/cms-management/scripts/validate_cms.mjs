#!/usr/bin/env tsx
/**
 * validate_cms.mjs — prove a generated `seed.json` fits the Payload admin.
 *
 * The single source for the "data fits the admin panel" guarantee. Run with
 * `tsx` from inside a generated iter dir (the dir that holds `src/payload.config.ts`,
 * `node_modules/`, and `seed.json`). The script lives in the `cms-management` skill
 * but resolves the Payload config + package from `process.cwd()`, so it works
 * from any location as long as cwd is the iter dir.
 *
 *   pnpm exec tsx <skill>/scripts/validate_cms.mjs [seed.json]
 *
 * It enforces the three fit invariants from the plan:
 *   1. Schema is valid    — `@payload-config` loads (admin can render it).
 *   2. Content is structural — every seed doc matches the field shape DERIVED
 *      FROM the live config (types, required, select options, block discrimination)
 *      plus a bidirectional orphan-key check (no content key missing from the
 *      schema; no required field missing from the content). DB-free.
 *   3. Content is semantic  — each doc is accepted by Payload's Local API in a
 *      rolled-back transaction (write-time validation with field paths). Only
 *      runs when `APP_DATABASE_URL` is set; skipped (not failed) otherwise.
 *
 * Invariant 2 is derived from the config object itself, never hand-maintained,
 * so it cannot drift from the real schema (plan Risk 2).
 *
 * Alongside invariant 2 it runs two DB-free triple checks: every schema block
 * is registered in RenderBlocks (`block-triple`), and every registered block
 * component's destructured props are schema field names (`component-props`) —
 * the renderer spreads stored blocks onto components, so a drifted prop name
 * renders an empty section with no error anywhere.
 *
 * Output: one line of JSON to stdout —
 *   { ok, invariants: {schema, structure, semantic}, errors: [{path, kind, hint}] }
 * Exit code 0 when ok, 1 when any blocking fit error is found, 2 on bad usage.
 */
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

// Seed top-level keys map to a Payload global or collection. The seed contract:
//   { siteSettings?: {...}, pages?: [{slug,...}], collections?: { <slug>: [docs] } }
const GLOBAL_KEYS = { siteSettings: 'site-settings' };
const COLLECTION_KEYS = { pages: 'pages' };
// Payload-managed/meta keys that legitimately appear on stored docs and must not
// be flagged as orphan content keys.
const META_KEYS = new Set([
  'id',
  'blockType',
  'blockName',
  'createdAt',
  'updatedAt',
  '_status',
  'globalType',
]);

// Props the renderer injects into every block component (not schema fields), so
// a component may destructure them without tripping the component-props check.
// `searchParams` is threaded from the route so faceted blocks can read `?tag=`.
const RENDERER_PROPS = new Set(['searchParams']);

// Slugs of the content collections registered in the live config. Populated once
// the config loads (in `main`) and used to validate `collectionList` block
// bindings — the block's `collection` is a free-text slug (collections are
// generation-driven), so an unregistered value would 500 at render.
const validCollectionSlugs = new Set();

// One spelling of a `'slug': Component` registry entry — shared by the two
// COMPONENT checks (component-props, item-triple) so their key charclasses
// cannot drift (matchAll clones the regex, so the shared /g instance is safe).
// checkBlockRegistry deliberately keeps its own KEY-ONLY regex: it must also
// count entries whose value is not a bare identifier (an inline wrapper like
// `slug: () => …`), which this component-capturing spelling would skip —
// reading those as unregistered would false-fail the block-triple gate.
const REGISTRY_ENTRY_RE =
  /[,{]\s*['"]?([\w][\w-]*)['"]?\s*:\s*([A-Za-z_$][\w$]*)/g;

function err(path, kind, hint) {
  return { path, kind, hint };
}

/**
 * Flatten Payload presentational wrappers (row, collapsible, unnamed group,
 * unnamed tabs) so their child fields live in the same data namespace as the
 * parent. Named group/array/blocks/tabs and leaf fields are returned as-is;
 * `ui` fields and fields without a data identity are dropped.
 */
function dataFields(fields) {
  const out = [];
  for (const f of fields || []) {
    if (!f || typeof f !== 'object') continue;
    if (f.type === 'ui') continue;
    if (f.type === 'row' || f.type === 'collapsible') {
      out.push(...dataFields(f.fields));
      continue;
    }
    if (f.type === 'group' && !f.name) {
      // An UNNAMED group is presentational (like row/collapsible): Payload does
      // not nest its data, so its children live in the parent's namespace. A
      // NAMED group is a real data namespace and falls through to `out.push(f)`.
      out.push(...dataFields(f.fields));
      continue;
    }
    if (f.type === 'tabs') {
      for (const tab of f.tabs || []) {
        if (tab.name) {
          // a named tab is a group namespace
          out.push({ name: tab.name, type: 'group', fields: tab.fields });
        } else {
          out.push(...dataFields(tab.fields));
        }
      }
      continue;
    }
    out.push(f);
  }
  return out;
}

function isPlainObject(v) {
  return v !== null && typeof v === 'object' && !Array.isArray(v);
}

/**
 * Convert markdown strings in `richText` fields to Lexical, in place, walking
 * the field schema alongside the data. Mirrors the seed's own conversion so the
 * semantic Local-API write validates the same shape that will be persisted.
 * `convert` is `convertMarkdownToLexical`; `editorConfig` the sanitized editor
 * config. Reuses `dataFields` so presentational wrappers share the namespace.
 */
function convertRichTextStrings(fields, data, editorConfig, convert) {
  if (!fields || !isPlainObject(data)) return;
  for (const f of dataFields(fields)) {
    const value = f.name ? data[f.name] : data;
    if (f.type === 'richText') {
      if (f.name && typeof value === 'string') {
        data[f.name] = convert({ editorConfig, markdown: value });
      }
    } else if (f.type === 'group' && f.name) {
      convertRichTextStrings(f.fields, value, editorConfig, convert);
    } else if (f.type === 'array' && Array.isArray(value)) {
      for (const item of value)
        convertRichTextStrings(f.fields, item, editorConfig, convert);
    } else if (f.type === 'blocks' && Array.isArray(value)) {
      const bySlug = new Map((f.blocks || []).map(b => [b.slug, b]));
      for (const item of value) {
        const block = bySlug.get(item?.blockType);
        if (block)
          convertRichTextStrings(block.fields, item, editorConfig, convert);
      }
    }
  }
}

// Capability probe: whether THIS app's baked seed script can convert markdown
// strings to Lexical at write time. Apps from older template snapshots lack
// the converter — for them a string richText must be rejected here, not
// deferred to a `pnpm seed` failure. Memoized (the validator runs once per
// seed file).
let _seedConvertsMarkdown = null;
function seedConvertsMarkdown() {
  if (_seedConvertsMarkdown === null) {
    try {
      const seedSrc = fs.readFileSync(
        path.resolve(process.cwd(), 'scripts/seed-payload.ts'),
        'utf-8'
      );
      _seedConvertsMarkdown = seedSrc.includes('markdownDoc');
    } catch {
      _seedConvertsMarkdown = false;
    }
  }
  return _seedConvertsMarkdown;
}

function looksLikeLexical(v) {
  return isPlainObject(v) && isPlainObject(v.root);
}

/** Validate one data object against a list of Payload field configs. */
function validateObject(fields, data, prefix, errors) {
  const flat = dataFields(fields);
  const known = new Set();
  for (const f of flat) {
    if (f.name) known.add(f.name);
    validateField(
      f,
      f.name ? data?.[f.name] : data,
      joinPath(prefix, f.name),
      errors
    );
  }
  // Orphan-key check (content → schema): a key present in content but absent
  // from the schema would be silently dropped / uneditable in the admin.
  if (isPlainObject(data)) {
    for (const key of Object.keys(data)) {
      if (META_KEYS.has(key) || known.has(key)) continue;
      errors.push(
        err(
          joinPath(prefix, key),
          'orphan-key',
          `content key "${key}" has no matching field in the schema; the admin would drop it. Remove it or add the field to the schema.`
        )
      );
    }
  }
}

function joinPath(prefix, key) {
  if (key === undefined || key === null) return prefix;
  return prefix ? `${prefix}.${key}` : key;
}

/** Validate a single field's value (orphan/required checks live in validateObject). */
function validateField(field, value, p, errors) {
  const present = value !== undefined && value !== null && value !== '';
  if (!present) {
    // Required check (schema → content): a required field missing from content
    // makes the admin reject the doc. A falsy default (0, false, '') still
    // counts as a default — only `undefined` means "no default".
    if (field.required && field.defaultValue === undefined) {
      errors.push(
        err(
          p,
          'missing-required',
          `required field "${field.name}" is missing from the content.`
        )
      );
    }
    return;
  }
  switch (field.type) {
    case 'text':
    case 'textarea':
    case 'email':
    case 'code':
    case 'date':
      expect(
        typeof value === 'string',
        p,
        `expected a string for ${field.type} field`,
        errors
      );
      break;
    case 'number':
      expect(typeof value === 'number', p, 'expected a number', errors);
      break;
    case 'checkbox':
      expect(typeof value === 'boolean', p, 'expected a boolean', errors);
      break;
    case 'select':
    case 'radio': {
      const opts = (field.options || []).map(o =>
        typeof o === 'string' ? o : o.value
      );
      const vals = field.hasMany
        ? Array.isArray(value)
          ? value
          : [value]
        : [value];
      for (const v of vals) {
        expect(
          opts.includes(v),
          p,
          `value "${v}" is not one of the allowed options: ${opts.join(', ')}`,
          errors
        );
      }
      break;
    }
    case 'richText':
      // A richText value is either a Lexical document ({ root: {...} }, built
      // with lexicalDoc()) or a markdown string, which the seed converts to
      // Lexical at write time (markdownDoc). Markdown is freeform so a string
      // cannot be fully validated DB-free — but the one classifiable mistake
      // is a JSON-*stringified* Lexical doc: the seed would convert it as
      // markdown and the page would render the literal JSON text. Catch that
      // here rather than at publish time.
      // Strings are valid ONLY when this app's baked seed script can actually
      // convert them — an app from an older template snapshot has no
      // markdown→Lexical path, and accepting the string here just defers the
      // failure to `pnpm seed` (Payload's Local API rejects raw strings).
      expect(
        (typeof value === 'string' && seedConvertsMarkdown()) ||
          looksLikeLexical(value),
        p,
        seedConvertsMarkdown()
          ? 'expected a lexical richText document ({ root: {...} }, use lexicalDoc()) or a markdown string'
          : "expected a lexical richText document ({ root: {...} }, use lexicalDoc()) — this app's seed script cannot convert markdown strings",
        errors
      );
      if (typeof value === 'string' && value.trimStart().startsWith('{')) {
        let parsed;
        try {
          parsed = JSON.parse(value);
        } catch {
          parsed = undefined; // genuinely markdown-ish text starting with '{'
        }
        expect(
          !looksLikeLexical(parsed),
          p,
          'string is a JSON-stringified lexical document — pass the object itself (lexicalDoc()), not its JSON text, or the page will render the literal JSON',
          errors
        );
      }
      break;
    case 'json':
      break; // any JSON value is acceptable
    case 'group':
      if (
        expect(
          isPlainObject(value),
          p,
          'expected an object for a group field',
          errors
        )
      ) {
        validateObject(field.fields, value, p, errors);
      }
      break;
    case 'array':
      if (expect(Array.isArray(value), p, 'expected an array', errors)) {
        value.forEach((item, i) =>
          validateObject(field.fields, item, `${p}[${i}]`, errors)
        );
      }
      break;
    case 'blocks':
      if (
        expect(Array.isArray(value), p, 'expected an array of blocks', errors)
      ) {
        const bySlug = new Map((field.blocks || []).map(b => [b.slug, b]));
        value.forEach((item, i) => {
          const ip = `${p}[${i}]`;
          const slug = item?.blockType;
          if (!slug) {
            errors.push(
              err(ip, 'missing-blockType', 'each block needs a "blockType" key')
            );
            return;
          }
          const block = bySlug.get(slug);
          if (!block) {
            errors.push(
              err(
                `${ip}.blockType`,
                'unknown-block',
                `blockType "${slug}" is not in this collection's block library: ${[...bySlug.keys()].join(', ')}`
              )
            );
            return;
          }
          validateObject(block.fields, item, ip, errors);
          // collectionList and relatedItems bind to a content collection by
          // slug. Collections are generation-driven, so verify the slug is
          // registered — an unknown value passes the text-field check but 500s
          // (collectionList) or renders an invisible empty section
          // (relatedItems) at render.
          if (slug === 'collectionList' || slug === 'relatedItems') {
            const target = item?.collection;
            if (
              typeof target === 'string' &&
              target &&
              !validCollectionSlugs.has(target)
            ) {
              errors.push(
                err(
                  `${ip}.collection`,
                  'unknown-collection',
                  `${slug} is bound to "${target}", which is not a registered content collection: ${[...validCollectionSlugs].join(', ') || '(none)'}`
                )
              );
            }
          }
        });
      }
      break;
    default:
      // point, upload, relationship, etc. — not part of the seed contract; leave
      // them to the semantic Local-API layer rather than guessing their shape.
      break;
  }
}

function expect(cond, p, hint, errors) {
  if (!cond) errors.push(err(p, 'type-mismatch', hint));
  return cond;
}

/** Collect every block slug declared anywhere in the config's field tree. */
function collectBlockSlugs(fields, into) {
  for (const f of dataFields(fields)) {
    if (f.type === 'blocks') {
      for (const b of f.blocks || []) into.add(b.slug);
      for (const b of f.blocks || []) collectBlockSlugs(b.fields, into);
    } else if (f.type === 'group' || f.type === 'array') {
      collectBlockSlugs(f.fields, into);
    }
  }
}

/**
 * Extract the `blockComponents = { ... }` object literal with a brace-balance
 * scan. A non-greedy regex (`\{[\s\S]*?\n\s*\}`) stops at the first line-start
 * `}`, so a value spanning lines or a nested literal truncates the map and
 * every slug after the cut reads as unregistered — a false `block-triple`
 * error that blocks a valid generation. Returns the literal including braces,
 * or '' when the map is absent.
 */
function extractBlockComponentsBody(src) {
  return extractNamedObjectBody(src, 'blockComponents');
}

// Drop whole-line `//` comments from an extracted object-literal body. The
// registries carry sentinel comment lines between entries (the deterministic
// injector writes generated entries below them), and the entry regex keys off a
// preceding `,`/`{` — a comment line between entries would otherwise hide the
// first generated entry, falsely reporting it as unregistered. Only full-line
// comments are removed, so `://` inside any value is untouched.
function stripCommentLines(body) {
  return body
    .split('\n')
    .filter(line => !line.trim().startsWith('//'))
    .join('\n');
}

// Generalized form of the above for any `<name> = { ... }` object literal (the
// item registry reuses it for `itemComponents`).
function extractNamedObjectBody(src, name) {
  // Tolerate an optional type annotation between the name and `=`
  // (`itemComponents: Record<...> = {`); generics carry no `=`, so `[^=]*` is
  // safe up to the assignment.
  const declMatch = src.match(new RegExp(`${name}\\s*(?::[^=]*)?=\\s*\\{`));
  if (!declMatch) return '';
  const open = declMatch.index + declMatch[0].length - 1;
  let depth = 0;
  for (let i = open; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}' && --depth === 0) return src.slice(open, i + 1);
  }
  // Unbalanced braces mean a file tsc rejects anyway. The empty body makes
  // every slug report as unregistered — acceptable steering toward rewriting
  // the registry, and identical to how an absent map already behaves.
  return '';
}

/**
 * Block-triple check (governed-extensible blocks): every block declared in the
 * schema must also be registered in RenderBlocks' component map, or the renderer
 * silently skips it (`blockComponents[blockType]` returns undefined → null). The
 * matching component file + identical prop names are enforced by `tsc`.
 */
function checkBlockRegistry(config, cwd, errors) {
  const slugs = new Set();
  for (const c of config.collections || []) collectBlockSlugs(c.fields, slugs);
  for (const g of config.globals || []) collectBlockSlugs(g.fields, slugs);
  if (slugs.size === 0) return;
  const registryPath = path.resolve(
    cwd,
    'src/components/blocks/RenderBlocks.tsx'
  );
  let src;
  try {
    src = fs.readFileSync(registryPath, 'utf-8');
  } catch {
    errors.push(
      err(
        'src/components/blocks/RenderBlocks.tsx',
        'block-triple',
        'RenderBlocks.tsx not found; cannot verify the block registry'
      )
    );
    return;
  }
  // Extract the `blockComponents` object literal. The body keeps the opening
  // brace so the first key is preceded by `{` like the rest are by `,`.
  const body = stripCommentLines(extractBlockComponentsBody(src));
  const registered = new Set();
  // Key charclass must match registry_inject's slug charset ([a-zA-Z0-9_-]):
  // a kebab-case key ('story-scroller':) that the regex cannot capture reads
  // as unregistered — a false, unrepairable block-triple error.
  for (const m of body.matchAll(/[,{]\s*['"]?([\w][\w-]*)['"]?\s*:/g)) {
    registered.add(m[1]);
  }
  for (const slug of slugs) {
    if (!registered.has(slug)) {
      errors.push(
        err(
          `RenderBlocks.tsx:${slug}`,
          'block-triple',
          `block "${slug}" has a schema but no entry in RenderBlocks' blockComponents map; ship the full triple (schema + component + registry) so the renderer can render it.`
        )
      );
    }
  }
}

/**
 * Component-prop check: the renderer spreads each stored block onto its
 * component, so a destructured prop that is not a schema field is always
 * undefined — the section renders empty with no error anywhere (`tsc` only
 * catches it when the component annotates its props with the generated
 * `@/payload-types` interface, which is exactly what a drifted generation
 * tends not to do). Verify mechanically: every prop a registered block
 * component destructures must be a top-level field of its block schema.
 * Components that take a whole props object (no destructure) or use a rest
 * prop are skipped — `tsc` remains the check for those.
 */
/**
 * Shared prop-extraction for the registry gates (blocks + items): resolve a
 * registered component's file via its registry import (falling back to the
 * `<Name>.tsx` convention) and extract the first destructure of its parameter
 * list. Returns `null` when the file is missing (tsc fails the build there, not
 * this gate) or `{ fileBase, props: null }` when the component takes a whole
 * props object / rest prop — tsc remains the check for those. `[^}]*` stops at
 * the first closing brace, so props after a nested destructure go unchecked —
 * under-checking, never a false positive.
 */
function destructuredProps(dir, registrySrc, componentName) {
  const importMatch = registrySrc.match(
    new RegExp(
      `import\\s*\\{[^}]*\\b${componentName}\\b[^}]*\\}\\s*from\\s*['"]\\./([\\w-]+)['"]`
    )
  );
  const fileBase = `${importMatch ? importMatch[1] : componentName}.tsx`;
  let src;
  try {
    src = fs.readFileSync(path.join(dir, fileBase), 'utf-8');
  } catch {
    return null;
  }
  const fnMatch =
    src.match(
      new RegExp(`function\\s+${componentName}\\s*\\(\\s*\\{([^}]*)`)
    ) ||
    src.match(
      new RegExp(`(?:const|let)\\s+${componentName}\\s*=[^(]*\\(\\s*\\{([^}]*)`)
    );
  if (!fnMatch || fnMatch[1].includes('...')) return { fileBase, props: null };
  const props = splitTopLevel(fnMatch[1])
    .map(s => s.split(/[:=]/)[0].trim())
    .filter(Boolean);
  return { fileBase, props };
}

// Split a destructured-param body on TOP-LEVEL commas only. A default value
// that is a multi-element array/object literal legally contains commas
// (`labels = ['a', 'b']`) — a naive split turns its tail into a bogus extra
// "prop" that is never a schema field, false-failing the component-props /
// item-triple gates on a valid generation.
function splitTopLevel(body) {
  const parts = [];
  let depth = 0;
  let start = 0;
  let quote = null;
  for (let i = 0; i < body.length; i++) {
    const c = body[i];
    if (quote) {
      if (c === '\\') i++;
      else if (c === quote) quote = null;
      continue;
    }
    if (c === "'" || c === '"' || c === '`') quote = c;
    else if (c === '[' || c === '{' || c === '(') depth++;
    else if (c === ']' || c === '}' || c === ')') depth--;
    else if (c === ',' && depth === 0) {
      parts.push(body.slice(start, i));
      start = i + 1;
    }
  }
  parts.push(body.slice(start));
  return parts;
}

function checkComponentProps(config, cwd, errors) {
  const blockFields = new Map(); // slug -> Set of top-level field names
  const visit = fields => {
    for (const f of dataFields(fields)) {
      if (f.type === 'blocks') {
        for (const b of f.blocks || []) {
          if (!blockFields.has(b.slug)) {
            blockFields.set(
              b.slug,
              new Set(
                dataFields(b.fields)
                  .map(x => x.name)
                  .filter(Boolean)
              )
            );
          }
          visit(b.fields);
        }
      } else if (f.type === 'group' || f.type === 'array') {
        visit(f.fields);
      }
    }
  };
  for (const c of config.collections || []) visit(c.fields);
  for (const g of config.globals || []) visit(g.fields);
  if (blockFields.size === 0) return;

  const blocksDir = path.resolve(cwd, 'src/components/blocks');
  let registrySrc;
  try {
    registrySrc = fs.readFileSync(
      path.join(blocksDir, 'RenderBlocks.tsx'),
      'utf-8'
    );
  } catch {
    return; // missing registry is already a block-triple error
  }
  const body = stripCommentLines(extractBlockComponentsBody(registrySrc));
  for (const m of body.matchAll(REGISTRY_ENTRY_RE)) {
    const [, slug, componentName] = m;
    const fields = blockFields.get(slug);
    if (!fields) continue; // schema-less registry entry is the triple check's concern
    const resolved = destructuredProps(blocksDir, registrySrc, componentName);
    if (!resolved || !resolved.props) continue;
    const { fileBase, props } = resolved;
    for (const prop of props) {
      if (fields.has(prop) || META_KEYS.has(prop) || RENDERER_PROPS.has(prop))
        continue;
      errors.push(
        err(
          `src/components/blocks/${fileBase}:${prop}`,
          'component-props',
          `component ${componentName} destructures prop "${prop}", which is not a field of block "${slug}" (fields: ${[...fields].join(', ')}). The renderer spreads the stored block onto the component, so this prop is always undefined and its UI renders empty. Use the schema field names exactly.`
        )
      );
    }
  }
}

// Props the item renderer injects into every item-layout component (not schema
// fields): `collection` (the item's collection slug) and `related` (same-cluster
// items). Allowed alongside the collection's own field names.
const ITEM_RENDERER_PROPS = new Set(['collection', 'related']);

/**
 * Item-triple check: the baked catch-all route renders each content item
 * through `RenderItem.tsx`'s `itemComponents` map (collection slug → layout
 * component), falling back to a neutral default. Every registered entry must key
 * a real content collection (else the route would never dispatch to it), and the
 * layout component's destructured props must be the collection's field names
 * (plus the renderer-injected `collection`/`related`) — same failure mode as
 * blocks: the renderer spreads the item onto the layout, so a drifted prop is
 * always undefined and its UI renders empty.
 */
function checkItemRegistry(config, cwd, errors) {
  const registryPath = path.resolve(
    cwd,
    'src/components/collections/RenderItem.tsx'
  );
  let src;
  try {
    src = fs.readFileSync(registryPath, 'utf-8');
  } catch {
    return; // template without per-collection item layouts (older image) — skip
  }
  const body = stripCommentLines(extractNamedObjectBody(src, 'itemComponents'));
  if (!body) return;
  const dir = path.resolve(cwd, 'src/components/collections');
  for (const m of body.matchAll(REGISTRY_ENTRY_RE)) {
    const [, collection, componentName] = m;
    if (!validCollectionSlugs.has(collection)) {
      errors.push(
        err(
          `RenderItem.tsx:${collection}`,
          'item-triple',
          `item layout is registered for "${collection}", which is not a registered content collection: ${[...validCollectionSlugs].join(', ') || '(none)'}. Register the collection in generated.ts or remove the entry.`
        )
      );
      continue;
    }
    const fieldNames = new Set(
      dataFields(fieldsForCollection(config, collection) || [])
        .map(x => x.name)
        .filter(Boolean)
    );
    const resolved = destructuredProps(dir, src, componentName);
    if (!resolved || !resolved.props) continue;
    const { fileBase, props } = resolved;
    for (const prop of props) {
      if (
        fieldNames.has(prop) ||
        META_KEYS.has(prop) ||
        ITEM_RENDERER_PROPS.has(prop)
      )
        continue;
      errors.push(
        err(
          `src/components/collections/${fileBase}:${prop}`,
          'item-triple',
          `item layout ${componentName} destructures prop "${prop}", which is not a field of collection "${collection}" (fields: ${[...fieldNames].join(', ')}). The route spreads the item onto the layout, so this prop is always undefined. Use the collection's field names exactly (or the injected "collection"/"related").`
        )
      );
    }
  }
}

// A captured-route raw-HTML blob is detected by either signal: a field/key named
// `*__capturedPage` (the page-migration fallback's marker), or a long string
// value dense with STRUCTURAL container tags. Content-level tags (p, span, li,
// img, headings) are deliberately excluded, and so are table/figure/picture/svg:
// markdown permits inline HTML, and a long legitimate article body embedding a
// few HTML tables or captioned figures must not trip the gate — a captured page
// dump always carries LAYOUT containers (div/section/nav/…), which tabular or
// figure content does not imply.
const RAW_HTML_MIN_LEN = 1500;
const RAW_HTML_MIN_TAGS = 8;
const RAW_HTML_TAG_RE =
  /<\/?(?:div|section|article|header|footer|nav|main|aside)\b/gi;

function looksLikeRawHtmlBlob(value) {
  if (typeof value !== 'string' || value.length < RAW_HTML_MIN_LEN)
    return false;
  const matches = value.match(RAW_HTML_TAG_RE);
  return !!matches && matches.length >= RAW_HTML_MIN_TAGS;
}

/**
 * no-raw-html invariant: a content site's value is decomposed, editable
 * blocks — not a route dumped verbatim into one raw-HTML field. The page
 * migration fallback does exactly that (`<slug>__capturedPage` fields), and the
 * "no raw HTML" rule was previously prompt-only and unenforced. Reject any
 * `*__capturedPage` key or any string value that is a dense block-level HTML
 * blob, anywhere in the seed, so a non-decomposed route fails the gate and
 * forces a repair instead of silently shipping uneditable content.
 */
function checkNoRawHtml(node, prefix, errors) {
  if (Array.isArray(node)) {
    node.forEach((item, i) => checkNoRawHtml(item, `${prefix}[${i}]`, errors));
    return;
  }
  if (!isPlainObject(node)) return;
  for (const [key, value] of Object.entries(node)) {
    const p = joinPath(prefix, key);
    if (/__capturedPage$/i.test(key)) {
      errors.push(
        err(
          p,
          'no-raw-html',
          `field "${key}" holds a captured raw-HTML page; the route was not decomposed into blocks. Replace it with editable blocks (hero, richText, gallery, …) so the content is CMS-editable.`
        )
      );
      continue;
    }
    if (looksLikeRawHtmlBlob(value)) {
      errors.push(
        err(
          p,
          'no-raw-html',
          `value at "${p}" is a large raw-HTML blob (${value.length} chars). Decompose it into editable blocks instead of storing markup verbatim.`
        )
      );
      continue;
    }
    checkNoRawHtml(value, p, errors);
  }
}

function fieldsForGlobal(config, slug) {
  return config.globals?.find(g => g.slug === slug)?.fields;
}
function fieldsForCollection(config, slug) {
  return config.collections?.find(c => c.slug === slug)?.fields;
}

async function main() {
  const cwd = process.cwd();
  const seedArg = process.argv[2] || process.env.SEED_FILE || 'seed.json';
  const seedPath = path.isAbsolute(seedArg)
    ? seedArg
    : path.resolve(cwd, seedArg);

  const errors = [];
  const invariants = { schema: 'fail', structure: 'fail', semantic: 'skipped' };

  // --- Invariant 1: schema loads ---
  let config;
  try {
    const cfgPath = path.resolve(cwd, 'src/payload.config.ts');
    const mod = await import(pathToFileURL(cfgPath).href);
    config = await mod.default;
    // The "registered content collection" set is the generated collections
    // ONLY. `config.collections` also holds system collections (pages, users,
    // media, Payload internals) — letting those satisfy the collectionList /
    // item-triple binding gates would pass a binding that renders broken cards
    // (none of the status/slug guards apply to e.g. `users`), exactly the
    // class these gates exist to catch.
    let contentSlugs = null;
    try {
      const gen = await import(
        pathToFileURL(path.resolve(cwd, 'src/payload/collections/generated.ts'))
          .href
      );
      if (Array.isArray(gen.generatedCollections))
        contentSlugs = gen.generatedCollections.map(c => c.slug);
    } catch {
      // Older image without the module — fall back to all collections rather
      // than false-failing every binding.
    }
    for (const s of contentSlugs ?? (config.collections || []).map(c => c.slug))
      validCollectionSlugs.add(s);
    // A content collection registered directly in payload.config.ts (agent or
    // older tooling) is just as bindable — accept any collection carrying the
    // content SIGNATURE: a top-level `slug` field (routable) plus a publish
    // lifecycle, either a custom `status` field or Payload-native drafts
    // (`versions.drafts` → `_status`). System collections (pages has neither
    // status nor drafts; users/media lack slug) stay excluded.
    for (const c of config.collections || []) {
      if (validCollectionSlugs.has(c.slug)) continue;
      const names = new Set(
        dataFields(c.fields || [])
          .map(f => f.name)
          .filter(Boolean)
      );
      const hasLifecycle = names.has('status') || Boolean(c.versions?.drafts);
      if (names.has('slug') && hasLifecycle) validCollectionSlugs.add(c.slug);
    }
    invariants.schema = 'pass';
  } catch (e) {
    errors.push(
      err(
        'payload.config.ts',
        'config-load',
        `config failed to load: ${e?.message || e}`
      )
    );
    return emit(false, invariants, errors);
  }

  // --- Read seed ---
  let seed;
  try {
    seed = JSON.parse(fs.readFileSync(seedPath, 'utf-8'));
  } catch (e) {
    errors.push(
      err(seedArg, 'seed-read', `could not read/parse seed: ${e?.message || e}`)
    );
    return emit(false, invariants, errors);
  }

  // --- no-raw-html check: reject captured/undecomposed routes (DB-free) ---
  checkNoRawHtml(seed, '', errors);

  // --- Block-triple check: schema ↔ registry consistency (DB-free) ---
  checkBlockRegistry(config, cwd, errors);

  // --- Component-prop check: schema ↔ component prop names (DB-free) ---
  checkComponentProps(config, cwd, errors);

  // --- Item-triple check: collection ↔ RenderItem layout registry (DB-free) ---
  checkItemRegistry(config, cwd, errors);

  // --- Invariant 2: structural (DB-free), derived from config ---
  const docs = []; // {collection|global, data, path} for the semantic layer
  for (const [key, slug] of Object.entries(GLOBAL_KEYS)) {
    if (seed[key] === undefined) continue;
    const fields = fieldsForGlobal(config, slug);
    if (!fields) {
      errors.push(
        err(key, 'unknown-global', `no global "${slug}" in the config`)
      );
      continue;
    }
    validateObject(fields, seed[key], key, errors);
    docs.push({ global: slug, data: seed[key], path: key });
  }
  for (const [key, slug] of Object.entries(COLLECTION_KEYS)) {
    const arr = seed[key];
    if (arr === undefined) continue;
    if (!Array.isArray(arr)) {
      errors.push(
        err(key, 'type-mismatch', `expected an array of ${slug} docs`)
      );
      continue;
    }
    const fields = fieldsForCollection(config, slug);
    if (!fields) {
      errors.push(
        err(key, 'unknown-collection', `no collection "${slug}" in the config`)
      );
      continue;
    }
    arr.forEach((doc, i) => {
      validateObject(fields, doc, `${key}[${i}]`, errors);
      docs.push({ collection: slug, data: doc, path: `${key}[${i}]` });
    });
  }
  // Arbitrary additional collections: seed.collections = { <slug>: [docs] }
  if (isPlainObject(seed.collections)) {
    for (const [slug, arr] of Object.entries(seed.collections)) {
      const fields = fieldsForCollection(config, slug);
      if (!fields) {
        errors.push(
          err(
            `collections.${slug}`,
            'unknown-collection',
            `no collection "${slug}" in the config`
          )
        );
        continue;
      }
      if (!Array.isArray(arr)) {
        errors.push(
          err(
            `collections.${slug}`,
            'type-mismatch',
            'expected an array of docs'
          )
        );
        continue;
      }
      arr.forEach((doc, i) => {
        validateObject(fields, doc, `collections.${slug}[${i}]`, errors);
        docs.push({
          collection: slug,
          data: doc,
          path: `collections.${slug}[${i}]`,
        });
      });
    }
  }
  invariants.structure = errors.length === 0 ? 'pass' : 'fail';

  // --- Invariant 3: semantic via Local API (DB-gated) ---
  if (process.env.APP_DATABASE_URL) {
    try {
      await runSemantic(cwd, config, docs, errors);
      invariants.semantic = errors.some(e => e.kind === 'semantic')
        ? 'fail'
        : 'pass';
    } catch (e) {
      // Infra failure (no reachable DB, etc.) — surface as a skip, not a false
      // blocking error. The structural layer remains the hard gate.
      invariants.semantic = 'skipped';
      process.stderr.write(`semantic layer skipped: ${e?.message || e}\n`);
    }
  }

  return emit(errors.length === 0, invariants, errors);
}

/**
 * Semantic validation: open one transaction, attempt each write with Payload's
 * Local API (which runs the same write-time validation the admin uses), collect
 * ValidationError field paths, then roll the transaction back so nothing is
 * persisted.
 */
async function runSemantic(cwd, config, docs, errors) {
  const require = createRequire(
    pathToFileURL(path.join(cwd, 'package.json')).href
  );
  const { getPayload } = await import(
    pathToFileURL(require.resolve('payload')).href
  );
  const payload = await getPayload({ config });

  // Markdown strings in richText fields are converted to Lexical at seed time;
  // do the same here so the Local-API write sees what the seed will actually
  // persist — otherwise a markdown body would pass the structural check but
  // fail this layer with a spurious richText type error.
  let editorConfig = null;
  let convert = null;
  try {
    const lexical = await import(
      pathToFileURL(require.resolve('@payloadcms/richtext-lexical')).href
    );
    editorConfig = await lexical.editorConfigFactory.default({ config });
    convert = lexical.convertMarkdownToLexical;
  } catch {
    // converter unavailable — markdown strings fall through and the write-time
    // richText validation reports any that need it.
  }
  if (editorConfig && convert) {
    for (const d of docs) {
      const fields = d.global
        ? fieldsForGlobal(config, d.global)
        : fieldsForCollection(config, d.collection);
      convertRichTextStrings(fields, d.data, editorConfig, convert);
    }
  }

  const transactionID = await payload.db.beginTransaction();
  try {
    for (const d of docs) {
      try {
        if (d.global) {
          await payload.updateGlobal({
            slug: d.global,
            data: d.data,
            req: { transactionID },
          });
        } else {
          await payload.create({
            collection: d.collection,
            data: d.data,
            req: { transactionID },
          });
        }
      } catch (e) {
        const fieldErrs = e?.data?.errors;
        if (Array.isArray(fieldErrs) && fieldErrs.length) {
          for (const fe of fieldErrs) {
            errors.push(
              err(
                `${d.path}.${fe.path ?? fe.field ?? ''}`,
                'semantic',
                fe.message
              )
            );
          }
        } else {
          errors.push(err(d.path, 'semantic', e?.message || String(e)));
        }
      }
    }
  } finally {
    if (transactionID) await payload.db.rollbackTransaction(transactionID);
    await dropScratchSchema(payload);
  }
}

/**
 * Drop the scratch schema once validation is done. Payload `push` creates the
 * schema's tables on connect and the rollback only undoes the row inserts,
 * not that DDL — without this, every validate run leaves a dead
 * `payload_*_validate` schema in the per-app DB. Guarded to the `_validate`
 * suffix so the live `payload_<iter>` content schema can never be dropped,
 * and best-effort: cleanup must not turn a finished validation into a
 * failure.
 */
async function dropScratchSchema(payload) {
  const schema = process.env.PAYLOAD_SCHEMA || '';
  if (!schema.endsWith('_validate')) return;
  try {
    await payload.db.pool.query(`DROP SCHEMA IF EXISTS "${schema}" CASCADE`);
  } catch (e) {
    process.stderr.write(`scratch schema drop failed: ${e?.message || e}\n`);
  }
}

function emit(ok, invariants, errors) {
  process.stdout.write(JSON.stringify({ ok, invariants, errors }) + '\n');
  process.exit(ok ? 0 : 1);
}

main().catch(e => {
  process.stdout.write(
    JSON.stringify({
      ok: false,
      invariants: null,
      errors: [err('', 'crash', e?.message || String(e))],
    }) + '\n'
  );
  process.exit(1);
});
