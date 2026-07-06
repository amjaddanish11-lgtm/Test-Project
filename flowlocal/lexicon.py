"""Local personalization store: user lexicon (hotwords) in SQLite.

Terms bias ASR (via Whisper initial_prompt) and are protected from cleanup.
Repeated user corrections can be promoted into the lexicon (correction
mining), keeping personalization fully on-device.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Term:
    term: str
    aliases: List[str]
    language: str = ""
    tag: str = ""
    hits: int = 0


class Lexicon:
    def __init__(self, db_path: str = ":memory:"):
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS terms (
                   term TEXT PRIMARY KEY,
                   aliases TEXT NOT NULL DEFAULT '',
                   language TEXT NOT NULL DEFAULT '',
                   tag TEXT NOT NULL DEFAULT '',
                   hits INTEGER NOT NULL DEFAULT 0
               )"""
        )
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS corrections (
                   heard TEXT NOT NULL,
                   corrected TEXT NOT NULL,
                   count INTEGER NOT NULL DEFAULT 1,
                   PRIMARY KEY (heard, corrected)
               )"""
        )
        self.conn.commit()

    def add(self, term: str, aliases: Optional[List[str]] = None,
            language: str = "", tag: str = "") -> None:
        self.conn.execute(
            "INSERT INTO terms(term, aliases, language, tag) VALUES(?,?,?,?) "
            "ON CONFLICT(term) DO UPDATE SET aliases=excluded.aliases, "
            "language=excluded.language, tag=excluded.tag",
            (term, ",".join(aliases or []), language, tag),
        )
        self.conn.commit()

    def remove(self, term: str) -> bool:
        cur = self.conn.execute("DELETE FROM terms WHERE term=?", (term,))
        self.conn.commit()
        return cur.rowcount > 0

    def terms(self) -> List[Term]:
        rows = self.conn.execute(
            "SELECT term, aliases, language, tag, hits FROM terms ORDER BY hits DESC, term"
        ).fetchall()
        return [Term(t, a.split(",") if a else [], l, g, h) for t, a, l, g, h in rows]

    def bias_prompt(self, limit: int = 40) -> str:
        """Whisper initial_prompt string biasing toward user vocabulary."""
        names = [t.term for t in self.terms()[:limit]]
        return ("Glossary: " + ", ".join(names) + ".") if names else ""

    def resolve_aliases(self, text: str) -> str:
        """Replace known misheard aliases with canonical spellings."""
        import re
        for t in self.terms():
            for alias in t.aliases:
                if alias and alias.lower() != t.term.lower():
                    text = re.sub(rf"\b{re.escape(alias)}\b", t.term, text,
                                  flags=re.IGNORECASE)
        return text

    # --- correction mining -------------------------------------------------
    def record_correction(self, heard: str, corrected: str) -> None:
        self.conn.execute(
            "INSERT INTO corrections(heard, corrected) VALUES(?,?) "
            "ON CONFLICT(heard, corrected) DO UPDATE SET count=count+1",
            (heard, corrected),
        )
        self.conn.commit()

    def promote_corrections(self, threshold: int = 3) -> List[str]:
        """Promote repeated corrections into lexicon entries; return promoted terms."""
        rows = self.conn.execute(
            "SELECT heard, corrected FROM corrections WHERE count>=?", (threshold,)
        ).fetchall()
        promoted = []
        for heard, corrected in rows:
            self.add(corrected, aliases=[heard], tag="mined")
            promoted.append(corrected)
        return promoted
