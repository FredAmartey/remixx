"use client";

import Image from "next/image";
import { featuredTracks } from "@/lib/featured";
import {
  featuredToPlayerTrack,
  usePlayer,
} from "@/components/player/PlayerProvider";

export function AlbumRow({
  onSelect,
}: {
  onSelect?: (query: string) => void;
}) {
  const player = usePlayer();
  const queue = featuredTracks.map(featuredToPlayerTrack);

  return (
    <div className="mt-10 grid grid-cols-2 gap-5 md:grid-cols-3 xl:grid-cols-5">
      {featuredTracks.map((a, i) => (
        <button
          key={a.slug}
          type="button"
          onClick={() => {
            player.playTrack(queue, i);
            onSelect?.(a.query);
          }}
          className="group min-w-0 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper/70"
          aria-label={`Use ${a.title} by ${a.artist} as a recommendation seed`}
        >
          <div className="relative aspect-square overflow-hidden rounded-[3px] border border-cream/10 bg-walnut-deep shadow-[0_22px_60px_rgba(0,0,0,0.34)] transition duration-300 group-hover:-translate-y-1 group-hover:border-copper/50 group-active:translate-y-0">
            <Image
              src={a.cover}
              alt={`${a.title} album artwork`}
              fill
              sizes="(max-width: 768px) 42vw, (max-width: 1280px) 18vw, 190px"
              className="object-cover"
            />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_35%_20%,rgba(232,161,74,0.22),transparent_42%),linear-gradient(to_top,rgba(12,8,5,0.42),transparent_52%)] opacity-80 transition group-hover:opacity-45" />
          </div>
          <div className="mt-3">
            <div className="truncate font-display text-base text-cream">
              {a.title}
            </div>
            <div className="mt-1 truncate font-sans text-[11px] uppercase text-cream-muted tracking-[0.16em]">
              {a.artist}
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}
