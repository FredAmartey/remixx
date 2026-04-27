# Model Card — Remixx 1.0

## Goal / Task
Recommend music in conversational form. Given a natural-language request, mood description, or list of favorite songs, return ranked picks plus a DJ-voice commentary explaining the choices.

## Data Used
- 500 tracks sampled from the [Kaggle Spotify Tracks Dataset](https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset) (114K rows; sampled with genre diversity, max 30 per genre)
- Per-track features used: title, artist, genre, mood (derived from valence + energy), energy, valence, danceability, acousticness, tempo
- Vibe descriptions (Claude-generated 1-2 sentence semantic blurbs, one per track) embedded alongside metadata via late-fusion averaging in the FAISS index

## Algorithm Summary (in plain language)

1. **You ask.** Could be a vibe ("songs for late at night"), a playlist request ("45 minute focus playlist"), or a list of songs you love.
2. **Remixx classifies what you meant** using Claude Haiku — chat / playlist / taste.
3. **It searches semantically.** A sentence-transformer model embeds your message and finds the 30 most-related tracks in the catalog by cosine similarity. The FAISS index uses late fusion: each track is encoded twice (metadata + a Claude-generated vibe description) and the two normalized embeddings are averaged. This makes "feel like…" queries match on the actual feel, not just the title and genre.
4. **It scores them with the original recommender.** The Module 3 weighted-feature scorer re-ranks the candidates by genre/mood/energy/valence/danceability/acoustic match. This gives you a transparent point breakdown for every pick.
5. **It critiques itself.** Claude Sonnet reviews the top picks and flags any that obviously don't fit your intent. If it spots problems, it can reorder.
6. **A DJ talks to you.** One of four DJ personas (warm, snark, nerd, hype) generates commentary explaining the picks in its own voice.
7. **You see the work.** Every step streams to the UI in real time. The agent's reasoning is visible, not a black box.

## Observed Behavior / Biases

- **Genre dominance**: the +2.0 genre weight in the reranker means a perfect mood+energy match from the wrong genre can lose to a mediocre match from the right genre. This is intentional (genre is a strong identity signal) but creates filter bubbles.
- **Catalog skew**: sampled with 30-per-genre cap, but some popular genres still have stronger representation in the dataset's underlying distribution. Latin, K-pop, and Asian non-English markets are over- or under-represented depending on how the source dataset was scraped.
- **Energy-valence coupling**: the reranker uses the user's target energy as the valence reference, assuming high-energy listeners want positive music. This is wrong for high-energy angry/sad music (metal, drill).
- **Single-taste assumption**: each request is independent. The system has no model of you over time.
- **No lyric understanding**: a sad song with high-energy production is scored on energy, not emotional content.
- **English-Western bias**: prompts and persona few-shots are English. Non-English requests still work but the persona output will be in English.
- **Latency**: per-turn ~12-20s (down from ~30-50s in v0.1) thanks to Haiku for the critique step and parallel intent+retrieval. Still bound by the Agent SDK subprocess overhead — direct API key shaves another 3-5s.

## Evaluation Process

`backend/eval/run_eval.py` runs the full agent on 25 predefined queries with a 5-pick golden-set check (genre OR mood overlap with expected sets). Mix of 8 chat queries, 8 playlist queries, 8 taste-seed queries, and 1 edge case ("i love mexico").

Sample run results: ~84% pass rate, avg latency 32s, avg confidence 0.76.

## Intended Use

- Classroom demonstration of a conversational AI system that combines RAG, agent reasoning, and persona-based specialization
- Reference architecture for "natural-language music search with explainable picks"
- A jumping-off point for a real product (would need 100x catalog and a feedback loop)

## Non-Intended Use

- Not for production music streaming — no licensing, no playback infrastructure, no royalty handling
- Not for mental-health-adjacent recommendations — the system can't tell if a sad-themed pick is appropriate or harmful for a user in distress
- Not for medical/therapeutic music selection — there's no clinical validation
- Not as a moderation system — the guardrails block obvious prompt injection but aren't a substitute for content-safety review
- Not for generating playlists in a curated brand voice — personas are caricatures, not professionally-edited tones

## Ideas for Improvement

1. **Per-source retrieval weighting** — currently the metadata + vibe fusion is a simple average. Letting the agent learn weights per query mode (e.g. emphasize vibe for "feels like" queries, emphasize metadata for genre-specific asks) would lift quality further.
2. **Add a feedback loop** — thumbs up/down per pick, weights adjust over time. Currently weights are static.
3. **Real audio features from Spotify API** — replace the dataset's pre-computed values with live API calls for current tracks
4. **Multi-track-context personalization** — accept a "playlist seed" of songs you've recently played and bias retrieval toward continuity
5. **Long-term user model that learns from saved-playlist signals** — data is now persisted in SQLite, just no learning loop yet
6. **Streaming `/playlist` and `/taste` like `/chat` does** — currently they wait for the full agent turn before returning

## Reflection

See [reflection.md](reflection.md).
