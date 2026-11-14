
import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";

import {
  createConversation,
  deleteConversation,
  getConversation,
  getConversations,
} from "./services/conversationApi";

import {
  streamConversationMessage,
} from "./services/chatStreamApi";

import type { AIProvider } from "./types/chat";
import type {
  Conversation,
  StoredMessage,
} from "./types/conversation";

import "./App.css";

function App() {
  const [provider, setProvider] =
    useState<AIProvider>("gemini");

  const [conversations, setConversations] =
    useState<Conversation[]>([]);

  const [selectedId, setSelectedId] =
    useState<string | null>(null);

  const [messages, setMessages] =
    useState<StoredMessage[]>([]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  const locked = loading || busy;

  async function refreshConversations() {
    const result = await getConversations();
    setConversations(result);
  }

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        const result = await getConversations();
        if (!cancelled) setConversations(result);
      } catch {
        if (!cancelled) {
          setError("Failed to load conversations");
        }
      }
    }

    void initialize();

    return () => {
      cancelled = true;
      abortRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  async function selectConversation(id: string) {
    if (locked) return;

    setBusy(true);
    setError(null);

    try {
      const conversation = await getConversation(id);

      setSelectedId(conversation.id);
      setProvider(conversation.provider);
      setMessages(conversation.messages);
      setInput("");
    } catch {
      setError("Failed to load conversation");
    } finally {
      setBusy(false);
    }
  }

  async function handleNewChat() {
    if (locked) return;

    setBusy(true);
    setError(null);

    try {
      const conversation = await createConversation(
        provider
      );

      await refreshConversations();

      setSelectedId(conversation.id);
      setMessages([]);
      setInput("");
    } catch {
      setError("Failed to create conversation");
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(id: string) {
    if (locked) return;

    setBusy(true);
    setError(null);

    try {
      await deleteConversation(id);
      await refreshConversations();

      if (selectedId === id) {
        setSelectedId(null);
        setMessages([]);
      }
    } catch {
      setError("Failed to delete conversation");
    } finally {
      setBusy(false);
    }
  }

  async function handleSend(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const prompt = input.trim();

    if (!prompt || locked) return;

    setLoading(true);
    setError(null);

    const controller = new AbortController();
    abortRef.current = controller;

    const userMessage: StoredMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: prompt,
      created_at: new Date().toISOString(),
    };

    const assistantId = crypto.randomUUID();

    const assistantMessage: StoredMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
    };

    let conversationId = selectedId;

    try {
      // Automatically create a conversation
      // when the first message is sent.
      if (!conversationId) {
        const conversation = await createConversation(
          provider,
          prompt.slice(0, 100)
        );

        if (controller.signal.aborted) return;

        conversationId = conversation.id;
        setSelectedId(conversationId);
        await refreshConversations();
      }

      if (controller.signal.aborted) return;

      setMessages((previous) => [
        ...previous,
        userMessage,
        assistantMessage,
      ]);

      setInput("");

      await streamConversationMessage(
        conversationId,
        prompt,
        {
          onDelta: (delta) => {
            if (controller.signal.aborted) return;

            setMessages((previous) =>
              previous.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      content: message.content + delta,
                    }
                  : message
              )
            );
          },
        },
        controller.signal
      );

      if (controller.signal.aborted) return;

      // Reload canonical message IDs and timestamps
      // from PostgreSQL after successful persistence.
      const saved = await getConversation(conversationId);

      if (controller.signal.aborted) return;

      setMessages(saved.messages);
      await refreshConversations();
    } catch (err) {
      if (!controller.signal.aborted) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to send message"
        );

        // Reload persisted history. If generation failed,
        // the incomplete turn wasn't committed.
        if (conversationId) {
          try {
            const saved = await getConversation(
              conversationId
            );
            setMessages(saved.messages);
          } catch {
            setMessages((previous) =>
              previous.filter(
                (message) =>
                  message.id !== userMessage.id &&
                  message.id !== assistantId
              )
            );
          }
        }

        setInput(prompt);
      }
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null;
      }

      setLoading(false);
    }
  }

  function handleStop() {
    abortRef.current?.abort();
    abortRef.current = null;
    setLoading(false);

    // Reload authoritative database history.
    // This removes any incomplete local response.
    if (selectedId) {
      void getConversation(selectedId)
        .then((conversation) => {
          setMessages(conversation.messages);
        })
        .catch(() => {
          setError("Failed to refresh conversation");
        });
    }
  }

  return (
    <div className="chat-layout">
      <aside className="sidebar">
        <h2>Conversations</h2>

        <select
          value={provider}
          disabled={locked || selectedId !== null}
          onChange={(event) =>
            setProvider(
              event.target.value as AIProvider
            )
          }
        >
          <option value="gemini">Gemini</option>
          <option value="openai">OpenAI</option>
        </select>

        <button
          onClick={handleNewChat}
          disabled={locked}
        >
          + New Chat
        </button>

        <button
          disabled={locked}
          onClick={() => {
            setSelectedId(null);
            setMessages([]);
            setInput("");
            setError(null);
          }}
        >
          Choose Provider
        </button>

        <div className="conversation-list">
          {conversations.map((conversation) => (
            <div
              key={conversation.id}
              className="conversation-item"
            >
              <button
                className={
                  selectedId === conversation.id
                    ? "selected"
                    : ""
                }
                disabled={locked}
                onClick={() =>
                  void selectConversation(
                    conversation.id
                  )
                }
              >
                {conversation.title}
                <small>{conversation.provider}</small>
              </button>

              <button
                className="delete-button"
                disabled={locked}
                onClick={() =>
                  void handleDelete(
                    conversation.id
                  )
                }
                aria-label={`Delete ${conversation.title}`}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </aside>

      <section className="app">
        <header className="header">
          <div>
            <h1>🤖 AI Chatbot</h1>
            <p>
              {selectedId
                ? `Current provider: ${provider}`
                : `New ${provider} conversation`}
            </p>
          </div>
        </header>

        <main className="chat-container">
          {messages.length === 0 && (
            <div className="empty-state">
              <h2>How can I help you today?</h2>
              <p>Start a new conversation.</p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`message ${message.role}`}
            >
              <div className="message-content">
                {message.content ||
                  (loading ? "Thinking..." : "")}
              </div>
            </div>
          ))}

          <div ref={endRef} />
        </main>

        {error && (
          <div className="error-message" role="alert">
            {error}
          </div>
        )}

        <form
          className="chat-form"
          onSubmit={handleSend}
        >
          <input
            value={input}
            disabled={locked}
            placeholder="Ask me anything..."
            onChange={(event) =>
              setInput(event.target.value)
            }
          />

          {loading ? (
            <button
              type="button"
              onClick={handleStop}
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              disabled={locked || !input.trim()}
            >
              Send
            </button>
          )}
        </form>
      </section>
    </div>
  );
}

export default App;
