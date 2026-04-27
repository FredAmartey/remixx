export function Hero() {
  return (
    <section className="flex items-center gap-12">
      {/* Left: copy */}
      <div className="flex-1 max-w-[520px]">
        <h1 className="font-display text-6xl text-cream tracking-tight leading-[1.05]">
          Tonight&rsquo;s mix is ready.
        </h1>
        <p className="font-display italic text-lg text-cream-muted leading-relaxed mt-6 max-w-[440px]">
          Picked from your last 14 days. Slower, hopeful, room for breath.
        </p>
        <div className="flex items-center gap-8 mt-10">
          <a
            href="#"
            className="font-sans text-sm tracking-wide text-copper hover:text-copper-glow underline underline-offset-[6px] decoration-copper/40 hover:decoration-copper-glow transition-colors"
          >
            Play now &rarr;
          </a>
          <a
            href="#"
            className="font-sans text-sm tracking-wide text-cream-muted hover:text-cream transition-colors"
          >
            Inspect picks
          </a>
        </div>
      </div>

      {/* Right: vinyl */}
      <div className="flex-1 flex items-center justify-center">
        <div className="relative aspect-square w-[360px]">
          {/* Disc */}
          <div
            className="absolute inset-0 rounded-full animate-[spin_30s_linear_infinite]"
            style={{
              background:
                "radial-gradient(circle at 50% 50%, #1a130e 0%, #0a0705 55%, #1a130e 70%, #050302 100%)",
              boxShadow:
                "inset 0 0 0 1px rgba(245,239,227,0.04), inset 0 0 0 36px rgba(245,239,227,0.025), inset 0 0 0 60px rgba(245,239,227,0.01), inset 0 0 0 84px rgba(245,239,227,0.025), inset 0 0 0 108px rgba(245,239,227,0.01), inset 0 0 60px rgba(0,0,0,0.6), 0 30px 80px -20px rgba(0,0,0,0.6)",
            }}
          >
            {/* Center label */}
            <div
              className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[120px] w-[120px] rounded-full flex items-center justify-center"
              style={{
                background:
                  "radial-gradient(circle at 50% 35%, #E8A14A 0%, #C97939 60%, #8a4f23 100%)",
                boxShadow:
                  "inset 0 0 0 1px rgba(0,0,0,0.25), 0 2px 6px rgba(0,0,0,0.4)",
              }}
            >
              <span className="font-display italic text-cream text-base tracking-tight">
                Remixx
              </span>
            </div>
            {/* Spindle hole */}
            <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[6px] w-[6px] rounded-full bg-black" />
          </div>
        </div>
      </div>
    </section>
  );
}
