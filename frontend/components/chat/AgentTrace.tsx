"use client";
import { ChevronRight } from "lucide-react";
import { useState } from "react";
import type { Step } from "@/lib/api";

export function AgentTrace({ steps, totalMs }: { steps: Step[]; totalMs?: number }) {
  const [open, setOpen] = useState(true);
  if (steps.length === 0 && !totalMs) return null;
  return (
    <aside
      className={`fixed top-0 right-0 h-screen border-l border-cream/10 bg-walnut-deep transition-all overflow-y-auto ${
        open ? "w-[360px]" : "w-12"
      }`}
    >
      <button
        onClick={() => setOpen(!open)}
        className="absolute top-6 left-3 text-cream-muted hover:text-cream transition-colors"
        aria-label={open ? "Collapse trace" : "Expand trace"}
      >
        <ChevronRight className={`w-4 h-4 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="px-6 pt-6 pb-24">
          <div className="text-[10px] tracking-[0.2em] uppercase text-copper mb-6">
            Agent · trace
          </div>
          <div className="flex flex-col">
            {steps.map((s, i) => (
              <div key={i} className="flex items-start gap-4 py-4 border-b border-cream/5 last:border-b-0">
                <span className="w-6 h-6 rounded-full border border-copper/40 text-copper text-xs flex items-center justify-center font-mono mt-0.5 shrink-0">
                  {typeof s.step === "number" ? s.step : "·"}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="font-sans text-sm text-cream">{s.title}</div>
                  {s.detail && (
                    <div className="font-sans text-xs text-cream-muted mt-1">{s.detail}</div>
                  )}
                </div>
                {s.ms !== undefined && (
                  <span className="font-mono text-[11px] text-cream-muted/70 tabular-nums shrink-0">
                    {s.ms}ms
                  </span>
                )}
              </div>
            ))}
            {totalMs !== undefined && (
              <div className="mt-6 pt-4 border-t border-cream/10 font-mono text-[11px] text-cream-muted">
                total · {(totalMs / 1000).toFixed(1)}s
              </div>
            )}
          </div>
        </div>
      )}
    </aside>
  );
}
