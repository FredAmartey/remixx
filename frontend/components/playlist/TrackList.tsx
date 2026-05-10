"use client";

import type { Pick } from "@/lib/api";
import { Pause, Play } from "lucide-react";
import {
  picksToPlayerQueue,
  usePlayer,
} from "@/components/player/PlayerProvider";

export function TrackList({ picks }: { picks: (Pick & { _arc?: string })[] }) {
  const player = usePlayer();
  const queue = picksToPlayerQueue(picks);

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
              <span className="font-sans text-xs uppercase tracking-[0.14em] text-cream-muted">
                {" "}
                — {p.artist}
              </span>
            </div>
            <div className="font-sans text-xs text-cream-muted/70 truncate">
              {p.genre} · {p.mood}
            </div>
          </div>
          <div className="hidden md:flex items-center gap-2 shrink-0">
            {p._arc && (
              <span className="font-sans text-[11px] text-copper">
                · {p._arc}
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={() => {
              if (player.isCurrent(p.id)) {
                player.toggle();
              } else {
                player.playTrack(queue, i);
              }
            }}
            className="justify-self-end text-cream-muted/60 opacity-100 transition-all hover:text-copper focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper/70 md:opacity-0 md:group-hover:opacity-100"
            aria-label={
              player.isCurrent(p.id) && player.playing
                ? `Pause ${p.title}`
                : `Play ${p.title}`
            }
            aria-pressed={player.isCurrent(p.id) && player.playing}
          >
            {player.isCurrent(p.id) && player.playing ? (
              <Pause className="h-4 w-4" />
            ) : (
              <Play className="h-4 w-4" />
            )}
          </button>
        </div>
      ))}
    </div>
  );
}
