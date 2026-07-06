"""Constrained dictation cleanup.

Cleanup is deliberately narrow: it removes disfluencies, fixes casing and
punctuation spacing, and applies spoken-command substitutions. It never
rewrites meaning, and it never touches protected spans (numbers, URLs,
emails, IDs, and user lexicon terms).

Levels:
    verbatim  - return the raw transcript untouched
    light     - filler removal + casing/punctuation normalization (default)
    polished  - light + false-start collapse and spoken punctuation commands
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Tuple

FILLERS = {
    "um", "uh", "erm", "uhm", "hmm", "mmm", "uhh", "umm", "er", "ah",
}
# Multi-word fillers removed only in `polished` mode (riskier: "you know"
# can be meaningful).
SOFT_FILLERS = ("you know", "i mean", "sort of like", "kind of like")

SPOKEN_COMMANDS = {
    "new line": "\n",
    "new paragraph": "\n\n",
    "period": ".",
    "full stop": ".",
    "comma": ",",
    "question mark": "?",
    "exclamation mark": "!",
    "exclamation point": "!",
    "colon": ":",
    "semicolon": ";",
    "open quote": "“",
    "close quote": "”",
}

# Spans the cleanup stage must never modify.
PROTECTED_PATTERNS = [
    re.compile(r"https?://\S+"),                          # URLs
    re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),           # emails
    re.compile(r"\b\d[\d,.:/-]*\d\b|\b\d\b"),             # numbers, dates, IDs
    re.compile(r"\b[A-Z]{2,}[A-Z0-9-]*\b"),               # acronyms / SKUs
    re.compile(r"(?<![\w.])(?:[\w-]+/)+[\w.-]+"),         # paths, owner/repo
]


@dataclass
class CleanupResult:
    raw: str
    text: str
    level: str
    protected_spans: List[Tuple[int, int, str]] = field(default_factory=list)
    removed_fillers: int = 0


def find_protected_spans(text: str, lexicon_terms: List[str] = ()) -> List[Tuple[int, int, str]]:
    spans = []
    for pat in PROTECTED_PATTERNS:
        for m in pat.finditer(text):
            spans.append((m.start(), m.end(), m.group()))
    for term in lexicon_terms:
        for m in re.finditer(re.escape(term), text, re.IGNORECASE):
            spans.append((m.start(), m.end(), m.group()))
    return sorted(spans)


def _in_protected(idx: int, spans: List[Tuple[int, int, str]]) -> bool:
    return any(s <= idx < e for s, e, _ in spans)


def _remove_fillers(text: str, spans, aggressive: bool) -> Tuple[str, int]:
    removed = 0
    out_tokens = []
    for m in re.finditer(r"\S+|\s+", text):
        tok = m.group()
        word = tok.strip(",.!?;:").lower()
        if (
            tok.strip()
            and word in FILLERS
            and not _in_protected(m.start(), spans)
        ):
            removed += 1
            continue
        out_tokens.append(tok)
    result = "".join(out_tokens)
    if aggressive:
        for phrase in SOFT_FILLERS:
            new = re.sub(rf"(?<!\w)(?:, )?{re.escape(phrase)},?(?= )", "", result, flags=re.IGNORECASE)
            removed += 1 if new != result else 0
            result = new
    return result, removed


def _collapse_false_starts(text: str) -> str:
    # "I went to the- to the store" -> "I went to the store"
    text = re.sub(r"\b([\w']+)-\s+\1\b", r"\1", text, flags=re.IGNORECASE)
    # Immediate word repeats: "the the" -> "the" (never inside numbers/protected;
    # numbers don't match \w'+ repeats with identical casing rarely intended).
    text = re.sub(r"\b([A-Za-z']+)(\s+\1)+\b", r"\1", text, flags=re.IGNORECASE)
    return text


def _apply_spoken_commands(text: str) -> str:
    for phrase, repl in SPOKEN_COMMANDS.items():
        if repl.startswith("\n"):
            text = re.sub(rf"[,.]?[ \t]*\b{phrase}\b[,.]?[ \t]*", repl, text, flags=re.IGNORECASE)
        else:
            # [ \t]* (not \s*) so previously inserted newlines survive
            text = re.sub(rf"[ \t]*\b{phrase}\b[ \t]*", repl + " ", text, flags=re.IGNORECASE)
    return text


def _normalize(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ([,.!?;:])", r"\1", text)
    text = re.sub(r"([,.!?;:])(?=[A-Za-z])", r"\1 ", text)
    text = re.sub(r" +\n", "\n", text).strip()
    # Sentence-initial capitalization.
    def cap(m):
        return m.group(1) + m.group(2).upper()
    text = re.sub(r"(^|[.!?]\s+|\n)([a-z])", cap, text)
    return text


def _merge_spans(spans: List[Tuple[int, int, str]]) -> List[Tuple[int, int, str]]:
    merged: List[Tuple[int, int, str]] = []
    for s, e, lit in spans:
        if merged and s < merged[-1][1]:
            ps, pe, _ = merged[-1]
            if e > pe:
                merged[-1] = (ps, e, "")
        else:
            merged.append((s, e, lit))
    return merged


def cleanup(raw: str, level: str = "light", lexicon_terms: List[str] = ()) -> CleanupResult:
    if level not in ("verbatim", "light", "polished"):
        raise ValueError(f"unknown cleanup level: {level}")
    if level == "verbatim" or not raw.strip():
        return CleanupResult(raw=raw, text=raw, level=level)

    spans = find_protected_spans(raw, lexicon_terms)

    # Mask protected spans with placeholders so no transformation can touch
    # them, then restore verbatim at the end.
    literals: List[str] = []
    masked = []
    cursor = 0
    for s, e, _ in _merge_spans(spans):
        masked.append(raw[cursor:s])
        masked.append(f"{len(literals)}")
        literals.append(raw[s:e])
        cursor = e
    masked.append(raw[cursor:])
    text = "".join(masked)

    text, removed = _remove_fillers(text, [], aggressive=(level == "polished"))
    if level == "polished":
        text = _collapse_false_starts(text)
        text = _apply_spoken_commands(text)
    text = _normalize(text)

    for i, literal in enumerate(literals):
        text = text.replace(f"{i}", literal)

    return CleanupResult(raw=raw, text=text, level=level,
                         protected_spans=spans, removed_fillers=removed)
