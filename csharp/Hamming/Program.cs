// Лабораторна робота №6 — «Захист даних»
// Codewars: Error correction #1 - Hamming Code
//
// Самоперевірка розв'язку, надісланого на платформу. Сам розв'язок
// (клас CodeWars) підключено з solution/CodeWars.cs без копіювання, тож
// тут перевіряється буквально той самий код.
//
// Запуск:
//   dotnet run --project csharp/Hamming -- selftest
//   dotnet run --project csharp/Hamming -- encode "текст"
//   dotnet run --project csharp/Hamming -- decode 000111...

using System;
using System.Linq;
using System.Text;

namespace Lab6.Hamming;

public static class Program
{
    /// <summary>Приклади з Codewars: (функція, вхід, очікуваний вихід).</summary>
    private static readonly (string Fn, string In, string Out)[] Cases =
    {
        ("Encode", "hey",
         "000111111000111000000000000111111000000111000111000111111111111000000111"),
        ("Decode", "100111111000111001000010000111111000000111001111000111110110111000010111",
         "hey"),
        ("Decode", "000111000111000111000001000000111111000000111111000111111111000000111011000111111111000111000000",
         "T3st"),
        ("Decode", "000111000111000111000010000000111111111111011111000111111111000000111111000111101111000111000000000000111000000000000111000000111000000111000111",
         "T?st!%"),
    };

    public static int Main(string[] args)
    {
        Console.OutputEncoding = new UTF8Encoding(false);
        if (args.Length == 0) return Usage();
        return args[0] switch
        {
            "selftest" => SelfTest(),
            "encode" when args.Length > 1 => Print(CodeWars.Encode(args[1])),
            "decode" when args.Length > 1 => Print(CodeWars.Decode(args[1])),
            _ => Usage(),
        };
    }

    private static int Print(string s)
    {
        Console.WriteLine(s);
        return 0;
    }

    private static int Usage()
    {
        Console.Error.WriteLine("вживання: selftest | encode <текст> | decode <біти>");
        return 2;
    }

    private static int SelfTest()
    {
        int failures = 0;

        // 1. Приклади платформи.
        foreach (var (fn, input, expected) in Cases)
        {
            string got = fn == "Encode" ? CodeWars.Encode(input) : CodeWars.Decode(input);
            bool ok = got == expected;
            failures += ok ? 0 : 1;
            Console.WriteLine($"[{(ok ? "OK" : "FAIL")}] {fn}({Preview(input)})");
        }

        // 2. Кодування з подальшим декодуванням повертає вихідний текст.
        var rnd = new Random(20261004);
        int roundTrips = 0;
        for (int i = 0; i < 2000; i++)
        {
            string text = RandomAscii(rnd, rnd.Next(0, 40));
            if (CodeWars.Decode(CodeWars.Encode(text)) == text) roundTrips++;
        }
        Console.WriteLine($"кодування й декодування: збіг {roundTrips} з 2000");
        failures += roundTrips == 2000 ? 0 : 1;

        // 3. Одне спотворення в кожній трійці виправляється завжди.
        int corrected = 0;
        for (int i = 0; i < 2000; i++)
        {
            string text = RandomAscii(rnd, rnd.Next(1, 30));
            char[] bits = CodeWars.Encode(text).ToCharArray();
            for (int t = 0; t < bits.Length; t += 3)
            {
                int k = t + rnd.Next(3);
                bits[k] = bits[k] == '0' ? '1' : '0';
            }
            if (CodeWars.Decode(new string(bits)) == text) corrected++;
        }
        Console.WriteLine($"по одному спотворенню в кожній трійці: виправлено {corrected} з 2000");
        failures += corrected == 2000 ? 0 : 1;

        // 4. Два спотворення в одній трійці дають хибний біт — межа можливостей коду.
        string sample = "A";
        char[] two = CodeWars.Encode(sample).ToCharArray();
        two[0] = two[0] == '0' ? '1' : '0';
        two[1] = two[1] == '0' ? '1' : '0';
        bool miscorrected = CodeWars.Decode(new string(two)) != sample;
        Console.WriteLine($"два спотворення в одній трійці дають хибний біт: {(miscorrected ? "так" : "ні")}");
        failures += miscorrected ? 0 : 1;

        Console.WriteLine(failures == 0 ? "пройдено все" : $"FAIL: {failures}");
        return failures == 0 ? 0 : 1;
    }

    private static string RandomAscii(Random rnd, int length) =>
        new string(Enumerable.Range(0, length).Select(_ => (char)rnd.Next(32, 127)).ToArray());

    private static string Preview(string s) => s.Length <= 24 ? s : s[..21] + "...";
}
