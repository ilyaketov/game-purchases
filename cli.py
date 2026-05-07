"""
Запуск из командной строки — для скриптов и автоматизации.

Примеры:
    python cli.py --r1 report1.xlsx --r2 report2.xlsx --genba genba.xlsx
    python cli.py --r1 report1.xlsx --r2 report2.xlsx --genba genba.xlsx --out ./reports
    python cli.py --r2 report2.xlsx --genba genba.xlsx --ploshadka Plati Eneba
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from engine import Pipeline
from config import PLOSHADKA_MAP


def main():
    parser = argparse.ArgumentParser(
        description="Game Purchases — сборка отчётов закупа для QuickBooks",
    )
    parser.add_argument("--r1", type=Path, help="Universal Report (старый формат)")
    parser.add_argument("--r2", type=Path, help="Universal Report shipped (новый формат)")
    parser.add_argument("--genba", type=Path, help="genbaFile с ценами Genba")
    parser.add_argument("--out", type=Path, default=Path("./reports"),
                        help="Папка для готовых отчётов (default: ./reports)")
    parser.add_argument(
        "--ploshadka", nargs="+", choices=list(PLOSHADKA_MAP.keys()),
        help="Какие площадки собирать (default: все доступные)",
    )
    args = parser.parse_args()

    if not (args.r1 or args.r2):
        print("Ошибка: нужен хотя бы один из --r1 или --r2", file=sys.stderr)
        sys.exit(1)

    print(f"→ Загрузка файлов...")
    pipeline = Pipeline(args.r1, args.r2, args.genba)

    print(f"→ Валидация...")
    v = pipeline.validate()
    if v.unmapped_suppliers:
        print(f"⚠ Неизвестные поставщики ({len(v.unmapped_suppliers)} шт):")
        for raw, n in sorted(v.unmapped_suppliers.items(), key=lambda x: -x[1])[:10]:
            print(f"    {raw!r}: {n} строк")
        print("  (эти строки будут пропущены)")

    print(f"→ Найдены площадки: {', '.join(v.available_ploshadki)}")

    targets = args.ploshadka or list(v.available_ploshadki.keys())
    print(f"→ Сборка: {', '.join(targets)}")

    args.out.mkdir(parents=True, exist_ok=True)
    for key in targets:
        try:
            agg = pipeline.aggregate(key)
            if agg.empty:
                print(f"  · {key}: нет данных, пропускаем")
                continue
            path = pipeline.save_to_excel(
                agg, key, args.out / f"{key}_zakup_svod.xlsx"
            )
            active = agg[agg["qty"] > 0]
            print(f"  · {key}: {int(active['qty'].sum()):>6,} ключей, "
                  f"${active['cost'].sum():>11,.2f}, {len(active)} продуктов "
                  f"→ {path.name}")
        except Exception as e:
            print(f"  · {key}: ОШИБКА — {e}")

    print(f"\n✓ Готово, файлы в {args.out.resolve()}")


if __name__ == "__main__":
    main()
