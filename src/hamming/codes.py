"""
Два коди Гемінга: (3,1) із задачі та класичний (7,4) для порівняння.

Коди Гемінга мають параметри n = 2^r − 1, k = n − r, де r — кількість
перевірних бітів. Найменший випадок r = 2 дає код (3,1): одне
інформаційне число та два перевірні, тобто біт просто повторюється тричі.
Отже, «спрощений алгоритм» із задачі — це не наближення до коду Гемінга,
а точно код Гемінга (3,1), і декодування більшістю голосів для нього
збігається із синдромним декодуванням.

Обидва коди мають мінімальну відстань 3: виправляють будь-яку одну помилку
в блоці, але не дві. Відрізняються вони швидкістю (часткою корисних бітів):
1/3 проти 4/7.

Біти подано рядками з символів '0' і '1' — так само, як у задачі.
"""

from __future__ import annotations

__all__ = [
    "BITS_PER_CHAR",
    "text_to_bits",
    "bits_to_text",
    "encode",
    "decode",
    "majority",
    "hamming74_encode_block",
    "hamming74_decode_block",
    "hamming74_encode",
    "hamming74_decode",
]

BITS_PER_CHAR = 8


# --------------------------------------------------------------------------- #
#  Текст <-> біти
# --------------------------------------------------------------------------- #

def text_to_bits(text: str) -> str:
    """
    Кожен символ — 8 двійкових цифр його ASCII-коду з провідними нулями.

    ``format(104, "08b")`` дає ``"01101000"``; без доповнення нулями
    (``bin(104)`` -> ``"0b1101000"``) межі між символами зсунулися б.
    """
    for ch in text:
        if ord(ch) > 0x7F:
            raise ValueError("символ %r не належить до ASCII" % ch)
    return "".join(format(ord(ch), "08b") for ch in text)


def bits_to_text(bits: str) -> str:
    """Групи по 8 бітів -> символи ASCII."""
    _check_bits(bits, BITS_PER_CHAR)
    return "".join(chr(int(bits[i:i + 8], 2)) for i in range(0, len(bits), 8))


def _check_bits(bits: str, multiple: int) -> None:
    if any(b not in "01" for b in bits):
        raise ValueError("очікуються лише символи '0' і '1'")
    if len(bits) % multiple:
        raise ValueError("довжина %d не кратна %d" % (len(bits), multiple))


# --------------------------------------------------------------------------- #
#  Код Гемінга (3,1) — розв'язок задачі
# --------------------------------------------------------------------------- #

def encode(text: str) -> str:
    """Кодування з задачі: кожен біт ASCII-коду повторюється тричі."""
    return "".join(bit * 3 for bit in text_to_bits(text))


def majority(triple: str) -> str:
    """Біт, що трапляється в трійці щонайменше двічі."""
    return "1" if triple.count("1") >= 2 else "0"


def decode(bits: str) -> str:
    """
    Декодування з задачі: голосування більшістю в кожній трійці.

    Довжина входу кратна 24 (8 бітів × 3 повтори), тож результат завжди
    ділиться на цілі символи.
    """
    _check_bits(bits, 3 * BITS_PER_CHAR)
    data = "".join(majority(bits[i:i + 3]) for i in range(0, len(bits), 3))
    return bits_to_text(data)


# --------------------------------------------------------------------------- #
#  Класичний код Гемінга (7,4)
# --------------------------------------------------------------------------- #
#  Позиції 1..7; перевірні біти стоять на позиціях 1, 2, 4 (степені двійки),
#  інформаційні — на 3, 5, 6, 7. Синдром — це XOR номерів позицій, на яких
#  стоїть одиниця; для правильного слова він дорівнює нулю, а для слова з
#  однією помилкою — номеру спотвореної позиції.

_DATA_POS = (3, 5, 6, 7)


def hamming74_encode_block(data: str) -> str:
    """Чотири інформаційні біти -> кодове слово з семи бітів."""
    if len(data) != 4 or any(b not in "01" for b in data):
        raise ValueError("потрібно рівно 4 біти")
    word = [0] * 8                                  # індекс 0 не використовується
    for pos, bit in zip(_DATA_POS, data):
        word[pos] = int(bit)
    for p in (1, 2, 4):
        word[p] = sum(word[i] for i in range(1, 8) if i & p and i != p) % 2
    return "".join(str(b) for b in word[1:])


def _syndrome(word: str) -> int:
    s = 0
    for pos, bit in enumerate(word, 1):
        if bit == "1":
            s ^= pos
    return s


def hamming74_decode_block(word: str) -> str:
    """Сім бітів -> чотири інформаційні; одну помилку виправляє синдром."""
    if len(word) != 7 or any(b not in "01" for b in word):
        raise ValueError("потрібно рівно 7 бітів")
    bits = list(word)
    s = _syndrome(word)
    if s:
        bits[s - 1] = "1" if bits[s - 1] == "0" else "0"
    return "".join(bits[p - 1] for p in _DATA_POS)


def hamming74_encode(text: str) -> str:
    """Текст -> послідовність кодових слів (7,4), по два на символ."""
    data = text_to_bits(text)
    return "".join(hamming74_encode_block(data[i:i + 4]) for i in range(0, len(data), 4))


def hamming74_decode(bits: str) -> str:
    """Послідовність кодових слів (7,4) -> текст."""
    _check_bits(bits, 14)
    data = "".join(hamming74_decode_block(bits[i:i + 7]) for i in range(0, len(bits), 7))
    return bits_to_text(data)
