import {
  calculateCost, createAssistantMessageEventStream, getCurrentTools,
  type AssistantMessage, type JsonObject, type Model, type SimpleStreamOptions,
  type TextContent, type ThinkingContent, type ToolCall, type TranscriptContext,
} from "@earendil-works/pi-ai";
import { count, isRecord, list, parse, record, runBridge, text } from "./bridge.ts";
import { attachReplay, makePayload, wireName } from "./transcript.ts";

export function streamClaudeCode(model: Model<string>, context: TranscriptContext, options: SimpleStreamOptions,
  workspace: () => Promise<string>) {
  const stream = createAssistantMessageEventStream();
  const message: AssistantMessage = {
    role: "assistant", api: model.api, provider: model.provider, model: model.id,
    content: [], stopReason: "pending", timestamp: Date.now(),
    usage: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, totalTokens: 0,
      cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 } },
  };
  void (async () => {
    let active: { index: number; block: TextContent | ThinkingContent } | undefined;
    const endBlock = () => {
      if (!active) return;
      const { index, block } = active;
      if (block.type === "text") stream.push({ type: "text_end", contentIndex: index, content: block.text, partial: message });
      else stream.push({ type: "thinking_end", contentIndex: index, content: block.thinking, partial: message });
      active = undefined;
    };
    const delta = (kind: "text" | "thinking", value: string) => {
      if (active?.block.type !== kind) {
        endBlock();
        const block: TextContent | ThinkingContent = kind === "text" ? { type: "text", text: "" } : { type: "thinking", thinking: "" };
        const index = message.content.length;
        message.content.push(block);
        active = { index, block };
        stream.push({ type: kind === "text" ? "text_start" : "thinking_start", contentIndex: index, partial: message });
      }
      if (!active) throw new Error("Claude Code content block was not initialized.");
      if (active.block.type === "text") active.block.text += value;
      else active.block.thinking += value;
      stream.push({ type: kind === "text" ? "text_delta" : "thinking_delta", contentIndex: active.index, delta: value, partial: message });
    };
    try {
      options.signal?.throwIfAborted();
      if (options.deferred || options.fetch || (options.maxRetries ?? 0) > 0) {
        throw new Error("Claude Code does not support deferred requests, custom fetch, or provider retries. Pi owns retries.");
      }
      if (options.headers && Object.keys(options.headers).some((key) => key.toLowerCase() !== "traceparent")) {
        throw new Error("Claude Code owns request headers and authentication; custom headers are unsupported.");
      }
      let payload = makePayload(model, context, options);
      const replacement = await options.onPayload?.(payload, model);
      if (replacement !== undefined) payload = record(parse(JSON.stringify(replacement)));
      const request: JsonObject = { payload, cwd: await workspace(),
        observeStream: Boolean(options.onProviderStreamEvent), observeResponse: Boolean(options.onResponse) };
      const names = new Map(getCurrentTools(context.messages).map((tool) => [wireName(tool.name), tool.name]));
      stream.push({ type: "start", partial: message });
      let result: JsonObject | undefined;
      for await (const raw of runBridge({ request, env: options.env, signal: options.signal })) {
        const event = record(raw);
        if (event.type === "error") {
          let detail = text(event.message);
          if (event.status === 400 && /prompt is too long|context[_ ]length[_ ]exceeded/i.test(detail)) {
            detail = `context_length_exceeded: ${detail}`;
          }
          throw new Error(detail);
        }
        if (event.type === "response") {
          const headers = record(event.headers);
          const normalized: Record<string, string> = {};
          for (const [key, value] of Object.entries(headers)) normalized[key] = text(value);
          await options.onResponse?.({ status: count(event.status), headers: normalized }, model);
        } else if (event.type === "provider_event") {
          await options.onProviderStreamEvent?.(event.event, model);
        } else if (event.type === "delta") {
          if (result) throw new Error("Claude Code emitted content after its final result.");
          if (event.kind !== "text" && event.kind !== "thinking") throw new Error("Claude Code returned an unknown delta.");
          delta(event.kind, text(event.delta));
        } else if (event.type === "result") {
          if (result) throw new Error("Claude Code returned more than one final result.");
          result = event;
        } else throw new Error("Claude Code returned an unknown bridge event.");
      }
      if (!result) throw new Error("Claude Code ended without a complete response.");
      endBlock();
      const finalText = text(result.text);
      const finalThinking = text(result.thinking);
      const shownText = message.content.filter((block) => block.type === "text").map((block) => block.text).join("");
      const shownThinking = message.content.filter((block) => block.type === "thinking").map((block) => block.thinking).join("");
      if (shownText !== finalText || shownThinking !== finalThinking) throw new Error("Claude Code final content disagrees with its stream.");
      const usage = record(record(result.usage).native_usage);
      message.usage.input = count(usage.input_tokens);
      message.usage.output = count(usage.output_tokens);
      message.usage.cacheRead = count(usage.cache_read_input_tokens ?? 0);
      message.usage.cacheWrite = count(usage.cache_creation_input_tokens ?? 0);
      if (isRecord(usage.cache_creation) && usage.cache_creation.ephemeral_1h_input_tokens !== undefined) {
        message.usage.cacheWrite1h = count(usage.cache_creation.ephemeral_1h_input_tokens);
        if (message.usage.cacheWrite1h > message.usage.cacheWrite) throw new Error("Claude Code returned inconsistent cache usage.");
      }
      message.usage.totalTokens = message.usage.input + message.usage.output + message.usage.cacheRead + message.usage.cacheWrite;
      message.usage.cost = calculateCost(model, message.usage);
      const rawCost = record(result.usage).native_cost;
      const cost = isRecord(rawCost) ? rawCost : undefined;
      const modelUsage = isRecord(cost?.modelUsage) ? Object.values(cost.modelUsage) : [];
      const total = cost?.total_cost_usd;
      const nativeCost = typeof total === "number" && Number.isFinite(total) && total >= 0 &&
        modelUsage.length > 0 && modelUsage.every((entry) => isRecord(entry) && entry.costBasis === "list");
      const catalogCost = Object.values(model.cost).some((rate) => rate > 0);
      if (nativeCost) message.usage.cost.total = count(total);
      message.diagnostics = [{ type: "claude_code_cost", timestamp: Date.now(), details: {
        source: nativeCost ? "native-list-estimate" : catalogCost ? "catalog-list-estimate" : "unavailable",
        components: catalogCost ? "catalog-list-estimate" : "unavailable",
        status: nativeCost || catalogCost ? "estimated" : "unknown",
        billing: "Not a subscription charge. Total and components may use different estimates. Zero with unavailable pricing means unknown, not free.",
      } }];
      message.rawStopReason = typeof result.rawStopReason === "string" ? result.rawStopReason : undefined;
      message.responseId = typeof result.responseId === "string" ? result.responseId : undefined;
      message.responseModel = typeof result.responseModel === "string" ? result.responseModel : undefined;
      const refusal = result.finish === "content_filter";
      const truncated = message.rawStopReason === "max_tokens" || message.rawStopReason === "model_context_window_exceeded";
      if (refusal && !finalText) {
        delta("text", typeof result.refusal === "string" && result.refusal ? result.refusal : "Claude declined this request.");
        endBlock();
      }
      if (!refusal && !truncated) {
        const tools = list(result.toolCalls).map((rawCall): ToolCall => {
          const call = record(rawCall);
          const name = names.get(text(call.name));
          if (!name || options.toolChoice === "none") throw new Error("Claude Code requested a tool outside Pi's declared inventory.");
          return { type: "toolCall", id: text(call.id), name, arguments: record(call.arguments) };
        });
        for (const tool of tools) {
          const index = message.content.length;
          message.content.push({ ...tool, arguments: {} });
          stream.push({ type: "toolcall_start", contentIndex: index, partial: message });
          message.content[index] = tool;
          stream.push({ type: "toolcall_delta", contentIndex: index, delta: JSON.stringify(tool.arguments), partial: message });
          stream.push({ type: "toolcall_end", contentIndex: index, toolCall: tool, partial: message });
        }
      }
      const hasTools = message.content.some((block) => block.type === "toolCall");
      message.stopReason = refusal ? "stop" : truncated || result.finish === "length" ? "length" : hasTools ? "toolUse" : "stop";
      if (!refusal && !truncated) attachReplay(message, result.replay);
      stream.push({ type: "done", reason: message.stopReason, message });
    } catch (error) {
      endBlock();
      message.diagnostics ??= [{ type: "claude_code_cost", timestamp: Date.now(), details: {
        source: "unavailable", components: "unavailable", status: "unknown",
        billing: "Request ended without complete accounting. Numeric zero means unknown, not free.",
      } }];
      message.stopReason = options.signal?.aborted ? "aborted" : "error";
      message.errorMessage = options.signal?.aborted ? "Claude Code request cancelled."
        : error instanceof Error ? error.message : "Claude Code request failed.";
      stream.push({ type: "error", reason: message.stopReason, error: message });
    } finally {
      stream.end();
    }
  })();
  return stream;
}
