
import type { AIProvider } from "./chat";

export interface StoredMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  provider: AIProvider;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: StoredMessage[];
}
