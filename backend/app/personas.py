"""DJ voices for fast, specialized commentary.

Set REMIXX_USE_LLM_COMMENTARY=1 if you explicitly want slower Claude-generated
commentary. The default is local template commentary so demos return quickly.
"""
from __future__ import annotations

import os

PERSONAS = {
    "warm": {
        "name": "Warm Late-Night",
        "tagline": "Late-night radio host who lingers",
        "system": (
            "You are a late-night radio DJ — warm, intimate, lingering. "
            "Talk like you're whispering to one listener at 2am. Short paragraphs, sensory language. "
            "Never use bullet points. Never hedge."
        ),
    },
    "snark": {
        "name": "Snarky Critic",
        "tagline": "Pitchfork-grade snark, brief and cutting",
        "system": (
            "You are a Pitchfork-grade music critic — sharp, opinionated, brief. "
            "One paragraph max. Cut the fluff. Land an actual judgment."
        ),
    },
    "nerd": {
        "name": "Theory Nerd",
        "tagline": "Music theory tangents and chord nerdery",
        "system": (
            "You are a music theory nerd — explain picks via chord progressions, time signatures, "
            "production techniques. Be specific (Dorian mode, sidechain compression, polyrhythm, "
            "parallel fifths). Brief but substantive."
        ),
    },
    "hype": {
        "name": "Hype",
        "tagline": "High-energy hype, no hedging",
        "system": (
            "You are a hype DJ — high energy, no hedging, exclamation marks earned. "
            "Every line lands a punch. Be brief."
        ),
    },
}


def commentary(persona: str, user_query: str, picks: list[dict]) -> str:
    """Generate persona-specialized commentary for a list of picks."""
    if persona not in PERSONAS:
        persona = "warm"
    if os.getenv("REMIXX_USE_LLM_COMMENTARY") == "1":
        return _llm_commentary(persona, user_query, picks)
    return _fast_commentary(persona, user_query, picks)


def taste_commentary(
    persona: str,
    seed_songs: list[str],
    profile: dict,
    picks: list[dict],
) -> str:
    """Taste-specific commentary that references the supplied seed pattern."""
    if persona not in PERSONAS:
        persona = "warm"
    if os.getenv("REMIXX_USE_LLM_COMMENTARY") == "1":
        return _llm_commentary(
            persona,
            f"music similar to: {', '.join(seed_songs)}",
            picks,
        )

    top = picks[0] if picks else {}
    second = picks[1] if len(picks) > 1 else top
    seed_text = _seed_summary(seed_songs)
    texture = profile.get("summary", "The seeds share a recognizable center.")
    title = top.get("title", "the first pick")
    artist = top.get("artist", "this catalog")
    second_title = second.get("title", "the next pick")
    genre = profile.get("genre", "melodic pop")
    mood = profile.get("mood", "chill")
    energy = profile.get("energy", 0.5)

    if persona == "snark":
        return (
            f"Your seeds read as {seed_text}: big melodic lift, clean hooks, and a little sunrise-sized drama. "
            f"So no, the match is not generic recommendation soup. Start with {title} by {artist}; it sits closest to the {genre}/{mood} center at about {energy} energy. "
            f"{second_title} keeps the same widescreen shape without just copying the seed artist."
        )
    if persona == "nerd":
        return (
            f"The seed cluster is {seed_text}: anthemic harmonic motion, bright upper-register melody, and steady mid-high energy. "
            f"{title} by {artist} leads because it tracks that {genre}/{mood} profile, while {second_title} keeps the lift but changes the arrangement color. "
            f"{texture}"
        )
    if persona == "hype":
        return (
            f"This taste profile wants lift. {seed_text} points to huge choruses and sky-open momentum, so run {title} by {artist} first. "
            f"Then hit {second_title}; it keeps the arc bright without turning the set into a tribute act."
        )
    return (
        f"I hear {seed_text}: open-hearted melody, widescreen build, and enough glow to make the room feel bigger. "
        f"{title} by {artist} is the closest doorway into that feeling, with {second_title} following as the softer turn. "
        f"{texture}"
    )


def _seed_summary(seed_songs: list[str]) -> str:
    artists = []
    titles = []
    for seed in seed_songs:
        if " - " in seed:
            title, artist = seed.rsplit(" - ", 1)
        elif " by " in seed.lower():
            title, artist = seed.rsplit(" by ", 1)
        else:
            title, artist = seed, ""
        title = title.strip()
        artist = artist.strip()
        if title:
            titles.append(title)
        if artist and artist.lower() not in {a.lower() for a in artists}:
            artists.append(artist)
    if artists:
        return f"{', '.join(titles[:3])} by {', '.join(artists[:2])}"
    return ", ".join(titles[:3])


def _fast_commentary(persona: str, user_query: str, picks: list[dict]) -> str:
    top = picks[0] if picks else {}
    second = picks[1] if len(picks) > 1 else top
    title = top.get("title", "the opener")
    artist = top.get("artist", "the catalog")
    genre = top.get("genre", "left-field")
    mood = top.get("mood", "focused")
    energy = float(top.get("energy", 0.5) or 0.5)
    energy_word = "low-lit" if energy < 0.45 else "moving" if energy < 0.7 else "charged"
    second_title = second.get("title", "the next pick")

    if persona == "snark":
        return (
            f"For “{user_query},” start with {title} by {artist}. "
            f"It actually understands the assignment: {genre}, {mood}, {energy_word}, not generic playlist filler. "
            f"{second_title} keeps the thread moving, and the rest of the set stays close enough to the brief without turning into algorithm soup."
        )
    if persona == "nerd":
        return (
            f"{title} by {artist} leads because its {mood} profile and {energy:.2f} energy sit closest to the query. "
            f"The reranker is favoring {genre} texture, moderate tempo, and tracks with a cleaner acoustic/electronic balance. "
            f"{second_title} is the hinge: it keeps the harmonic color stable while widening the set."
        )
    if persona == "hype":
        return (
            f"Run {title} first. {artist} gives this mix its spine: {genre}, {mood}, ready immediately. "
            f"Then hit {second_title} and let the set climb. No dead air, no overthinking, just a tight run of tracks that match the ask."
        )
    closing = (
        "Keep the volume low and let the edges blur a little."
        if energy < 0.7
        else "Turn it up and let the first hit do the arguing."
    )
    return (
        f"Start with {title} by {artist}. It has the right weather for “{user_query}”: {mood}, {energy_word}, and close enough to breathe. "
        f"{second_title} settles in after it, so the mix feels chosen instead of shuffled. "
        f"{closing}"
    )


def _llm_commentary(persona: str, user_query: str, picks: list[dict]) -> str:
    from app.llm import LLMClient

    p = PERSONAS[persona]
    pick_lines = "\n".join(
        f"  {i+1}. {song.get('title', '?')} — {song.get('artist', '?')}"
        for i, song in enumerate(picks)
    )
    prompt = f"""User: {user_query}
Picks:
{pick_lines}

You:"""
    client = LLMClient()
    return client.complete(
        "sonnet",
        prompt,
        system=p["system"],
        max_tokens=300,
    ).strip()
