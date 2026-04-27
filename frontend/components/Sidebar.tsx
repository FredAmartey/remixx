import { Home, Search, Library } from "lucide-react";

const navItems = [
  { label: "Home", icon: Home },
  { label: "Search", icon: Search },
  { label: "Your Library", icon: Library },
];

const playlists = [
  "Late Drives",
  "Sunday Slow",
  "Studio Sessions",
  "Heartbreak Hours",
  "Deep Focus",
  "Saturday Hangover",
];

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 bottom-0 w-[240px] bg-walnut-deep flex flex-col">
      {/* Wordmark */}
      <div className="px-6 pt-6">
        <span className="font-display text-2xl italic text-copper tracking-tight">
          Remixx
        </span>
      </div>

      {/* Nav */}
      <nav className="px-6 mt-8 flex flex-col gap-4">
        {navItems.map(({ label, icon: Icon }) => (
          <a
            key={label}
            href="#"
            className="flex items-center gap-3 text-cream hover:text-copper-glow transition-colors"
          >
            <Icon className="h-4 w-4 text-cream-muted" strokeWidth={1.5} />
            <span className="font-display italic text-base">{label}</span>
          </a>
        ))}
      </nav>

      {/* Divider */}
      <div className="mx-6 mt-8 border-t border-cream/10" />

      {/* Playlists header */}
      <div className="px-6 mt-6">
        <span className="font-sans text-[10px] uppercase tracking-[0.18em] text-copper">
          Playlists
        </span>
      </div>

      {/* Playlists */}
      <div className="px-6 mt-3 flex flex-col gap-2.5">
        {playlists.map((name) => (
          <a
            key={name}
            href="#"
            className="font-sans text-sm text-cream/70 hover:text-cream transition-colors"
          >
            {name}
          </a>
        ))}
      </div>

      {/* User pill */}
      <div className="mt-auto mb-6 px-6 flex items-center gap-3">
        <div className="h-8 w-8 rounded-full bg-copper/20 flex items-center justify-center text-copper font-sans text-xs">
          F
        </div>
        <div className="flex flex-col leading-tight">
          <span className="font-sans text-sm text-cream">Fred Amartey</span>
          <span className="font-sans text-[10px] uppercase tracking-wider text-cream-muted">
            Pro
          </span>
        </div>
      </div>
    </aside>
  );
}
