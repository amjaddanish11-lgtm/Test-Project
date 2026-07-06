"""ASR provider interface and router.

Three-lane routing per the design doc:
  Lane A (default): faster-whisper multilingual
  Lane B (fast):    smaller/distilled model for English on weak hardware
  Lane C (fallback) pluggable long-tail provider

Heavy dependencies are imported lazily so the core package (cleanup,
lexicon, tests) works without any ML stack installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class Segment:
    text: str
    start: float
    end: float
    language: str = ""


class ASRProvider:
    name = "base"

    def transcribe(self, audio, sample_rate: int = 16000,
                   language: Optional[str] = None,
                   initial_prompt: str = "") -> Iterable[Segment]:
        raise NotImplementedError


class FasterWhisperProvider(ASRProvider):
    name = "faster-whisper"

    def __init__(self, model_size: str = "large-v3", device: str = "auto",
                 compute_type: str = "auto"):
        from faster_whisper import WhisperModel  # lazy: optional dependency
        self.model = WhisperModel(model_size, device=device,
                                  compute_type=compute_type)

    def transcribe(self, audio, sample_rate=16000, language=None,
                   initial_prompt=""):
        segments, info = self.model.transcribe(
            audio,
            language=language,
            initial_prompt=initial_prompt or None,
            vad_filter=True,
        )
        for s in segments:
            yield Segment(text=s.text.strip(), start=s.start, end=s.end,
                          language=info.language)


class Router:
    """Pick a provider by language and hardware profile."""

    def __init__(self, default: ASRProvider,
                 fast: Optional[ASRProvider] = None,
                 fallback: Optional[ASRProvider] = None,
                 fast_languages: tuple = ("en",)):
        self.default = default
        self.fast = fast
        self.fallback = fallback
        self.fast_languages = fast_languages

    def pick(self, language: Optional[str] = None,
             duration_s: float = 0.0) -> ASRProvider:
        if self.fast and language in self.fast_languages and duration_s < 15:
            return self.fast
        return self.default


def default_router(model_size: str = "small", device: str = "auto") -> Router:
    """Build a router with whatever is installed. `small` keeps first-run
    downloads modest; bump to large-v3 or turbo on GPU machines."""
    return Router(default=FasterWhisperProvider(model_size, device=device))
