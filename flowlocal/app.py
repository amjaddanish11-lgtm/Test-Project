"""Pipeline orchestration: audio → ASR → lexicon → cleanup → insertion.

Raw and cleaned transcripts are both kept (reversible cleanup); every
utterance is appended to a local JSONL log for correction mining.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from .cleanup import cleanup
from .lexicon import Lexicon

DATA_DIR = Path.home() / ".flowlocal"
LEXICON_DB = str(DATA_DIR / "lexicon.db")
TRANSCRIPT_LOG = DATA_DIR / "transcripts.jsonl"


def process_text(raw: str, lexicon: Lexicon, level: str = "light") -> str:
    """Text half of the pipeline (testable without audio/models)."""
    resolved = lexicon.resolve_aliases(raw)
    terms = [t.term for t in lexicon.terms()]
    return cleanup(resolved, level=level, lexicon_terms=terms).text


def _log(raw: str, cleaned: str) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with TRANSCRIPT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "raw": raw,
                            "clean": cleaned}, ensure_ascii=False) + "\n")


def dictate(model_size: str = "small", level: str = "light",
            insert_mode: str = "stdout", language: str | None = None) -> None:
    """Continuous VAD-segmented dictation loop."""
    from .asr import default_router
    from .audio import record_utterances, SAMPLE_RATE
    from .insert import get_inserter

    lexicon = Lexicon(LEXICON_DB)
    router = default_router(model_size)
    inserter = get_inserter(insert_mode)
    prompt = lexicon.bias_prompt()

    print(f"flowlocal: listening (model={model_size}, cleanup={level}, "
          f"insert={insert_mode}). Ctrl+C to stop.")
    for audio in record_utterances():
        provider = router.pick(language, duration_s=len(audio) / SAMPLE_RATE)
        raw = " ".join(s.text for s in provider.transcribe(
            audio, language=language, initial_prompt=prompt)).strip()
        if not raw:
            continue
        cleaned = process_text(raw, lexicon, level)
        _log(raw, cleaned)
        inserter.insert(cleaned)


def transcribe_file(path: str, model_size: str = "small",
                    level: str = "light", language: str | None = None) -> str:
    from .asr import default_router
    from .audio import load_wav

    lexicon = Lexicon(LEXICON_DB)
    provider = default_router(model_size).default
    raw = " ".join(s.text for s in provider.transcribe(
        load_wav(path), language=language,
        initial_prompt=lexicon.bias_prompt())).strip()
    cleaned = process_text(raw, lexicon, level)
    _log(raw, cleaned)
    return cleaned
