"use client";

/**
 * Hand-drawn-feeling SVG arc: rises from track 1, peaks around the middle,
 * descends to the end. Track dots sit along the curve. Three editorial labels
 * mark "opening" / "peak" / "wind-down".
 *
 * Geometry uses sine to lay out the dots, but the curve itself is one cubic
 * Bezier so it reads as illustrative rather than plotted.
 */
export function NarrativeArc({ trackCount = 10 }: { trackCount?: number }) {
  const W = 200;
  const H = 400;
  const padTop = 60;
  const padBottom = 60;
  const padLeft = 60;
  const padRight = 30;

  const xMin = padLeft;
  const xMax = W - padRight;
  const yBase = H - padBottom;
  const yPeak = padTop;

  const n = Math.max(2, trackCount);

  // Dot positions — sine arc from baseline up to peak and back down.
  const dots = Array.from({ length: n }, (_, i) => {
    const t = i / (n - 1); // 0..1
    const x = xMin + (xMax - xMin) * t;
    // sin(pi * t): 0 at ends, 1 at middle
    const y = yBase - (yBase - yPeak) * Math.sin(Math.PI * t);
    return { x, y };
  });

  // Curve: one cubic that swoops up to peak and back down. Tangents are
  // weighted to read as a hand-drawn arc rather than a perfect bell.
  const xMid = (xMin + xMax) / 2;
  const c1x = xMin + (xMax - xMin) * 0.32;
  const c1y = yPeak - 30; // pull up past the peak for a softer rise
  const c2x = xMin + (xMax - xMin) * 0.68;
  const c2y = yPeak - 30;
  const path = `M ${xMin} ${yBase} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${xMax} ${yBase}`;

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      height="100%"
      className="select-none"
      aria-hidden="true"
    >
      {/* Soft baseline guide */}
      <line
        x1={xMin}
        y1={yBase}
        x2={xMax}
        y2={yBase}
        stroke="rgb(var(--color-cream) / 0.08)"
        strokeWidth={0.5}
        strokeDasharray="2 4"
      />

      {/* The curve */}
      <path
        d={path}
        fill="none"
        stroke="rgb(var(--color-copper))"
        strokeWidth={1.5}
        strokeLinecap="round"
        opacity={0.85}
      />

      {/* Faint shadow under the curve for warmth */}
      <path
        d={`${path} L ${xMax} ${yBase} L ${xMin} ${yBase} Z`}
        fill="rgb(var(--color-copper) / 0.06)"
      />

      {/* Track dots */}
      {dots.map((d, i) => (
        <g key={i}>
          <circle
            cx={d.x}
            cy={d.y}
            r={3}
            fill="rgb(var(--color-walnut-deep))"
            stroke="rgb(var(--color-copper))"
            strokeWidth={1.25}
          />
        </g>
      ))}

      {/* Editorial labels */}
      <text
        x={xMin - 4}
        y={yBase - 6}
        textAnchor="end"
        className="font-display"
        fontStyle="italic"
        fontSize="11"
        fill="rgb(var(--color-copper))"
      >
        opening
      </text>
      <text
        x={xMid}
        y={yPeak - 12}
        textAnchor="middle"
        className="font-display"
        fontStyle="italic"
        fontSize="12"
        fill="rgb(var(--color-copper))"
      >
        peak
      </text>
      <text
        x={xMax + 4}
        y={yBase - 6}
        textAnchor="start"
        className="font-display"
        fontStyle="italic"
        fontSize="11"
        fill="rgb(var(--color-copper))"
      >
        wind-down
      </text>

      {/* Tiny tick numbers on the first/last/peak (subtle, monospace) */}
      <text
        x={dots[0].x}
        y={yBase + 16}
        textAnchor="middle"
        fontFamily="ui-monospace, monospace"
        fontSize="8"
        fill="rgb(var(--color-cream-muted) / 0.6)"
      >
        01
      </text>
      <text
        x={dots[dots.length - 1].x}
        y={yBase + 16}
        textAnchor="middle"
        fontFamily="ui-monospace, monospace"
        fontSize="8"
        fill="rgb(var(--color-cream-muted) / 0.6)"
      >
        {String(n).padStart(2, "0")}
      </text>
    </svg>
  );
}
