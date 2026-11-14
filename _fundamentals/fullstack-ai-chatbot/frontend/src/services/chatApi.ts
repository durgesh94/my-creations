
import { API_BASE_URL } from "../config";

import type {
  AIProvider,
  ChatMessage,
} from "../types/chat";

interface ChatRequest {
  provider: AIProvider;
  messages: Pick<ChatMessage, "role" | "content">[];
}

interface ChatResponse {
  provider: AIProvider;
  response: string;
}

export async function sendChatMessage(
  request: ChatRequest,
  signal?: AbortSignal
): Promise<ChatResponse> {
  let response: Response;

  try {
    response = await fetch(
      `${API_BASE_URL}/api/v1/chat`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
        signal,
      }
    );
  } catch (error) {
    if (
      error instanceof DOMException &&
      error.name === "AbortError"
    ) {
      throw error;
    }

    throw new Error(
      "Unable to connect to FastAPI. Check that the backend is running."
    );
  }

  if (!response.ok) {
    let message = `API request failed (${response.status})`;

    try {
      const data: unknown = await response.json();

      if (
        typeof data === "object" &&
        data !== null &&
        "detail" in data &&
        typeof data.detail === "string"
      ) {
        message = data.detail;
      }
    } catch {
      // Keep the HTTP status error message.
    }

    throw new Error(message);
  }

  const data: ChatResponse = await response.json();

  if (
    typeof data.response !== "string" ||
    !data.response.trim()
  ) {
    throw new Error("AI returned an empty response");
  }

  return data;
}
