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