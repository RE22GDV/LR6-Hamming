"""
Командний інтерфейс роботи.

    python run.py selftest             приклади Codewars
    python run.py encode "текст"       кодування (3,1)
    python run.py decode 000111...     декодування з виправленням
    python run.py demo "текст" [p]     передача через зашумлений канал
    python run.py forge "hey" "hex"    підміна тексту без жодного сигналу
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from .analysis import flips_to_change, repetition_bit_error
from .channel import bsc, flip
from .codes import decode, encode

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "tests" / "codewars_cases.json"


def _out(s: str = "") -> None:
    sys.stdout.write(s + "\n")


def cmd_selftest(_a) -> int:
    cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    passed = 0
    _out("Приклади Codewars")
    _out("-" * 70)
    for c in cases:
        fn = encode if c["function"] == "Encode" else decode
        ok = fn(c["input"]) == c["expected"]
        passed += ok
        shown = c["input"] if len(c["input"]) <= 30 else c["input"][:27] + "..."
        _out("[%s] %s(%s)" % ("OK" if ok else "FAIL", c["function"], shown))
    _out("-" * 70)
    _out("Пройдено %d з %d" % (passed, len(cases)))
    return 0 if passed == len(cases) else 1


def cmd_demo(a) -> int:
    rng = random.Random(a.seed)
    sent = encode(a.text)
    received = bsc(sent, a.p, rng)
    flipped = sum(x != y for x, y in zip(sent, received))
    got = decode(received)
    _out("Текст           : %s" % a.text)
    _out("Бітів у каналі  : %d" % len(sent))
    _out("Спотворено      : %d (%.1f %%), p = %.3f" % (flipped, 100 * flipped / len(sent), a.p))
    _out("Отримано        : %s" % got)
    _out("Збіг            : %s" % ("так" if got == a.text else "ні"))
    _out("Теорія          : біт декодується хибно з імовірністю %.5f" % repetition_bit_error(a.p))
    return 0


def cmd_forge(a) -> int:
    bits = encode(a.original)
    data_diff = [i for i, (x, y) in enumerate(zip(
        "".join(format(ord(c), "08b") for c in a.original),
        "".join(format(ord(c), "08b") for c in a.forged))) if x != y]
    positions = [p for i in data_diff for p in (3 * i, 3 * i + 1)]
    forged = flip(bits, positions)
    _out("Оригінал        : %s" % a.original)
    _out("Інвертовано     : %d бітів із %d" % (len(positions), len(bits)))
    _out("Декодер видав   : %s" % decode(forged))
    _out("Мінімум за формулою: %d" % flips_to_change(a.original, a.forged))
    _out("Декодер не повідомив про жодну проблему: код виправляє шум, а не підміну.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="hamming", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest").set_defaults(func=cmd_selftest)
    p = sub.add_parser("encode"); p.add_argument("text")
    p.set_defaults(func=lambda a: _out(encode(a.text)) or 0)
    p = sub.add_parser("decode"); p.add_argument("bits")
    p.set_defaults(func=lambda a: _out(decode(a.bits)) or 0)
    p = sub.add_parser("demo"); p.add_argument("text"); p.add_argument("p", nargs="?", type=float, default=0.05)
    p.add_argument("--seed", type=int, default=1); p.set_defaults(func=cmd_demo)
    p = sub.add_parser("forge"); p.add_argument("original"); p.add_argument("forged")
    p.set_defaults(func=cmd_forge)
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if a.cmd == "forge" and len(a.original) != len(a.forged):
        _out("тексти мають бути однакової довжини")
        return 2
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
