"""Microphone capture and VAD segmentation (Silero VAD).

Yields utterance-sized float32 numpy buffers at 16 kHz. Imports are lazy so
the core package works without audio dependencies installed.
"""

from __future__ import annotations

from typing import Iterator

SAMPLE_RATE = 16000
FRAME_MS = 32  # Silero expects 512-sample frames at 16 kHz
FRAME_SAMPLES = SAMPLE_RATE * FRAME_MS // 1000


def record_utterances(
    speech_threshold: float = 0.5,
    silence_end_ms: int = 600,
    max_utterance_s: int = 30,
) -> Iterator["numpy.ndarray"]:
    """Blocking generator: capture mic audio, emit one buffer per utterance.

    Endpointing: an utterance ends after `silence_end_ms` of non-speech or
    at `max_utterance_s`, whichever comes first.
    """
    import numpy as np
    import sounddevice as sd
    from silero_vad import load_silero_vad
    import torch

    vad = load_silero_vad()
    silence_frames_needed = max(1, silence_end_ms // FRAME_MS)
    max_frames = max_utterance_s * 1000 // FRAME_MS

    buf, in_speech, silent = [], False, 0
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                        blocksize=FRAME_SAMPLES) as stream:
        while True:
            frame, _ = stream.read(FRAME_SAMPLES)
            frame = frame[:, 0]
            prob = vad(torch.from_numpy(frame), SAMPLE_RATE).item()
            speaking = prob >= speech_threshold

            if speaking:
                in_speech, silent = True, 0
                buf.append(frame)
            elif in_speech:
                silent += 1
                buf.append(frame)  # keep trailing context
                if silent >= silence_frames_needed:
                    yield np.concatenate(buf)
                    buf, in_speech, silent = [], False, 0

            if in_speech and len(buf) >= max_frames:
                yield np.concatenate(buf)
                buf, in_speech, silent = [], False, 0


def load_wav(path: str) -> "numpy.ndarray":
    """Load a WAV/audio file as 16 kHz mono float32 (for `flowlocal transcribe`)."""
    import numpy as np
    import wave

    with wave.open(path, "rb") as w:
        rate = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        if w.getnchannels() > 1:
            data = data.reshape(-1, w.getnchannels()).mean(axis=1)
        audio = data.astype(np.float32) / 32768.0
    if rate != SAMPLE_RATE:
        # simple linear resample; fine for dictation-grade audio
        idx = np.linspace(0, len(audio) - 1, int(len(audio) * SAMPLE_RATE / rate))
        audio = np.interp(idx, np.arange(len(audio)), audio).astype(np.float32)
    return audio
