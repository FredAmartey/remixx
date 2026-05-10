"use client";

import {
  Suspense,
  useEffect,
  useState,
  type Dispatch,
  type SetStateAction,
} from "react";
import { useSearchParams } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { NowPlayingBar } from "@/components/NowPlayingBar";
import { PersonaSelector } from "@/components/chat/PersonaSelector";
import { NarrativeArc } from "@/components/playlist/NarrativeArc";
import { TrackList } from "@/components/playlist/TrackList";
import {
  generatePlaylist,
  savePlaylist,
  type PlaylistResult,
} from "@/lib/api";

export default function PlaylistPage() {
  const [persona, setPersona] = useState("warm");
  const [prompt, setPrompt] = useState("");
  const [duration, setDuration] = useState("45");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PlaylistResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved">(
    "idle",
  );

  useEffect(() => {
    setPersona(localStorage.getItem("remixx.persona") ?? "warm");
  }, []);

  async function buildWith(nextPrompt: string, nextDuration: string, nextPersona: string) {
    const p = nextPrompt.trim();
    const d = parseInt(nextDuration, 10);
    if (!p || !Number.isFinite(d) || d <= 0) return;
    setLoading(true);
    setError(null);
    setSaveState("idle");
    try {
      const r = await generatePlaylist(p, d, nextPersona);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const handlePersonaChange = (key: string) => {
    setPersona(key);
    try {
      localStorage.setItem("remixx.persona", key);
    } catch {}
    if (result && !loading) {
      void buildWith(result.prompt, String(result.duration_min), key);
    }
  };

  async function build() {
    await buildWith(prompt, duration, persona);
  }

  async function handleSave() {
    if (!result) return;
    setSaveState("saving");
    setError(null);
    try {
      const name = result.prompt.slice(0, 80);
      await savePlaylist(name, result.prompt, result.picks);
      setSaveState("saved");
    } catch (e) {
      setSaveState("idle");
      setError(e instanceof Error ? e.message : "Could not save playlist");
    }
  }

  function regenerate() {
    setResult(null);
    setSaveState("idle");
    void buildWith(prompt, duration, persona);
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-h-screen flex-1 flex-col pb-24 md:ml-[284px]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-cream/5 px-6 pb-4 pt-6 md:px-12">
          <Suspense fallback={null}>
            <PlaylistQuerySync
              setPrompt={setPrompt}
              setDuration={setDuration}
            />
          </Suspense>
          <div className="flex items-center gap-3">
            <span className="w-1.5 h-1.5 rounded-full bg-copper animate-pulse" />
            <span className="font-display italic text-cream-muted text-sm">
              Remixx · Playlist
            </span>
          </div>
          <PersonaSelector value={persona} onChange={handlePersonaChange} />
        </div>

        {!result && !loading && (
          <div className="flex-1 flex items-center justify-center px-12">
            <div className="max-w-2xl w-full flex flex-col items-center text-center gap-8">
              <h1 className="font-sans text-cream text-4xl font-semibold leading-tight md:text-5xl">
                Build me a playlist.
              </h1>
              <p className="max-w-md font-sans text-base leading-7 text-cream-muted">
                Describe the vibe and the duration. We&rsquo;ll build a 10&ndash;12 track arc.
              </p>

              <form
                className="mt-4 flex w-full flex-col items-stretch justify-center gap-6 md:flex-row md:items-end"
                onSubmit={(e) => {
                  e.preventDefault();
                  void build();
                }}
              >
                <div className="flex-1 max-w-md">
                  <input
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="vibe…"
                    className="w-full bg-transparent border-b border-cream/20 px-1 py-3 font-sans text-sm text-cream transition-colors placeholder:text-cream-muted/60 focus:border-copper focus:outline-none"
                  />
                </div>
                <div className="w-32">
                  <input
                    value={duration}
                    onChange={(e) =>
                      setDuration(e.target.value.replace(/[^0-9]/g, ""))
                    }
                    inputMode="numeric"
                    placeholder="min"
                    className="w-full bg-transparent border-b border-cream/20 focus:border-copper focus:outline-none px-1 py-3 text-cream font-mono text-sm placeholder:text-cream-muted/60 transition-colors text-center"
                  />
                </div>
              </form>

              <button
                type="button"
                onClick={() => void build()}
                disabled={!prompt.trim()}
                className="font-sans text-sm font-semibold text-copper underline decoration-copper decoration-1 underline-offset-[6px] transition-colors hover:text-copper-glow disabled:opacity-30"
              >
                Build &rarr;
              </button>

              {error && (
                <div className="font-sans text-sm text-copper-glow/80">
                  {error}
                </div>
              )}
            </div>
          </div>
        )}

        {loading && (
          <div className="flex-1 flex items-center justify-center px-12">
            <div className="self-center pl-6 border-l-2 border-copper/40">
              <div className="font-sans text-sm text-cream-muted">
                thinking<span className="animate-pulse">…</span>
              </div>
            </div>
          </div>
        )}

        {result && !loading && (
          <div className="flex-1 overflow-y-auto px-12 py-12">
            <div className="max-w-5xl mx-auto">
              {/* Prompt echo */}
              <div className="mb-10">
                <div className="font-sans text-[10px] uppercase tracking-[0.2em] text-copper mb-2">
                  Playlist
                </div>
                <h2 className="font-sans text-cream text-3xl font-semibold leading-tight">
                  {result.prompt}
                </h2>
                <div className="font-sans text-cream-muted text-sm mt-2">
                  {result.duration_min} minutes &middot; {result.picks.length} tracks
                </div>
              </div>

              {/* Two-column layout: track list + arc */}
              <div className="grid grid-cols-1 md:grid-cols-[65%_35%] gap-10">
                <div>
                  <TrackList picks={result.picks} />
                </div>
                <div className="md:sticky md:top-8 self-start">
                  <div className="h-[400px] w-full">
                    <NarrativeArc trackCount={result.picks.length} />
                  </div>
                </div>
              </div>

              {/* Commentary */}
              {result.commentary && (
                <div className="mt-12 pl-6 border-l-2 border-copper/60 max-w-2xl">
                  <div className="font-sans text-cream text-sm leading-7 whitespace-pre-line">
                    {result.commentary}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="mt-12 flex items-center gap-8 text-sm">
                <button
                  type="button"
                  onClick={() => void handleSave()}
                  disabled={saveState !== "idle"}
                  className="font-sans text-copper hover:text-copper-glow underline underline-offset-4 decoration-copper/60 disabled:opacity-50 transition-colors"
                >
                  {saveState === "saved"
                    ? "Saved"
                    : saveState === "saving"
                      ? "Saving…"
                      : "Save"}
                </button>
                <span className="text-cream-muted/40">·</span>
                <button
                  type="button"
                  onClick={regenerate}
                  className="font-sans text-cream-muted hover:text-cream underline underline-offset-4 decoration-cream/30 transition-colors"
                >
                  Regenerate
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
      <NowPlayingBar />
    </div>
  );
}

function PlaylistQuerySync({
  setPrompt,
  setDuration,
}: {
  setPrompt: Dispatch<SetStateAction<string>>;
  setDuration: Dispatch<SetStateAction<string>>;
}) {
  const params = useSearchParams();

  useEffect(() => {
    const nextPrompt = params.get("prompt");
    const nextDuration = params.get("duration");
    if (nextPrompt) setPrompt(nextPrompt);
    if (nextDuration && /^\d+$/.test(nextDuration)) setDuration(nextDuration);
  }, [params, setDuration, setPrompt]);

  return null;
}
