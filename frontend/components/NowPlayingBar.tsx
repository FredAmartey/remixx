"use client";

import Image from "next/image";
import { Pause, Play, SkipBack, SkipForward, Volume2 } from "lucide-react";
import type { CSSProperties } from "react";
import { usePlayer } from "@/components/player/PlayerProvider";

function formatTime(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const rest = Math.floor(seconds % 60);
  return `${minutes}:${String(rest).padStart(2, "0")}`;
}

export function NowPlayingBar({ rightOffset = 0 }: { rightOffset?: number } = {}) {
  const {
    currentTrack,
    next,
    playing,
    previous,
    progress,
    setProgress,
    setVolume,
    toggle,
    volume,
  } = usePlayer();
  const progressPercent =
    currentTrack.durationSeconds > 0
      ? (progress / currentTrack.durationSeconds) * 100
      : 0;

  return (
    <div
      className="fixed bottom-0 left-0 z-30 flex h-24 items-center gap-4 border-t border-copper/20 bg-walnut-deep/95 px-4 shadow-[0_-22px_80px_rgba(0,0,0,0.22)] md:left-[284px] md:gap-6 md:px-7"
      style={{ right: rightOffset }}
    >
      {/* Left: track info */}
      <div className="flex min-w-0 items-center gap-4 md:w-[330px]">
        <div className="relative h-[62px] w-[62px] flex-shrink-0 overflow-hidden rounded-[3px] border border-cream/10">
          <Image
            src={currentTrack.cover}
            alt={`${currentTrack.title} album artwork`}
            fill
            sizes="62px"
            className="object-cover"
          />
        </div>
        <div className="flex min-w-0 flex-col overflow-hidden leading-tight">
          <span className="truncate font-display text-xl text-cream">
            {currentTrack.title}
          </span>
          <span className="mt-1 truncate font-sans text-xs uppercase tracking-[0.18em] text-cream-muted">
            {currentTrack.artist}
          </span>
        </div>
      </div>

      {/* Center: controls + progress */}
      <div className="flex flex-1 flex-col items-center gap-3">
        <div className="flex items-center gap-6 text-cream-muted">
          <button
            type="button"
            onClick={previous}
            className="transition-colors hover:text-cream focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper/70"
            aria-label="Previous"
          >
            <SkipBack className="h-4 w-4" strokeWidth={1.5} />
          </button>
          <button
            type="button"
            onClick={toggle}
            className="flex h-9 w-9 items-center justify-center rounded-full border border-cream/20 text-cream transition-colors hover:border-copper hover:text-copper focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper/70"
            aria-label={playing ? "Pause" : "Play"}
            aria-pressed={playing}
          >
            {playing ? (
              <Pause className="h-4 w-4" strokeWidth={1.5} fill="currentColor" />
            ) : (
              <Play className="ml-0.5 h-4 w-4" strokeWidth={1.5} fill="currentColor" />
            )}
          </button>
          <button
            type="button"
            onClick={next}
            className="transition-colors hover:text-cream focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper/70"
            aria-label="Next"
          >
            <SkipForward className="h-4 w-4" strokeWidth={1.5} />
          </button>
        </div>
        <div className="flex w-full max-w-[520px] items-center gap-3">
          <span className="font-sans text-[10px] tabular-nums text-cream-muted">
            {formatTime(progress)}
          </span>
          <input
            aria-label="Playback position"
            type="range"
            min={0}
            max={currentTrack.durationSeconds}
            value={Math.min(progress, currentTrack.durationSeconds)}
            onChange={(event) => setProgress(Number(event.target.value))}
            className="range-copper flex-1"
            style={{ "--range-progress": `${progressPercent}%` } as CSSProperties}
          />
          <span className="font-sans text-[10px] tabular-nums text-cream-muted">
            {currentTrack.duration}
          </span>
        </div>
      </div>

      {/* Right: volume */}
      <div className="hidden w-[200px] items-center justify-end gap-3 text-cream-muted lg:flex">
        <Volume2 className="h-4 w-4" strokeWidth={1.5} />
        <input
          aria-label="Volume"
          type="range"
          min={0}
          max={100}
          value={volume}
          onChange={(event) => setVolume(Number(event.target.value))}
          className="range-copper w-24"
          style={{ "--range-progress": `${volume}%` } as CSSProperties}
        />
      </div>
    </div>
  );
}
