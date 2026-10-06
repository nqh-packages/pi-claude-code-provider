import { createHash } from "node:crypto";
import {
  collapseSystemMessages, getCurrentSystemPrompt, getCurrentTools,
  type AssistantMessage, type ImageContent, type JsonObject, type Model,
  type SimpleStreamOptions, type TextContent, type TranscriptContext,
} from "@earendil-works/pi-ai";
import { transformMessages } from "@earendil-works/pi-ai/api/transform-messages";
import { parse, record } from "./bridge.ts";

export function wireName(name: string): string {
  return /^[A-Za-z0-9_-]{1,50}$/.test(name) ? name : `tool_${createHash("sha256").update(name).digest("hex").slice(0, 40)}`;
}

function media(content: (TextContent | ImageContent)[]): JsonObject[] {
  return content.map((block): JsonObject => {
    if (block.type === "text") return { type: "text", text: block.text };
    return { type: "image", source: { type: "base64", media_type: block.mimeType, data: block.data } };
  });
}

export function projection(message: AssistantMessage): JsonObject {
  return {
    text: message.content.filter((block) => block.type === "text").map((block) => block.text).join(""),
    thinking: message.content.filter((block) => block.type === "thinking").map((block) => block.thinking).join(""),
    toolCalls: message.content.filter((block) => block.type === "toolCall").map((block) => ({
      id: block.id, name: block.name, arguments: block.arguments,
    })),
  };
}

export function attachReplay(message: AssistantMessage, replay: JsonObject["replay"]): void {
  const signature = JSON.stringify({ type: "claude-code-replay", version: 1, projection: projection(message), replay });
  const first = message.content[0];
  if (!first) return;
  if (first.type === "text") first.textSignature = signature;
  else if (first.type === "thinking") first.thinkingSignature = signature;
  else first.thoughtSignature = signature;
}

function replay(message: AssistantMessage): JsonObject["replay"] | undefined {
  const first = message.content[0];
  if (!first) return undefined;
  const signature = first.type === "text" ? first.textSignature
    : first.type === "thinking" ? first.thinkingSignature : first.thoughtSignature;
  if (!signature) return undefined;
  try {
    const envelope = record(parse(signature));
    if (envelope.type === "claude-code-replay" && envelope.version === 1 &&
      JSON.stringify(envelope.projection) === JSON.stringify(projection(message))) {
      return envelope.replay;
    }
  } catch { /* Foreign provider signatures are not this transport's replay carrier. */ }
  return undefined;
}

export function makePayload(model: Model<string>, context: TranscriptContext, options: SimpleStreamOptions): JsonObject {
  const collapsed = collapseSystemMessages(context);
  const tools = options.toolChoice === "none" ? [] : getCurrentTools(collapsed.messages);
  const messages: JsonObject[] = [];
  const system = getCurrentSystemPrompt(collapsed.messages);
  if (system) messages.push({ role: "system", content: system });
  const history = transformMessages(collapsed.messages, model,
    (id) => /^[A-Za-z0-9_-]{1,64}$/.test(id) ? id : `call_${createHash("sha256").update(id).digest("hex").slice(0, 48)}`);
  for (const message of history) {
    if (message.role === "system") continue;
    if (message.role === "user") {
      messages.push({ role: "user", content: typeof message.content === "string" ? message.content : media(message.content) });
    } else if (message.role === "toolResult") {
      messages.push({ role: "tool", tool_call_id: message.toolCallId, content: media(message.content), is_error: message.isError });
    } else {
      const visible = projection(message);
      const carrier = message.provider === model.provider && message.model === model.id ? replay(message) : undefined;
      messages.push({ role: "assistant", content: visible.text ?? "", tool_calls:
        message.content.filter((block) => block.type === "toolCall").map((block) => ({
          id: block.id, type: "function", function: { name: wireName(block.name), arguments: JSON.stringify(block.arguments) },
        })), ...(carrier ? { reasoning_details: carrier } : {}) });
    }
  }
  const declarations = tools.map((tool) => {
    if (tool.constrainedSampling && tool.constrainedSampling.type === "json_schema" && tool.constrainedSampling.strict === "require") {
      throw new Error(`Claude Code cannot enforce strict tool schema for ${tool.name}.`);
    }
    return { type: "function", function: { name: wireName(tool.name), description: tool.description,
      parameters: record(parse(JSON.stringify(tool.parameters))) } };
  });
  const effort = options.reasoning === "minimal" ? "low" : options.reasoning;
  return {
    model: model.id, messages, tools: declarations, max_tokens: options.maxTokens ?? model.maxTokens,
    timeout: (options.timeoutMs ?? 180_000) / 1000,
    extra_body: { reasoning: effort ? { enabled: true, effort } : { enabled: false } },
  };
}
