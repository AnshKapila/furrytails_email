// @ts-nocheck — runs under Bun on the sandbox (node/Bun globals); no
// TypeScript toolchain in this repo compiles it.
//
// Rejects file writes that land outside the session's workspace root.
//
// Why: website_create iteration agents occasionally emit `apply_patch` /
// `write` paths with the long `app_<uuid>/iterations/iterN/src` middle
// segment dropped (LLM path elision), so files silently land under the
// team EFS root (`/efs/team_<id>/apps/page.tsx`) instead of the iteration
// tree. When the stranded file is the home page, the iteration has no `/`
// route and its design slot fails readiness (V2-5796, observed twice in
// prod on 2026-07-20). The opencode `permission.edit/write` globs cannot
// express "outside the workspace" and the built-in external-directory
// permission is deliberately "allow" (headless runs would hang on "ask"),
// so this plugin is the enforcement point.
//
// Activation is opt-in per run: the platform sets KITE_WRITE_BOUNDARY to
// the absolute workspace root (the iteration dir) for website_create
// iteration sessions. Runs without the env — conversational edits, team
// tasks, migrations — load the plugin as a no-op. Throwing from
// `tool.execute.before` fails only that tool call; the error text is
// returned to the model, which retries with a corrected path.
import { isAbsolute, resolve } from "node:path";

// apply_patch envelope headers that carry a file path. `Move to:` is the
// rename destination — a rescue-move must also stay inside the boundary.
const PATCH_HEADER_RE =
  /^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$/gm;

// Arg keys are production-confirmed: the V2-5796 incident's own Loki
// captures carry `tool_input_preview={'patchText': '*** Begin Patch…'}`
// for apply_patch, and the stream-event fixtures pin `filePath` for
// write/edit. If either key drifts in an opencode upgrade, collectPaths
// finds nothing and the guard below fails CLOSED (rejects the call) —
// loud on the first DP run — instead of silently letting writes escape.
const GUARDED_TOOLS = new Set(["write", "edit", "patch", "apply_patch"]);

function collectPaths(tool: string, args: any): string[] {
  const paths: string[] = [];
  if (typeof args?.filePath === "string") paths.push(args.filePath);
  const patchText = args?.patchText;
  if (
    (tool === "patch" || tool === "apply_patch") &&
    typeof patchText === "string"
  ) {
    for (const match of patchText.matchAll(PATCH_HEADER_RE)) {
      paths.push(match[1].trim());
    }
  }
  return paths;
}

export const IterWriteBoundary = async () => {
  const boundaryEnv = process.env["KITE_WRITE_BOUNDARY"];
  if (!boundaryEnv || !isAbsolute(boundaryEnv)) return {};
  const boundary = resolve(boundaryEnv);

  return {
    "tool.execute.before": async (
      input: { tool: string; sessionID: string; callID: string },
      output: { args: any }
    ) => {
      if (!GUARDED_TOOLS.has(input.tool)) return;
      const paths = collectPaths(input.tool, output.args);
      // Fail closed on arg-shape drift: a guarded write tool whose target
      // path cannot be determined must not run unguarded. A valid call
      // always carries filePath / patchText, so this only fires when the
      // tool schema changed under us — a hard, immediately-visible break
      // beats silently reopening the stranded-write hole.
      if (paths.length === 0) {
        throw new Error(
          `iter-write-boundary: could not determine the target path of this ` +
            `'${input.tool}' call, so it was blocked. Retry with the standard ` +
            `arguments (filePath, or an apply_patch envelope with ` +
            `'*** Add/Update/Delete File:' headers).`
        );
      }
      // Relative paths resolve against the session cwd, which the runner
      // sets to the workspace root — those are inside by construction.
      for (const rawPath of paths) {
        const resolved = resolve(boundary, rawPath);
        if (resolved === boundary || resolved.startsWith(boundary + "/")) {
          continue;
        }
        throw new Error(
          `Path is outside this workspace and was not written: ${rawPath}\n` +
            `Every file of this iteration lives under ${boundary}/ — ` +
            `use a path relative to the workspace root (e.g. src/app/page.tsx).`
        );
      }
    },
  };
};
