// Codewars - "Error correction #1 - Hamming Code" (6 kyu)
// https://www.codewars.com/kata/5ef9ca8b76be6d001d5e1c3e
//
// Every bit of the 8-bit ASCII code is sent three times. The receiver takes
// a majority vote in each triple, so any single flip inside a triple is
// corrected. This is exactly the Hamming code with r = 2 parity bits:
// n = 2^r - 1 = 3, k = n - r = 1, minimum distance 3, corrects 1 error.

using System;
using System.Text;

public class CodeWars
{
    public static string Encode(string text)
    {
        var bits = new StringBuilder(text.Length * 24);
        foreach (char symbol in text)
        {
            // Convert.ToString(value, 2) drops leading zeros ('h' -> "1101000"),
            // so the code is padded on the left to exactly 8 binary digits.
            string octet = Convert.ToString((int)symbol, 2).PadLeft(8, '0');
            foreach (char bit in octet)
            {
                bits.Append(bit, 3);      // triple every bit: 0 -> 000, 1 -> 111
            }
        }
        return bits.ToString();
    }

    public static string Decode(string bits)
    {
        var text = new StringBuilder(bits.Length / 24);
        for (int start = 0; start < bits.Length; start += 24)   // 24 = 8 bits * 3
        {
            int value = 0;
            for (int j = 0; j < 8; j++)
            {
                int k = start + 3 * j;
                int ones = (bits[k] - '0') + (bits[k + 1] - '0') + (bits[k + 2] - '0');
                // Majority vote: two or three ones mean the sent bit was 1.
                value = (value << 1) | (ones >= 2 ? 1 : 0);
            }
            text.Append((char)value);
        }
        return text.ToString();
    }
}
