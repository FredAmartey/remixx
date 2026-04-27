"use client";
import { useEffect, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";
import { fetchPersonas } from "@/lib/api";

type Persona = { key: string; name: string; tagline: string };

export function PersonaSelector({
  value,
  onChange,
}: {
  value: string;
  onChange: (key: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const wrapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    fetchPersonas().then(setPersonas).catch(() => setPersonas([]));
  }, []);

  // Close on outside click
  useEffect(() => {
    const onDocClick = (e: MouseEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    };
    if (open) document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  const current = personas.find((p) => p.key === value);

  return (
    <div ref={wrapRef} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 font-display italic text-cream-muted hover:text-cream text-sm transition-colors"
      >
        {current?.name ?? value}
        <ChevronDown
          className={`w-3.5 h-3.5 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && personas.length > 0 && (
        <div className="absolute right-0 top-full mt-2 w-72 bg-walnut-deep border border-cream/10 shadow-2xl z-50">
          {personas.map((p) => {
            const active = p.key === value;
            return (
              <button
                key={p.key}
                onClick={() => {
                  onChange(p.key);
                  setOpen(false);
                }}
                className="w-full text-left px-5 py-4 hover:bg-walnut transition-colors border-b border-cream/5 last:border-b-0"
              >
                <div
                  className={`font-display text-base ${
                    active
                      ? "text-cream underline underline-offset-4 decoration-copper decoration-2"
                      : "text-cream"
                  }`}
                >
                  {p.name}
                </div>
                <div className="font-display italic text-xs text-cream-muted/80 mt-1">
                  {p.tagline}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
