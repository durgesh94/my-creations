import { BrowserRouter, Link, Navigate, Outlet, Route, Routes } from "react-router-dom";

import "./AppShell.css";
import Agent from "./components/agent/Agent";
import Chat from "./components/chat/Chat";

function Landing() {
  return (
    <main className="landing">
      <h1>What would you like to use?</h1>
      <div className="landing-actions">
        <Link to="/agent" className="landing-card">
          <strong>Agent</strong>
          <span>Hospital assistant that can use tools.</span>
        </Link>
        <Link to="/chat" className="landing-card">
          <strong>Chat</strong>
          <span>Talk to Gemini or OpenAI.</span>
        </Link>
      </div>
    </main>
  );
}

function PageLayout() {
  return (
    <div className="app-root">
      <div className="app-view">
        <Outlet />
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route element={<PageLayout />}>
          <Route path="/agent" element={<Agent />} />
          <Route path="/chat" element={<Chat />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
