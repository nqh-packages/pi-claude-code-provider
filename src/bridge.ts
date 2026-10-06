import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import type { JsonObject, JsonValue } from "@earendil-works/pi-ai";

const bridgePath = fileURLToPath(new URL("../runtime/bridge.py", import.meta.url));

function isList(value: JsonValue | undefined): value is readonly JsonValue[] {
  return Array.isArray(value);
}

export function isRecord(value: JsonValue | undefined): value is JsonObject {
  return value !== null && value !== undefined && typeof value === "object" && !isList(value);
}

export function record(value: JsonValue | undefined): JsonObject {
  if (!isRecord(value)) throw new Error("Claude Code bridge returned an invalid object.");
  return value;
}

export function text(value: JsonValue | undefined): string {
  if (typeof value !== "string") throw new Error("Claude Code bridge returned invalid text.");
  return value;
}

export function count(value: JsonValue | undefined): number {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    throw new Error("Claude Code bridge returned an invalid count.");
  }
  return value;
}

export function list(value: JsonValue | undefined): readonly JsonValue[] {
  if (!Array.isArray(value)) throw new Error("Claude Code bridge returned an invalid list.");
  return value;
}

function isJson(value: unknown): value is JsonValue {
  if (value === null || typeof value === "string" || typeof value === "boolean") return true;
  if (typeof value === "number") return Number.isFinite(value);
  if (Array.isArray(value)) return value.every(isJson);
  return typeof value === "object" && Object.values(value).every(isJson);
}

export function parse(value: string): JsonValue {
  const decoded: unknown = JSON.parse(value);
  if (!isJson(decoded)) throw new Error("Claude Code bridge returned invalid JSON.");
  return decoded;
}

export async function* runBridge({ operation, request, env, signal }: {
  operation?: "status" | "catalog" | "discover";
  request?: JsonObject;
  env?: Record<string, string>;
  signal?: AbortSignal;
}): AsyncGenerator<JsonValue, void, unknown> {
  signal?.throwIfAborted();
  const child = spawn(env?.PI_CLAUDE_CODE_PYTHON ?? process.env.PI_CLAUDE_CODE_PYTHON ?? "python3",
    ["-B", "-u", bridgePath, ...(operation ? [operation] : [])], {
      env: { ...process.env, ...env }, stdio: ["pipe", "pipe", "ignore"],
    });
  const completion = new Promise<{ code: number | null; error?: Error }>((resolve) => {
    child.once("error", (error) => resolve({ code: null, error }));
    child.once("close", (code) => resolve({ code }));
  });
  child.stdin.on("error", () => { /* A failed or cancelled child can close its input first. */ });
  let closed = false;
  let force: ReturnType<typeof setTimeout> | undefined;
  child.once("close", () => { closed = true; clearTimeout(force); });
  const cancel = () => {
    if (!closed && !force) {
      child.stdin.end(`${JSON.stringify({ type: "cancel" })}\n`);
      // Let Python close its native client first. Windows SIGTERM is an abrupt kill.
      force = setTimeout(() => child.kill("SIGKILL"), 10_000);
      force.unref();
    }
  };
  const abort = () => cancel();
  signal?.addEventListener("abort", abort, { once: true });
  if (signal?.aborted) cancel();
  if (request && !signal?.aborted) child.stdin.write(`${JSON.stringify(request)}\n`);
  else child.stdin.end();
  child.stdout.setEncoding("utf8");
  let buffer = "";
  try {
    // JSONL splits only on LF, not Unicode paragraph/line separators.
    for await (const chunk of child.stdout) {
      if (typeof chunk !== "string") throw new Error("Claude Code bridge did not return UTF-8 text.");
      buffer += chunk;
      let newline: number;
      while ((newline = buffer.indexOf("\n")) !== -1) {
        const line = buffer.slice(0, newline).replace(/\r$/, "");
        buffer = buffer.slice(newline + 1);
        if (!line) continue;
        const value = parse(line);
        yield value;
        if (request && !closed && !signal?.aborted) {
          const kind = record(value).type;
          if (kind === "response" || kind === "provider_event") {
            child.stdin.write(`${JSON.stringify({ type: "ack" })}\n`);
          }
        }
      }
    }
    const exit = await completion;
    if (buffer.trim()) throw new Error("Claude Code bridge ended with a partial JSONL record.");
    if (exit.error) throw new Error("Cannot start Python. Install Python 3.10+ or set PI_CLAUDE_CODE_PYTHON.");
    if (exit.code !== 0) throw new Error("Claude Code bridge exited before completing the request.");
    signal?.throwIfAborted();
  } finally {
    signal?.removeEventListener("abort", abort);
    if (!closed) {
      cancel();
      await completion;
      clearTimeout(force);
    }
  }
}

export async function inspectBridge(operation: "status" | "catalog" | "discover", signal?: AbortSignal) {
  let result: JsonValue | undefined;
  const timeout = AbortSignal.timeout(operation === "discover" ? 30_000 : 25_000);
  for await (const value of runBridge({ operation, signal: signal ? AbortSignal.any([signal, timeout]) : timeout })) {
    result = value;
  }
  if (result === undefined) throw new Error("Claude Code bridge returned no setup information.");
  return result;
}
