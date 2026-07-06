"""Text insertion backends.

MVP strategy per the design doc: clipboard + paste simulation as the robust
fallback; platform accessibility/IME integration comes later behind the
same interface.
"""

from __future__ import annotations

import subprocess
import sys


class Inserter:
    name = "base"

    def insert(self, text: str) -> None:
        raise NotImplementedError


class StdoutInserter(Inserter):
    """Print to stdout — useful for piping and debugging."""
    name = "stdout"

    def insert(self, text: str) -> None:
        print(text, flush=True)


class ClipboardInserter(Inserter):
    """Copy to clipboard; the user pastes (or we simulate paste if possible)."""
    name = "clipboard"

    def __init__(self, simulate_paste: bool = False):
        self.simulate_paste = simulate_paste

    def insert(self, text: str) -> None:
        import pyperclip
        pyperclip.copy(text)
        if self.simulate_paste:
            self._paste()

    @staticmethod
    def _paste() -> None:
        if sys.platform == "darwin":
            subprocess.run(["osascript", "-e",
                            'tell application "System Events" to keystroke "v" using command down'],
                           check=False)
        elif sys.platform.startswith("linux"):
            subprocess.run(["xdotool", "key", "ctrl+v"], check=False)
        # Windows paste simulation lands with the TSF/SendInput backend.


def get_inserter(mode: str = "stdout") -> Inserter:
    if mode == "stdout":
        return StdoutInserter()
    if mode == "clipboard":
        return ClipboardInserter()
    if mode == "paste":
        return ClipboardInserter(simulate_paste=True)
    raise ValueError(f"unknown inserter: {mode}")
