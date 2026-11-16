
import { API_BASE_URL } from "../config";

export interface AgentChatRequest {
  conversation_id: string;
  message: string;
}

export interface AgentChatResponse {
  conversation_id: string;
  response: string;
}

export async function sendAgentMessage(
  payload: AgentChatRequest
): Promise<AgentChatResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/agent/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    const error = await response.text();

    throw new Error(
      `Agent request failed (${response.status}): ${error}`
    );
  }

  return response.json();
}
