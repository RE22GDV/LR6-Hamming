"""
Codewars - "Error correction #1 - Hamming Code" (6 kyu)
https://www.codewars.com/kata/5ef9ca8b76be6d001d5e1c3e

Python version of the same solution as CodeWars.cs, kept for comparison.

Every bit of the 8-bit ASCII code is sent three times; the receiver takes a
majority vote in each triple, so any single flip inside a triple is
corrected. This is exactly the Hamming code with r = 2: n = 3, k = 1.
"""


def encode(string):
    # format(code, "08b") pads with leading zeros to exactly 8 digits:
    # ord("h") = 104 -> "01101000" (bin(104) would give "0b1101000").
    return "".join(bit * 3 for char in string for bit in format(ord(char), "08b"))


def decode(bits):
    # Majority vote in every triple: two or three ones mean the sent bit was 1.
    data = "".join("1" if bits[i:i + 3].count("1") >= 2 else "0"
                   for i in range(0, len(bits), 3))
    # Every 8 corrected bits form one ASCII code.
    return "".join(chr(int(data[i:i + 8], 2)) for i in range(0, len(data), 8))
