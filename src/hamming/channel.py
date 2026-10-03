"""
Моделі каналу зв'язку та перемежування.

* :func:`bsc` — двійковий симетричний канал: кожен біт незалежно
  спотворюється з імовірністю p. Це модель випадкового шуму.
* :func:`burst` — пакет спотворень: b сусідніх бітів поспіль. Так
  поводяться імпульсні завади, і саме тут код із задачі вразливий, бо
  два спотворення в одній трійці він уже не виправляє.
* :func:`interleave` / :func:`deinterleave` — перемежування блоками:
  біти сусідніх трійок розносяться далеко один від одного, тож пакет
  спотворень розподіляється між різними трійками.

Генератор випадкових чисел передається явно, щоб експерименти
відтворювалися.
"""

from __future__ import annotations

import random

__all__ = ["flip", "bsc", "burst", "interleave", "deinterleave"]


def flip(bits: str, positions) -> str:
    """Інвертувати біти на заданих позиціях."""
    out = list(bits)
    for i in positions:
        out[i] = "1" if out[i] == "0" else "0"
    return "".join(out)


def bsc(bits: str, p: float, rng: random.Random) -> str:
    """Двійковий симетричний канал з імовірністю спотворення біта p."""
    if not 0.0 <= p <= 1.0:
        raise ValueError("імовірність має лежати в [0, 1]")
    return "".join(("1" if b == "0" else "0") if rng.random() < p else b for b in bits)


def burst(bits: str, length: int, start: int) -> str:
    """Пакет спотворень: ``length`` бітів поспіль, починаючи з ``start``."""
    if length < 0 or not 0 <= start <= len(bits) - length:
        raise ValueError("пакет виходить за межі повідомлення")
    return flip(bits, range(start, start + length))


def interleave(bits: str, depth: int) -> str:
    """
    Перемежування таблицею з ``depth`` рядків: запис по рядках, читання по
    стовпцях. Довжина має ділитися на ``depth``.
    """
    if depth < 1 or len(bits) % depth:
        raise ValueError("довжина має ділитися на глибину перемежування")
    cols = len(bits) // depth
    return "".join(bits[r * cols + c] for c in range(cols) for r in range(depth))


def deinterleave(bits: str, depth: int) -> str:
    """Обернене перетворення до :func:`interleave`."""
    if depth < 1 or len(bits) % depth:
        raise ValueError("довжина має ділитися на глибину перемежування")
    cols = len(bits) // depth
    out = [""] * len(bits)
    for idx, b in enumerate(bits):
        c, r = divmod(idx, depth)
        out[r * cols + c] = b
    return "".join(out)
