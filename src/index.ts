import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createProvider, type Model, type SimpleStreamOptions, type TranscriptContext } from "@earendil-works/pi-ai";
import { getBuiltinModels } from "@earendil-works/pi-ai/providers/all";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { count, inspectBridge, list, record, text } from "./bridge.ts";
import { streamClaudeCode } from "./stream.ts";

export default async function (pi: ExtensionAPI) {
  const id = "claude-code";
  const api = "claude-code-stream";
  const knownModels = getBuiltinModels("anthropic");
  const catalog = (value: Awaited<ReturnType<typeof inspectBridge>>): Model<typeof api>[] => list(value).flatMap((raw) => {
    const row = record(raw);
    const route = text(row.id);
    const known = knownModels.find((model) => model.id === route.replace(/\[1m\]$/, ""));
    // Uncatalogued routes need real capability metadata before Pi can advertise them.
    if (!known) return [];
    if (typeof row.thinkingOff !== "boolean") throw new Error("Claude Code catalog lacks thinking metadata.");
    return [{
      id: route, name: `Claude ${text(row.label)}${row.note ? ` (${text(row.note)})` : ""}`,
      provider: id, api, baseUrl: "process://claude", input: known.input, reasoning: known.reasoning,
      thinkingLevelMap: { ...known.thinkingLevelMap, minimal: "low", off: row.thinkingOff ? "off" : null },
      contextWindow: count(row.contextWindow), maxTokens: known.maxTokens, cost: known.cost,
    }];
  });
  const models = catalog(await inspectBridge("catalog"));
  let workspace: Promise<string> | undefined;
  const lifetime = new AbortController();
  const active = new Set<Promise<unknown>>();
  const streamSimple = (model: Model<typeof api>, context: TranscriptContext, options: SimpleStreamOptions = {}) => {
    const signal = options.signal ? AbortSignal.any([options.signal, lifetime.signal]) : lifetime.signal;
    const stream = streamClaudeCode(model, context, { ...options, signal },
      () => workspace ??= mkdtemp(join(tmpdir(), "pi-claude-code-")));
    const settled = stream.result();
    active.add(settled);
    void settled.finally(() => active.delete(settled));
    return stream;
  };
  const status = async (signal: AbortSignal) => record(await inspectBridge("status", signal));
  pi.registerProvider(createProvider({
    id, name: "Claude Code (subscription, experimental)", models,
    auth: { apiKey: {
      name: "Claude Code sign-in",
      check: async ({ signal }) => {
        const current = await status(signal);
        return current.available === true && current.logged_in === true ? { type: "api_key", source: "Claude Code sign-in" } : undefined;
      },
      resolve: async ({ signal }) => {
        const current = await status(signal);
        if (current.available !== true || current.logged_in !== true) return undefined;
        return { auth: {}, source: "Claude Code sign-in" };
      },
    } },
    fetchModels: async ({ signal, allowNetwork }) => allowNetwork ? catalog(await inspectBridge("discover", signal)) : models,
    api: { stream: streamSimple, streamSimple },
  }));
  pi.registerCommand("claude-code-status", {
    description: "Check the official Claude Code sign-in without reading or printing tokens.",
    handler: async (_args, ctx) => {
      const current = record(await inspectBridge("status", ctx.signal));
      ctx.ui.notify(current.logged_in === true ? `Claude Code signed in. ${text(current.plan)}. Select claude-code in /model.`
        : text(current.detail), current.logged_in === true ? "info" : "warning");
    },
  });
  pi.on("session_shutdown", async () => {
    lifetime.abort();
    await Promise.allSettled(active);
    if (workspace) await rm(await workspace, { recursive: true, force: true });
  });
}
