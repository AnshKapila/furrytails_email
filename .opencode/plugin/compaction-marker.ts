// @ts-nocheck — runs under Bun on the sandbox (node/Bun globals); no
// TypeScript toolchain in this repo compiles it.
// Marks opencode auto-compaction summary messages in the per-run NDJSON
// stream log so the platform parser can keep them out of user-visible
// assistant output.
//
// Why: `opencode run --format json` emits a `text` event for EVERY completed
// text part of the root session (run.ts filters on sessionID only). When
// auto-compaction fires mid-turn, its summary is written as an assistant
// message in the SAME session, so its text streams out indistinguishable
// from the model's real reply — and the platform relayed it to users as
// chat/Slack content (including secrets the summary preserved from the
// session, e.g. "Critical Context" entries). The message-level `summary`
// flag never reaches stdout in json mode, so this plugin tees it into the
// stream log instead.
//
// The summary assistant message is created with `summary: true` BEFORE its
// content streams (compaction.ts builds the MessageV2.Assistant with
// `summary: true` and calls session.updateMessage(msg) ahead of
// processor.process), so this marker line lands in the stream log before
// the summary's final `text` event. Verified against opencode v1.14.51
// source (session/compaction.ts; cli/cmd/run.ts emit()).
//
// Emitted line shape (parsed by `_process_json_line`'s "compaction_summary"
// branch): {"type": "compaction_summary", "summary_message_id": "msg_...",
// "summary_session_id": "ses_..."}. The distinct key names (never plain
// `sessionID`) keep these lines out of the root session-id capture.
import { appendFileSync } from "node:fs";
import { currentLogPath } from "./lib/runtime-state";

const seen = new Set<string>();
const MAX_SEEN = 1000;

export const CompactionMarker = async () => {
  return {
    event: async ({ event }: { event: { type: string; properties?: any } }) => {
      try {
        if (event.type !== "message.updated") return;
        const info = event.properties?.info ?? {};
        // `message.updated` fires on creation and again on updates/finish;
        // dedupe so each summary message is marked once.
        if (info.role !== "assistant" || info.summary !== true || !info.id)
          return;
        if (seen.has(info.id)) return;
        if (seen.size >= MAX_SEEN) seen.clear();
        seen.add(info.id);
        const logPath = currentLogPath();
        if (!logPath) return;
        appendFileSync(
          logPath,
          JSON.stringify({
            type: "compaction_summary",
            summary_message_id: info.id,
            summary_session_id: info.sessionID ?? "",
          }) + "\n"
        );
      } catch {
        // Marking must never break the run.
      }
    },
  };
};
