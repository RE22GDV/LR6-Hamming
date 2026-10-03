"""
Перехресна перевірка: розв'язок на C# (той самий файл, що й на Codewars)
проти незалежної реалізації на Python.

Тести автоматично пропускаються, якщо .NET SDK не встановлено.
"""

from __future__ import annotations

import json
import random
import shutil
import subprocess
from pathlib import Path

import pytest

from hamming import decode, encode, flip

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "csharp" / "Hamming"
CASES = json.loads((ROOT / "tests" / "codewars_cases.json").read_text(encoding="utf-8"))["cases"]

dotnet_required = pytest.mark.skipif(shutil.which("dotnet") is None,
                                     reason=".NET SDK не встановлено")


def _run(args: list[str]) -> str:
    proc = subprocess.run(["dotnet", "run", "--project", str(PROJECT), "--"] + args,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=300)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return proc.stdout.rstrip("\n")


@dotnet_required
def test_csharp_selftest_passes() -> None:
    out = _run(["selftest"])
    assert "пройдено все" in out and "FAIL" not in out


@dotnet_required
@pytest.mark.parametrize("case", CASES, ids=[c["function"] + str(i) for i, c in enumerate(CASES)])
def test_csharp_reproduces_codewars_cases(case: dict) -> None:
    mode = "encode" if case["function"] == "Encode" else "decode"
    assert _run([mode, case["input"]]) == case["expected"]


@dotnet_required
def test_both_implementations_agree_on_random_corruptions() -> None:
    rng = random.Random(11)
    text = "Cross check 42!"
    bits = flip(encode(text), [t + rng.randrange(3) for t in range(0, 24 * len(text), 3)])
    assert _run(["encode", text]) == encode(text)
    assert _run(["decode", bits]) == decode(bits) == text
