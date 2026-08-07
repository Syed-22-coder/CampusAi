import type { ChatMessage } from "@/lib/types";
import SourceCitation from "./SourceCitation";
import DepartmentSuggestion from "./DepartmentSuggestion";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm
        ${isUser ? "bg-ink text-parchment" : "bg-white text-ink border border-slate/10"}`}
      >
        <p>{message.content}</p>
        {!isUser && message.sources && <SourceCitation sources={message.sources} />}
        {!isUser && message.department && (
          <DepartmentSuggestion department={message.department} />
        )}
      </div>
    </div>
  );
}