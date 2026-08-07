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
