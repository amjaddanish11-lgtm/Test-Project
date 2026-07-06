"""FlowLocal command-line interface."""

from __future__ import annotations

import argparse
import sys


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="flowlocal",
                                description="Local-first dictation.")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dictate", help="live dictation from the microphone")
    d.add_argument("--model", default="small",
                   help="faster-whisper model size (small, medium, large-v3, turbo)")
    d.add_argument("--cleanup", default="light",
                   choices=["verbatim", "light", "polished"])
    d.add_argument("--insert", default="stdout",
                   choices=["stdout", "clipboard", "paste"])
    d.add_argument("--language", default=None)

    t = sub.add_parser("transcribe", help="transcribe an audio file")
    t.add_argument("path")
    t.add_argument("--model", default="small")
    t.add_argument("--cleanup", default="light",
                   choices=["verbatim", "light", "polished"])
    t.add_argument("--language", default=None)

    lx = sub.add_parser("lexicon", help="manage the personal vocabulary")
    lxsub = lx.add_subparsers(dest="lexcmd", required=True)
    a = lxsub.add_parser("add")
    a.add_argument("term")
    a.add_argument("--alias", default="", help="comma-separated misheard forms")
    a.add_argument("--tag", default="")
    r = lxsub.add_parser("remove")
    r.add_argument("term")
    lxsub.add_parser("list")

    c = sub.add_parser("clean", help="run cleanup on stdin text (no models)")
    c.add_argument("--cleanup", default="light",
                   choices=["verbatim", "light", "polished"])

    args = p.parse_args(argv)

    if args.cmd == "dictate":
        from .app import dictate
        try:
            dictate(args.model, args.cleanup, args.insert, args.language)
        except KeyboardInterrupt:
            print("\nstopped.")
        return 0

    if args.cmd == "transcribe":
        from .app import transcribe_file
        print(transcribe_file(args.path, args.model, args.cleanup, args.language))
        return 0

    if args.cmd == "lexicon":
        from .app import LEXICON_DB
        from .lexicon import Lexicon
        lex = Lexicon(LEXICON_DB)
        if args.lexcmd == "add":
            aliases = [x.strip() for x in args.alias.split(",") if x.strip()]
            lex.add(args.term, aliases, tag=args.tag)
            print(f"added: {args.term}")
        elif args.lexcmd == "remove":
            print("removed" if lex.remove(args.term) else "not found")
        else:
            for t in lex.terms():
                extra = f" (aliases: {', '.join(t.aliases)})" if t.aliases else ""
                print(f"{t.term}{extra}")
        return 0

    if args.cmd == "clean":
        from .app import LEXICON_DB, process_text
        from .lexicon import Lexicon
        text = sys.stdin.read()
        print(process_text(text, Lexicon(LEXICON_DB), args.cleanup))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
