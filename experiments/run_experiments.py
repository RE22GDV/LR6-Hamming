"""
Обчислювальні експерименти лабораторної роботи.

    python experiments/run_experiments.py            # усі експерименти
    python experiments/run_experiments.py --quick    # скорочений прогін

Результати:
    docs/results/experiments.json   — усі виміряні величини
    docs/results/summary.md         — зведена таблиця
    docs/figures/*.png              — рисунки (+ pdf/ — версії без заголовків)

Теоретичні криві обчислюються перебором усіх шаблонів спотворень, а
симуляція з фіксованим зерном слугує незалежною перевіркою, тож прогін
відтворюється число в число.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402

from hamming import (  # noqa: E402
    HAMMING74_CROSSOVER,
    burst,
    char_error_hamming74,
    char_error_repetition,
    char_error_uncoded,
    decode,
    deinterleave,
    encode,
    flips_to_change,
    hamming74_decode_block,
    hamming74_encode_block,
    hamming74_error_exact,
    hamming_family,
    interleave,
    repetition_bit_error,
    triple_outcomes,
)

# --------------------------------------------------------------------------- #
#  Оформлення: категорійні слоти 1–3 (синій, помаранчевий, бірюзовий)
# --------------------------------------------------------------------------- #

SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e3e2de"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "axes.titlecolor": INK,
    "axes.titlesize": 12, "axes.titleweight": "semibold", "axes.labelsize": 9.5,
    "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "xtick.color": INK_2, "ytick.color": INK_2, "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5, "legend.frameon": False, "legend.fontsize": 9,
    "lines.linewidth": 2.0, "font.size": 10,
})

FIG = ROOT / "docs" / "figures"
RES = ROOT / "docs" / "results"
CASES = json.loads((ROOT / "tests" / "codewars_cases.json").read_text(encoding="utf-8"))["cases"]


def _n(v: float, d: int = 2) -> str:
    return ("%.*f" % (d, v)).replace(".", ",")


def _finish(ax, note: str | None = None) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    if note:
        ax.text(0.995, -0.17, note, transform=ax.transAxes, ha="right", va="top",
                fontsize=7.5, color=INK_2)


def save(fig, name: str) -> str:
    """Із заголовком — для README; без заголовка (pdf/) — для звіту."""
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name, dpi=200, bbox_inches="tight")
    (FIG / "pdf").mkdir(parents=True, exist_ok=True)
    for ax in fig.axes:
        ax.set_title("")
    if fig._suptitle is not None:
        fig.suptitle("")
    fig.savefig(FIG / "pdf" / name, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("    рисунок -> docs/figures/%s (+ pdf/)" % name)
    return "docs/figures/" + name


# --------------------------------------------------------------------------- #
#  Допоміжні симуляції на рівні бітів
# --------------------------------------------------------------------------- #

def _flip_bits(bits: list[int], p: float, rng: random.Random) -> list[int]:
    return [b ^ (rng.random() < p) for b in bits]


def simulate_repetition(p: float, n_bits: int, rng: random.Random) -> float:
    data = [rng.getrandbits(1) for _ in range(n_bits)]
    sent = [b for b in data for _ in range(3)]
    got = _flip_bits(sent, p, rng)
    wrong = sum((got[3 * i] + got[3 * i + 1] + got[3 * i + 2] >= 2) != data[i]
                for i in range(n_bits))
    return wrong / n_bits


def simulate_hamming74(p: float, n_blocks: int, rng: random.Random) -> float:
    wrong = 0
    for _ in range(n_blocks):
        data = "".join(rng.choice("01") for _ in range(4))
        word = [int(b) for b in hamming74_encode_block(data)]
        got = "".join(str(b) for b in _flip_bits(word, p, rng))
        wrong += sum(a != b for a, b in zip(hamming74_decode_block(got), data))
    return wrong / (4 * n_blocks)


def crossover_hamming74() -> float:
    """p, за якого код (7,4) перестає зменшувати частку хибних бітів."""
    lo, hi = 0.01, 0.4
    for _ in range(60):
        mid = (lo + hi) / 2
        if hamming74_error_exact(mid)["bit"] < mid:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# --------------------------------------------------------------------------- #
#  Експеримент 1 — залишкова частка хибних бітів
# --------------------------------------------------------------------------- #

def exp_bit_error(rng: random.Random, quick: bool) -> dict:
    print("[1] Залишкова частка хибних бітів")
    grid = [10 ** (-3 + 2.7 * i / 59) for i in range(60)]             # 0,001 .. ~0,5
    theory = {
        "uncoded": grid,
        "rep": [repetition_bit_error(p) for p in grid],
        "h74": [hamming74_error_exact(p)["bit"] for p in grid],
    }
    sim_p = [0.02, 0.05, 0.1, 0.2, 0.3, 0.4]
    n_bits = 40_000 if quick else 200_000
    sim = {
        "rep": [simulate_repetition(p, n_bits, rng) for p in sim_p],
        "h74": [simulate_hamming74(p, n_bits // 4, rng) for p in sim_p],
    }
    cross = crossover_hamming74()

    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    ax.loglog(grid, theory["uncoded"], color=INK_2, linestyle="--", linewidth=1.4,
              label="без кодування")
    ax.loglog(grid, theory["rep"], color=S1, label="Гемінг (3,1), швидкість 1/3")
    ax.loglog(grid, theory["h74"], color=S2, label="Гемінг (7,4), швидкість 4/7")
    ax.loglog(sim_p, [max(v, 1e-9) for v in sim["rep"]], "o", color=S1,
              markerfacecolor=SURFACE, markeredgewidth=1.6, markersize=6)
    ax.loglog(sim_p, sim["h74"], "s", color=S2, markerfacecolor=SURFACE,
              markeredgewidth=1.6, markersize=6)
    ax.axvline(cross, color=S2, linestyle=":", linewidth=1.2)
    ax.text(cross * 1.06, 2e-6, "(7,4) перестає\nдопомагати:\np* = (3 − √3)/6\n≈ %s" % _n(cross, 4),
            fontsize=8, color=S2, va="bottom")
    ax.set_xlabel("імовірність спотворення біта в каналі, p")
    ax.set_ylabel("частка хибних бітів після декодування")
    ax.set_ylim(1e-6, 1)
    ax.legend(loc="upper left")
    ax.set_title("Рис. 1. Скільки помилок лишається після декодування")
    _finish(ax, "лінії — точний перебір шаблонів; маркери — симуляція, %s бітів на точку"
            % "{:,}".format(n_bits).replace(",", " "))
    path = save(fig, "fig1_bit_error.png")

    for p, r, h in zip(sim_p, sim["rep"], sim["h74"]):
        print("    p=%.2f  (3,1) сим %.5f / теорія %.5f   (7,4) сим %.5f / теорія %.5f"
              % (p, r, repetition_bit_error(p), h, hamming74_error_exact(p)["bit"]))
    print("    (7,4) перестає допомагати за p ≈ %.4f" % cross)
    return {
        "figure": path, "sim_bits": n_bits, "sim_p": sim_p, "sim": sim,
        "theory_at_sim_p": {
            "rep": [repetition_bit_error(p) for p in sim_p],
            "h74": [hamming74_error_exact(p)["bit"] for p in sim_p],
        },
        "h74_crossover_p": cross,
        "h74_crossover_closed_form": HAMMING74_CROSSOVER,
        "table_p": [0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5],
        "table": [{"p": p, "uncoded": p, "rep": repetition_bit_error(p),
                   "h74": hamming74_error_exact(p)["bit"]}
                  for p in (0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5)],
    }


# --------------------------------------------------------------------------- #
#  Експеримент 2 — помилки на рівні символу
# --------------------------------------------------------------------------- #

def exp_char_error() -> dict:
    print("[2] Частка хибних символів")
    grid = [i / 200 for i in range(1, 101)]                          # 0,005 .. 0,5
    unc = [char_error_uncoded(p) for p in grid]
    rep = [char_error_repetition(p) for p in grid]
    h74 = [char_error_hamming74(p) for p in grid]

    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    ax.plot(grid, [100 * v for v in unc], color=INK_2, linestyle="--", linewidth=1.4,
            label="без кодування")
    ax.plot(grid, [100 * v for v in rep], color=S1, label="Гемінг (3,1)")
    ax.plot(grid, [100 * v for v in h74], color=S2, label="Гемінг (7,4)")
    ax.set_xlabel("імовірність спотворення біта в каналі, p")
    ax.set_ylabel("частка хибних символів")
    ax.yaxis.set_major_formatter(PercentFormatter())
    ax.set_xlim(0, 0.5)
    ax.set_ylim(0, 102)
    ax.legend(loc="lower right")
    ax.set_title("Рис. 2. Частка хибних символів (8 бітів) після декодування")
    _finish(ax, "точні формули: символ хибний, якщо хибний хоча б один із восьми бітів")
    path = save(fig, "fig2_char_error.png")

    points = [0.01, 0.05, 0.1]
    rows = [{"p": p, "uncoded": char_error_uncoded(p), "rep": char_error_repetition(p),
             "h74": char_error_hamming74(p)} for p in points]
    for r in rows:
        print("    p=%.2f  без коду %.4f   (3,1) %.5f   (7,4) %.5f"
              % (r["p"], r["uncoded"], r["rep"], r["h74"]))
    return {"figure": path, "rows": rows}


# --------------------------------------------------------------------------- #
#  Експеримент 3 — сімейство кодів Гемінга: швидкість проти надійності
# --------------------------------------------------------------------------- #

def exp_family() -> dict:
    print("[3] Сімейство кодів Гемінга")
    p = 0.01
    rows = []
    for row in hamming_family(7):
        n = row["n"]
        fail = 1 - (1 - p) ** n - n * p * (1 - p) ** (n - 1)
        rows.append({**row, "block_fail": fail, "p": p})

    fig, ax1 = plt.subplots(figsize=(9.2, 4.2))
    labels = ["(%d,%d)" % (r["n"], r["k"]) for r in rows]
    x = range(len(rows))
    ax1.bar(x, [100 * r["rate"] for r in rows], color=S1, width=0.6, zorder=3,
            label="швидкість k/n")
    ax1.set_xticks(list(x), labels)
    ax1.set_ylabel("частка корисних бітів")
    ax1.yaxis.set_major_formatter(PercentFormatter())
    ax1.set_ylim(0, 110)
    for xi, r in zip(x, rows):
        ax1.annotate("%s %%" % _n(100 * r["rate"], 0), xy=(xi, 100 * r["rate"]),
                     xytext=(0, 4), textcoords="offset points", ha="center", fontsize=8.5)
        ax1.annotate("збій блоку\n%s %%" % _n(100 * r["block_fail"], 2),
                     xy=(xi, 6), ha="center", fontsize=7.5, color=SURFACE)
    ax1.set_xlabel("код Гемінга (n, k); перший — код із задачі")
    ax1.set_title("Рис. 3. Довші коди Гемінга економніші, але частіше дають збій блоку")
    _finish(ax1, "збій блоку — імовірність двох і більше спотворень у блоці за p = %s"
            % _n(p, 2))
    path = save(fig, "fig3_family.png")
    for r in rows:
        print("    (%3d,%3d)  швидкість %.3f  збій блоку %.5f" % (r["n"], r["k"], r["rate"], r["block_fail"]))
    return {"figure": path, "p": p, "rows": rows}


# --------------------------------------------------------------------------- #
#  Експеримент 4 — пакети спотворень і перемежування
# --------------------------------------------------------------------------- #

def exp_burst() -> dict:
    print("[4] Пакети спотворень і перемежування")
    text = "Error correction!"                           # 17 символів, 408 бітів
    bits = encode(text)
    depth = len(bits) // 3
    sent_il = interleave(bits, depth)
    lengths = list(range(1, 9))
    plain, inter = [], []
    for b in lengths:
        starts = range(0, len(bits) - b + 1)
        ok_plain = sum(decode(burst(bits, b, s)) == text for s in starts)
        ok_inter = sum(decode(deinterleave(burst(sent_il, b, s), depth)) == text for s in starts)
        plain.append(100.0 * ok_plain / len(starts))
        inter.append(100.0 * ok_inter / len(starts))

    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    w = 0.38
    ax.bar([l - w / 2 for l in lengths], plain, width=w, color=INK_2, zorder=3,
           label="без перемежування")
    ax.bar([l + w / 2 for l in lengths], inter, width=w, color=S3, zorder=3,
           label="з перемежуванням")
    ax.set_xticks(lengths)
    ax.set_xlabel("довжина пакета спотворень, бітів поспіль")
    ax.set_ylabel("частка правильно відновлених повідомлень")
    ax.yaxis.set_major_formatter(PercentFormatter())
    ax.set_ylim(0, 112)
    ax.legend(loc="upper right")
    ax.set_title("Рис. 4. Перемежування розносить пакет спотворень по різних трійках")
    _finish(ax, "повідомлення з %d символів (%d бітів), глибина перемежування %d; "
                "перебрано всі можливі початки пакета" % (len(text), len(bits), depth))
    path = save(fig, "fig4_burst.png")
    for b, a, c in zip(lengths, plain, inter):
        print("    пакет %d: без %.1f %%  з перемежуванням %.1f %%" % (b, a, c))
    return {"figure": path, "text": text, "bits": len(bits), "depth": depth,
            "lengths": lengths, "plain_percent": plain, "interleaved_percent": inter}


# --------------------------------------------------------------------------- #
#  Експеримент 5 — навмисна підміна
# --------------------------------------------------------------------------- #

def exp_forgery() -> dict:
    print("[5] Навмисна підміна")
    pairs = [("hey", "hex"), ("pay 100", "pay 900"), ("YES", "NO!"), ("attack at 9", "attack at 1")]
    rows = []
    for a, b in pairs:
        need = flips_to_change(a, b)
        total = 24 * len(a)
        rows.append({"original": a, "forged": b, "flips": need, "bits": total,
                     "percent": 100.0 * need / total})
        print("    %-12s -> %-12s  інвертувати %2d бітів із %3d (%.2f %%)"
              % (a, b, need, total, 100.0 * need / total))
    outcomes = triple_outcomes()
    return {"rows": rows, "triple_outcomes": outcomes}


# --------------------------------------------------------------------------- #
#  Експеримент 6 — розподіл спотворень у прикладах платформи
# --------------------------------------------------------------------------- #

def exp_platform() -> dict:
    print("[6] Спотворення в прикладах платформи")
    variant = {"both": "C#, Python", "csharp": "C#", "python": "Python"}
    decode_cases = [c for c in CASES if c["function"] == "Decode"]
    rows = []
    for c in decode_cases:
        rows.append({"text": c["expected"], "bits": len(c["input"]),
                     "flipped": c["flipped_count"],
                     "percent": 100.0 * c["flipped_count"] / len(c["input"]),
                     "kata_language": c.get("kata_language", "csharp")})

    fig, axes = plt.subplots(len(rows), 1, figsize=(9.6, 0.62 * len(rows) + 1.0), sharex=False)
    for ax, c, r in zip(axes, decode_cases, rows):
        n = len(c["input"])
        ax.barh([0], [n], color=GRID, height=0.6)
        for i in c["flipped_bits"]:
            ax.barh([0], [max(n / 300, 1)], left=[i], color=S2, height=0.6)
        ax.set_xlim(0, n)
        ax.set_yticks([])
        ax.grid(False)
        ax.text(-0.01, 0.5, "«%s» · %s" % (r["text"] if len(r["text"]) <= 10 else r["text"][:9] + "…",
                                          variant[r["kata_language"]]),
                transform=ax.transAxes, ha="right", va="center", fontsize=8.5, color=INK)
        ax.text(1.01, 0.5, "%d із %d (%s %%)" % (r["flipped"], n, _n(r["percent"], 1)),
                transform=ax.transAxes, ha="left", va="center", fontsize=8, color=INK_2)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
    axes[-1].set_xlabel("позиція біта у вхідному рядку")
    fig.suptitle("Рис. 5. Спотворені біти в прикладах платформи: щонайбільше один на трійку",
                 fontsize=12, fontweight="semibold", color=INK)
    fig.tight_layout()
    path = save(fig, "fig5_platform.png")
    return {"figure": path, "rows": rows}


# --------------------------------------------------------------------------- #

def write_summary(results: dict) -> None:
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "experiments.json").write_text(json.dumps(results, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    be = results["bit_error"]
    lines = ["# Зведені результати експериментів", "",
             "Згенеровано автоматично: `python experiments/run_experiments.py`", "",
             "## Частка хибних бітів після декодування", "",
             "| p | без кодування | Гемінг (3,1) | Гемінг (7,4) |", "|---:|---:|---:|---:|"]
    for r in be["table"]:
        lines.append("| %.3f | %.6f | %.6f | %.6f |" % (r["p"], r["uncoded"], r["rep"], r["h74"]))
    lines += ["", "Код (7,4) перестає зменшувати частку хибних бітів за p ≈ %.4f." % be["h74_crossover_p"],
              "", "## Навмисна підміна", "", "| Оригінал | Підробка | Інвертувати бітів | Із |",
              "|---|---|---:|---:|"]
    for r in results["forgery"]["rows"]:
        lines.append("| %s | %s | %d | %d |" % (r["original"], r["forged"], r["flips"], r["bits"]))
    (RES / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n    зведення -> docs/results/summary.md")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    t0 = time.perf_counter()
    seed = 20261004
    results = {
        "meta": {"seed": seed, "quick": args.quick},
        "bit_error": exp_bit_error(random.Random(seed), args.quick),
        "char_error": exp_char_error(),
        "family": exp_family(),
        "burst": exp_burst(),
        "forgery": exp_forgery(),
        "platform": exp_platform(),
    }
    results["meta"]["total_seconds"] = time.perf_counter() - t0
    write_summary(results)
    print("Готово за %.1f с" % results["meta"]["total_seconds"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
