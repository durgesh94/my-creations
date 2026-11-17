
import { useEffect, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import "./Agent.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type Role = "user" | "assistant";

interface ChatMessage {
  id: string;
  role: Role;
  content: string;
}

interface Conversation {
  id: string;
  title: string;
  provider: string;
  created_at: string;
  updated_at: string;
}

interface ConversationDetail extends Conversation {
  messages: Array<{
    id: string;
    role: Role;
    content: string;
    sequence_number: number;
  }>;
}

interface AppointmentApproval {
  type: string;
  doctor_id: string;
  appointment_date: string;
  appointment_time: string;
  message: string;
}

interface AgentChatResponse {
  conversation_id: string;
  status: "completed" | "approval_required";
  response: string;
  approval: AppointmentApproval | null;
}

interface PendingApprovalResponse {
  status: "completed" | "approval_required";
  approval: AppointmentApproval | null;
}

async function apiRequest<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Request failed (${response.status}): ${detail}`
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

const conversationApi = {
  list: () =>
    apiRequest<Conversation[]>("/api/v1/conversations"),

  get: (id: string) =>
    apiRequest<ConversationDetail>(
      `/api/v1/conversations/${id}`
    ),

  create: () =>
    apiRequest<Conversation>("/api/v1/conversations", {
      method: "POST",
      body: JSON.stringify({
        title: "New conversation",
        provider: "gemini",
      }),
    }),

  delete: (id: string) =>
    apiRequest<void>(`/api/v1/conversations/${id}`, {
      method: "DELETE",
    }),
};

const agentApi = {
  pending: (conversationId: string) =>
    apiRequest<PendingApprovalResponse>(
      `/api/v1/agent/pending/${conversationId}`
    ),

  approve: (conversationId: string, decision: "approve" | "reject") =>
    apiRequest<AgentChatResponse>("/api/v1/agent/approval", {
      method: "POST",
      body: JSON.stringify({
        conversation_id: conversationId,
        decision,
      }),
    }),

  chat: (conversationId: string, message: string) =>
    apiRequest<AgentChatResponse>("/api/v1/agent/chat", {
      method: "POST",
      body: JSON.stringify({
        conversation_id: conversationId,
        message,
      }),
    }),
};

function Agent() {
  const [conversations, setConversations] = useState<
    Conversation[]
  >([]);
  const [activeConversationId, setActiveConversationId] =
    useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [pendingApproval, setPendingApproval] =
    useState<AppointmentApproval | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const activeIdRef = useRef<string | null>(null);
  const busyRef = useRef(false);
  const historyRequestRef = useRef(0);

  useEffect(() => {
    void loadConversations();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading, pendingApproval]);

  async function loadConversations() {
    try {
      const data = await conversationApi.list();
      setConversations(data);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  async function selectConversation(id: string) {
    if (busyRef.current) return;

    const requestId = ++historyRequestRef.current;
    activeIdRef.current = id;
    setActiveConversationId(id);
    setMessages([]);
    setPendingApproval(null);
    setError(null);
    setLoadingHistory(true);

    try {
      const conversation = await conversationApi.get(id);

      if (requestId !== historyRequestRef.current) return;

      setMessages(
        [...conversation.messages]
          .sort(
            (a, b) =>
              a.sequence_number - b.sequence_number
          )
          .filter(
            (message) =>
              message.role === "user" ||
              message.role === "assistant"
          )
          .map((message) => ({
            id: message.id,
            role: message.role,
            content: message.content,
          }))
      );

      const pending = await agentApi.pending(id);
      if (requestId !== historyRequestRef.current) return;
      setPendingApproval(
        pending.status === "approval_required"
          ? pending.approval
          : null
      );
    } catch (err) {
      if (requestId === historyRequestRef.current) {
        setError(getErrorMessage(err));
      }
    } finally {
      if (requestId === historyRequestRef.current) {
        setLoadingHistory(false);
      }
    }
  }

  async function createConversation(): Promise<
    string | null
  > {
    if (busyRef.current) return null;

    setCreating(true);
    setError(null);

    try {
      const conversation = await conversationApi.create();

      ++historyRequestRef.current;
      activeIdRef.current = conversation.id;
      setActiveConversationId(conversation.id);
      setMessages([]);
      setPendingApproval(null);
      setInput("");
      setLoadingHistory(false);

      setConversations((previous) => [
        conversation,
        ...previous,
      ]);

      return conversation.id;
    } catch (err) {
      setError(getErrorMessage(err));
      return null;
    } finally {
      setCreating(false);
    }
  }

  async function deleteConversation(id: string) {
    if (busyRef.current) return;

    if (!window.confirm("Delete this conversation?")) {
      return;
    }

    try {
      await conversationApi.delete(id);

      setConversations((previous) =>
        previous.filter((item) => item.id !== id)
      );

      if (activeIdRef.current === id) {
        ++historyRequestRef.current;
        activeIdRef.current = null;
        setActiveConversationId(null);
        setMessages([]);
        setPendingApproval(null);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  async function handleSend(event?: FormEvent) {
    event?.preventDefault();

    const message = input.trim();

    if (
      !message ||
      busyRef.current ||
      creating ||
      loadingHistory ||
      pendingApproval !== null
    ) {
      return;
    }

    busyRef.current = true;
    setLoading(true);
    setError(null);

    const conversationId = activeIdRef.current;

    if (!conversationId) {
      busyRef.current = false;
      setLoading(false);
      setError("Create a conversation before sending.");
      return;
    }

    const temporaryMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: message,
    };

    setMessages((previous) => [
      ...previous,
      temporaryMessage,
    ]);
    setInput("");

    try {
      const result = await agentApi.chat(
        conversationId,
        message
      );

      setMessages((previous) => [
        ...previous,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.response,
        },
      ]);
      setPendingApproval(
        result.status === "approval_required"
          ? result.approval
          : null
      );

      // Refresh generated conversation titles and ordering.
      await loadConversations();
    } catch (err) {
      setError(getErrorMessage(err));

      // The backend might have persisted the request
      // even if the HTTP response failed. Reload history
      // rather than blindly retrying the request.
      try {
        const detail = await conversationApi.get(
          conversationId
        );

        setMessages(
          detail.messages
            .sort(
              (a, b) =>
                a.sequence_number - b.sequence_number
            )
            .map((item) => ({
              id: item.id,
              role: item.role,
              content: item.content,
            }))
        );
      } catch {
        // Keep the optimistic message visible.
      }
    } finally {
      busyRef.current = false;
      setLoading(false);
    }
  }

  async function handleApproval(decision: "approve" | "reject") {
    const conversationId = activeIdRef.current;
    if (!conversationId || !pendingApproval || busyRef.current) return;

    busyRef.current = true;
    setLoading(true);
    setError(null);

    try {
      const result = await agentApi.approve(conversationId, decision);
      if (activeIdRef.current !== conversationId) return;

      setPendingApproval(
        result.status === "approval_required"
          ? result.approval
          : null
      );
      setMessages((previous) => [
        ...previous,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.response,
        },
      ]);
      await loadConversations();
    } catch (err) {
      setError(getErrorMessage(err));
      // Re-read graph state: approval might have completed
      // even if the network response was lost.
      try {
        const state = await agentApi.pending(conversationId);
        if (activeIdRef.current === conversationId) {
          setPendingApproval(state.approval);
        }
      } catch {
        // Keep the approval controls visible for inspection.
      }
    } finally {
      busyRef.current = false;
      setLoading(false);
    }
  }

  function handleInputKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>
  ) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSend();
    }
  }

  const activeConversation = conversations.find(
    (conversation) =>
      conversation.id === activeConversationId
  );

  return (
    <div className="app-shell">
      <aside
        className={`sidebar ${
          sidebarOpen ? "sidebar-open" : "sidebar-closed"
        }`}
      >
        <div className="sidebar-header">
          <h2>Hospital AI</h2>
          <button
            className="new-chat-button"
            onClick={() => void createConversation()}
            disabled={loading || creating}
          >
            {creating ? "Creating..." : "+ New Chat"}
          </button>
        </div>

        <div className="conversation-list">
          {conversations.map((conversation) => (
            <div
              key={conversation.id}
              className={`conversation-item ${
                activeConversationId === conversation.id
                  ? "active"
                  : ""
              }`}
            >
              <button
                className="conversation-select"
                onClick={() =>
                  void selectConversation(conversation.id)
                }
                disabled={loading || creating}
              >
                {conversation.title}
              </button>

              <button
                className="delete-button"
                title="Delete conversation"
                aria-label={`Delete ${conversation.title}`}
                disabled={loading || creating}
                onClick={() =>
                  void deleteConversation(conversation.id)
                }
              >
                ×
              </button>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          Powered by Gemini + LangGraph
        </div>
      </aside>

      <main className="chat-main">
        <header className="chat-header">
          <button
            className="menu-button"
            onClick={() =>
              setSidebarOpen((previous) => !previous)
            }
            aria-label="Toggle sidebar"
          >
            ☰
          </button>

          <div>
            <h1>
              {activeConversation?.title ??
                "Hospital AI Assistant"}
            </h1>
            <span className="header-subtitle">
              Agentic AI Chatbot
            </span>
          </div>

          <span className="status-indicator">
            ● AI Agent
          </span>
        </header>

        <section className="messages-container">
          {!activeConversationId && (
            <div className="welcome-screen">
              <div className="welcome-icon">✦</div>
              <h2>How can I help you today?</h2>
              <p>
                Find doctors, check available slots,
                explore appointments, or ask about
                hospital policies.
              </p>

              <button
                className="start-chat-button"
                onClick={() =>
                  void createConversation()
                }
                disabled={creating}
              >
                Start New Conversation
              </button>
            </div>
          )}

          {activeConversationId &&
            !loadingHistory &&
            messages.length === 0 && (
              <div className="welcome-screen">
                <div className="welcome-icon">✦</div>
                <h2>Ask your hospital AI agent</h2>
                <p>
                  Try asking: Find cardiology doctors
                </p>
              </div>
            )}

          {loadingHistory && (
            <div className="loading-history">
              Loading conversation...
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`message-row ${message.role}`}
            >
              <div className="message-avatar">
                {message.role === "assistant" ? "AI" : "U"}
              </div>

              <div className="message-content">
                <div className="message-author">
                  {message.role === "assistant"
                    ? "Hospital AI"
                    : "You"}
                </div>

                <div className="message-text">
                  {message.content}
                </div>
              </div>
            </div>
          ))}

          {pendingApproval && !loadingHistory && (
            <div className="approval-card" role="group" aria-label="Appointment approval">
              <h3>Confirm mock appointment</h3>
              <p>Doctor ID: {pendingApproval.doctor_id}</p>
              <p>Date: {pendingApproval.appointment_date}</p>
              <p>Time: {pendingApproval.appointment_time}</p>
              <div className="approval-actions">
                <button
                  type="button"
                  onClick={() => void handleApproval("approve")}
                  disabled={loading}
                >
                  Confirm Booking
                </button>
                <button
                  type="button"
                  onClick={() => void handleApproval("reject")}
                  disabled={loading}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {loading && (
            <div className="message-row assistant">
              <div className="message-avatar">AI</div>
              <div className="message-content">
                <div className="message-author">
                  Hospital AI
                </div>
                <div className="typing-indicator">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </section>

        <div className="composer-area">
          {error && (
            <div className="error-banner" role="alert">
              {error}
              <button onClick={() => setError(null)}>
                ×
              </button>
            </div>
          )}

          <form
            className="composer"
            onSubmit={(event) => void handleSend(event)}
          >
            <textarea
              value={input}
              onChange={(event) =>
                setInput(event.target.value)
              }
              onKeyDown={handleInputKeyDown}
              placeholder={
                activeConversationId
                  ? pendingApproval
                    ? "Confirm or cancel the pending booking above"
                    : "Message Hospital AI..."
                  : "Create a conversation to start..."
              }
              disabled={
                !activeConversationId ||
                loading ||
                loadingHistory ||
                pendingApproval !== null
              }
              rows={2}
            />

            <button
              type="submit"
              className="send-button"
              disabled={
                !input.trim() ||
                !activeConversationId ||
                loading ||
                loadingHistory ||
                pendingApproval !== null
              }
            >
              {loading ? "..." : "➤"}
            </button>
          </form>

          <p className="composer-note">
            AI responses may be inaccurate. Verify
            important medical information.
          </p>
        </div>
      </main>
    </div>
  );
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong. Please try again.";
}

export default Agent;
