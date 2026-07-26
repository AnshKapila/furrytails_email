---
name: website-contact-form-management
description: >
  Use this skill when adding, wiring, or troubleshooting a visitor-submission
  form in the single-file HTML/Vite website template — for example "add a
  contact form", "make the form actually send", or "submissions are not
  arriving". It owns the injected `submitContactForm` runtime. For Next.js
  forms, follow `nextjs-code-writing`; use `website-visual-design` for styling.
mode: sandbox
---

# Contact form submissions

Use the platform-injected `submitContactForm(formElement)` runtime API to handle form submissions — never raw `fetch` or a module import in generated app HTML. The function takes an `HTMLFormElement`, extracts all fields (including email, subject, and body), and submits them to the platform's contact form endpoint at `/api/v1/website-contact-form-management/submit`. The form must include an `input[type="email"]`.

The backend route is already registered at `POST /api/v1/website-contact-form-management/submit` via `@app/backend-core/website-contact-form-management`. It validates the payload (email required, plus text_body/html_body/json_body) and forwards it to the platform API. Create no new backend routes for contact form submission.

The HTML email template is already handled by platform utilities. Create no custom email templates for contact form submissions.

# How submitContactForm becomes available

The platform injects two scripts at build time to make `submitContactForm` available inside the main `<script>` tag. The injection is gated on `id="main_script"` — if the main `<script>` tag is missing this ID, the injection silently does nothing and `submitContactForm` will never be available.

1. A `<script type="module">` is inserted immediately before the main `<script>` tag. It imports the utility from the platform package and dispatches a CustomEvent when ready:

```html
<script type="module">
import { submitContactForm } from '@appsmithorg/template-frontend/utility';
document.dispatchEvent(new CustomEvent('kite:core-ready', {
  detail: { submitContactForm }
}));
</script>
```

2. An event listener is injected at the start of the main `<script>` tag that receives the loaded function:

```js
let submitContactForm = null;
document.addEventListener('kite:core-ready', (e) => {
  submitContactForm = e.detail.submitContactForm;
});
```

Because the module loads asynchronously, `submitContactForm` starts as `null` and is populated once the module resolves. Always guard calls with a typeof check and provide a fallback simulation for development/preview when the platform script hasn't loaded:

```js
if (typeof submitContactForm === 'function') {
  await submitContactForm(e.target);
} else {
  await new Promise(resolve => setTimeout(resolve, 1500));
}
```

Generated code must not replicate this injection — the platform handles it automatically. The code inside the main `<script>` tag simply uses the `submitContactForm` variable that the injected listener populates.

# Wiring the submit handler

The submit event listener must be attached after the form element is in the DOM. Attach it inline inside the render function that creates the form — do not define a separate setup function. The existing codebase pattern is: render the HTML, then `document.getElementById('form-id').addEventListener('submit', ...)` in the same function. If you add a contact form to a page that already has a render function (e.g. `renderAbout`), add the listener at the end of that function body after the HTML is set.

## Verify before finishing

- The form contains a valid `input[type="email"]`.
- The runtime script that owns rendering has `id="main_script"`.
- The submit listener is attached after the form is inserted into the DOM.
- The handler calls the injected `submitContactForm(formElement)` and does not
  add a raw endpoint call or module import.
