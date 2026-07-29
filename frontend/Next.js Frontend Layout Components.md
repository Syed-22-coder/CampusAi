# CampusAI — Next.js Frontend Layout & Components

**Sprint Task:** Develop Next.js Frontend layout & components
**Owner:** Syed (UI/UX Lead)
**Sprint:** Meeting 2 → Meeting 3
**Stack:** Next.js 14 (App Router) + TypeScript + Tailwind CSS

This document is the deliverable for the Meeting 3 check-in. It covers the visual
design direction, the folder structure, and working component code for the chat
interface, avatar panel, source citations, and department recommendations —
the six "must have" MVP items from Meeting 1.

---

## 1. Design Direction

Before writing code, here's the visual identity so the whole team (and Nairobi's
slides) stay consistent.

**Concept:** A college front-desk, not a generic chatbot. The tone should feel like
an official, trustworthy campus service — closer to a registrar's window than a
consumer AI app.

| Token | Value | Use |
|---|---|---|
| Ink Navy | `#1B2A4A` | Header, primary buttons, assistant bubble text |
| Parchment | `#F7F3E9` | Page background |
| Paper White | `#FFFFFF` | Card / bubble surfaces |
| Brass | `#A6802A` | Accent — links, active states, the "seal" mark |
| Slate | `#4A5568` | Secondary text, borders |
| Verified Green | `#2F6F4E` | Source-citation confirmation only |

**Typography**
- Display / headings: `Fraunces` (serif, academic weight) — used sparingly for the header title and empty-state headline.
- Body / chat text: `Inter` — legible at small sizes, works for long RAG answers.
- Utility / labels: `IBM Plex Mono` — citation numbers, timestamps, "Verified" tags.

**Signature element — the Verified Seal**
Every AI answer gets a small circular "seal" badge next to its source citation
(like an embossed university stamp), instead of a generic link icon. This is the
one recognizable visual detail tying the whole product back to the "verified
college information" pitch from the problem statement, and it doubles as the
QA hook for Nairobi (easy to point to during testing/demo: "see, it's cited").

**Layout concept**
```
┌─────────────────────────────────────────────┐
│ Header (logo, college name, avatar toggle)   │
├───────────────┬───────────────────────────────┤
│               │  Message thread (scrollable)  │
│  Sidebar      │  ┌─────────────────────────┐  │
│  (history +   │  │ assistant bubble          │  │
│  quick topics)│  │  ↳ source seal + link     │  │
│  collapses    │  └─────────────────────────┘  │
│  on mobile    │  ┌───────────────────┐         │
│               │  │ user bubble       │         │
│               │  └───────────────────┘         │
│               ├───────────────────────────────┤
│               │  Input bar (text, mic, send)  │
└───────────────┴───────────────────────────────┘
```
On mobile the sidebar collapses into a slide-over drawer; the avatar panel
collapses into a small floating circle above the input bar.

---

## 2. Folder Structure

```
frontend/
├─ app/
│  ├─ layout.tsx
│  ├─ page.tsx
│  └─ globals.css
├─ components/
│  ├─ Header.tsx
│  ├─ Sidebar.tsx
│  ├─ ChatWindow.tsx
│  ├─ MessageBubble.tsx
│  ├─ SourceCitation.tsx
│  ├─ DepartmentSuggestion.tsx
│  ├─ AvatarPanel.tsx
│  └─ InputBar.tsx
├─ lib/
│  └─ types.ts
├─ tailwind.config.ts
└─ package.json
```

---

## 3. Tailwind Config (design tokens as theme)

```ts
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1B2A4A",
        parchment: "#F7F3E9",
        brass: "#A6802A",
        slate: "#4A5568",
        verified: "#2F6F4E",
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "serif"],
        body: ["var(--font-inter)", "sans-serif"],
        mono: ["var(--font-plex-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
```

---

## 4. Shared Types

```ts
// lib/types.ts
export type Role = "user" | "assistant";

export interface Source {
  title: string;
  url: string;
  verifiedDate?: string;
}

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  sources?: Source[];
  department?: string;
}
```

---

## 5. Root Layout

```tsx
// app/layout.tsx
import type { Metadata } from "next";
import { Fraunces, Inter, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

const fraunces = Fraunces({ subsets: ["latin"], variable: "--font-fraunces" });
const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-plex-mono",
});

export const metadata: Metadata = {
  title: "CampusAI — Virtual Receptionist",
  description: "Ask CampusAI about admissions, financial aid, IT, and more.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body
        className={`${fraunces.variable} ${inter.variable} ${plexMono.variable} font-body bg-parchment text-ink antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
```

---

## 6. Header

```tsx
// components/Header.tsx
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
```

---

## 7. Sidebar (conversation history / quick topics)

```tsx
// components/Sidebar.tsx
"use client";

const QUICK_TOPICS = [
  "Admissions deadlines",
  "Financial aid",
  "Course registration",
  "IT support",
  "Academic advising",
];

interface SidebarProps {
  open: boolean;
  onSelectTopic: (topic: string) => void;
}

export default function Sidebar({ open, onSelectTopic }: SidebarProps) {
  return (
    <aside
      className={`w-64 shrink-0 border-r border-slate/15 bg-white p-4 transition-all
      ${open ? "block" : "hidden"} md:block`}
    >
      <h2 className="mb-2 font-display text-sm text-slate">Quick topics</h2>
      <ul className="space-y-1">
        {QUICK_TOPICS.map((topic) => (
          <li key={topic}>
            <button
              onClick={() => onSelectTopic(topic)}
              className="w-full rounded px-2 py-1.5 text-left text-sm text-ink hover:bg-parchment"
            >
              {topic}
            </button>
          </li>
        ))}
      </ul>

      <h2 className="mb-2 mt-6 font-display text-sm text-slate">History</h2>
      <p className="text-xs text-slate/70">
        Conversation history will appear here once session storage is wired up
        (nice-to-have, Meeting 4+).
      </p>
    </aside>
  );
}
```

---

## 8. Source Citation (signature "seal" element)

```tsx
// components/SourceCitation.tsx
import { ShieldCheck } from "lucide-react";
import type { Source } from "@/lib/types";

export default function SourceCitation({ sources }: { sources: Source[] }) {
  if (!sources?.length) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {sources.map((source) => (
        <a
          key={source.url}
          href={source.url}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1.5 rounded-full border border-verified/40 bg-verified/10 px-2.5 py-1 text-xs font-mono text-verified hover:bg-verified/20"
        >
          <ShieldCheck size={13} />
          {source.title}
        </a>
      ))}
    </div>
  );
}
```

---

## 9. Department Recommendation Card

```tsx
// components/DepartmentSuggestion.tsx
import { ArrowRight } from "lucide-react";

export default function DepartmentSuggestion({ department }: { department: string }) {
  return (
    <div className="mt-2 flex items-center justify-between rounded-lg border border-brass/30 bg-brass/5 px-3 py-2 text-sm">
      <span className="text-slate">
        This sounds like a question for <strong className="text-ink">{department}</strong>.
      </span>
      <ArrowRight size={16} className="text-brass" />
    </div>
  );
}
```

---

## 10. Message Bubble

```tsx
// components/MessageBubble.tsx
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
```

---

## 11. Avatar Panel

```tsx
// components/AvatarPanel.tsx
"use client";

interface AvatarPanelProps {
  speaking: boolean;
}

// Placeholder for the TalkingHead avatar (Syed/Abrar to wire the real
// avatar library into this container — canvas mounts here in Meeting 4).
export default function AvatarPanel({ speaking }: AvatarPanelProps) {
  return (
    <div className="hidden w-56 shrink-0 flex-col items-center justify-center border-l border-slate/15 bg-white p-4 lg:flex">
      <div
        className={`h-32 w-32 rounded-full border-4 transition-all ${
          speaking ? "border-brass animate-pulse" : "border-slate/20"
        } bg-parchment`}
        aria-label="Avatar placeholder"
      />
      <p className="mt-3 font-mono text-xs text-slate">
        {speaking ? "speaking…" : "idle"}
      </p>
    </div>
  );
}
```

---

## 12. Input Bar

```tsx
// components/InputBar.tsx
"use client";

import { useState } from "react";
import { Mic, Send } from "lucide-react";

interface InputBarProps {
  onSend: (text: string) => void;
}

export default function InputBar({ onSend }: InputBarProps) {
  const [value, setValue] = useState("");

  const handleSend = () => {
    if (!value.trim()) return;
    onSend(value.trim());
    setValue("");
  };

  return (
    <div className="flex items-center gap-2 border-t border-slate/15 bg-white p-3">
      <button
        className="rounded-full p-2 text-slate hover:bg-parchment"
        aria-label="Voice input (coming soon)"
        title="Voice input — nice-to-have, Meeting 4"
      >
        <Mic size={18} />
      </button>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
        placeholder="Ask about admissions, financial aid, registration…"
        className="flex-1 rounded-full border border-slate/20 bg-parchment px-4 py-2 text-sm outline-none focus:border-brass"
      />
      <button
        onClick={handleSend}
        className="rounded-full bg-ink p-2 text-parchment hover:bg-ink/90"
        aria-label="Send message"
      >
        <Send size={18} />
      </button>
    </div>
  );
}
```

---

## 13. Chat Window (composes the thread)

```tsx
// components/ChatWindow.tsx
import type { ChatMessage } from "@/lib/types";
import MessageBubble from "./MessageBubble";

export default function ChatWindow({ messages }: { messages: ChatMessage[] }) {
  if (messages.length === 0) {
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
    </div>
  );
}
```

---

## 14. Page Assembly

```tsx
// app/page.tsx
"use client";

import { useState } from "react";
import Header from "@/components/Header";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import InputBar from "@/components/InputBar";
import AvatarPanel from "@/components/AvatarPanel";
import type { ChatMessage } from "@/lib/types";

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // Placeholder send handler — Abrar's FastAPI/LangChain endpoint plugs in here.
  const handleSend = (text: string) => {
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);

    // Mocked assistant reply until the backend endpoint is ready (Meeting 3/4).
    setSpeaking(ttsEnabled);
    setTimeout(() => {
      const reply: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "This is a placeholder answer — connect the RAG endpoint to replace it.",
        sources: [{ title: "Registrar Office", url: "#" }],
        department: "Registrar's Office",
      };
      setMessages((prev) => [...prev, reply]);
      setSpeaking(false);
    }, 600);
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
          <ChatWindow messages={messages} />
          <InputBar onSend={handleSend} />
        </div>
        <AvatarPanel speaking={speaking} />
      </div>
    </main>
  );
}
```

---

## 15. Responsive Behavior

| Breakpoint | Sidebar | Avatar panel | Input bar |
|---|---|---|---|
| `< md` (mobile) | Hidden, opens as drawer via header menu | Hidden | Full width, mic + send |
| `md – lg` (tablet) | Always visible, fixed width | Hidden | Full width |
| `≥ lg` (desktop) | Always visible | Visible, fixed width | Full width |

Accessibility floor covered: all icon-only buttons have `aria-label`s, focus is
keyboard-visible via Tailwind's default ring on interactive elements, and no
motion beyond the subtle avatar pulse (respects `prefers-reduced-motion` if
added at the CSS layer — flagged as a follow-up).

---

## 16. Status for Meeting 3

**Completed**
- Folder structure, Tailwind design tokens, and font setup
- Header, Sidebar, ChatWindow, MessageBubble, SourceCitation, DepartmentSuggestion, AvatarPanel, InputBar — all built and composed on `app/page.tsx`
- Responsive layout (mobile drawer → desktop three-column)
- Mocked send/receive flow so the UI is demoable without the backend

**Next (blocked on other workstreams)**
- Swap the mocked reply in `handleSend` for Abrar's FastAPI/LangChain endpoint
- Wire the real TalkingHead avatar into `AvatarPanel`
- Push skeleton to GitHub (per Meeting 2 note: skeletons weren't uploaded yet)

**No blockers on my side** — ready to integrate as soon as the backend endpoint is available.
