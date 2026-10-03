"""
Точний аналіз надійності кодів — без симуляції.

Блок із n бітів має 2^n можливих шаблонів спотворень. У двійковому
симетричному каналі шаблон із w спотвореннями трапляється з імовірністю
p^w · (1 − p)^(n − w). Перебравши всі шаблони й декодувавши кожен,
отримуємо точні ймовірності залишкових помилок: для коду (3,1) це 8
шаблонів, для (7,4) — 128. Симуляція в експериментах потрібна лише як
незалежна перевірка цих чисел.

Для коду (3,1) результат має й замкнену форму: біт декодується хибно,
якщо спотворено щонайменше два з трьох повторів,

    P_b = 3p²(1 − p) + p³ = 3p² − 2p³.
"""

from __future__ import annotations

from itertools import product

from .codes import hamming74_decode_block, hamming74_encode_block, majority

__all__ = [
    "pattern_probability",
    "repetition_bit_error",
    "repetition_bit_error_exact",
    "hamming74_error_exact",
    "hamming74_bit_error",
    "HAMMING74_CROSSOVER",
    "char_error_uncoded",
    "char_error_repetition",
    "char_error_hamming74",
    "hamming_family",
    "triple_outcomes",
    "flips_to_change",
]


def pattern_probability(weight: int, n: int, p: float) -> float:
    """Імовірність конкретного шаблону з ``weight`` спотвореннями в блоці з n бітів."""
    return p ** weight * (1.0 - p) ** (n - weight)


# --------------------------------------------------------------------------- #
#  Код (3,1)
# --------------------------------------------------------------------------- #

def repetition_bit_error(p: float) -> float:
    """Замкнена формула: P_b = 3p² − 2p³."""
    return 3 * p ** 2 - 2 * p ** 3


def repetition_bit_error_exact(p: float) -> float:
    """Та сама ймовірність, але отримана перебором усіх 8 шаблонів."""
    total = 0.0
    for pattern in product((0, 1), repeat=3):
        for sent in "01":
            received = "".join(str(int(sent) ^ e) for e in pattern)
            if majority(received) != sent:
                total += 0.5 * pattern_probability(sum(pattern), 3, p)
    return total


def triple_outcomes() -> list[dict]:
    """
    Усі шаблони спотворень однієї трійки та результат декодування.

    Показує межу можливостей коду точно: 0 або 1 спотворення — біт
    відновлюється, 2 або 3 — декодер упевнено видає хибний біт і ніяк не
    сигналізує про проблему.
    """
    rows = []
    for pattern in product((0, 1), repeat=3):
        received = "".join(str(1 ^ e) for e in pattern)      # надіслано "111"
        rows.append({
            "pattern": "".join(map(str, pattern)),
            "flips": sum(pattern),
            "received": received,
            "decoded": majority(received),
            "correct": majority(received) == "1",
        })
    return rows


# --------------------------------------------------------------------------- #
#  Код (7,4)
# --------------------------------------------------------------------------- #

def hamming74_error_exact(p: float) -> dict:
    """
    Точні ймовірності для коду (7,4) перебором 16 слів × 128 шаблонів.

    Повертає частку хибних інформаційних бітів і ймовірність того, що
    хоча б один із чотирьох інформаційних бітів блоку хибний.
    """
    bit_errors = 0.0
    block_errors = 0.0
    for data in product("01", repeat=4):
        data = "".join(data)
        word = hamming74_encode_block(data)
        for pattern in product((0, 1), repeat=7):
            received = "".join(str(int(b) ^ e) for b, e in zip(word, pattern))
            decoded = hamming74_decode_block(received)
            wrong = sum(a != b for a, b in zip(decoded, data))
            prob = pattern_probability(sum(pattern), 7, p) / 16.0
            bit_errors += prob * wrong / 4.0
            block_errors += prob * (wrong > 0)
    return {"bit": bit_errors, "block": block_errors}


def hamming74_bit_error(p: float) -> float:
    """
    Замкнена форма частки хибних інформаційних бітів коду (7,4):

        P_b = p²(9 − 26p + 30p² − 12p³).

    Поліном отримано символьним підсумовуванням тих самих 16 × 128
    випадків, що й у :func:`hamming74_error_exact`, і збігається з ним.
    """
    return p ** 2 * (9 - 26 * p + 30 * p ** 2 - 12 * p ** 3)


#: Імовірність спотворення, за якої код (7,4) перестає зменшувати частку
#: хибних бітів: єдиний корінь рівняння P_b(p) = p на інтервалі (0; 1/2).
HAMMING74_CROSSOVER = (3 - 3 ** 0.5) / 6


# --------------------------------------------------------------------------- #
#  Помилки на рівні символу
# --------------------------------------------------------------------------- #

def char_error_uncoded(p: float) -> float:
    """Символ (8 бітів) без кодування хибний, якщо спотворено хоч один біт."""
    return 1.0 - (1.0 - p) ** 8


def char_error_repetition(p: float) -> float:
    """
    Для коду (3,1) кожен біт символу захищено окремою трійкою, тож вісім
    бітів декодуються незалежно: 1 − (1 − P_b)^8 — точна формула.
    """
    return 1.0 - (1.0 - repetition_bit_error(p)) ** 8


def char_error_hamming74(p: float) -> float:
    """Символ — це два незалежні блоки (7,4); біти в межах блоку залежні."""
    return 1.0 - (1.0 - hamming74_error_exact(p)["block"]) ** 2


# --------------------------------------------------------------------------- #
#  Сімейство кодів Гемінга
# --------------------------------------------------------------------------- #

def hamming_family(max_r: int = 7) -> list[dict]:
    """Параметри кодів Гемінга для r = 2..max_r: n = 2^r − 1, k = n − r."""
    rows = []
    for r in range(2, max_r + 1):
        n = 2 ** r - 1
        k = n - r
        rows.append({"r": r, "n": n, "k": k, "rate": k / n,
                     "overhead": n / k, "corrects": 1})
    return rows


# --------------------------------------------------------------------------- #
#  Навмисне втручання
# --------------------------------------------------------------------------- #

def flips_to_change(original: str, forged: str) -> int:
    """
    Скільки бітів каналу треба інвертувати, щоб після декодування коду (3,1)
    отримати інший текст тієї самої довжини.

    Для кожного інформаційного біта, що відрізняється, достатньо спотворити
    два з трьох повторів. Декодер при цьому не бачить нічого підозрілого:
    результат — коректне з його погляду повідомлення.
    """
    if len(original) != len(forged):
        raise ValueError("тексти мають бути однакової довжини")
    return 2 * sum(bin(ord(a) ^ ord(b)).count("1") for a, b in zip(original, forged))
