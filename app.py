"""
Веб-приложение KeyFlow — автоматизация отчётов закупа для QuickBooks.

Запуск:
    streamlit run app.py

Поднимает локальный сервер на http://localhost:8501
"""
from __future__ import annotations

import io
import shutil
import tempfile
import zipfile
from pathlib import Path

import pandas as pd
import streamlit as st

from engine import Pipeline
from config import PLOSHADKA_MAP

# ---------------------------------------------------------------------------
# Настройка страницы
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="KeyFlow — отчёты для QuickBooks",
    page_icon="📊",
    layout="wide",
)

st.title("KeyFlow")
st.caption("Автоматическая сборка отчётов закупа из биллинга")

# ---------------------------------------------------------------------------
# Шаг 1 — загрузка файлов
# ---------------------------------------------------------------------------
st.header("1. Загрузите сырые отчёты")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Универсальный отчёт 1")
    st.caption("Старый формат биллинга, ~80k строк")
    file_r1 = st.file_uploader(
        "Универсальный отчёт",
        type=["xlsx"],
        key="r1",
        label_visibility="collapsed",
    )

with col2:
    st.subheader("Универсальный отчёт 2")
    st.caption("Новый shipped-формат, ~310k строк")
    file_r2 = st.file_uploader(
        "Universal Report shipped",
        type=["xlsx"],
        key="r2",
        label_visibility="collapsed",
    )

with col3:
    st.subheader("genbaFile")
    st.caption("Цены закупа от Genba")
    file_genba = st.file_uploader(
        "genbaFile",
        type=["xlsx"],
        key="genba",
        label_visibility="collapsed",
    )

if not (file_r1 or file_r2):
    st.info("Загрузите хотя бы один из универсальных отчётов, чтобы продолжить.")
    st.stop()

# ---------------------------------------------------------------------------
# Сохраняем загруженные файлы во временную директорию (pandas работает с путями)
# ---------------------------------------------------------------------------
@st.cache_resource
def make_tmpdir():
    return tempfile.mkdtemp(prefix="keyflow_")


tmpdir = Path(make_tmpdir())


def _save_upload(uploaded_file, name: str) -> Path | None:
    if uploaded_file is None:
        return None
    target = tmpdir / name
    target.write_bytes(uploaded_file.getbuffer())
    return target


# ---------------------------------------------------------------------------
# Шаг 2 — валидация
# ---------------------------------------------------------------------------
st.header("2. Анализ данных")

with st.spinner("Загружаем файлы и проверяем поставщиков..."):
    p1_path = _save_upload(file_r1, "report1.xlsx")
    p2_path = _save_upload(file_r2, "report2.xlsx")
    pg_path = _save_upload(file_genba, "genba.xlsx")

    pipeline = Pipeline(p1_path, p2_path, pg_path)
    validation = pipeline.validate()

# Какие площадки нашлись
if not validation.available_ploshadki:
    st.error("В загруженных файлах не найдено ни одной известной площадки.")
    st.stop()

cols = st.columns(len(validation.available_ploshadki))
for col, (key, n) in zip(cols, validation.available_ploshadki.items()):
    with col:
        st.metric(key, f"{n:,} строк")

# Неизвестные поставщики — предупреждение
if validation.unmapped_suppliers:
    with st.expander(
        f"⚠️ Найдено {len(validation.unmapped_suppliers)} неизвестных поставщиков "
        "(они будут пропущены)",
        expanded=True,
    ):
        st.warning(
            "Эти имена не сопоставлены ни с одной группой в эталоне. "
            "Чтобы они попали в отчёт, добавьте их в `SUPPLIER_MAPPING` (config.py)."
        )
        df_unmapped = pd.DataFrame(
            [{"Сырое имя": k, "Строк": v}
             for k, v in sorted(validation.unmapped_suppliers.items(),
                                key=lambda x: -x[1])]
        )
        st.dataframe(df_unmapped, use_container_width=True, hide_index=True)
else:
    st.success("Все поставщики распознаны.")

# ---------------------------------------------------------------------------
# Шаг 3 — выбор площадок и генерация
# ---------------------------------------------------------------------------
st.header("3. Соберите отчёты")

selected = st.multiselect(
    "Площадки для сборки",
    options=list(validation.available_ploshadki.keys()),
    default=list(validation.available_ploshadki.keys()),
)

if not selected:
    st.info("Выберите хотя бы одну площадку.")
    st.stop()

if st.button("Собрать отчёты", type="primary"):
    out_dir = tmpdir / "output"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir()

    progress = st.progress(0, text="Генерация...")
    results = {}
    for i, key in enumerate(selected):
        progress.progress((i + 1) / len(selected), text=f"Обработка {key}...")
        try:
            agg = pipeline.aggregate(key)
            if agg.empty:
                results[key] = {"error": "Нет данных"}
                continue
            path = pipeline.save_to_excel(
                agg, key, out_dir / f"{key}_zakup_svod.xlsx"
            )
            active = agg[agg["qty"] > 0]
            results[key] = {
                "path": path,
                "qty": int(active["qty"].sum()),
                "cost": float(active["cost"].sum()),
                "suppliers": int(active["supplier_group"].nunique()),
                "products": len(active),
            }
        except Exception as e:
            results[key] = {"error": str(e)}

    progress.empty()

    # Результаты
    st.subheader("Готовые отчёты")

    success_results = {k: v for k, v in results.items() if "error" not in v}
    failed = {k: v for k, v in results.items() if "error" in v}

    if success_results:
        # Сводная таблица
        df_summary = pd.DataFrame([
            {
                "Площадка": k,
                "Поставщиков": v["suppliers"],
                "Продуктов": v["products"],
                "Ключей": f"{v['qty']:,}",
                "Себестоимость": f"${v['cost']:,.2f}",
            }
            for k, v in success_results.items()
        ])
        st.dataframe(df_summary, use_container_width=True, hide_index=True)

        # ZIP со всеми
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for k, v in success_results.items():
                zf.write(v["path"], arcname=Path(v["path"]).name)
        zip_buffer.seek(0)

        st.download_button(
            "📦 Скачать все файлы (ZIP)",
            data=zip_buffer,
            file_name="keyflow_reports.zip",
            mime="application/zip",
            type="primary",
        )

        # Отдельные файлы
        st.markdown("**Или скачайте отдельно:**")
        download_cols = st.columns(min(len(success_results), 4))
        for i, (k, v) in enumerate(success_results.items()):
            with download_cols[i % len(download_cols)]:
                with open(v["path"], "rb") as f:
                    st.download_button(
                        f"📄 {k}",
                        data=f.read(),
                        file_name=Path(v["path"]).name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dl_{k}",
                    )

    if failed:
        st.error("Не удалось обработать:")
        for k, v in failed.items():
            st.write(f"- **{k}**: {v['error']}")
