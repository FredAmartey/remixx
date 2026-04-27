import { Play, SkipBack, SkipForward, Volume2 } from "lucide-react";

export function NowPlayingBar() {
  return (
    <div className="fixed bottom-0 left-[240px] right-0 h-24 bg-walnut-deep border-t border-cream/10 flex items-center px-6 gap-6 z-10">
      {/* Left: track info */}
      <div className="flex items-center gap-4 w-[320px]">
        <div
          className="relative h-[60px] w-[60px] rounded-full flex-shrink-0 animate-[spin_30s_linear_infinite]"
          style={{
            background:
              "radial-gradient(circle at 50% 50%, #1a130e 0%, #0a0705 55%, #1a130e 70%, #050302 100%)",
            boxShadow:
              "inset 0 0 0 1px rgba(245,239,227,0.04), inset 0 0 0 8px rgba(245,239,227,0.025), inset 0 0 0 16px rgba(245,239,227,0.01)",
          }}
        >
          <div
            className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[20px] w-[20px] rounded-full"
            style={{
              background:
                "radial-gradient(circle at 50% 35%, #E8A14A 0%, #C97939 60%, #8a4f23 100%)",
            }}
          />
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[2px] w-[2px] rounded-full bg-black" />
        </div>
        <div className="flex flex-col leading-tight overflow-hidden">
          <span className="font-display italic text-cream text-sm truncate">
            Slow Rooms
          </span>
          <span className="font-sans text-xs text-cream-muted truncate">
            Mount Kimbie
          </span>
        </div>
      </div>

      {/* Center: controls + progress */}
      <div className="flex-1 flex flex-col items-center gap-3">
        <div className="flex items-center gap-6 text-cream-muted">
          <button
            className="hover:text-cream transition-colors"
            aria-label="Previous"
          >
            <SkipBack className="h-4 w-4" strokeWidth={1.5} />
          </button>
          <button
            className="h-9 w-9 rounded-full border border-cream/20 flex items-center justify-center text-cream hover:border-copper hover:text-copper transition-colors"
            aria-label="Play"
          >
            <Play className="h-4 w-4 ml-0.5" strokeWidth={1.5} fill="currentColor" />
          </button>
          <button
            className="hover:text-cream transition-colors"
            aria-label="Next"
          >
            <SkipForward className="h-4 w-4" strokeWidth={1.5} />
          </button>
        </div>
        <div className="w-full max-w-[480px] flex items-center gap-3">
          <span className="font-sans text-[10px] text-cream-muted tabular-nums">
            1:24
          </span>
          <div className="flex-1 h-px bg-cream/10 relative">
            <div className="absolute left-0 top-0 h-px bg-copper" style={{ width: "30%" }} />
            <div
              className="absolute top-1/2 -translate-y-1/2 h-2 w-2 rounded-full bg-copper"
              style={{ left: "calc(30% - 4px)" }}
            />
          </div>
          <span className="font-sans text-[10px] text-cream-muted tabular-nums">
            4:18
          </span>
        </div>
      </div>

      {/* Right: volume */}
      <div className="w-[200px] flex items-center justify-end gap-3 text-cream-muted">
        <Volume2 className="h-4 w-4" strokeWidth={1.5} />
        <div className="w-20 h-px bg-cream/10 relative">
          <div className="absolute left-0 top-0 h-px bg-cream-muted" style={{ width: "60%" }} />
        </div>
      </div>
    </div>
  );
}
