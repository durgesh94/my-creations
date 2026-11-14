
import { API_BASE_URL } from "../config";

import type {
  AIProvider,
  ChatMessage,
} from "../types/chat";

type ApiMessage = Pick<ChatMessage, "role" | "content">;

interface StreamRequest {
  provider: AIProvider;
  messages: ApiMessage[];
}

interface StreamCallbacks {
  onDelta: (text: string) => void;
}

interface StreamEvent {
  event: string;
  data: Record<string, unknown>;
}

function parseEvent(block: string): StreamEvent | null {
  let event = "message";
  const dataLines: string[] = [];

  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  if (!dataLines.length) return null;

  const data = JSON.parse(
    dataLines.join("\n")
  ) as Record<string, unknown>;

  return { event, data };
}

export async function streamChatMessage(
  request: StreamRequest,
  callbacks: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}/api/v1/chat/stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify(request),
        signal,
      }
    );
  } catch (error) {
    if (signal?.aborted) throw error;

    throw new Error(
      "Cannot connect to FastAPI backend"
    );
  }

  if (!response.ok) {
    throw new Error(
      `Streaming request failed: HTTP ${response.status}`
    );
  }

  if (!response.body) {
    throw new Error("Response body is not readable");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let buffer = "";
  let completed = false;

  function handleEvent(block: string) {
    const parsed = parseEvent(block);
    if (!parsed) return;

    if (parsed.event === "delta") {
      if (typeof parsed.data.content === "string") {
        callbacks.onDelta(parsed.data.content);
      }
    }

    if (parsed.event === "error") {
      throw new Error(
        typeof parsed.data.message === "string"
          ? parsed.data.message
          : "AI streaming failed"
      );
    }

    if (parsed.event === "done") {
      completed = true;
    }
  }

  try {
    while (true) {
      const { value, done } = await reader.read();

      if (done) break;

      buffer += decoder
        .decode(value, { stream: true })
        .replace(/\r\n/g, "\n");

      let boundary: number;

      while ((boundary = buffer.indexOf("\n\n")) !== -1) {
        const block = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);

        handleEvent(block);
      }
    }

    buffer += decoder.decode();

    if (buffer.trim()) {
      handleEvent(buffer);
    }

    if (!completed) {
      throw new Error(
        "Stream ended before completion"
      );
    }
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
