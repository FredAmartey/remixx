import type { Pick } from "@/lib/api";
import { Play } from "lucide-react";

export function TrackList({ picks }: { picks: (Pick & { _arc?: string })[] }) {
  return (
    <div className="space-y-1">
      {picks.map((p, i) => (
        <div
          key={p.id}
          className="grid grid-cols-[2rem_1fr_auto_2rem] items-center gap-4 py-3 border-b border-cream/5 last:border-b-0 group"
        >
          <span className="font-mono text-xs text-cream-muted/70 tabular-nums">
            {String(i + 1).padStart(2, "0")}
          </span>
          <div className="min-w-0">
            <div className="font-sans text-cream truncate">
              {p.title}
              <span className="font-display italic text-cream-muted">
                {" "}
                — {p.artist}
              </span>
            </div>
            <div className="font-display italic text-xs text-cream-muted/70 truncate">
              {p.genre} · {p.mood}
            </div>
          </div>
          <div className="hidden md:flex items-center gap-2 shrink-0">
            {p._arc && (
              <span className="font-display italic text-[11px] text-copper">
                · {p._arc}
              </span>
            )}
          </div>
          <button
            className="text-cream-muted/60 hover:text-copper opacity-0 group-hover:opacity-100 transition-all justify-self-end"
            aria-label={`Play ${p.title}`}
          >
            <Play className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
