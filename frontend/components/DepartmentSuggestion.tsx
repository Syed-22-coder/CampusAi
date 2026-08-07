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