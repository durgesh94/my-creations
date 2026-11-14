
export type AIProvider = "gemini" | "openai";

export type ChatRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
}

export interface ChatConversation {
  provider: AIProvider;
  messages: ChatMessage[];
}
