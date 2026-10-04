"""Точні ймовірності, канал, перемежування та навмисне втручання."""

from __future__ import annotations

import random

import pytest

from hamming import (
    HAMMING74_CROSSOVER,
    hamming74_bit_error,
    bsc,
    burst,
    char_error_hamming74,
    char_error_repetition,
    char_error_uncoded,
    decode,
    deinterleave,
    encode,
    flip,
    flips_to_change,
    hamming74_error_exact,
    hamming_family,
    interleave,
    repetition_bit_error,
    repetition_bit_error_exact,
    triple_outcomes,
)


@pytest.mark.parametrize("p", [0.0, 0.001, 0.01, 0.1, 0.25, 0.4, 0.5, 0.7, 1.0])
def test_formula_matches_exhaustive_enumeration(p: float) -> None:
    """Замкнена формула 3p² − 2p³ збігається з перебором усіх шаблонів."""
    assert repetition_bit_error(p) == pytest.approx(repetition_bit_error_exact(p), abs=1e-12)


@pytest.mark.parametrize("p", [0.001, 0.01, 0.1, 0.3, 0.49])
def test_repetition_helps_below_one_half(p: float) -> None:
    assert repetition_bit_error(p) < p


def test_repetition_is_useless_at_one_half_and_harmful_above() -> None:
    assert repetition_bit_error(0.5) == pytest.approx(0.5)
    assert repetition_bit_error(0.7) > 0.7


def test_hamming74_can_be_worse_than_no_coding() -> None:
    """
    Код (7,4) допомагає лише за досить малого p: за p = 0,3 частка хибних
    інформаційних бітів більша, ніж без кодування.
    """
    assert hamming74_error_exact(0.01)["bit"] < 0.01
    assert hamming74_error_exact(0.3)["bit"] > 0.3


def test_hamming74_block_error_matches_two_or_more_flips() -> None:
    """
    Блок (7,4) декодується правильно, якщо спотворень не більше одного.
    За двох і більше спотворень синдром указує не туди, і принаймні один
    інформаційний біт стає хибним. Тож ймовірність хибного блоку —
    P(≥ 2 спотворення з 7).
    """
    p = 0.05
    at_least_two = 1 - (1 - p) ** 7 - 7 * p * (1 - p) ** 6
    assert hamming74_error_exact(p)["block"] == pytest.approx(at_least_two, rel=1e-12)


def test_char_error_rates_are_ordered_at_small_p() -> None:
    p = 0.01
    assert char_error_repetition(p) < char_error_hamming74(p) < char_error_uncoded(p)


def test_simulation_agrees_with_theory() -> None:
    """Незалежна перевірка формули симуляцією каналу."""
    rng = random.Random(7)
    p, n = 0.1, 60000
    sent = "1" * 3 * n
    received = bsc(sent, p, rng)
    wrong = sum(received[i:i + 3].count("1") < 2 for i in range(0, len(received), 3))
    assert wrong / n == pytest.approx(repetition_bit_error(p), abs=0.003)


def test_triple_outcomes_show_exact_capability() -> None:
    rows = triple_outcomes()
    assert len(rows) == 8
    assert all(r["correct"] == (r["flips"] <= 1) for r in rows)


def test_hamming_family_parameters() -> None:
    rows = hamming_family(5)
    assert [(r["n"], r["k"]) for r in rows] == [(3, 1), (7, 4), (15, 11), (31, 26)]
    assert rows[0]["rate"] == pytest.approx(1 / 3)


# --------------------------------------------------------------------------- #
#  Пакети спотворень і перемежування
# --------------------------------------------------------------------------- #

def test_burst_of_two_inside_a_triple_breaks_the_code() -> None:
    bits = encode("Hamming")
    assert decode(burst(bits, 2, 0)) != "Hamming"


def test_interleaving_spreads_a_burst_across_triples() -> None:
    """
    Таблиця перемежування має по рядку на кожну трійку, тож у каналі йдуть
    спершу перші біти всіх трійок, потім другі, потім треті. Пакет довжиною
    не більше за кількість трійок D зачіпає щоразу різні трійки й після
    зворотного перетворення стає «одним спотворенням на трійку».
    """
    text = "Hamming!"
    bits = encode(text)
    depth = len(bits) // 3                       # D = 64 трійки
    sent = interleave(bits, depth)
    for length in (2, 3, depth):
        for start in range(0, len(sent) - length + 1, 7):
            received = burst(sent, length, start)
            assert decode(deinterleave(received, depth)) == text
    # Пакет, довший за D, неминуче вдруге зачепить якусь трійку.
    assert any(decode(deinterleave(burst(sent, depth + 1, s), depth)) != text
               for s in range(0, len(sent) - depth))


def test_interleave_round_trip() -> None:
    s = "".join(random.Random(3).choice("01") for _ in range(240))
    for depth in (1, 2, 3, 8, 24, 240):
        assert deinterleave(interleave(s, depth), depth) == s


def test_channel_rejects_bad_probability() -> None:
    with pytest.raises(ValueError):
        bsc("0101", 1.5, random.Random(0))


# --------------------------------------------------------------------------- #
#  Навмисне втручання
# --------------------------------------------------------------------------- #

def test_two_flips_turn_hey_into_hex_silently() -> None:
    """
    Код виправляє випадкові помилки, але не захищає від підміни: 'y' і 'x'
    відрізняються одним бітом, тож двох інвертованих бітів досить, щоб
    декодер видав інший осмислений текст і ніяк про це не сигналізував.
    """
    bits = encode("hey")
    assert flips_to_change("hey", "hex") == 2
    last_bit_triple = len(bits) - 3
    forged = flip(bits, [last_bit_triple, last_bit_triple + 1])
    assert decode(forged) == "hex"


def test_flips_to_change_requires_equal_length() -> None:
    with pytest.raises(ValueError):
        flips_to_change("ab", "abc")


@pytest.mark.parametrize("p", [0.0, 0.01, 0.1, 0.2113, 0.3, 0.5, 0.8, 1.0])
def test_hamming74_closed_form_matches_enumeration(p: float) -> None:
    """Поліном p²(9 − 26p + 30p² − 12p³) збігається з повним перебором."""
    assert hamming74_bit_error(p) == pytest.approx(hamming74_error_exact(p)["bit"], abs=1e-12)


def test_hamming74_crossover_is_three_minus_root_three_over_six() -> None:
    """
    Код (7,4) допомагає лише за p < (3 − √3)/6 ≈ 0,2113: у цій точці
    частка хибних бітів після декодування дорівнює p, а праворуч від неї —
    більша за p.
    """
    c = HAMMING74_CROSSOVER
    assert c == pytest.approx(0.2113248654, abs=1e-10)
    assert hamming74_bit_error(c) == pytest.approx(c, abs=1e-12)
    assert hamming74_bit_error(c - 0.01) < c - 0.01
    assert hamming74_bit_error(c + 0.01) > c + 0.01


def test_hamming74_reduces_character_errors_on_whole_interval() -> None:
    """
    Поріг (3 − √3)/6 стосується лише частки хибних інформаційних бітів.
    Частку хибних символів код (7,4) зменшує на всьому інтервалі (0; 0,5):
    за невдалого декодування помилки скупчуються в одному блоці.
    """
    grid = [i / 1000 for i in range(1, 500)]
    assert all(char_error_hamming74(p) < char_error_uncoded(p) for p in grid)
    p = 0.25
    assert hamming74_bit_error(p) > p                          # біти — гірше
    assert char_error_hamming74(p) < char_error_uncoded(p)     # символи — краще
