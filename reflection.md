# Reflection — Remixx Build

## How I worked with AI during this project

I used Claude Code (the CLI Fred is running this very build through) as my primary development partner. The workflow was:
1. **Brainstorming** the design through dialogue — surfacing requirements, constraints, and what would actually hit the rubric vs. what was polish
2. **Plan-driven execution** — wrote a phased implementation plan with bite-sized tasks, then dispatched fresh general-purpose subagents per task
3. **Inline review** — controller (me) verified each subagent's output via test runs, screenshots, and curl checks before continuing
4. **The image-to-code skill** for the visual direction — generated 13 design reference images via ChatGPT image generation, picked one, then implemented the UI faithfully against it

## One AI suggestion that helped

When I was scaffolding the FastAPI app, the implementer subagent caught an `asyncio.run() cannot be called from a running event loop` error on the first run of `/chat`. Root cause: the LLM client uses `asyncio.run` internally because the Claude Agent SDK's `query()` is async, but FastAPI is already running an event loop. Instead of editing the LLM client (which would have rippled into all callers), the subagent isolated the fix at the FastAPI layer — running the agent generator on a `threading.Thread` and pulling steps off a Queue via `loop.run_in_executor`. Clean, surgical, didn't break the synchronous LLM API. That's a fix I might have spent an hour debugging on my own.

## One AI suggestion that was wrong

The image-to-code skill's first batch of design references included 5 hero variations. The first one was a dark walnut-toned editorial layout with a vinyl record photograph. I picked it. Then it tried to extend that aesthetic to in-app surfaces (chat, playlist, settings) by generating cinematic full-bleed photographic backgrounds for each. Those didn't work — putting a person-with-headphones photograph behind a chat input fights readability and looks like a screensaver, not an app. I had to push back and explicitly say "the photographic full-bleed thing is hero-only; in-app surfaces inherit the palette but use functional layouts." The model defaulted to consistency-of-aesthetic over consistency-of-purpose. A senior designer would have caught that before generating; the AI didn't. Lesson: visual direction skills need the same hand-holding as code skills when it comes to context-appropriate execution.

## What surprised me

How much of the "magic" in conversational AI music apps is actually orchestration. The pipeline is mechanically simple — embed query, retrieve top-30, score, critique, write commentary — but composing those steps with observable streaming is what makes the experience feel alive. The agent trace panel showing `Parse intent · 10s` then `Self-critique · 8s` makes a 30-second total turn feel deliberate instead of slow.

I also underestimated how much persona specialization affects perceived intelligence. Same picks, different voice → completely different UX. The "snark" persona felt smart in a way the picks alone didn't.

## System limitations and future work

- Latency: 30-50s per chat turn, dominated by LLM round-trips. The agent SDK's subprocess overhead adds ~5s per call. Direct API would halve this.
- Single-taste model: every request is independent. No memory of past requests. Real personalization needs persistence + a learning signal.
- Static weights: the +2.0 genre / +1.5 mood weights are hand-tuned, not learned from user feedback.
- 500-song catalog: real recommenders work over 100M+ tracks. Many "no good match" failure modes get masked at scale.
- No audio playback: this is a recommendation surface, not a player. Integrating Spotify Web Playback would require OAuth + premium subscription handling.
- English-Western bias in personas and prompts.

## What I'd build next

- **Vibe descriptions wired into RAG** (the deferred Phase 1.3) — 1-2 sentence Claude-generated semantic blurbs per track, embedded alongside metadata for multi-source fusion. Designed but not built.
- **Feedback loop** — thumbs up/down adjusts persona-specific reranker weights
- **Real Spotify integration** — OAuth + Web Playback so picks actually play
- **Long-form playlist composer** — multi-turn conversation that builds and refines a playlist with the DJ
- **A quieter mode** — minimal UI without the agent trace panel, for users who just want results without the show
