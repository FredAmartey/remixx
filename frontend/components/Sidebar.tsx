import Link from "next/link";
import { SidebarNav } from "./SidebarNav";
import { playlistHref, playlistPresets } from "@/lib/featured";

export function Sidebar() {
  return (
    <aside className="fixed bottom-0 left-0 top-0 hidden w-[284px] flex-col border-r border-copper/20 bg-walnut-deep/95 shadow-[24px_0_80px_rgba(0,0,0,0.22)] md:flex">
      {/* Wordmark */}
      <div className="px-8 pt-8">
        <Link
          href="/chat"
          className="font-display text-4xl font-semibold text-copper transition-colors hover:text-copper-glow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper/70"
        >
          Remixx
        </Link>
      </div>

      {/* Nav (client component — handles active route) */}
      <SidebarNav />

      {/* Divider */}
      <div className="mx-8 mt-9 border-t border-cream/16" />

      {/* Playlists header */}
      <div className="px-8 mt-6 flex flex-col gap-4">
        {playlistPresets.map(({ name, prompt, duration }) => (
          <a
            key={name}
            href={playlistHref(prompt, duration)}
            className="font-sans text-base text-cream/62 transition-colors hover:text-cream focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper/70"
          >
            {name}
          </a>
        ))}
      </div>

      {/* User pill */}
      <div className="mb-7 mt-auto flex items-center gap-3 px-8">
        <div className="flex h-9 w-9 items-center justify-center rounded-[4px] border border-copper/30 bg-copper/10 font-sans text-xs text-copper">
          F
        </div>
        <div className="flex flex-col leading-tight">
          <span className="font-sans text-sm text-cream">Fred Amartey</span>
          <span className="font-sans text-[10px] uppercase tracking-[0.18em] text-cream-muted">
            Pro
          </span>
        </div>
      </div>
    </aside>
  );
}
