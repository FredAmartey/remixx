"use client";

export function SongInputGrid({
  values,
  onChange,
  disabled,
}: {
  values: string[];
  onChange: (values: string[]) => void;
  disabled?: boolean;
}) {
  function update(i: number, v: string) {
    const next = values.slice();
    next[i] = v;
    onChange(next);
  }

  return (
    <div className="flex flex-col gap-5 max-w-md">
      {values.map((v, i) => (
        <div key={i} className="flex items-center gap-4">
          <span className="font-display italic text-xs text-cream-muted/70 w-16 shrink-0 tabular-nums">
            Track {i + 1}
          </span>
          <input
            value={v}
            onChange={(e) => update(i, e.target.value)}
            disabled={disabled}
            placeholder={i < 3 ? "title — artist" : "optional"}
            className="flex-1 bg-transparent border-b border-cream/20 focus:border-copper focus:outline-none px-1 py-2 text-cream font-display italic text-base placeholder:text-cream-muted/50 placeholder:italic transition-colors"
          />
        </div>
      ))}
    </div>
  );
}
