/*
 * Kite analytics SDK — STAMP-DRIVEN.
 *
 * Emits events derived purely from the `data-kite-*` DOM stamps. What is CLOSED
 * and identical on every site is the `kite_event_type` PROPERTY (the machine
 * vocabulary below); event NAMES for interactions/conversions are per-site via
 * `data-kite-event` (evName) — cross-site queries MUST group on
 * kite_event_type, never on the event name. There is NO per-site plan/config engine: what is
 * tracked is decided by the stamps baked into the Payload block templates
 * (RenderBlocks surfaces + block-component CTAs), never by an agent-authored
 * events list.
 *
 * Inputs (inline from the server-rendered bootstrap):
 *   - window.__KITE_ENV__ : per-site identity (website/account id, token, host).
 * (the backend site_event_catalog is reference data for the analytics layer; the
 *  SDK does NOT read it at runtime.)
 *
 * Closed vocabulary (the single source for this contract — keep exact):
 *   Lifecycle: page_viewed, page_engaged, scroll_depth_reached,
 *     section_viewed, section_engaged, item_viewed.
 *   Interactions: cta_clicked, nav_clicked, content_expanded, media_engaged,
 *     form_submitted (incl. conversion_attempt:true on hooked forms),
 *     form_submit_failed.
 *   Conversions: the event NAME is the authored data-kite-event (else
 *     "<goal_type>_completed"); the closed handle is the PROPERTY
 *     kite_event_type="goal_completed" + is_conversion + goal_type — a literal
 *     "goal_completed" event name is only the no-goal-type fallback.
 * Interaction event NAMES honor data-kite-event via evName(); nav is
 * deliberately non-nameable (fixed "nav_clicked" — nav identity rides in
 * nav_id). Per-site variation rides in PROPERTY VALUES (surface_id, cta_id,
 * role, goal_type, item_id, data-kite-prop-* extras), never in new event
 * types.
 */
(function () {
  'use strict';

  var env = window.__KITE_ENV__;
  if (!env || !env.posthogToken || !window.posthog) return;

  var SCHEMA_VERSION = env.schemaVersion || '1.0';
  var DEBUG = !!env.debug || /[?&]kite_debug=1/.test(window.location.search);

  // ---- helpers -------------------------------------------------------------

  // Resolve window.posthog at CALL TIME. The inline loader stub is swapped for the
  // real instance once array.js finishes its async load; a reference captured at
  // boot goes stale and silently drops every later event. A swallowed failure is
  // surfaced when DEBUG is on (env.debug or ?kite_debug=1) so zero-delivery is
  // detectable instead of invisible.
  function capture(event, props) {
    var ph = window.posthog;
    if (!ph) return;
    try {
      ph.capture(event, props || {});
    } catch (e) {
      if (DEBUG && window.console)
        window.console.warn('[kite] capture failed:', event, e);
    }
  }

  // Interaction/conversion events use PostHog's DEFAULT transport (fetch +
  // keepalive), which survives page unload — verified live. Do NOT reintroduce
  // a { transport: 'sendBeacon' } capture option: that override silently
  // dropped 100% of interaction events (64KB batching interaction).

  function each(nodelist, fn) {
    for (var i = 0; i < nodelist.length; i++) fn(nodelist[i]);
  }

  function closestAttr(el, attr) {
    var node = el;
    while (node && node.nodeType === 1) {
      if (node.hasAttribute(attr)) return node;
      node = node.parentElement;
    }
    return null;
  }

  function surfaceContext(el) {
    var surface =
      el && el.nodeType === 1 ? closestAttr(el, 'data-kite-surface') : null;
    if (!surface) return {};
    return {
      surface_id: surface.getAttribute('data-kite-surface'),
      surface_type: surface.getAttribute('data-kite-surface-type') || undefined,
    };
  }

  // data-kite-prop-* → { name: value }
  function propsFromEl(el) {
    var out = {};
    if (!el || !el.attributes) return out;
    for (var i = 0; i < el.attributes.length; i++) {
      var a = el.attributes[i];
      if (a.name.indexOf('data-kite-prop-') === 0) {
        out[a.name.slice('data-kite-prop-'.length)] = a.value;
      }
    }
    return out;
  }

  function text(el) {
    return el && el.textContent
      ? el.textContent.trim().slice(0, 120)
      : undefined;
  }

  function toInt(v) {
    var n = parseInt(v, 10);
    return isNaN(n) ? undefined : n;
  }

  // Merge surface ctx + element props into a base props object.
  function withSurface(el, base) {
    var ctx = surfaceContext(el);
    if (ctx.surface_id !== undefined) base.surface_id = ctx.surface_id;
    if (ctx.surface_type !== undefined) base.surface_type = ctx.surface_type;
    var extra = propsFromEl(el);
    for (var k in extra) base[k] = extra[k];
    return base;
  }

  // Each interaction emits ONE event. Its NAME is the element's data-kite-event
  // (the PM-facing name); its machine class rides as the kite_event_type property
  // so cross-site/agent queries work regardless of the per-site name.
  function evName(el, fallback) {
    return (
      (el && el.getAttribute && el.getAttribute('data-kite-event')) || fallback
    );
  }

  // One stamped interaction event: NAME resolved via evName (authored
  // data-kite-event, else the machine fallback), surface context merged, and
  // the closed kite_event_type ALWAYS riding as the fallback name — the
  // invariant every interaction call site must hold, in one place so a future
  // call site can't get it wrong. nav_clicked and the hooked-form attempt use
  // literal names on purpose (see their call sites) and stay outside.
  function emitStamped(el, fallbackName, extraProps) {
    extraProps.kite_event_type = fallbackName;
    capture(evName(el, fallbackName), withSurface(el, extraProps));
  }

  // Fire a conversion goal event. The event NAME is the element's data-kite-event,
  // else "<goal_type>_completed" (never the generic "goal_completed", which would
  // not match the catalog's primary_conversion_event). Shared by DOM stamps
  // (emitGoal) and the JS success hook (window.__kite.conversion).
  function fireGoal(goalType, extraProps, el) {
    var props = el ? withSurface(el, {}) : {};
    props.kite_event_type = 'goal_completed';
    props.is_conversion = true;
    if (goalType) props.goal_type = goalType;
    if (el) {
      var cid = el.getAttribute('data-kite-cta-id');
      if (cid) props.cta_id = cid;
      var lbl = text(el);
      if (lbl) props.label = lbl;
      // Item dimension: which product/plan/service this conversion belongs to
      // (the stamp may sit on the element itself or an ancestor card).
      var itemEl = closestAttr(el, 'data-kite-item');
      if (itemEl) props.item_id = itemEl.getAttribute('data-kite-item');
      // How the goal completes: a form is a verifiable OUTCOME; mailto/tel is
      // INTENT (the click is all we can observe) — lets dashboards split them.
      // A conversion element INSIDE a stamped form also completes via that
      // form's submit (onSubmit resolves it via querySelector), so it is a
      // verifiable outcome too — 'button' would misclassify it as intent.
      var href = el.getAttribute && el.getAttribute('href');
      props.conversion_medium =
        (el.tagName && el.tagName.toLowerCase() === 'form') ||
        closestAttr(el, 'data-kite-form-type')
          ? 'form'
          : href && href.indexOf('mailto:') === 0
            ? 'mailto'
            : href && href.indexOf('tel:') === 0
              ? 'tel'
              : href
                ? 'link'
                : 'button';
    }
    if (extraProps) for (var k in extraProps) props[k] = extraProps[k];
    capture(
      evName(el, goalType ? goalType + '_completed' : 'goal_completed'),
      props,
    );
  }

  // A conversion element (a fire-and-forget link/button, or a submitted <form>)
  // emits its goal event and nothing else.
  function emitGoal(el) {
    var conv = closestAttr(el, 'data-kite-conversion');
    if (!conv) return false;
    fireGoal(conv.getAttribute('data-kite-conversion'), null, conv);
    return true;
  }

  // Success hook for JS/async conversions (marked data-kite-conversion-hook) —
  // forms AND non-form widgets: the element's own success handler calls this so
  // the goal fires ONLY on a real success, not on the submit/click attempt (the
  // native submit event fires even for a submission the app later rejects, and
  // onClick skips hooked conversions for the same reason). Guard the call site:
  // `window.__kite && window.__kite.conversion('booking')`.
  window.__kite = window.__kite || {};
  window.__kite.conversion = function (goalType, props) {
    // Auto-resolve the stamped element so the goal inherits surface_id /
    // cta_id / the authored data-kite-event name — call sites pass only the
    // goal type. Explicit props still win (applied last in fireGoal).
    // Prefer the form the visitor ACTUALLY submitted (recorded by onSubmit):
    // the same goal form can legitimately appear more than once on a page
    // (hero + footer), and document.querySelector would always attribute to
    // the document-first copy. The regex guard keeps the attribute selector
    // safe to build for the fallback.
    var el = null;
    if (
      lastHookedSubmitEl &&
      lastHookedSubmitEl.getAttribute &&
      lastHookedSubmitEl.getAttribute('data-kite-conversion') === goalType
    ) {
      el = lastHookedSubmitEl;
    } else if (goalType && /^[a-z_]+$/.test(goalType)) {
      try {
        el = document.querySelector(
          '[data-kite-conversion="' + goalType + '"]',
        );
      } catch (e) {
        el = null;
      }
    }
    fireGoal(goalType, props, el);
  };

  // ---- Layer 1 envelope ----------------------------------------------------

  function viewportBucket() {
    var w = window.innerWidth || 0;
    if (w < 480) return 'xs';
    if (w < 768) return 'sm';
    if (w < 1024) return 'md';
    if (w < 1440) return 'lg';
    return 'xl';
  }

  function trafficSource() {
    var p = new URLSearchParams(window.location.search);
    var medium = (p.get('utm_medium') || '').toLowerCase();
    var ref = document.referrer || '';
    var host = '';
    try {
      host = ref ? new URL(ref).host : '';
    } catch (e) {
      host = '';
    }
    if (
      p.get('gclid') ||
      p.get('msclkid') ||
      ['cpc', 'ppc', 'paid_search'].indexOf(medium) >= 0
    )
      return 'paid_search';
    if (
      p.get('fbclid') ||
      p.get('ttclid') ||
      p.get('li_fat_id') ||
      medium === 'paid_social'
    )
      return 'paid_social';
    if (medium === 'email') return 'email';
    if (
      /(chatgpt\.com|perplexity\.ai|claude\.ai|gemini\.google\.com)/.test(host)
    )
      return 'ai_assistant';
    if (/(google|bing|duckduckgo|yahoo|ecosia)\./.test(host) && host)
      return 'organic_search';
    if (
      /(facebook|instagram|twitter|x\.com|linkedin|reddit|youtube|tiktok|t\.co)/.test(
        host,
      )
    )
      return 'organic_social';
    if (host) return 'referral';
    return 'direct';
  }

  var CONSENT = env.consentState || 'granted';

  // NOTE: visit_number counts lifetime FULL PAGE LOADS (localStorage counter
  // incremented once per hard load), not sessions — a reload mid-visit
  // increments it. Rename/re-derive if session semantics are ever needed.
  function firstTouch() {
    if (CONSENT !== 'granted')
      return { is_new_visitor: null, visit_number: null };
    try {
      var raw = window.localStorage.getItem('__kite_ft');
      if (!raw) {
        window.localStorage.setItem('__kite_ft', JSON.stringify({ v: 1 }));
        return { is_new_visitor: true, visit_number: 1 };
      }
      var data = JSON.parse(raw);
      var n = (data.v || 1) + 1;
      window.localStorage.setItem('__kite_ft', JSON.stringify({ v: n }));
      return { is_new_visitor: false, visit_number: n };
    } catch (e) {
      return { is_new_visitor: null, visit_number: null };
    }
  }

  function pageContext() {
    var main = document.querySelector('[data-kite-page-id]');
    return {
      page_id: main ? main.getAttribute('data-kite-page-id') : undefined,
      page_type: main ? main.getAttribute('data-kite-page-type') : undefined,
    };
  }

  function registerEnvelope(includeFirstTouch) {
    var props = {
      schema_version: SCHEMA_VERSION,
      website_id: env.websiteId,
      account_id: env.accountId,
      traffic_source: trafficSource(),
      viewport_bucket: viewportBucket(),
      consent_state: CONSENT,
    };
    if (env.goalType) props.site_goal = env.goalType;
    var page = pageContext();
    for (var k in page) if (page[k] !== undefined) props[k] = page[k];
    if (includeFirstTouch) {
      var ft = firstTouch();
      props.is_new_visitor = ft.is_new_visitor;
      props.visit_number = ft.visit_number;
    }
    try {
      if (window.posthog) window.posthog.register(props);
    } catch (e) {
      if (DEBUG && window.console)
        window.console.warn('[kite] register failed', e);
    }
  }

  // ---- once-per-pageview guards -------------------------------------------

  var seen = {};
  function once(key) {
    if (seen[key]) return false;
    seen[key] = true;
    return true;
  }

  var keyCounter = 0;
  function elementKey(el) {
    if (!el.__kiteKey) el.__kiteKey = ++keyCounter;
    return el.__kiteKey;
  }

  // ---- universal page lifecycle -------------------------------------------

  var pageStart = Date.now();
  var activeMs = 0;
  var lastActive = Date.now();
  var maxScrollPct = 0;
  var interactionCount = 0;
  var loadSource = 'initial';
  // The conversion-hook form the visitor last submitted, so __kite.conversion
  // attributes the goal to that copy (not the document-first match). Null after
  // navigation: a hook fired on a later page falls back to querySelector.
  var lastHookedSubmitEl = null;

  // ONE reset point for every per-pageview counter. Resetting fields ad hoc in
  // onRouteChange is how interaction_count once leaked across SPA routes
  // (cumulative counts in every later page_engaged) — add new per-page state
  // HERE, never as a loose assignment at a call site.
  function resetPageState(source) {
    seen = {};
    // Clear PENDING section_viewed timers, not just the map: a surface >=50%
    // visible for <1s at navigation still has a live setTimeout that would fire
    // against the NEW page (stray section_viewed, and via the fresh once-key it
    // could even suppress the new page's legitimate one).
    for (var k in surfaceTimers) clearTimeout(surfaceTimers[k]);
    surfaceTimers = {};
    pageStart = Date.now();
    activeMs = 0;
    lastActive = Date.now();
    maxScrollPct = 0;
    interactionCount = 0;
    loadSource = source;
    lastHookedSubmitEl = null;
  }
  // Track path (excluding hash) so in-page anchor clicks (#features) are not
  // counted as pageviews — only real route changes (pathname/search) are.
  var lastPath = location.pathname + location.search;

  function emitPageViewed() {
    var ctx = pageContext();
    capture('page_viewed', {
      load_source: loadSource,
      page_id: ctx.page_id,
      page_type: ctx.page_type,
    });
  }

  function accumulateActive() {
    if (document.visibilityState === 'visible')
      activeMs += Date.now() - lastActive;
    lastActive = Date.now();
  }

  function emitPageEngagement() {
    // visibilitychange(hidden) and pagehide both fire on a normal unload — guard
    // so dwell/scroll/interaction metrics are not double-counted. Reset per SPA
    // route via onRouteChange's `seen = {}`.
    if (!once('page_engaged')) return;
    accumulateActive();
    // Flush dwell for any surface still in view at unload; section_engaged
    // otherwise only fires when a surface LEAVES the viewport, losing the
    // terminal surface of nearly every session.
    each(document.querySelectorAll('[data-kite-surface]'), function (el) {
      maybeSectionEngaged(el);
    });
    capture('page_engaged', {
      active_time_ms: activeMs,
      wall_time_ms: Date.now() - pageStart,
      max_scroll_pct: maxScrollPct,
      interaction_count: interactionCount,
    });
  }

  function onScroll() {
    var doc = document.documentElement;
    var scrollable = doc.scrollHeight - window.innerHeight;
    if (scrollable <= 0) {
      // Page fits the viewport — nothing to scroll. Record full depth for
      // page_engaged but do NOT emit synthetic scroll_depth_reached events
      // (which previously fired all of 25/50/75/100 at load with time≈0).
      maxScrollPct = 100;
      return;
    }
    var pct = Math.min(100, Math.round((window.scrollY / scrollable) * 100));
    if (pct > maxScrollPct) maxScrollPct = pct;
    [25, 50, 75, 100].forEach(function (m) {
      if (pct >= m && once('scroll_' + m)) {
        capture('scroll_depth_reached', {
          depth_pct: m,
          time_to_depth_ms: Date.now() - pageStart,
        });
      }
    });
  }

  // ---- universal surface lifecycle ----------------------------------------

  var surfaceTimers = {};
  var surfaceObserver = null;
  function observeSurfaces() {
    if (!('IntersectionObserver' in window)) return;
    // SPA navigations re-run this; disconnect the previous observer so it does
    // not keep firing on the old DOM and double-count section views.
    if (surfaceObserver) surfaceObserver.disconnect();
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          var el = entry.target;
          var key = elementKey(el);
          // A surface taller than the viewport can never have >=50% of ITS OWN
          // area on screen, so also treat "fills >=50% of the viewport" as viewed
          // (otherwise hero / long-form sections never emit section_viewed).
          var rect = entry.intersectionRect;
          var enough =
            entry.isIntersecting &&
            (entry.intersectionRatio >= 0.5 ||
              (rect && rect.height >= (window.innerHeight || 0) * 0.5));
          if (enough) {
            if (surfaceTimers[key]) return;
            surfaceTimers[key] = setTimeout(function () {
              emitSectionViewed(el);
            }, 1000);
          } else {
            if (surfaceTimers[key]) {
              clearTimeout(surfaceTimers[key]);
              delete surfaceTimers[key];
            }
            maybeSectionEngaged(el);
          }
        });
      },
      { threshold: [0, 0.25, 0.5, 0.75, 1] },
    );
    surfaceObserver = io;
    each(document.querySelectorAll('[data-kite-surface]'), function (n) {
      io.observe(n);
    });
  }

  function emitSectionViewed(el) {
    var ctx = surfaceContext(el);
    if (once('section_viewed_' + ctx.surface_id)) {
      capture('section_viewed', {
        surface_id: ctx.surface_id,
        surface_type: ctx.surface_type,
        position_index: toInt(el.getAttribute('data-kite-position')),
        time_to_view_ms: Date.now() - pageStart,
      });
    }
    el.__kiteEnteredAt = Date.now();
  }

  function maybeSectionEngaged(el) {
    if (!el.hasAttribute('data-kite-surface') || !el.__kiteEnteredAt) return;
    var ctx = surfaceContext(el);
    capture('section_engaged', {
      surface_id: ctx.surface_id,
      dwell_ms: Date.now() - el.__kiteEnteredAt,
    });
    el.__kiteEnteredAt = 0;
  }

  // ---- stamp-driven interaction handlers (the closed vocabulary) ----------

  function onClick(e) {
    interactionCount++;

    // Fire-and-forget conversion (call / WhatsApp / external link): the goal
    // completes on click, so count it now. A conversion on (or inside) a <form>
    // completes on SUBMIT, not click — skip it here; onSubmit / the success hook
    // fires it, and a scroll-to-form CTA carries no conversion stamp at all.
    var conv = closestAttr(e.target, 'data-kite-conversion');
    if (conv) {
      var convIsForm =
        (conv.tagName && conv.tagName.toLowerCase() === 'form') ||
        !!closestAttr(e.target, 'data-kite-form-type');
      if (!convIsForm) {
        // A hook-marked NON-form conversion (JS/async widget: booking modal,
        // checkout popover) completes in its own success handler via
        // window.__kite.conversion — the click is only the attempt. Firing
        // here too would double-count every widget conversion.
        if (!conv.hasAttribute('data-kite-conversion-hook')) {
          emitGoal(conv);
        }
        return; // the goal is the only event for this interaction
      }
      // Form-conversion submit control clicked: fall through to plain click
      // tracking; the goal is emitted only on a successful submit.
    }

    var cta = closestAttr(e.target, 'data-kite-cta-id');
    if (cta && !cta.hasAttribute('data-kite-conversion')) {
      // Item dimension: loop-rendered CTAs share one cta_id (the slot); the
      // per-item stamp (on the CTA or an ancestor card) tells items apart.
      var ctaItem = closestAttr(e.target, 'data-kite-item');
      emitStamped(cta, 'cta_clicked', {
        cta_id: cta.getAttribute('data-kite-cta-id'),
        role: cta.getAttribute('data-kite-role') || undefined,
        label: text(cta),
        item_id: ctaItem ? ctaItem.getAttribute('data-kite-item') : undefined,
      });
    }

    var nav = closestAttr(e.target, 'data-kite-nav');
    if (nav) {
      // Deliberately NOT evName(): nav links are non-nameable (fixed event,
      // identity rides in nav_id) or per-site nav names would explode cardinality.
      capture('nav_clicked', {
        kite_event_type: 'nav_clicked',
        nav_id: nav.getAttribute('data-kite-nav'),
        nav_location: nav.getAttribute('data-kite-nav-location') || undefined,
        link_text: text(nav),
        destination_url: nav.getAttribute('href') || undefined,
      });
    }

    var expand = closestAttr(e.target, 'data-kite-expand');
    // Once-key by the STAMP value, not elementKey(): a React re-render replaces
    // the DOM node, and a per-instance key would re-fire content_expanded for a
    // section the visitor already expanded this pageview.
    if (expand && once('expand_' + expand.getAttribute('data-kite-expand'))) {
      emitStamped(expand, 'content_expanded', {
        expand_id: expand.getAttribute('data-kite-expand'),
        label: text(expand),
      });
    }
  }

  function onSubmit(e) {
    var form = closestAttr(e.target, 'data-kite-form-type');
    if (!form) return;
    // The conversion may be on the <form> itself or on a control inside it.
    var convEl = form.hasAttribute('data-kite-conversion')
      ? form
      : form.querySelector && form.querySelector('[data-kite-conversion]');
    if (convEl) {
      // JS/async form (data-kite-conversion-hook): it fires the goal from its own
      // success handler via window.__kite.conversion(...). The native submit event
      // fires even for a submission the app later rejects, so do NOT fire the goal
      // here — but DO record the ATTEMPT, or attempted-vs-completed is invisible
      // (server-side failures would look identical to never trying). Literal
      // 'form_submitted' on purpose: evName(form, …) would resolve to the GOAL's
      // authored name and corrupt the funnel.
      if (
        (convEl.hasAttribute &&
          convEl.hasAttribute('data-kite-conversion-hook')) ||
        form.hasAttribute('data-kite-conversion-hook')
      ) {
        lastHookedSubmitEl = convEl;
        capture(
          'form_submitted',
          withSurface(form, {
            kite_event_type: 'form_submitted',
            form_type: form.getAttribute('data-kite-form-type'),
            conversion_attempt: true,
          }),
        );
        return;
      }
      // Plain HTML form: the submit event fires only AFTER native validation
      // passes (empty/invalid required fields block it), so reaching here means a
      // successful submit → the goal.
      emitGoal(convEl);
      return;
    }
    emitStamped(form, 'form_submitted', {
      form_type: form.getAttribute('data-kite-form-type'),
    });
  }

  // Track a FAILED submit attempt (e.g. Submit clicked with an empty/invalid
  // required field) as a plain, non-conversion event so it is visible without
  // inflating the goal. The `invalid` event fires per-field and does not bubble,
  // so listen in the capture phase and de-dupe the per-field burst to one event
  // per attempt (a new attempt fires a fresh burst on the next tick).
  var formFailPending = false;
  function onInvalid(e) {
    var field = e.target;
    var form =
      field && field.form
        ? closestAttr(field.form, 'data-kite-form-type')
        : null;
    if (!form || formFailPending) return;
    formFailPending = true;
    setTimeout(function () {
      formFailPending = false;
    }, 0);
    capture(
      'form_submit_failed',
      withSurface(form, {
        kite_event_type: 'form_submit_failed',
        form_type: form.getAttribute('data-kite-form-type'),
      }),
    );
  }

  // Item exposure: one item_viewed per unique data-kite-item value per pageview
  // when the element is >=50% visible. The once-key is the ITEM VALUE, so a
  // card and its inner button sharing a slug emit a single event, and a React
  // re-render (new DOM node) cannot re-fire it. Answers "how many items does a
  // visitor browse" — the gallery/collection blind spot.
  var itemObserver = null;
  function observeItems() {
    if (!('IntersectionObserver' in window)) return;
    if (itemObserver) itemObserver.disconnect();
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting || entry.intersectionRatio < 0.5) return;
          var el = entry.target;
          var value = el.getAttribute('data-kite-item');
          if (!value || !once('item_view_' + value)) return;
          io.unobserve(el);
          capture(
            'item_viewed',
            withSurface(el, {
              kite_event_type: 'item_viewed',
              item_id: value,
            }),
          );
        });
      },
      { threshold: [0.5] },
    );
    itemObserver = io;
    each(document.querySelectorAll('[data-kite-item]'), function (n) {
      io.observe(n);
    });
  }

  function wireMedia() {
    each(document.querySelectorAll('[data-kite-media]'), function (el) {
      // SPA navigations re-run this; a media element that persists across routes
      // would otherwise accumulate listeners and fire media_engaged N times. Mark
      // each element once.
      if (el.__kiteMediaWired) return;
      el.__kiteMediaWired = true;
      el.addEventListener('play', function () {
        // Stamp-keyed like content_expanded above: a re-rendered (replaced)
        // media node must not re-fire media_engaged within the same pageview.
        if (once('media_play_' + el.getAttribute('data-kite-media'))) {
          emitStamped(el, 'media_engaged', {
            media_id: el.getAttribute('data-kite-media'),
            action: 'play',
          });
        }
      });
    });
  }

  // ---- SPA navigation ------------------------------------------------------

  function onRouteChange() {
    var path = location.pathname + location.search;
    if (path === lastPath) return; // hash-only / in-page anchor — not a pageview
    lastPath = path;
    accumulateActive();
    emitPageEngagement();
    resetPageState('spa_navigation');
    registerEnvelope(false);
    emitPageViewed();
    observeSurfaces();
    observeItems();
    wireMedia();
    // Mirror start()'s load-time scroll seeding: a page that fits the viewport
    // never fires a scroll event, so without this a short SPA-navigated page
    // reports max_scroll_pct 0 while the same page hard-loaded reports 100.
    onScroll();
  }

  function patchHistory() {
    ['pushState', 'replaceState'].forEach(function (m) {
      var orig = history[m];
      history[m] = function () {
        var r = orig.apply(this, arguments);
        setTimeout(onRouteChange, 0);
        return r;
      };
    });
    window.addEventListener('popstate', function () {
      setTimeout(onRouteChange, 0);
    });
  }

  // ---- boot ----------------------------------------------------------------

  function start() {
    registerEnvelope(true);
    emitPageViewed();
    observeSurfaces();
    observeItems();
    wireMedia();
    patchHistory();

    document.addEventListener('click', onClick, true);
    document.addEventListener('submit', onSubmit, true);
    document.addEventListener('invalid', onInvalid, true);
    window.addEventListener('scroll', onScroll, { passive: true });
    document.addEventListener('keydown', function () {
      interactionCount++;
    });
    document.addEventListener('visibilitychange', function () {
      accumulateActive();
      if (document.visibilityState === 'hidden') emitPageEngagement();
    });
    window.addEventListener('pagehide', emitPageEngagement);
    onScroll();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
