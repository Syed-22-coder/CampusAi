"use client";

import { useState } from "react";
import { Mic, Send } from "lucide-react";

interface InputBarProps {
  onSend: (text: string) => void;
  disabled?: boolean;
}

export default function InputBar({ onSend, disabled }: InputBarProps) {
  const [value, setValue] = useState("");

  const handleSend = () => {
    if (!value.trim() || disabled) return;
    onSend(value.trim());
    setValue("");
  };

  return (
    <div className="flex items-center gap-2 border-t border-slate/15 bg-white p-3">
      <button
        className="rounded-full p-2 text-slate hover:bg-parchment disabled:opacity-40"
        aria-label="Voice input (coming soon)"
        disabled={disabled}
      >
        <Mic size={18} />
      </button>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
        disabled={disabled}
        placeholder={disabled ? "Waiting for a response…" : "Ask about admissions, financial aid, registration…"}
        className="flex-1 rounded-full border border-slate/20 bg-parchment px-4 py-2 text-sm outline-none focus:border-brass disabled:opacity-60"
      />
      <button
        onClick={handleSend}
        disabled={disabled}
        className="rounded-full bg-ink p-2 text-parchment hover:bg-ink/90 disabled:opacity-40"
        aria-label="Send message"
      >
        <Send size={18} />
      </button>
    </div>
  );
}