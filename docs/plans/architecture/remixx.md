# Remixx — Architecture & Design

Conversational AI music companion. Extends the Module 3 content-based recommender (weighted scoring across genre, mood, energy, valence, danceability, acousticness) into a full applied AI system with RAG, an observable agent loop, persona-based specialization, and an evaluation harness.

> **v1.0 status note:** SQLite persistence, vibe descriptions, and multi-source RAG fusion described below are **deferred** — designed but not shipped in v1.0. The current code is stateless per request and uses single-source RAG over catalog metadata. See [README.md](../../../README.md) for what actually ships.

## Product

Three modes share one chat surface.

- **Chat** — natural-language requests ("something for staying up too late but hopeful") → ranked picks with DJ commentary
- **Playlist** — structured requests ("a 45-minute focus playlist with a wind-down") → 10-song playlist with narrative arc, agent critiques and reorders
- **Taste mirror** — paste 3–10 favorite songs → deterministic profile inference from retrieved neighbors → recommends from catalog with explicit "why this matches you" reasoning

The Module 3 weighted scorer is preserved as a deterministic re-rank pass on top of the new RAG/agent pipeline.

## Architecture

```
Next.js + Tailwind frontend (chat UI, playlist canvas, taste-mirror, agent trace)
                  │ SSE streaming
FastAPI
  ├── intent classifier        (deterministic rules — chat | playlist | taste)
  ├── agent loop               (retrieve → rerank → critique → finalize)
  ├── RAG retriever            (TF-IDF by default; semantic FAISS opt-in)
  ├── reranker                 (Module 3 weighted scorer, ported)
  └── persona system           (4 fast specialized voices)
                  │
SQLite (sessions, saved playlists)
catalog.csv + vibes.json
```

**Data flow for a chat query:**
1. User input → SSE endpoint
2. Intent classifier tags mode and extracts duration or seed-song hints
3. RAG retrieves top candidates from title, artist, genre, mood, and cached vibe text
4. Module 3 scorer re-ranks candidates with explainable point breakdowns
5. Self-critique guardrail flags obvious energy and genre mismatches, then reorders
6. DJ persona generates fast specialized commentary in the selected voice
7. Stream tokens + structured agent steps back to UI

## Stack

| Layer | Choice | Reason |
|---|---|---|
| Backend | FastAPI (Python) | Course requires Python; FastAPI streams cleanly to Next.js |
| Frontend | Next.js 15 + Tailwind + shadcn | World-class UI ceiling, fast iteration |
| LLM | Optional for commentary only | Keeps the default request path fast; richer prose can be enabled when latency is acceptable |
| LLM transport | Claude Agent SDK + `anthropic` SDK fallback (`ANTHROPIC_API_KEY` env var) | Used by optional generation scripts and opt-in commentary |
| Retrieval | TF-IDF over metadata + vibe text by default | No API cost, no model startup, reproducible, sub-second |
| Semantic retrieval | sentence-transformers + FAISS behind `REMIXX_USE_SEMANTIC_RAG=1` | Quality option for demos where startup time is acceptable |
| Persistence | SQLite (file-based) | No setup, proper schema, supports sessions + saved playlists |
| Catalog | 500 songs from Kaggle Spotify dataset + Claude-generated vibe descriptions (cached) | Real songs, RAG-meaningful, reproducible |

## Stretch features (all 4)

| Stretch | Implementation |
|---|---|
| RAG enhancement | Retrieval uses catalog metadata plus cached vibe descriptions, with a heavier semantic FAISS path available as an opt-in quality mode. |
| Agentic workflow | Observable retrieve→rerank→critique→reorder loop. Each step streams to UI with timing markers. |
| Specialization | 4 DJ personas (warm late-night, snarky critic, music-theory nerd, hype). Local voice templates produce measurably different output on identical inputs. |
| Test harness | `eval/run_eval.py` runs 25 predefined queries, scores agreement with golden picks, measures latency, prints summary table. |

## Visual system (locked)

Reference: `design-refs/v1_copper_walnut.png`.

- **Background**: walnut #2A1F18 with subtle film grain
- **Text**: warm cream #F5EFE3
- **Accent**: copper #C97939 (single accent, used sparingly)
- **Typography**: editorial serif display (GT Sectra / Migra / Playfair Display fallback) for headlines, refined grotesk (Söhne / Inter) for UI
- **Visual signature**: photographic vinyl as recurring motif (album art, hero, now-playing thumb)
- **Layout**: classic three-zone music app (sidebar / main / now-playing bar)
- **Motion**: cinematic fade-through, smooth accordion expansion (for agent trace)
- **Banned**: glassmorphism, gradient mesh blobs, Spotify green, generic AI purple/blue, fake utility pills, photography of people, neon glow

## File structure

```
final-project/
├── README.md                 (project overview, setup, sample I/O)
├── model_card.md             (limitations, biases, evaluation summary)
├── reflection.md             (AI collaboration, helpful/flawed suggestions)
├── design-refs/              (image-to-code reference renders)
├── docs/
│   ├── plans/                (architecture, implementations, INDEX.md)
│   └── research/             (any background material)
├── assets/                   (architecture diagram + screenshots)
├── backend/
│   ├── app/
│   │   ├── main.py           (FastAPI entrypoint, /chat SSE endpoint)
│   │   ├── agent.py          (plan→retrieve→critique loop, observable steps)
│   │   ├── llm.py            (Agent SDK + anthropic SDK fallback shim)
│   │   ├── rag.py            (TF-IDF RAG default; FAISS semantic opt-in)
│   │   ├── reranker.py       (Module 3 scorer ported)
│   │   ├── personas.py       (4 DJ voices; optional LLM commentary)
│   │   ├── intent.py         (deterministic intent classifier)
│   │   └── db.py             (SQLite schema + queries)
│   ├── data/
│   │   ├── catalog.csv       (500 songs)
│   │   ├── vibes.json        (Claude-generated descriptions, cached)
│   │   └── index.faiss       (built on first run)
│   ├── scripts/
│   │   ├── build_index.py
│   │   └── generate_vibes.py
│   ├── eval/
│   │   ├── golden_set.json   (25 predefined queries + expected picks)
│   │   └── run_eval.py       (test harness)
│   └── tests/                (pytest)
└── frontend/
    ├── app/                  (Next.js App Router, page routes)
    ├── components/
    │   ├── chat/             (message stream, agent trace, input)
    │   ├── playlist/         (track list, narrative arc viz)
    │   ├── taste-mirror/     (paste favorites, profile output)
    │   ├── now-playing/      (bottom bar)
    │   └── ui/               (shadcn primitives)
    └── lib/                  (API client, types, utils)
```

## Reliability & guardrails

- **Input validation** (FastAPI): query length caps, prompt injection filter, rate limit per session
- **Output guardrails** (agent): deterministic self-critique catches obvious mismatches before returning to user
- **Confidence scoring**: each recommendation includes a confidence value derived from RAG similarity + reranker score agreement
- **Logging**: structured JSON logs of every request, retrieval, and confidence result — surfaced in agent trace UI
- **Eval harness**: 25-query golden set with pass/fail on top-3 agreement, latency, and confidence distribution

## Open decisions (deferred to implementation phase)

- Persona switching: dropdown in chat header vs. settings page (deferring; default to dropdown for visibility)
- Catalog source: specific Kaggle dataset (decide at implementation step 2; "Spotify Tracks Dataset" with 114K rows, sample 500)
- DB migrations: keep single-file SQLite, no migrations framework needed for this scope
