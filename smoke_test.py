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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--r1", required=True, help="Универсальный отчёт R1 .xlsx")
    parser.add_argument("--r2", required=True, help="Universal Report shipped R2 .xlsx")
    parser.add_argument("--genba", required=True, help="genbaFile .xlsx")
    parser.add_argument("--month", default="march 2026",
                        help="Month label for the report (only used in output)")
    args = parser.parse_args()

    print(f"Loading pipeline ({args.month})...")
    t0 = time.time()
    p = Pipeline(args.r1, args.r2, args.genba)
    print(f"  loaded in {time.time()-t0:.1f}s\n")

    v = p.validate()
    if v.unmapped_suppliers:
        print(f"⚠ {len(v.unmapped_suppliers)} unmapped suppliers — these rows will drop:")
        for raw, n in sorted(v.unmapped_suppliers.items(), key=lambda x: -x[1])[:10]:
            print(f"    {raw!r}: {n} rows")
        print()

    print(f"{'Marketplace':<12} {'Expected':>12} {'Actual':>12} {'Δ':>10}  Status")
    print("=" * 64)

    all_ok = True
    for key, expected in EXPECTED_MARCH_2026.items():
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
        print("\n✅ All 9 marketplaces match within $0.01")
        return 0
    print("\n❌ Some marketplaces changed — investigate before shipping")
    return 1


if __name__ == "__main__":
    sys.exit(main())
