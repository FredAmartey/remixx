"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { NowPlayingBar } from "@/components/NowPlayingBar";
import { PersonaSelector } from "@/components/chat/PersonaSelector";
import { PicksTable } from "@/components/PicksTable";
import { SongInputGrid } from "@/components/taste/SongInputGrid";
import { ProfileOutput } from "@/components/taste/ProfileOutput";
import { readTaste, type TasteResult } from "@/lib/api";

const EMPTY_TRACKS = ["", "", "", "", "", ""];

export default function TastePage() {
  const [persona, setPersona] = useState("warm");
  const [tracks, setTracks] = useState<string[]>(EMPTY_TRACKS);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TasteResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setPersona(localStorage.getItem("remixx.persona") ?? "warm");
  }, []);

  const handlePersonaChange = (key: string) => {
    setPersona(key);
    try {
      localStorage.setItem("remixx.persona", key);
    } catch {}
  };

  const seeded = tracks.map((t) => t.trim()).filter(Boolean);
  const enough = seeded.length >= 3;

  async function read() {
    if (!enough) return;
    setLoading(true);
    setError(null);
    try {
      const r = await readTaste(seeded, persona, 8);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-h-screen flex-1 flex-col pb-24 md:ml-[284px]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-cream/5 px-6 pb-4 pt-6 md:px-12">
          <div className="flex items-center gap-3">
            <span className="w-1.5 h-1.5 rounded-full bg-copper animate-pulse" />
            <span className="font-display italic text-cream-muted text-sm">
              Remixx · Taste mirror
            </span>
          </div>
          <PersonaSelector value={persona} onChange={handlePersonaChange} />
        </div>

        <div className="flex-1 overflow-y-auto px-12 py-12">
          <div className="max-w-5xl mx-auto">
            {/* Two-column offset */}
            <div className="grid grid-cols-1 md:grid-cols-[60%_40%] gap-12">
              <div className="flex flex-col gap-8">
                <div>
                  <h1 className="font-sans text-cream text-4xl font-semibold leading-tight md:text-5xl">
                    What do you actually listen to?
                  </h1>
                  <p className="mt-4 max-w-md font-sans text-base leading-7 text-cream-muted">
                    Paste 3&ndash;6 songs you love. We&rsquo;ll read your taste and
                    recommend from there.
                  </p>
                </div>

                <SongInputGrid
                  values={tracks}
                  onChange={setTracks}
                  disabled={loading}
                />

                <div className="flex items-center gap-6">
                  <button
                    type="button"
                    onClick={() => void read()}
                    disabled={!enough || loading}
                    className="font-sans text-sm font-semibold text-copper underline decoration-copper decoration-1 underline-offset-[6px] transition-colors hover:text-copper-glow disabled:opacity-30"
                  >
                    {loading ? "Reading…" : "Read my taste →"}
                  </button>
                  {!enough && (
                    <span className="font-sans text-xs text-cream-muted/60">
                      add at least 3 tracks
                    </span>
                  )}
                </div>

                {error && (
                  <div className="font-sans text-sm text-copper-glow/80">
                    {error}
                  </div>
                )}
              </div>

              {/* Right column: profile output (fades in after submit) */}
              <div className="md:pt-24">
                {loading && (
                  <div className="font-sans text-sm text-cream-muted">
                    reading<span className="animate-pulse">…</span>
                  </div>
                )}
                {result && !loading && (
                  <ProfileOutput profile={result.profile} />
                )}
              </div>
            </div>

            {/* Recommendations */}
            {result && !loading && (
              <div className="mt-16">
                <div className="border-t border-cream/10 pt-10">
                  <div className="font-sans text-[10px] uppercase tracking-[0.2em] text-copper mb-6">
                    Recommended
                  </div>
                  <PicksTable picks={result.picks} />
                </div>

                {result.commentary && (
                  <div className="mt-10 pl-6 border-l-2 border-copper/60 max-w-2xl">
                    <div className="font-sans text-cream text-sm leading-7 whitespace-pre-line">
                      {result.commentary}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
      <NowPlayingBar />
    </div>
  );
}
