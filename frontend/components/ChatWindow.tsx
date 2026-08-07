import type { ChatMessage } from "@/lib/types";
import MessageBubble from "./MessageBubble";
import LoadingIndicator from "./LoadingIndicator";

interface ChatWindowProps {
  messages: ChatMessage[];
  loading: boolean;
}

export default function ChatWindow({ messages, loading }: ChatWindowProps) {
  if (messages.length === 0 && !loading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-6 text-center">
        <h1 className="font-display text-2xl text-ink">How can I help?</h1>
        <p className="mt-2 max-w-sm text-sm text-slate">
          Ask about admissions, financial aid, registration, IT support, or
          academic advising — every answer is backed by an official source.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} />
      ))}
      {loading && <LoadingIndicator />}
    </div>
  );
}
