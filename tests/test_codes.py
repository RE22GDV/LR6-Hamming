"""Кодування, декодування та межі можливостей обох кодів."""

from __future__ import annotations

import json
import random
from itertools import product
from pathlib import Path

import pytest

from hamming import (
    bits_to_text,
    decode,
    encode,
    flip,
    hamming74_decode,
    hamming74_decode_block,
    hamming74_encode,
    hamming74_encode_block,
    majority,
    text_to_bits,
)

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "tests" / "codewars_cases.json").read_text(encoding="utf-8"))["cases"]
IDS = ["%s-%d" % (c["function"], i) for i, c in enumerate(CASES)]
RNG = random.Random(20261004)


def _ascii(n: int) -> str:
    return "".join(chr(RNG.randrange(32, 127)) for _ in range(n))


# --------------------------------------------------------------------------- #
#  Приклади платформи
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_codewars_case(case: dict) -> None:
    fn = encode if case["function"] == "Encode" else decode
    assert fn(case["input"]) == case["expected"]


def test_example_from_statement() -> None:
    """Приклад з умови, розписаний покроково."""
    assert [ord(c) for c in "hey"] == [104, 101, 121]
    assert text_to_bits("hey") == "011010000110010101111001"
    assert encode("hey") == (
        "000111111000111000000000"
        "000111111000000111000111"
        "000111111111111000000111"
    )


@pytest.mark.parametrize("case", [c for c in CASES if c["function"] == "Decode"],
                         ids=lambda c: repr(c["expected"][:12]))
def test_platform_corruptions_have_at_most_one_flip_per_triple(case: dict) -> None:
    """
    Саме тому приклади платформи декодуються: у кожній трійці не більше
    одного спотворення, хоча загалом спотворено до 9,7 % бітів.
    """
    clean = encode(case["expected"])
    flips = [i for i, (a, b) in enumerate(zip(case["input"], clean)) if a != b]
    assert flips == case["flipped_bits"]
    triples = [i // 3 for i in flips]
    assert len(triples) == len(set(triples))


# --------------------------------------------------------------------------- #
#  Провідні нулі та межові символи
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("ch,bits", [(" ", "00100000"), ("\x00", "00000000"),
                                     ("\x7f", "01111111"), ("A", "01000001")])
def test_leading_zeros_are_kept(ch: str, bits: str) -> None:
    """Кожен символ займає рівно 8 бітів, інакше межі між символами зсуваються."""
    assert text_to_bits(ch) == bits
    assert len(encode(ch)) == 24


def test_empty_text() -> None:
    assert encode("") == ""
    assert decode("") == ""


def test_non_ascii_is_rejected() -> None:
    with pytest.raises(ValueError, match="ASCII"):
        encode("ї")


@pytest.mark.parametrize("bad", ["0101", "01" * 12 + "2" * 0 + "x" * 24])
def test_decode_rejects_malformed_input(bad: str) -> None:
    with pytest.raises(ValueError):
        decode(bad)


# --------------------------------------------------------------------------- #
#  Властивості коду (3,1)
# --------------------------------------------------------------------------- #

def test_round_trip() -> None:
    for _ in range(500):
        text = _ascii(RNG.randrange(0, 30))
        assert decode(encode(text)) == text
        assert bits_to_text(text_to_bits(text)) == text


def test_any_single_flip_per_triple_is_corrected() -> None:
    """Будь-яке одне спотворення в кожній трійці виправляється."""
    for _ in range(300):
        text = _ascii(RNG.randrange(1, 20))
        bits = encode(text)
        positions = [t + RNG.randrange(3) for t in range(0, len(bits), 3)]
        assert decode(flip(bits, positions)) == text


def test_two_flips_in_a_triple_give_a_wrong_bit() -> None:
    """Межа можливостей: два спотворення в трійці — хибний біт без жодного сигналу."""
    bits = encode("A")
    for pair in ((0, 1), (0, 2), (1, 2)):
        assert decode(flip(bits, pair)) != "A"


@pytest.mark.parametrize("triple", ["".join(t) for t in product("01", repeat=3)])
def test_majority_vote(triple: str) -> None:
    assert majority(triple) == ("1" if triple.count("1") >= 2 else "0")


# --------------------------------------------------------------------------- #
#  Код (7,4)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("data", ["".join(d) for d in product("01", repeat=4)])
def test_hamming74_corrects_every_single_error(data: str) -> None:
    word = hamming74_encode_block(data)
    assert hamming74_decode_block(word) == data
    for i in range(7):
        assert hamming74_decode_block(flip(word, [i])) == data


def test_hamming74_minimum_distance_is_three() -> None:
    words = [hamming74_encode_block("".join(d)) for d in product("01", repeat=4)]
    distances = [sum(a != b for a, b in zip(u, v))
                 for i, u in enumerate(words) for v in words[i + 1:]]
    assert min(distances) == 3


def test_hamming74_round_trip() -> None:
    for _ in range(200):
        text = _ascii(RNG.randrange(0, 25))
        assert hamming74_decode(hamming74_encode(text)) == text


def test_repetition_is_hamming_3_1() -> None:
    """
    Код із задачі — це код Гемінга з r = 2: n = 3, k = 1. Два його кодові
    слова, 000 і 111, мають відстань 3, як і в усіх кодів Гемінга.
    """
    r = 2
    assert (2 ** r - 1, 2 ** r - 1 - r) == (3, 1)
    assert encode("\x00")[:3] == "000" and encode("\x7f")[3:6] == "111"


# --------------------------------------------------------------------------- #
#  Python-розв'язок для Codewars (той самий алгоритм, що й CodeWars.cs)
# --------------------------------------------------------------------------- #

def _load_python_solution():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "codewars_solution", ROOT / "solution" / "codewars_solution.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_python_codewars_solution(case: dict) -> None:
    """Python-файл для Codewars проходить приклади обох версій kata."""
    sol = _load_python_solution()
    fn = sol.encode if case["function"] == "Encode" else sol.decode
    assert fn(case["input"]) == case["expected"]


def test_python_solution_agrees_with_library_on_random_corruptions() -> None:
    sol = _load_python_solution()
    for _ in range(200):
        text = _ascii(RNG.randrange(1, 20))
        bits = flip(encode(text), [t + RNG.randrange(3) for t in range(0, 24 * len(text), 3)])
        assert sol.encode(text) == encode(text)
        assert sol.decode(bits) == decode(bits) == text
