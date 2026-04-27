import type { TasteProfile } from "@/lib/api";

export function ProfileOutput({ profile }: { profile: TasteProfile }) {
  // Build 5 ember tag-words from the inferred profile.
  const tags: string[] = [
    profile.genre,
    profile.mood,
    `${profile.energy.toFixed(1)} energy`,
    profile.likes_acoustic ? "acoustic" : "produced",
    profile.energy >= 0.6 ? "kinetic" : profile.energy <= 0.35 ? "still" : "midweight",
  ].filter(Boolean);

  return (
    <div className="flex flex-col gap-5 animate-in fade-in duration-700">
      <div className="font-sans text-[10px] uppercase tracking-[0.2em] text-copper">
        Profile
      </div>
      <p className="font-display italic text-cream text-xl leading-relaxed">
        {profile.summary}
      </p>
      <div className="flex flex-wrap gap-x-4 gap-y-2 mt-2">
        {tags.map((t, i) => (
          <span
            key={`${t}-${i}`}
            className="font-display italic text-sm text-copper"
          >
            · {t}
          </span>
        ))}
      </div>
    </div>
  );
}
