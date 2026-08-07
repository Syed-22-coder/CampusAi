"use client";

import { useState } from "react";
import Header from "@/components/Header";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import InputBar from "@/components/InputBar";
import AvatarPanel from "@/components/AvatarPanel";
import { sendChatMessage } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const sessionId = useState(() => crypto.randomUUID())[0];

  const handleSend = async (text: string) => {
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const reply = await sendChatMessage(text, sessionId);
      setMessages((prev) => [...prev, reply]);
      if (ttsEnabled) {
        setSpeaking(true);
        setTimeout(() => setSpeaking(false), 1500);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "Sorry — I couldn't reach the server just now. Please try again in a moment.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex h-screen flex-col">
      <Header
        onToggleSidebar={() => setSidebarOpen((o) => !o)}
        ttsEnabled={ttsEnabled}
        onToggleTts={() => setTtsEnabled((v) => !v)}
      />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar open={sidebarOpen} onSelectTopic={handleSend} />
        <div className="flex flex-1 flex-col">
          <ChatWindow messages={messages} loading={loading} />
          <InputBar onSend={handleSend} disabled={loading} />
        </div>
        <AvatarPanel speaking={speaking} />
      </div>
    </main>
  );
}
