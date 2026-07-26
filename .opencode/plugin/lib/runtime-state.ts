// @ts-nocheck — imported by sandbox OpenCode plugins under Bun.
// Shared by infra/plugins and coding/plugins: run_on_sandbox merges both source
// trees under one .opencode/plugin/ directory. Keep coding's relative import in
// sync if this module moves.
import { readFileSync } from "node:fs";

const RUNTIME_DIR = "/tmp/kite-opencode-runtime";

export function readState(name: string): string | undefined {
  try {
    return readFileSync(`${RUNTIME_DIR}/${name}`, "utf8").trim();
  } catch {
    return undefined;
  }
}

export function currentLogPath(): string | undefined {
  if (process.env["KITE_OPENCODE_REUSE_SERVER"] === "1") {
    const path = readState("stream-log-path");
    if (path) return path;
  }
  return process.env["OPENCODE_STREAM_LOG"];
}
