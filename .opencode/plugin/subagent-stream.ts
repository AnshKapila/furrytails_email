// @ts-nocheck — runs under Bun on the sandbox (node/Bun globals); no
// TypeScript toolchain in this repo compiles it.
// Streams sub-agent (Task tool child session) activity into the per-run
// NDJSON stream log so the platform worker log shows planner/executor/
// verifier steps live, not just the orchestrator's.
//
// Why a plugin: `opencode run --format json` filters stdout to the root
// session (run.ts: `if (part.sessionID !== sessionID) continue`), but the
// plugin `event` hook receives every Bus event unfiltered — child sessions
// included. We append child-session events to $OPENCODE_STREAM_LOG, the
// same file `_poll_stream_log` (opencode_cli.py) already tails. Verified
// against opencode v1.14.51 source (plugin/index.ts Bus.subscribeAll →
// hook["event"]; tool/task.ts child Session.create with parentID).
//
// Emitted line shape (parsed by `_process_json_line`'s "subagent" branch):
//   {"type": "subagent", "kind": "start|tool|text|step_finish|error",
//    "agent": "planner", "subagent_session_id": "ses_...", ...}
// The distinct top-level type + `subagent_session_id` key (never plain
// `sessionID`) keep these lines out of the root session-id capture and the
// assistant-message/tool handlers for the orchestrator's own stream.
import { appendFileSync } from "node:fs";
// Infra and coding plugins are merged into one sandbox .opencode/plugin/ tree;
// runtime-state.ts is supplied by infra/plugins/lib (covered by the merge test).
import { currentLogPath } from "./lib/runtime-state";

const MAX_FIELD_CHARS = 2000;
// Tool/text parts fire message.part.updated on every state transition;
// dedupe on part id + status so each tool call logs once per terminal
// status and each text part logs once.
const seen = new Set<string>();
const MAX_SEEN = 5000;

// Child session title is `<description> (@<name> subagent)` (tool/task.ts).
const AGENT_RE = /@([\w-]+) subagent/;

function clip(value: unknown): string {
  const text = typeof value === "string" ? value : JSON.stringify(value ?? "");
  return text.length > MAX_FIELD_CHARS
    ? text.slice(0, MAX_FIELD_CHARS) + "…"
    : text;
}

export const SubagentStreamLog = async () => {
  // sessionID -> agent name, learned from session.updated events that
  // carry a parentID. Parts arriving for unknown sessions (the root
  // orchestrator session) are ignored — stdout already covers those.
  const children = new Map<string, string>();

  const emit = (data: Record<string, unknown>) => {
    try {
      const logPath = currentLogPath();
      if (!logPath) return;
      appendFileSync(
        logPath,
        JSON.stringify({ type: "subagent", ...data }) + "\n"
      );
    } catch {
      // Logging must never break the run.
    }
  };

  const once = (key: string): boolean => {
    if (seen.has(key)) return false;
    if (seen.size >= MAX_SEEN) seen.clear();
    seen.add(key);
    return true;
  };

  return {
    event: async ({ event }: { event: { type: string; properties?: any } }) => {
      try {
        const props = event?.properties ?? {};

        if (event.type === "session.updated") {
          const info = props.info ?? {};
          const sid = props.sessionID ?? info.id;
          if (!info.parentID || !sid || children.has(sid)) return;
          const agent =
            AGENT_RE.exec(String(info.title ?? ""))?.[1] ?? "subagent";
          children.set(sid, agent);
          emit({
            kind: "start",
            agent,
            subagent_session_id: sid,
            title: clip(info.title ?? ""),
          });
          return;
        }

        if (event.type === "message.part.updated") {
          const part = props.part ?? {};
          const agent = children.get(part.sessionID);
          if (!agent) return;
          const base = { agent, subagent_session_id: part.sessionID };

          if (part.type === "tool") {
            const status = part.state?.status;
            if (status !== "completed" && status !== "error") return;
            if (!once(`${part.id}:${status}`)) return;
            const input = part.state?.input ?? {};
            emit({
              ...base,
              kind: "tool",
              tool: part.tool,
              status,
              file_path: input.filePath ?? input.path ?? "",
              input: clip(input),
              output: clip(part.state?.output ?? part.state?.error ?? ""),
            });
            return;
          }

          if (part.type === "text" && part.time?.end) {
            if (!once(`${part.id}:text`)) return;
            emit({ ...base, kind: "text", text: clip(part.text ?? "") });
            return;
          }

          if (part.type === "step-finish") {
            if (!once(`${part.id}:step`)) return;
            emit({
              ...base,
              kind: "step_finish",
              reason: part.reason ?? "",
              tokens: part.tokens ?? {},
            });
          }
          return;
        }

        if (event.type === "session.error") {
          const sid = props.sessionID;
          const agent = sid ? children.get(sid) : undefined;
          if (!agent) return;
          emit({
            kind: "error",
            agent,
            subagent_session_id: sid,
            error: clip(props.error ?? {}),
          });
        }
      } catch {
        // Logging must never break the run.
      }
    },
  };
};
