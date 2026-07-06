# FlowLocal — local-first dictation (Wispr Flow alternative)

FlowLocal is a fully local dictation system: speech in, clean text typed into
whatever app has focus. No cloud path, no telemetry. It implements the
routed, cascaded architecture from the project design doc:

```
Mic → Noise/AGC → VAD (Silero) → Segmenter → ASR Router
        ├─ Lane A: Whisper via faster-whisper (broad multilingual default)
        ├─ Lane B: distil-whisper / whisper.cpp (fast / CPU path)
        └─ Lane C: long-tail fallback (pluggable)
     → Entity guardrails + hotword resolver
     → Cleanup (rules first; optional small local LLM)
     → Insertion (clipboard+paste fallback; accessibility later)
     → Local personalization store (SQLite lexicon, edit-diff mining)
```

## Design principles

- **Local-only by default.** Audio and transcripts never leave the machine.
- **Reversible cleanup.** Raw transcript, cleaned transcript, and inserted
  text are stored separately; cleanup never rewrites meaning.
- **Protected spans.** Numbers, URLs, emails, IDs, and lexicon terms are
  never altered by the cleanup stage.
- **Routed, not monolithic.** ASR back ends sit behind one provider
  interface; pick per language/hardware profile.

## Install

```bash
pip install -e ".[full]"     # faster-whisper + audio capture + VAD
pip install -e .             # core only (cleanup/lexicon, no models)
```

## Usage

```bash
flowlocal dictate                 # VAD-segmented continuous dictation
flowlocal dictate --push-to-talk  # hold Enter to talk
flowlocal transcribe file.wav     # offline file transcription
flowlocal lexicon add "Kubernetes" --alias "kubernetes,k8s"
flowlocal lexicon list
```

Cleanup levels: `--cleanup verbatim|light|polished` (default `light`).

## Layout

| Module | Role |
|---|---|
| `flowlocal/audio.py` | mic capture + Silero VAD segmentation |
| `flowlocal/asr.py` | ASR provider interface + faster-whisper backend + router |
| `flowlocal/cleanup.py` | constrained rules cleanup with protected spans |
| `flowlocal/lexicon.py` | SQLite hotword store + prompt biasing |
| `flowlocal/insert.py` | clipboard / typing insertion backends |
| `flowlocal/app.py` | pipeline orchestration |

## Tests

```bash
python -m pytest tests/    # cleanup + lexicon tests run with zero ML deps
```
