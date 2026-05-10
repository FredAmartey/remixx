export type FeaturedTrack = {
  slug: string;
  title: string;
  artist: string;
  cover: string;
  query: string;
  genre: string;
  mood: string;
  duration: string;
};

export const featuredTracks: FeaturedTrack[] = [
  {
    slug: "after-rain",
    title: "After the Rain",
    artist: "Marlowe",
    cover: "/remixx-assets/cover-after-rain.png",
    query: "rainy late-night songs with hopeful, slow energy",
    genre: "downtempo",
    mood: "hopeful",
    duration: "4:18",
  },
  {
    slug: "silver-lining",
    title: "Silver Lining",
    artist: "Juno Oak",
    cover: "/remixx-assets/cover-silver-lining.png",
    query: "quiet moonlit songs with soft texture and room to breathe",
    genre: "ambient pop",
    mood: "soft",
    duration: "3:52",
  },
  {
    slug: "half-light",
    title: "Half Light",
    artist: "Sofia Astrom",
    cover: "/remixx-assets/cover-half-light.png",
    query: "shadowy intimate vocals with low light and warm production",
    genre: "art pop",
    mood: "moody",
    duration: "4:05",
  },
  {
    slug: "wide-open-sky",
    title: "Wide Open Sky",
    artist: "Amos Lee",
    cover: "/remixx-assets/cover-wide-open-sky.png",
    query: "wide open sunset songs with patient build and copper warmth",
    genre: "folk",
    mood: "open",
    duration: "3:47",
  },
  {
    slug: "hotel-north",
    title: "Hotel North, Vol. II",
    artist: "The Native Sons",
    cover: "/remixx-assets/cover-hotel-north.png",
    query: "noir hotel songs for late night, lonely windows, slow pulse",
    genre: "indie soul",
    mood: "nocturnal",
    duration: "4:31",
  },
];

export const playlistPresets = [
  {
    name: "Late Drives",
    prompt: "late-night drives, wet pavement, warm and hopeful",
    duration: 45,
  },
  {
    name: "Sunday Slow",
    prompt: "slow Sunday morning songs, gentle and unhurried",
    duration: 38,
  },
  {
    name: "Studio Sessions",
    prompt: "focused studio work, textured electronic songs, low distraction",
    duration: 60,
  },
  {
    name: "Heartbreak Hours",
    prompt: "heartbreak songs that feel honest but not hopeless",
    duration: 42,
  },
  {
    name: "Deep Focus",
    prompt: "deep focus music with no sharp edges and steady momentum",
    duration: 50,
  },
  {
    name: "Saturday Hangover",
    prompt: "Saturday recovery music, warm low energy, soft rhythm",
    duration: 36,
  },
];

export function playlistHref(prompt: string, duration: number) {
  const params = new URLSearchParams({
    prompt,
    duration: String(duration),
  });
  return `/playlist?${params.toString()}`;
}
