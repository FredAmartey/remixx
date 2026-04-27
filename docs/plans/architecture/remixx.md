# Remixx — Architecture & Design

Conversational AI music companion. Extends the Module 3 content-based recommender (weighted scoring across genre, mood, energy, valence, danceability, acousticness) into a full applied AI system with RAG, an observable agent loop, persona-based specialization, and an evaluation harness.

## Product

Three modes share one chat surface.

- **Chat** — natural-language requests ("something for staying up too late but hopeful") → ranked picks with DJ commentary
- **Playlist** — structured requests ("a 45-minute focus playlist with a wind-down") → 10-song playlist with narrative arc, agent critiques and reorders
- **Taste mirror** — paste 5–10 favorite songs → LLM extracts taste profile → recommends from catalog with explicit "why this matches you" reasoning

The Module 3 weighted scorer is preserved as a deterministic re-rank pass on top of the new RAG/agent pipeline.

## Architecture

```
Next.js + Tailwind frontend (chat UI, playlist canvas, taste-mirror, agent trace)
                  │ SSE streaming
FastAPI
  ├── intent classifier        (Haiku 4.5 — chat | playlist | taste)
  ├── agent loop               (Sonnet 4.6 — plan → retrieve → critique → fix)
  ├── RAG retriever            (sentence-transformers + FAISS)
  ├── reranker                 (Module 3 weighted scorer, ported)
  └── persona system           (4 voices, few-shot specialized)
                  │
SQLite (sessions, saved playlists)
catalog.csv + vibes.json + index.faiss
```

**Data flow for a chat query:**
1. User input → SSE endpoint
2. Intent classifier (Haiku) tags mode, extracts query embedding seed
3. RAG retrieves top-30 candidates by semantic similarity over (title + artist + genre + mood + Claude-generated vibe description)
4. Agent (Sonnet) plans → retrieves → self-critiques ranking → reorders. Each step streamed to UI as collapsible trace
5. Module 3 scorer re-ranks final top-K with explainable point breakdowns
6. DJ persona generates commentary in selected voice
7. Stream tokens + structured agent steps back to UI

## Stack

| Layer | Choice | Reason |
|---|---|---|
| Backend | FastAPI (Python) | Course requires Python; FastAPI streams cleanly to Next.js |
| Frontend | Next.js 15 + Tailwind + shadcn | World-class UI ceiling, fast iteration |
| LLM | Claude Sonnet 4.6 (reasoning) + Haiku 4.5 (cheap ops) | Best instruction-following for agent; user has subscription |
| LLM transport | Claude Agent SDK (default) + `anthropic` SDK fallback (`ANTHROPIC_API_KEY` env var) | Free for Fred while building; grader path works without subscription |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local) | No API cost, instant, reproducible |
| Vector store | FAISS (local index file) | Fast, no infra |
| Persistence | SQLite (file-based) | No setup, proper schema, supports sessions + saved playlists |
| Catalog | 500 songs from Kaggle Spotify dataset + Claude-generated vibe descriptions (cached) | Real songs, RAG-meaningful, reproducible |

## Stretch features (all 4)

| Stretch | Implementation |
|---|---|
| RAG enhancement | Multi-source retrieval: 3 indices (metadata, vibe descriptions, mood tags) with weighted fusion. Eval harness measures quality lift over single-source baseline. |
| Agentic workflow | Observable plan→retrieve→critique→reorder loop. Each step streamed to UI as a collapsible trace panel with timing markers. |
| Specialization | 4 DJ personas (warm late-night, snarky critic, music-theory nerd, hype). Each has curated few-shot examples. Output measurably differs by persona on identical inputs. |
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
│   │   ├── rag.py            (FAISS + sentence-transformers, multi-source fusion)
│   │   ├── reranker.py       (Module 3 scorer ported)
│   │   ├── personas.py       (4 DJ voices with few-shot examples)
│   │   ├── intent.py         (Haiku-based intent classifier)
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
- **Output guardrails** (agent): self-critique loop catches obvious mismatches before returning to user
- **Confidence scoring**: each recommendation includes a confidence value derived from RAG similarity + reranker score agreement
- **Logging**: structured JSON logs of every LLM call, every retrieval, every critique pass — surfaced in agent trace UI
- **Eval harness**: 25-query golden set with pass/fail on top-3 agreement, latency, and confidence distribution

## Open decisions (deferred to implementation phase)

- Persona switching: dropdown in chat header vs. settings page (deferring; default to dropdown for visibility)
- Catalog source: specific Kaggle dataset (decide at implementation step 2; "Spotify Tracks Dataset" with 114K rows, sample 500)
- DB migrations: keep single-file SQLite, no migrations framework needed for this scope
