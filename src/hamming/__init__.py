"""
Лабораторна робота №6 — «Error correction #1 - Hamming Code» (Codewars).

Код Гемінга (3,1) — кожен біт повторюється тричі, декодування більшістю
голосів — і порівняння з класичним кодом Гемінга (7,4).

* :mod:`hamming.codes`    — кодування й декодування обох кодів;
* :mod:`hamming.channel`  — модель шуму, пакети спотворень, перемежування;
* :mod:`hamming.analysis` — точні ймовірності помилок перебором шаблонів.
"""

from .analysis import (
    HAMMING74_CROSSOVER,
    hamming74_bit_error,
    char_error_hamming74,
    char_error_repetition,
    char_error_uncoded,
    flips_to_change,
    hamming74_error_exact,
    hamming_family,
    pattern_probability,
    repetition_bit_error,
    repetition_bit_error_exact,
    triple_outcomes,
)
from .channel import bsc, burst, deinterleave, flip, interleave
from .codes import (
    BITS_PER_CHAR,
    bits_to_text,
    decode,
    encode,
    hamming74_decode,
    hamming74_decode_block,
    hamming74_encode,
    hamming74_encode_block,
    majority,
    text_to_bits,
)

__version__ = "1.0.0"
