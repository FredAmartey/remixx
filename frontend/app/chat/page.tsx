"use client";
import { useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { NowPlayingBar } from "@/components/NowPlayingBar";
import { AgentTrace } from "@/components/chat/AgentTrace";
import { MessageList, type Message } from "@/components/chat/MessageList";
import { MessageInput } from "@/components/chat/MessageInput";
import { PersonaSelector } from "@/components/chat/PersonaSelector";
import { streamChat, type Step } from "@/lib/api";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [steps, setSteps] = useState<Step[]>([]);
  const [totalMs, setTotalMs] = useState<number | undefined>(undefined);
  const [streaming, setStreaming] = useState(false);
  const [persona, setPersona] = useState<string>(() => {
    if (typeof window === "undefined") return "warm";
    return localStorage.getItem("remixx.persona") ?? "warm";
  });

  const handlePersonaChange = (key: string) => {
    setPersona(key);
    try {
      localStorage.setItem("remixx.persona", key);
    } catch {}
  };

  async function send(message: string) {
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

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-[240px] mr-[360px] mb-24 flex flex-col h-screen">
        <div className="px-12 pt-8 pb-4 border-b border-cream/5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="w-1.5 h-1.5 rounded-full bg-copper animate-pulse" />
            <span className="font-display italic text-cream-muted text-sm">
              Remixx · Chat
            </span>
          </div>
          <PersonaSelector value={persona} onChange={handlePersonaChange} />
        </div>
        <MessageList messages={messages} isStreaming={streaming} />
        <MessageInput onSubmit={send} disabled={streaming} />
      </div>
      <AgentTrace steps={steps} totalMs={totalMs} />
      <NowPlayingBar rightOffset={steps.length > 0 || totalMs !== undefined ? 360 : 0} />
    </div>
  );
}
