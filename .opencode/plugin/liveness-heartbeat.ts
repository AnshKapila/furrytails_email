// @ts-nocheck — runs under Bun on the sandbox (node/Bun globals); no
// TypeScript toolchain in this repo compiles it.
//
// Warm-server (attach) turns have no reliable stdout event stream: the attach
// CLI's SSE consumer can deliver zero events for an entire run (opencode
// 1.14.51), leaving the per-run stream log silent while the server-side
// session is actively working. The platform idle watchdog reads that silence
// as a stall and kills healthy runs at its hard threshold. This plugin runs
// inside the server process — the Bus `event` hook sees every event — and
// appends a throttled liveness line to the active turn's stream log so
// `_poll_stream_log` (opencode_cli.py) observes real activity. Content still
// flows through the attach CLI and its exit-time recovery; this line only
// proves the run is alive.
//
// Emitted line shape (freshness-stamped then discarded by
// `_process_json_line`'s "kite_liveness" branch):
//   {"type": "kite_liveness", "event_type": "message.part.updated"}
import { appendFileSync } from "node:fs";
// Infra and coding plugins are merged into one sandbox .opencode/plugin/ tree;
// runtime-state resolves the ACTIVE turn's stream log (republished atomically
// by the runner before every attach), so heartbeats land in the file the
// current turn's poller tails.
import { currentLogPath } from "./lib/runtime-state";

const HEARTBEAT_INTERVAL_MS = 15_000;
let lastBeatMs = 0;

export const LivenessHeartbeat = async () => {
  // The gap this closes exists only for warm-server turns; cold runs stream
  // stdout natively and need no extra lines.
  if (process.env["KITE_OPENCODE_REUSE_SERVER"] !== "1") return {};

  return {
    event: async ({ event }: { event: { type: string } }) => {
      try {
        const now = Date.now();
        if (now - lastBeatMs < HEARTBEAT_INTERVAL_MS) return;
        const logPath = currentLogPath();
        if (!logPath) return;
        lastBeatMs = now;
        appendFileSync(
          logPath,
          JSON.stringify({
            type: "kite_liveness",
            event_type: String(event?.type ?? ""),
          }) + "\n"
        );
      } catch {
        // Liveness must never break the run.
      }
    },
  };
};
