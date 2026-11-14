import { useEffect, useRef, useState, type FormEvent } from "react";

import { streamChatMessage } from "./services/chatStreamApi";

import type { AIProvider, ChatMessage } from "./types/chat";

import "./App.css";

type ConversationStore = Record<AIProvider, ChatMessage[]>;

const initialConversations: ConversationStore = {
  gemini: [],
  openai: [],
};

function App() {
  const [provider, setProvider] = useState<AIProvider>("gemini");

  const [conversations, setConversations] =
    useState<ConversationStore>(initialConversations);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // Synchronous guard against duplicate requests.
  const activeRef = useRef(false);

  const messages = conversations[provider];

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  function cancelActiveRequest() {
    abortRef.current?.abort();
    abortRef.current = null;
    activeRef.current = false;
    setLoading(false);
  }

  function handleProviderChange(nextProvider: AIProvider) {
    cancelActiveRequest();
    setProvider(nextProvider);
    setError(null);
  }

  function clearConversation() {
    cancelActiveRequest();
    setError(null);

    setConversations((previous) => ({
      ...previous,
      [provider]: [],
    }));
  }

  async function handleSend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const prompt = input.trim();

    if (!prompt || activeRef.current) return;

    activeRef.current = true;

    const currentProvider = provider;

    const controller = new AbortController();
    abortRef.current = controller;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: prompt,
    };

    const assistantMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "",
    };

    const history = [...conversations[currentProvider], userMessage];

    setInput("");
    setError(null);
    setLoading(true);

    // Add both messages immediately.
    setConversations((previous) => ({
      ...previous,
      [currentProvider]: [...history, assistantMessage],
    }));

    let generatedText = "";

    try {
      await streamChatMessage(
        {
          provider: currentProvider,
          messages: history.map(({ role, content }) => ({
            role,
            content,
          })),
        },
        {
          onDelta: (delta) => {
            if (controller.signal.aborted) return;

            generatedText += delta;

            setConversations((previous) => ({
              ...previous,
              [currentProvider]: previous[currentProvider].map((message) =>
                message.id === assistantMessage.id
                  ? {
                      ...message,
                      content: generatedText,
                    }
                  : message,
              ),
            }));
          },
        },
        controller.signal,
      );

      if (!generatedText.trim()) {
        throw new Error("AI returned no text");
      }
    } catch (err) {
      if (controller.signal.aborted) return;

      setError(err instanceof Error ? err.message : "Streaming failed");

      // Remove the failed turn, preserving
      // the previously completed conversation.
      setConversations((previous) => ({
        ...previous,
        [currentProvider]: previous[currentProvider].filter(
          (message) =>
            message.id !== userMessage.id && message.id !== assistantMessage.id,
        ),
      }));

      setInput(prompt);
    } finally {
      if (controller.signal.aborted) {
        // Remove the interrupted turn from conversation
        // history so it isn't sent as completed context.
        setConversations((previous) => ({
          ...previous,
          [currentProvider]: previous[currentProvider].filter(
            (message) =>
              message.id !== userMessage.id &&
              message.id !== assistantMessage.id,
          ),
        }));
      }

      if (abortRef.current === controller) {
        abortRef.current = null;
        activeRef.current = false;
        setLoading(false);
      }
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>🤖 AI Chatbot</h1>
          <p>FastAPI + React + AI Streaming</p>
        </div>

        <button className="clear-button" onClick={clearConversation}>
          Clear Chat
        </button>
      </header>

      <div className="provider-bar">
        <label htmlFor="provider">AI Provider</label>

        <select
          id="provider"
          value={provider}
          onChange={(event) =>
            handleProviderChange(event.target.value as AIProvider)
          }
        >
          <option value="gemini">Google Gemini</option>
          <option value="openai">OpenAI GPT</option>
        </select>
      </div>

      <main className="chat-container">
        {messages.length === 0 && (
          <div className="empty-state">
            <h2>How can I help you today?</h2>
            <p>Start chatting with {provider}.</p>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="message-content">
              {message.content || (loading ? "Thinking..." : "")}
            </div>
          </div>
        ))}

        <div ref={chatEndRef} />
      </main>

      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}

      <form className="chat-form" onSubmit={handleSend}>
        <input
          type="text"
          value={input}
          placeholder="Ask me anything..."
          onChange={(event) => setInput(event.target.value)}
          disabled={loading}
        />

        {loading ? (
          <button type="button" onClick={cancelActiveRequest}>
            Stop
          </button>
        ) : (
          <button type="submit" disabled={!input.trim()}>
            Send
          </button>
        )}
      </form>
    </div>
  );
}

export default App;
