"use client";

import { Menu, Volume2 } from "lucide-react";

interface HeaderProps {
  onToggleSidebar: () => void;
  ttsEnabled: boolean;
  onToggleTts: () => void;
}

export default function Header({ onToggleSidebar, ttsEnabled, onToggleTts }: HeaderProps) {
  return (
    <header className="flex items-center justify-between border-b border-slate/20 bg-ink px-4 py-3 text-parchment">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="rounded p-1 hover:bg-white/10 md:hidden"
          aria-label="Toggle conversation history"
        >
          <Menu size={20} />
        </button>
        <span className="font-display text-lg tracking-wide">CampusAI</span>
        <span className="hidden font-mono text-xs text-brass sm:inline">
          verified answers · your college
        </span>
      </div>

      <button
        onClick={onToggleTts}
        className={`flex items-center gap-2 rounded-full border border-brass/60 px-3 py-1 text-xs font-mono transition ${
          ttsEnabled ? "bg-brass text-ink" : "text-brass hover:bg-brass/10"
        }`}
      >
        <Volume2 size={14} />
        {ttsEnabled ? "Voice on" : "Voice off"}
      </button>
    </header>
  );
}
