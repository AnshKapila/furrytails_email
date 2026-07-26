"""Shared utilities for one-shot LLM-call scripts (planners, generators).

Runs on the E2B sandbox at /top/e2b/. No external dependencies beyond stdlib.
All calls go through the OpenAI-compatible chat-completions surface exposed by
the metadata proxy, so the same helper works for OpenAI, Anthropic, and Google
models — only the ``model`` argument changes.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

# A degenerate upstream response (no choices, or null/empty content) is
# transient with reasoning models — gemini-3.1-pro-preview intermittently
# returns ``content: null`` after a long reasoning turn, never emitting the
# answer — and a fresh call almost always succeeds. ``call_llm`` retries such
# responses in-process so recovery does not fall to the caller (e.g. the
# opencode agent re-running an entire planning script), which is slower and
# non-deterministic. One retry covers the common single-null case while keeping
# worst-case latency bounded; the caller's own retry remains the outer backstop.
_EMPTY_RESPONSE_RETRIES = 1
_EMPTY_RESPONSE_BACKOFF_SECS = 1.0

# ``call_llm_parsed`` makes at most this many call+parse attempts. One retry
# keeps worst-case latency bounded at ~2x a single call; the driving agent's
# own re-run of the whole script remains the outer backstop.
_PARSED_CALL_ATTEMPTS = 2


def proxy_url(node_name: str) -> str:
    """Build the session-scoped metadata-proxy URL for an LLM call."""
    workflow = os.environ.get("OR_TRACE_WORKFLOW_NAME", "") or "_"
    message = os.environ.get("OR_TRACE_MESSAGE_ID", "") or "_"
    node = urllib.parse.quote(node_name, safe="")
    workflow_seg = urllib.parse.quote(workflow, safe="")
    message_seg = urllib.parse.quote(message, safe="")
    return f"http://localhost:8787/s/{node}/{workflow_seg}/{message_seg}/v1/chat/completions"


def _post_chat_completions(
    *,
    url: str,
    payload: dict,
    api_key: str,
    timeout: int | None,
) -> str:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        response = json.load(resp)

    choices = response.get("choices") or []
    if not choices:
        raise RuntimeError(f"LLM returned no choices: {response!r}")
    content = (choices[0].get("message") or {}).get("content") or ""
    if not content.strip():
        raise RuntimeError(
            f"LLM returned empty content. usage={response.get('usage')!r}; "
            f"finish_reason={(choices[0] or {}).get('finish_reason')!r}"
        )
    return content


def call_llm(
    *,
    url: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    max_tokens: int | None = None,
    temperature: float = 0.7,
    reasoning_effort: str | None = None,
    timeout: int | None = 300,
) -> str:
    """Make a single OpenAI-compatible chat completion call and return the content.

    Provider-agnostic: pass ``model`` in the OpenRouter-prefixed form
    (``openai/...``, ``google/...``, ``anthropic/...``) and the proxy routes
    accordingly.

    ``timeout=None`` disables the urllib timeout entirely — useful for calls
    where the upstream model can take more than the default 300s and a
    caller's wrapper (e.g. the agent's bash tool) is the real budget.

    A degenerate response (no choices / null-or-empty content) is retried
    in-process — see ``_EMPTY_RESPONSE_RETRIES``.
    """
    payload: dict = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if reasoning_effort is not None:
        payload["reasoning"] = {"effort": reasoning_effort}

    for _ in range(_EMPTY_RESPONSE_RETRIES):
        try:
            return _post_chat_completions(
                url=url, payload=payload, api_key=api_key, timeout=timeout
            )
        except RuntimeError:
            # _post_chat_completions raises RuntimeError only for a degenerate
            # response (no choices / empty content), which is retryable. Network
            # and HTTP errors raise other types and propagate to the caller.
            time.sleep(_EMPTY_RESPONSE_BACKOFF_SECS)
    # Final attempt outside the loop: a still-degenerate response propagates
    # to the caller (and the structure proves to the type checker that every
    # path returns or raises).
    return _post_chat_completions(url=url, payload=payload, api_key=api_key, timeout=timeout)


def call_llm_parsed(*, parse, warnings: list[str], **call_kwargs):
    """Call the LLM and parse the response, retrying once in-process.

    Without this, both failure shapes fall to the driving agent as a blind
    full-script re-run — slower, non-deterministic, and (for the generator
    scripts) it abandons work already in flight, e.g. the image-generation
    future dispatched alongside the LLM call. Two shapes are retried:

    - transient transport errors (connection failures, timeouts, HTTP 5xx,
      degenerate responses) — retried with the identical payload;
    - parse failures (``parse`` raising ValueError/json.JSONDecodeError) —
      retried with the parse error appended after the user prompt as a
      correction note. The model does not see its previous (oversized)
      response, so this is a re-roll with explicit JSON discipline, not a
      true repair — but the static prompt prefix is unchanged, preserving
      provider prefix caching.

    HTTP 4xx errors are not retried: they recur deterministically.

    Each retry appends a breadcrumb to ``warnings`` (the caller's list, so
    breadcrumbs survive even when the final attempt raises). Returns the
    parsed value; raises the final attempt's error on exhaustion.
    """
    base_user_prompt = call_kwargs["user_prompt"]
    for attempt in range(1, _PARSED_CALL_ATTEMPTS + 1):
        is_last = attempt == _PARSED_CALL_ATTEMPTS
        try:
            response = call_llm(**call_kwargs)
        except urllib.error.HTTPError as e:
            if e.code < 500 or is_last:
                raise
            warnings.append(f"LLM call attempt {attempt} failed, retrying: HTTPError: {e}")
            continue
        except (urllib.error.URLError, TimeoutError, RuntimeError) as e:
            if is_last:
                raise
            warnings.append(f"LLM call attempt {attempt} failed, retrying: {type(e).__name__}: {e}")
            continue
        try:
            return parse(response)
        except (ValueError, json.JSONDecodeError) as e:
            if is_last:
                raise
            warnings.append(
                f"response parse failed on attempt {attempt}, retrying with the error fed back: {e}"
            )
            call_kwargs["user_prompt"] = (
                f"{base_user_prompt}\n\n"
                "## Correction\n"
                f"Your previous response could not be parsed: {e}. "
                "Respond again with ONLY the complete, valid JSON object — no markdown "
                "fences, no commentary, every string properly escaped and terminated."
            )
    raise AssertionError("unreachable: every final attempt returns or raises")


def read_file(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_frontmatter(text: str) -> str:
    """Drop YAML frontmatter (``---`` ... ``---``) from a SKILL.md body."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[i + 1 :]).lstrip("\n")
    return text


def read_rule(skills_dir: pathlib.Path, name: str) -> str:
    path = skills_dir / name / "SKILL.md"
    if not path.is_file():
        raise RuntimeError(f"Rule file missing: {path}")
    return strip_frontmatter(read_file(path))


def load_prompt(
    name: str,
    variables: dict[str, str] | None = None,
    *,
    prompts_dir: pathlib.Path,
) -> str:
    """Load a prompt template and substitute ``${key}`` placeholders."""
    prompt_path = prompts_dir / name
    template = read_file(prompt_path)
    if variables:
        for key, value in variables.items():
            template = template.replace(f"${{{key}}}", str(value))
    return template


def strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences that LLMs occasionally emit around JSON."""
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else text
        if text.endswith("```"):
            text = text[: -len("```")].rstrip()
    return text
