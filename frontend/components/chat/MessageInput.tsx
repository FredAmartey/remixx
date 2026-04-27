"use client";
import { ArrowUp } from "lucide-react";
import { useRef } from "react";

export function MessageInput({
  onSubmit,
  disabled,
}: {
  onSubmit: (message: string) => void;
  disabled?: boolean;
}) {
  const ref = useRef<HTMLInputElement | null>(null);
  return (
    <form
      className="border-t border-cream/10 px-12 py-6 flex items-center gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        const v = ref.current?.value.trim();
        if (!v) return;
        onSubmit(v);
        if (ref.current) ref.current.value = "";
      }}
    >
      <input
        ref={ref}
        disabled={disabled}
        placeholder="Type a vibe…"
        className="flex-1 bg-transparent border-b border-cream/20 focus:border-copper focus:outline-none px-1 py-3 text-cream font-display italic placeholder:text-cream-muted/60 placeholder:italic transition-colors"
      />
      <button
        type="submit"
        disabled={disabled}
        className="text-copper hover:text-copper-glow disabled:opacity-30 transition-colors"
        aria-label="Send"
      >
        <ArrowUp className="w-5 h-5" />
      </button>
    </form>
  );
}
