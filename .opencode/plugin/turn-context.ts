// @ts-nocheck — runs under Bun on the sandbox (node/Bun globals); no
// TypeScript toolchain in this repo compiles it.
//
// A persistent OpenCode server keeps the process environment from its first
// turn. Refresh the two per-turn values needed by commands the agent launches:
// trace attribution and the short-lived capability token. The runner publishes
// both with atomic renames before `opencode run --attach`, so no hook can read
// a partially-written value. Platform conversations are single-flight, making
// the newest values unambiguous.
import { readState } from "./lib/runtime-state";

export const TurnContext = async () => {
  if (process.env["KITE_OPENCODE_REUSE_SERVER"] !== "1") return {};

  return {
    "shell.env": async (
      _input: unknown,
      output: { env: Record<string, string> }
    ) => {
      const messageID = readState("active-message-id");
      const sandboxToken = readState("sandbox-token");
      // An existing empty state file is an explicit clear for this turn, not a
      // request to inherit the persistent server's first-turn environment.
      if (messageID !== undefined) output.env.OR_TRACE_MESSAGE_ID = messageID;
      if (sandboxToken !== undefined)
        output.env.KITE_SANDBOX_TOKEN = sandboxToken;
    },
  };
};
