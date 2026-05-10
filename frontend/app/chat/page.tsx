"use client";
import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { NowPlayingBar } from "@/components/NowPlayingBar";
import { Hero } from "@/components/Hero";
import { AgentTrace } from "@/components/chat/AgentTrace";
import { MessageList, type Message } from "@/components/chat/MessageList";
import { MessageInput } from "@/components/chat/MessageInput";
import { PersonaSelector } from "@/components/chat/PersonaSelector";
import { streamChat, type Step } from "@/lib/api";
import {
  featuredToPlayerTrack,
  usePlayer,
} from "@/components/player/PlayerProvider";
import { featuredTracks } from "@/lib/featured";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [steps, setSteps] = useState<Step[]>([]);
  const [totalMs, setTotalMs] = useState<number | undefined>(undefined);
  const [streaming, setStreaming] = useState(false);
  const [persona, setPersona] = useState("warm");
  const player = usePlayer();

  useEffect(() => {
    setPersona(localStorage.getItem("remixx.persona") ?? "warm");
  }, []);

  const handlePersonaChange = (key: string) => {
    setPersona(key);
    try {
      localStorage.setItem("remixx.persona", key);
    } catch {}
  };

  async function send(message: string) {
    if (streaming) return;
    setMessages((m) => [...m, { role: "user", content: message }]);
    setSteps([]);
    setTotalMs(undefined);
    setStreaming(true);

    try {
      for await (const ev of streamChat(message, persona)) {
        if (ev.type === "step") {
          setSteps((s) => [...s, ev.payload]);
        } else if (ev.type === "result") {
          setMessages((m) => [...m, { role: "assistant", result: ev.payload }]);
          setTotalMs(ev.payload.total_ms);
        } else if (ev.type === "error") {
          setMessages((m) => [
            ...m,
            {
              role: "assistant",
              result: {
                picks: [],
                commentary: `Couldn't process that — ${ev.payload.error}`,
                total_ms: 0,
                intent: { mode: "chat", duration_min: null, seed_songs: [] },
              },
            },
          ]);
        }
      }
    } catch (err) {
      console.error("stream failed:", err);
    } finally {
      setStreaming(false);
    }
  }

  const traceVisible = steps.length > 0 || totalMs !== undefined;
  const featuredQueue = featuredTracks.map(featuredToPlayerTrack);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div
        className={`flex h-screen flex-1 flex-col pb-24 transition-[margin] duration-300 md:ml-[284px] ${
          traceVisible ? "xl:mr-[360px]" : ""
        }`}
      >
        <div className="flex items-center justify-between border-b border-cream/5 px-6 pb-4 pt-6 md:px-12">
          <div className="flex items-center gap-3">
            <span className="w-1.5 h-1.5 rounded-full bg-copper animate-pulse" />
            <span className="font-display italic text-cream-muted text-sm">
              Remixx · Home
            </span>
          </div>
          <PersonaSelector value={persona} onChange={handlePersonaChange} />
        </div>
        {messages.length === 0 && !streaming ? (
          <div className="flex-1 overflow-y-auto">
            <Hero
              disabled={streaming}
              onPlayNow={() => {
                player.playTrack(featuredQueue, 0);
                void send("songs for late night, hopeful, slower, room for breath");
              }}
              onInspectPicks={() =>
                void send("inspect tonight's slow hopeful mix and explain the picks")
              }
              onAlbumSelect={(query) => void send(query)}
            />
          </div>
        ) : (
          <MessageList messages={messages} isStreaming={streaming} />
        )}
        <MessageInput onSubmit={send} disabled={streaming} />
      </div>
      <AgentTrace steps={steps} totalMs={totalMs} />
      <NowPlayingBar rightOffset={traceVisible ? 360 : 0} />
    </div>
  );
}
