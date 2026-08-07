import type { ChatMessage, Source } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

interface ChatApiResponse {
  answer: string;
  sources?: Source[];
  department?: string;
}

export async function sendChatMessage(
  message: string,
  sessionId?: string
): Promise<ChatMessage> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!res.ok) {
    throw new Error(`Chat request failed: ${res.status}`);
  }

  const data: ChatApiResponse = await res.json();

  return {
    id: crypto.randomUUID(),
    role: "assistant",
    content: data.answer,
    sources: data.sources,
    department: data.department,
  };
}
