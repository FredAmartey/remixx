"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Pick } from "@/lib/api";
import { featuredTracks, type FeaturedTrack } from "@/lib/featured";

export type PlayerTrack = {
  id: string;
  title: string;
  artist: string;
  cover: string;
  duration: string;
  durationSeconds: number;
  genre?: string;
  mood?: string;
};

type PlayerContextValue = {
  queue: PlayerTrack[];
  currentTrack: PlayerTrack;
  currentIndex: number;
  playing: boolean;
  progress: number;
  volume: number;
  playTrack: (queue: PlayerTrack[], index?: number) => void;
  toggle: () => void;
  previous: () => void;
  next: () => void;
  setProgress: (seconds: number) => void;
  setVolume: (volume: number) => void;
  isCurrent: (id: string) => boolean;
};

const PlayerContext = createContext<PlayerContextValue | null>(null);

function durationToSeconds(duration: string) {
  const [minutes, seconds] = duration.split(":").map((v) => Number(v));
  if (!Number.isFinite(minutes) || !Number.isFinite(seconds)) return 240;
  return minutes * 60 + seconds;
}

export function featuredToPlayerTrack(track: FeaturedTrack): PlayerTrack {
  return {
    id: track.slug,
    title: track.title,
    artist: track.artist,
    cover: track.cover,
    duration: track.duration,
    durationSeconds: durationToSeconds(track.duration),
    genre: track.genre,
    mood: track.mood,
  };
}

export function pickToPlayerTrack(pick: Pick): PlayerTrack {
  const fallback = featuredTracks[Math.abs(hashCode(pick.id)) % featuredTracks.length];
  return {
    id: pick.id,
    title: pick.title,
    artist: pick.artist,
    cover: fallback.cover,
    duration: fallback.duration,
    durationSeconds: durationToSeconds(fallback.duration),
    genre: pick.genre,
    mood: pick.mood,
  };
}

export function picksToPlayerQueue(picks: Pick[]) {
  return picks.map(pickToPlayerTrack);
}

function hashCode(value: string) {
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash << 5) - hash + value.charCodeAt(i);
    hash |= 0;
  }
  return hash;
}

const defaultQueue = featuredTracks.map(featuredToPlayerTrack);

export function PlayerProvider({ children }: { children: ReactNode }) {
  const [queue, setQueue] = useState<PlayerTrack[]>(defaultQueue);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgressState] = useState(84);
  const [volume, setVolumeState] = useState(62);

  const currentTrack = queue[currentIndex] ?? defaultQueue[0];

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(() => {
      setProgressState((seconds) => {
        if (seconds + 1 < currentTrack.durationSeconds) return seconds + 1;
        setCurrentIndex((index) => (index + 1) % queue.length);
        return 0;
      });
    }, 1000);
    return () => window.clearInterval(timer);
  }, [currentTrack.durationSeconds, playing, queue.length]);

  const value = useMemo<PlayerContextValue>(
    () => ({
      queue,
      currentTrack,
      currentIndex,
      playing,
      progress,
      volume,
      playTrack(nextQueue, index = 0) {
        if (nextQueue.length === 0) return;
        setQueue(nextQueue);
        setCurrentIndex(Math.min(Math.max(index, 0), nextQueue.length - 1));
        setProgressState(0);
        setPlaying(true);
      },
      toggle() {
        setPlaying((next) => !next);
      },
      previous() {
        setCurrentIndex((index) => (index - 1 + queue.length) % queue.length);
        setProgressState(0);
        setPlaying(true);
      },
      next() {
        setCurrentIndex((index) => (index + 1) % queue.length);
        setProgressState(0);
        setPlaying(true);
      },
      setProgress(seconds) {
        setProgressState(Math.min(Math.max(seconds, 0), currentTrack.durationSeconds));
      },
      setVolume(nextVolume) {
        setVolumeState(Math.min(Math.max(nextVolume, 0), 100));
      },
      isCurrent(id) {
        return currentTrack.id === id;
      },
    }),
    [currentIndex, currentTrack, playing, progress, queue, volume],
  );

  return (
    <PlayerContext.Provider value={value}>{children}</PlayerContext.Provider>
  );
}

export function usePlayer() {
  const context = useContext(PlayerContext);
  if (!context) {
    throw new Error("usePlayer must be used inside PlayerProvider");
  }
  return context;
}
