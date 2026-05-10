"use client";

import Image from "next/image";
import { AlbumRow } from "@/components/AlbumRow";

export function Hero({
  onPlayNow,
  onInspectPicks,
  onAlbumSelect,
  disabled,
}: {
  onPlayNow: () => void;
  onInspectPicks: () => void;
  onAlbumSelect: (query: string) => void;
  disabled?: boolean;
}) {
  return (
    <section className="relative min-h-[calc(100dvh-15.5rem)] overflow-hidden border-b border-cream/10">
      <Image
        src="/remixx-assets/hero-walnut-vinyl.png"
        alt="Walnut desk with a black vinyl record"
        fill
        priority
        sizes="(max-width: 768px) 100vw, calc(100vw - 284px)"
        className="object-cover object-[44%_center]"
      />
      <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(20,13,8,0.28),rgba(18,10,5,0.08)_38%,rgba(12,7,4,0.72)_74%),linear-gradient(0deg,rgba(16,10,6,0.88),rgba(16,10,6,0.06)_42%,rgba(16,10,6,0.20))]" />
      <div className="absolute inset-0 opacity-[0.16] mix-blend-soft-light [background-image:radial-gradient(rgba(245,239,227,0.35)_0.6px,transparent_0.6px)] [background-size:3px_3px]" />

      <div className="relative z-10 flex min-h-[calc(100dvh-15.5rem)] flex-col justify-end px-6 pb-6 pt-14 md:px-12 xl:px-16">
        <div className="ml-auto max-w-[560px] pb-6 xl:mr-6">
          <h1 className="font-display text-[4rem] leading-[0.92] text-cream text-balance md:text-[5.4rem] xl:text-[6.8rem]">
            Tonight&rsquo;s mix is ready.
          </h1>
          <p className="mt-5 max-w-[460px] font-display text-lg italic leading-snug text-cream-muted md:text-xl xl:text-2xl">
            Picked from your last 14 days. Slower, hopeful, room for breath.
          </p>
          <div className="mt-7 flex items-center gap-8">
            <button
              type="button"
              onClick={onPlayNow}
              disabled={disabled}
              className="font-display text-xl italic text-copper underline decoration-copper/50 underline-offset-[7px] transition hover:text-copper-glow hover:decoration-copper-glow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper/70 disabled:opacity-40"
            >
              Play now &rarr;
            </button>
            <button
              type="button"
              onClick={onInspectPicks}
              disabled={disabled}
              className="font-sans text-sm text-cream-muted transition hover:text-cream focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper/70 disabled:opacity-40"
            >
              Inspect picks
            </button>
          </div>
        </div>

        <AlbumRow onSelect={onAlbumSelect} />
        <div className="sr-only">
          Album artwork buttons use tonight&apos;s mix as a seed for the AI picker.
        </div>
      </div>
    </section>
  );
}
