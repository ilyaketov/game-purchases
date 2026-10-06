"""Sanity-check that all 9 marketplace totals match the reference month.

Run after any change to engine.py / config.py to make sure you haven't
broken anything quietly. Provide three input files via env vars or CLI args.

Usage:
    python smoke_test.py --r1 report1.xlsx --r2 report2.xlsx --genba genba.xlsx

Expected output: 9 lines of "✓" — all marketplaces match within $0.01.
Anything else means the change altered marketplace totals; investigate before shipping.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from engine import Pipeline


# Reference totals for March 2026 (the month we verified against manual reports).
# These should hold for any month-equivalent file with the same marketplace shape.
EXPECTED_MARCH_2026 = {
    "Plati":      482366.35,
    "Kinguin":     46821.49,
    "Eneba":       30761.08,
    "G2A":          5838.07,
    "Driffle":      2487.72,
    "Tao":         83628.35,
    "ChinaPlay":    8632.24,
    "B2B":        100274.66,
    "GamersBase":   1336.18,
}


# Август 2026 — проверено против ручных «ЗАКУП (свод)» из бс-файлов (курс RUB/CNY 12,8293).
# Известные отличия от ручных эталонов (приложение здесь корректнее или эталон неполный):
#   Plati   +10.20  — усреднение цены Genba по всем строкам 'MP_Plati' в genbaFile;
#   Eneba   −18.99  — в эталоне Callback Games и One More Time пересчитаны по курсу 12,34, Kishmish — по 12,83;
#   Tao    +231.46  — 32 ключа Boltray Games, которых нет в эталоне Тао;
#   Driffle  −0.02  — округление.
#   Kinguin, G2A, GGSel — до цента.
EXPECTED_AUGUST_2026 = {
    "Plati":      97886.31,
    "GGSel":      57839.09,
    "Kinguin":    31101.18,
    "Eneba":      44157.07,
    "G2A":        11456.38,
    "Driffle":     5781.32,
    "Tao":        12403.72,
    "ChinaPlay":   5253.27,
    "B2B":       303423.54,
    "GamersBase":   191.63,
}
EXPECTED = {"march 2026": EXPECTED_MARCH_2026, "august 2026": EXPECTED_AUGUST_2026}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--r1", required=True, help="Универсальный отчёт R1 .xlsx")
    parser.add_argument("--r2", required=True, help="Universal Report shipped R2 .xlsx")
    parser.add_argument("--genba", required=True, help="genbaFile .xlsx")
    parser.add_argument("--month", default="march 2026", choices=sorted(EXPECTED),
                        help="Reference month: 'march 2026' or 'august 2026'")
    parser.add_argument("--rub-cny", type=float, default=None,
                        help="RUB per 1 CNY (march 2026: 11, august 2026: 12.8293)")
    args = parser.parse_args()

    print(f"Loading pipeline ({args.month})...")
    t0 = time.time()
    rate = args.rub_cny or (11.0 if args.month == "march 2026" else 12.8293)
    p = Pipeline(args.r1, args.r2, args.genba, rub_cny_rate=rate)
    print(f"  loaded in {time.time()-t0:.1f}s\n")

    v = p.validate()
    if v.unmapped_suppliers:
        print(f"⚠ {len(v.unmapped_suppliers)} unmapped suppliers — will appear as 'НЕ РАСПОЗНАН' (dropped only in B2B/GamersBase):")
        for raw, n in sorted(v.unmapped_suppliers.items(), key=lambda x: -x[1])[:10]:
            print(f"    {raw!r}: {n} rows")
        print()

    print(f"{'Marketplace':<12} {'Expected':>12} {'Actual':>12} {'Δ':>10}  Status")
    print("=" * 64)

    all_ok = True
    expected_map = EXPECTED[args.month]
    for key, expected in expected_map.items():
        agg = p.aggregate(key)
        if agg.empty:
            print(f"{key:<12} {expected:>12,.2f} {'(empty)':>12}      —  ✗ NO DATA")
            all_ok = False
            continue

        actual = float(agg[agg["qty"] > 0]["cost"].sum())
        delta = actual - expected
        match = abs(delta) < 0.01
        status = "✓" if match else f"✗ CHANGED"
        if not match:
            all_ok = False
        print(f"{key:<12} {expected:>12,.2f} {actual:>12,.2f} {delta:>+10,.2f}  {status}")

    print("=" * 64)
    if all_ok:
        print(f"\n✅ All {len(expected_map)} marketplaces match within $0.01")
        return 0
    print("\n❌ Some marketplaces changed — investigate before shipping")
    return 1


if __name__ == "__main__":
    sys.exit(main())
