const albums = [
  { title: "Slow Rooms", artist: "Mount Kimbie" },
  { title: "Cirrus", artist: "Bonobo" },
  { title: "Awake", artist: "Tycho" },
  { title: "Made to Stray", artist: "Mount Kimbie" },
  { title: "Roygbiv", artist: "Boards of Canada" },
];

export function AlbumRow() {
  return (
    <div className="mt-16 flex gap-5">
      {albums.map((a) => (
        <div key={a.title} className="group cursor-pointer">
          <div
            className="relative h-[180px] w-[180px] rounded-sm border border-cream/10 bg-walnut-deep overflow-hidden transition-all duration-300 group-hover:border-copper/40"
            style={{
              backgroundImage:
                "radial-gradient(circle at 30% 25%, rgba(232,161,74,0.08) 0%, rgba(26,19,14,0) 60%)",
            }}
          >
            <div
              className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
              style={{
                background:
                  "radial-gradient(circle at 50% 50%, rgba(232,161,74,0.18) 0%, rgba(26,19,14,0) 70%)",
              }}
            />
          </div>
          <div className="mt-3">
            <div className="font-display text-base text-cream">{a.title}</div>
            <div className="font-sans text-sm text-cream-muted mt-1">
              {a.artist}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
