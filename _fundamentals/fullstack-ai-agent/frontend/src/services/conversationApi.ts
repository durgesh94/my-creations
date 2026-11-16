
import { API_BASE_URL } from "../config";
import type { AIProvider } from "../types/chat";
import type {
  Conversation,
  ConversationDetail,
} from "../types/conversation";


async function apiRequest<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    }
  );

  if (!response.ok) {
    throw new Error(
      `API request failed: HTTP ${response.status}`
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}


export function getConversations() {
  return apiRequest<Conversation[]>(
    "/api/v1/conversations"
  );
}


export function createConversation(
  provider: AIProvider,
  title: string = "New conversation"
) {
  return apiRequest<Conversation>(
    "/api/v1/conversations",
    {
      method: "POST",
      body: JSON.stringify({
        provider,
        title,
      }),
    }
  );
}


export function getConversation(id: string) {
  return apiRequest<ConversationDetail>(
    `/api/v1/conversations/${id}`
  );
}


export function deleteConversation(id: string) {
  return apiRequest<void>(
    `/api/v1/conversations/${id}`,
    {
      method: "DELETE",
    }
  );
}
