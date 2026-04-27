import type { ChatResult } from "@/lib/api";
import { PicksTable } from "@/components/PicksTable";

export type Message =
  | { role: "user"; content: string }
  | { role: "assistant"; result: ChatResult };

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
