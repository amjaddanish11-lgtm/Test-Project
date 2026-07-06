#!/usr/bin/env python3
"""
FlowLocal — single-file local dictation tool (Wispr Flow alternative).

WHAT THIS IS
    Speak into your mic -> local Whisper model transcribes it -> filler
    words and false starts get cleaned up -> the text is copied to your
    clipboard (and optionally auto-pasted into whatever app is focused).
    Everything runs on your machine. No cloud, no account, no telemetry.

ONE-TIME SETUP
    pip install faster-whisper sounddevice numpy pyperclip

    (First run also downloads a Whisper model automatically, ~150MB-3GB
    depending on --model size, cached under ~/.cache/huggingface.)

USAGE
    python flowlocal_single.py                     # listen + copy to clipboard
    python flowlocal_single.py --paste             # also auto-paste (types Ctrl/Cmd+V)
    python flowlocal_single.py --model small        # bigger/more accurate (default: base)
    python flowlocal_single.py --cleanup verbatim   # no cleanup, raw transcript
    python flowlocal_single.py --lexicon-add "Kubernetes,k8s,cooper netties"
    python flowlocal_single.py --lexicon-list

HOW IT WORKS
    1. Mic audio streams in via sounddevice.
    2. A simple energy-based voice-activity detector groups audio into
       utterances (speech start -> ~0.6s of silence -> utterance end).
    3. Each utterance is transcribed locally with faster-whisper.
    4. Your personal lexicon (stored in ~/.flowlocal/lexicon.json) is used
       to bias recognition toward names/terms you've added, and to fix
       known mis-hearings automatically.
    5. Cleanup removes filler words ("um", "uh"), collapses false starts
       ("the the" -> "the"), fixes casing/punctuation spacing, and
       supports spoken punctuation ("comma", "period", "new paragraph").
       URLs, emails, numbers, dates, acronyms, and lexicon terms are never
       altered by cleanup.
    6. The cleaned text is copied to your clipboard automatically (and
       pasted for you if you pass --paste).

Press Ctrl+C to stop.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

DATA_DIR = Path.home() / ".flowlocal"
LEXICON_PATH = DATA_DIR / "lexicon.json"
LOG_PATH = DATA_DIR / "transcripts.jsonl"

# --------------------------------------------------------------------------
# Cleanup: constrained, reversible dictation cleanup
# --------------------------------------------------------------------------

FILLERS = {"um", "uh", "erm", "uhm", "hmm", "mmm", "uhh", "umm", "er", "ah"}

SPOKEN_COMMANDS = {
    "new paragraph": "\n\n",
    "new line": "\n",
    "period": ".",
    "full stop": ".",
    "comma": ",",
    "question mark": "?",
    "exclamation mark": "!",
    "exclamation point": "!",
    "colon": ":",
    "semicolon": ";",
}

PROTECTED_PATTERNS = [
    re.compile(r"https?://\S+"),
    re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),
    re.compile(r"\b\d[\d,.:/-]*\d\b|\b\d\b"),
    re.compile(r"\b[A-Z]{2,}[A-Z0-9-]*\b"),
]


def find_protected_spans(text, lexicon_terms=()):
    spans = []
    for pat in PROTECTED_PATTERNS:
        for m in pat.finditer(text):
            spans.append((m.start(), m.end()))
    for term in lexicon_terms:
        for m in re.finditer(re.escape(term), text, re.IGNORECASE):
            spans.append((m.start(), m.end()))
    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return merged


def cleanup(raw: str, level: str, lexicon_terms=()) -> str:
    if level == "verbatim" or not raw.strip():
        return raw

    spans = find_protected_spans(raw, lexicon_terms)
    literals, masked, cursor = [], [], 0
    for s, e in spans:
        masked.append(raw[cursor:s])
        masked.append(str(len(literals)))
        literals.append(raw[s:e])
        cursor = e
    masked.append(raw[cursor:])
    text = "".join(masked)

    # Remove filler words (word-boundary, case-insensitive).
    out = []
    for tok in re.finditer(r"\S+|\s+", text):
        w = tok.group().strip(",.!?;:").lower()
        if tok.group().strip() and w in FILLERS:
            continue
        out.append(tok.group())
    text = "".join(out)

    if level == "polished":
        text = re.sub(r"\b([\w']+)-\s+\1\b", r"\1", text, flags=re.IGNORECASE)
        text = re.sub(r"\b([A-Za-z']+)(\s+\1)+\b", r"\1", text, flags=re.IGNORECASE)
        for phrase, repl in SPOKEN_COMMANDS.items():
            if repl.startswith("\n"):
                text = re.sub(rf"[,.]?[ \t]*\b{phrase}\b[,.]?[ \t]*", repl, text, re.IGNORECASE)
            else:
                text = re.sub(rf"[ \t]*\b{phrase}\b[ \t]*", repl + " ", text, re.IGNORECASE)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ([,.!?;:])", r"\1", text)
    text = re.sub(r"([,.!?;:])(?=[A-Za-z])", r"\1 ", text)
    text = re.sub(r" +\n", "\n", text).strip()
    text = re.sub(r"(^|[.!?]\s+|\n)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)

    for i, literal in enumerate(literals):
        text = text.replace(str(i), literal)
    return text


# --------------------------------------------------------------------------
# Lexicon: personal vocabulary stored as plain JSON (no DB dependency)
# --------------------------------------------------------------------------

def load_lexicon() -> dict:
    if LEXICON_PATH.exists():
        return json.loads(LEXICON_PATH.read_text())
    return {}


def save_lexicon(lex: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    LEXICON_PATH.write_text(json.dumps(lex, indent=2))


def lexicon_add(term: str, aliases: list[str]) -> None:
    lex = load_lexicon()
    lex[term] = sorted(set(lex.get(term, []) + aliases))
    save_lexicon(lex)
    print(f"Added '{term}' (aliases: {', '.join(lex[term]) or 'none'})")


def lexicon_list() -> None:
    lex = load_lexicon()
    if not lex:
        print("(lexicon is empty)")
    for term, aliases in lex.items():
        extra = f"  aliases: {', '.join(aliases)}" if aliases else ""
        print(f"{term}{extra}")


def resolve_aliases(text: str, lex: dict) -> str:
    for term, aliases in lex.items():
        for alias in aliases:
            if alias.lower() != term.lower():
                text = re.sub(rf"\b{re.escape(alias)}\b", term, text, flags=re.IGNORECASE)
    return text


def bias_prompt(lex: dict) -> str:
    return f"Glossary: {', '.join(lex.keys())}." if lex else ""


# --------------------------------------------------------------------------
# Insertion: clipboard, optionally auto-paste
# --------------------------------------------------------------------------

def insert_text(text: str, do_paste: bool) -> None:
    try:
        import pyperclip
        pyperclip.copy(text)
    except ImportError:
        print("[warn] pyperclip not installed; printing instead of copying to clipboard")
        print(text)
        return

    if do_paste:
        if sys.platform == "darwin":
            subprocess.run(
                ["osascript", "-e",
                 'tell application "System Events" to keystroke "v" using command down'],
                check=False,
            )
        elif sys.platform.startswith("linux"):
            subprocess.run(["xdotool", "key", "ctrl+v"], check=False)
        elif sys.platform == "win32":
            try:
                import ctypes
                # Ctrl down, V down, V up, Ctrl up
                ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0x56, 0, 0, 0)
                ctypes.windll.user32.keybd_event(0x56, 0, 2, 0)
                ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)
            except Exception as e:
                print(f"[warn] auto-paste failed on Windows: {e}")


def log_transcript(raw: str, cleaned: str) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "raw": raw, "clean": cleaned}) + "\n")


# --------------------------------------------------------------------------
# Audio capture + simple energy-based VAD (no extra VAD model required)
# --------------------------------------------------------------------------

def record_utterances(silence_end_s: float = 0.6, max_utterance_s: float = 30.0,
                      energy_threshold: float = 0.012):
    import numpy as np
    import sounddevice as sd

    sample_rate = 16000
    frame_samples = int(sample_rate * 0.03)  # 30ms frames
    silence_frames_needed = max(1, int(silence_end_s / 0.03))
    max_frames = int(max_utterance_s / 0.03)

    buf, in_speech, silent = [], False, 0
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="float32",
                        blocksize=frame_samples) as stream:
        while True:
            frame, _ = stream.read(frame_samples)
            frame = frame[:, 0]
            energy = float(np.sqrt(np.mean(frame ** 2)))
            speaking = energy >= energy_threshold

            if speaking:
                in_speech, silent = True, 0
                buf.append(frame)
            elif in_speech:
                silent += 1
                buf.append(frame)
                if silent >= silence_frames_needed:
                    yield np.concatenate(buf)
                    buf, in_speech, silent = [], False, 0

            if in_speech and len(buf) >= max_frames:
                yield np.concatenate(buf)
                buf, in_speech, silent = [], False, 0


# --------------------------------------------------------------------------
# Main dictation loop
# --------------------------------------------------------------------------

def dictate(model_size: str, cleanup_level: str, do_paste: bool, language: str | None) -> None:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("Missing dependency. Run:\n"
             "    pip install faster-whisper sounddevice numpy pyperclip")
        sys.exit(1)

    print(f"Loading Whisper model '{model_size}' (first run downloads it, please wait)...")
    model = WhisperModel(model_size, device="auto", compute_type="auto")

    lex = load_lexicon()
    prompt = bias_prompt(lex)

    print(f"Ready. Listening (model={model_size}, cleanup={cleanup_level}, "
         f"paste={'on' if do_paste else 'off'}). Speak naturally. Ctrl+C to stop.\n")

    try:
        for audio in record_utterances():
            segments, _ = model.transcribe(audio, language=language,
                                           initial_prompt=prompt or None, vad_filter=True)
            raw = " ".join(s.text.strip() for s in segments).strip()
            if not raw:
                continue
            resolved = resolve_aliases(raw, lex)
            cleaned = cleanup(resolved, cleanup_level, list(lex.keys()))
            log_transcript(raw, cleaned)
            print(f"> {cleaned}")
            insert_text(cleaned, do_paste)
    except KeyboardInterrupt:
        print("\nStopped.")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", default="base",
                  help="Whisper model size: tiny, base, small, medium, large-v3 (default: base)")
    p.add_argument("--cleanup", default="light", choices=["verbatim", "light", "polished"])
    p.add_argument("--paste", action="store_true", help="auto-paste after copying to clipboard")
    p.add_argument("--language", default=None, help="force a language code, e.g. en, es, fr")
    p.add_argument("--lexicon-add", metavar="TERM,alias1,alias2",
                  help='add a term with optional aliases, e.g. "Kubernetes,k8s,cooper netties"')
    p.add_argument("--lexicon-list", action="store_true", help="print your saved lexicon")
    args = p.parse_args()

    if args.lexicon_list:
        lexicon_list()
        return
    if args.lexicon_add:
        parts = [x.strip() for x in args.lexicon_add.split(",") if x.strip()]
        lexicon_add(parts[0], parts[1:])
        return

    dictate(args.model, args.cleanup, args.paste, args.language)


if __name__ == "__main__":
    main()
