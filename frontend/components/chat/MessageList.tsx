import type { ChatResult, Pick } from "@/lib/api";
import { Play } from "lucide-react";

export type Message =
  | { role: "user"; content: string }
  | { role: "assistant"; result: ChatResult };

function PicksTable({ picks }: { picks: Pick[] }) {
  return (
    <div className="mt-8 space-y-1">
      {picks.map((p, i) => (
        <div
          key={p.id}
          className="grid grid-cols-[2rem_1fr_auto_2rem] items-center gap-4 py-3 border-b border-cream/5 last:border-b-0 group"
        >
          <span className="font-mono text-xs text-cream-muted/70 tabular-nums">
            {String(i + 1).padStart(2, "0")}
          </span>
          <div className="min-w-0">
            <div className="font-sans text-cream truncate">{p.title}</div>
            <div className="font-display italic text-sm text-cream-muted truncate">
              {p.artist}
            </div>
          </div>
          <div className="hidden md:flex gap-2 text-[11px] font-display italic text-copper/80 shrink-0">
            <span>{p.genre}</span>
            <span className="text-cream-muted/40">·</span>
            <span>{p.mood}</span>
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

export function MessageList({ messages, isStreaming }: { messages: Message[]; isStreaming: boolean }) {
  return (
    <div className="flex-1 overflow-y-auto px-12 py-12">
      <div className="max-w-2xl mx-auto flex flex-col gap-12">
        {messages.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="self-end max-w-[85%]">
              <div className="font-display text-cream text-xl leading-relaxed text-right">
                {m.content}
              </div>
            </div>
          ) : (
            <div key={i} className="self-start max-w-full pl-6 border-l-2 border-copper">
              <div className="font-display italic text-cream text-lg leading-relaxed whitespace-pre-line">
                {m.result.commentary}
              </div>
              <PicksTable picks={m.result.picks} />
            </div>
          )
        )}
        {isStreaming && (
          <div className="self-start pl-6 border-l-2 border-copper/40">
            <div className="font-display italic text-cream-muted/60">
              thinking<span className="animate-pulse">…</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
