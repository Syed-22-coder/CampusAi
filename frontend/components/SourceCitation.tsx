import { ShieldCheck } from "lucide-react";
import type { Source } from "@/lib/types";

export default function SourceCitation({ sources }: { sources: Source[] }) {
  if (!sources?.length) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {sources.map((source) => (
        
         <a key={source.url}
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