export type Step = {
  step: number | string;
  title?: string;
  detail?: string;
  ms?: number;
};

export type Pick = {
  id: string;
  title: string;
  artist: string;
  album?: string;
  genre: string;
  mood: string;
  energy: number;
  valence?: number;
  danceability?: number;
  acousticness?: number;
  tempo_bpm?: number;
  _score?: number;
  _reasons?: string[];
  _arc?: string;
};

export type ChatResult = {
  picks: Pick[];
  commentary: string;
  total_ms: number;
  intent: { mode: string; duration_min: number | null; seed_songs: string[] };
};

export type ChatStreamEvent =
  | { type: "step"; payload: Step }
  | { type: "result"; payload: ChatResult }
  | { type: "error"; payload: { error: string } };

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function* streamChat(
  message: string,
  persona: string,
  k = 5,
): AsyncGenerator<ChatStreamEvent> {
  const res = await fetch(`${API}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, persona, k }),
  });
  if (!res.body) throw new Error("no body");
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE event blocks separated by blank line
    const blocks = buffer.split(/\n\n/);
    buffer = blocks.pop() ?? "";

    for (const block of blocks) {
      const lines = block.split("\n").map((l) => l.trim()).filter(Boolean);
      let event = "message";
      let data = "";
      for (const line of lines) {
        if (line.startsWith(":")) continue; // SSE comment / heartbeat
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (!data) continue;
      try {
        const parsed = JSON.parse(data);
        if (event === "step") yield { type: "step", payload: parsed };
        else if (event === "result") yield { type: "result", payload: parsed };
        else if (event === "error") yield { type: "error", payload: parsed };
      } catch {
        // ignore malformed lines
      }
    }
  }
}

export async function fetchPersonas(): Promise<{ key: string; name: string; tagline: string }[]> {
  const res = await fetch(`${API}/personas`);
  return res.json();
}
