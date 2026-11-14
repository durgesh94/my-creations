
import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";

import { sendChatMessage } from "./services/chatApi";

import type {
  AIProvider,
  ChatMessage,
} from "./types/chat";

import "./App.css";

type ConversationStore = Record<
  AIProvider,
  ChatMessage[]
>;

const initialConversations: ConversationStore = {
  gemini: [],
  openai: [],
};

function App() {
  const [provider, setProvider] =
    useState<AIProvider>("gemini");

  const [conversations, setConversations] =
    useState<ConversationStore>(
      initialConversations
    );

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortControllerRef =
    useRef<AbortController | null>(null);

  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const messages = conversations[provider];

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  function handleProviderChange(
    nextProvider: AIProvider
  ) {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;

    setLoading(false);
    setError(null);
    setProvider(nextProvider);
  }

  function clearConversation() {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;

    setLoading(false);
    setError(null);

    setConversations((previous) => ({
      ...previous,
      [provider]: [],
    }));
  }

  async function handleSend(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const prompt = input.trim();

    if (!prompt || loading) return;

    const currentProvider = provider;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: prompt,
    };

    // Build history before updating React state.
    const history = [
      ...conversations[currentProvider],
      userMessage,
    ];

    const controller = new AbortController();

    abortControllerRef.current = controller;

    setLoading(true);
    setError(null);
    setInput("");

    setConversations((previous) => ({
      ...previous,
      [currentProvider]: history,
    }));

    try {
      const result = await sendChatMessage(
        {
          provider: currentProvider,
          messages: history.map(
            ({ role, content }) => ({
              role,
              content,
            })
          ),
        },
        controller.signal
      );

      if (controller.signal.aborted) return;

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: result.response,
      };

      setConversations((previous) => ({
        ...previous,
        [currentProvider]: [
          ...previous[currentProvider],
          assistantMessage,
        ],
      }));
    } catch (err) {
      if (controller.signal.aborted) return;

      // Remove the failed user message so the
      // next request has a valid conversation.
      setConversations((previous) => ({
        ...previous,
        [currentProvider]:
          previous[currentProvider].filter(
            (message) => message.id !== userMessage.id
          ),
      }));

      setInput(prompt);

      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong"
      );
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
        setLoading(false);
      }
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>🤖 AI Chatbot</h1>
          <p>React + FastAPI + OpenAI + Gemini</p>
        </div>

        <button
          className="clear-button"
          onClick={clearConversation}
        >
          Clear Chat
        </button>
      </header>

      <div className="provider-bar">
        <label htmlFor="provider">
          AI Provider
        </label>

        <select
          id="provider"
          value={provider}
          onChange={(event) =>
            handleProviderChange(
              event.target.value as AIProvider
            )
          }
        >
          <option value="gemini">
            Google Gemini
          </option>

          <option value="openai">
            OpenAI GPT
          </option>
        </select>
      </div>

      <main className="chat-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <h2>How can I help you today?</h2>
            <p>
              Start a conversation with {provider}.
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`message ${message.role}`}
            >
              <div className="message-content">
                {message.content}
              </div>
            </div>
          ))
        )}

        {loading && (
          <div className="message assistant">
            <div className="message-content">
              AI is thinking...
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
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
          type="text"
          placeholder="Ask me anything..."
          value={input}
          onChange={(event) =>
            setInput(event.target.value)
          }
          disabled={loading}
        />

        <button
          type="submit"
          disabled={loading || !input.trim()}
        >
          {loading ? "Sending..." : "Send"}
        </button>
      </form>
    </div>
  );
}

export default App;
