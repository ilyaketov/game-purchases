"""
Конфигурация автоматизации отчётов закупа для QuickBooks.

Все справочники и константы вынесены сюда для удобства поддержки
без правки кода движка.
"""

# ---------------------------------------------------------------------------
# Маппинг площадок: имя → фильтры в сырых отчётах
# ---------------------------------------------------------------------------
# r1, r2, genba — могут быть строкой ИЛИ списком строк (для комбинированных площадок)
PLOSHADKA_MAP = {
    "Plati":      {"r1": "закуп плати",   "r2": "закуп плати",                    "genba": "плати"},
    "Kinguin":    {"r1": "закуп кингвин", "r2": "закуп кингвин",                  "genba": "кингвин"},
    "Eneba":      {"r1": "закуп энеба",   "r2": "закуп энеба",                    "genba": "eneba"},
    "G2A":        {"r1": None,            "r2": "закуп г2а",                      "genba": "g2a"},
    "Driffle":    {"r1": None,            "r2": "закуп дриффл",                   "genba": "driffle"},
    "Tao":        {"r1": None,            "r2": "закуп тао",                      "genba": "тао"},
    "ChinaPlay":  {"r1": None,            "r2": ["закуп чайна", "costchinaplay"], "genba": ["chinaplay", "costchinaplay"]},
    "B2B":        {"r1": "продажи б2б",   "r2": ["закуп b2b", "Продажи б2б"],     "genba": "b2b",
                   # Закуп PLAION учитывается весь, даже если ключи передали на другие площадки:
                   # эталон агрегирует PLAION по всем зонам, не только по продажам б2б.
                   "extra_supplier_substrings": ["PLAION"]},
    "GamersBase": {"r1": None,            "r2": ["закуп гб", "costgb"],           "genba": ["gb", "costgb"]},
}

# ---------------------------------------------------------------------------
# Сопоставление сырых имён поставщиков → группа в финальном своде
# ---------------------------------------------------------------------------
SUPPLIER_MAPPING = {
    # Стандартные издатели
    "Hooded Horse":        "Hooded Horse",
    "Nacon (Point Nexus)": "Nacon",
    "Nacon":               "Nacon",
    "Team17":              "Team17",
    "Team 17":             "Team17",  # вариант в Tao
    "Owlcat Games":        "Owlcat Games",
    "Green Man Gaming":    "Green Man Gaming",
    "ALAWAR":              "ALAWAR",
    "Fulqrum Publishing":  "Fulqrum Publishing",
    "Offworld Industries": "Offworld Industries",
    "THQ Nordic Games":    "THQ Nordic Games",
    "Stunlock Studios":    "Stunlock Studios",
    "Stunlock Studios AB": "Stunlock Studios",  # вариант в Tao
    "DOOR 407":            "DOOR 407",
    "Iceberg Interactive": "Iceberg Interactive",
    "MINTROCKET":          "MINTROCKET",
    "Aspyr":               "Aspyr",
    "Shiravune":           "Shiravune",
    "ArtDock":             "ArtDock",
    "Gamersky":            "Gamersky",
    "Gamersky Games":      "Gamersky",
    "Gamersky games":      "Gamersky",
    # Особые имена групп
    "Ytopia":              "YTOPIA LLC",
    "YTOPIA":              "YTOPIA LLC",
    # CNY-поставщики (см. CNY_SUPPLIERS ниже)
    "Kishmish Games":      "Kishmish Games",
    "One More Time":       "One More Time",
    "Callback Games":      "Callback Games",
    # Новые из Tao/ChinaPlay
    "Daedalic":                    "Daedalic",
    "DAEDALIC ENTERTAINMENT GMBH": "Daedalic",
    "META Publishing":             "META Publishing",
    "Quantic Dream":               "Quantic Dream",
    "Quantic Dream (Point Nexus)": "Quantic Dream",
    "QUANTIC DREAM":               "Quantic Dream",
    "Thunderful Publishing":       "Thunderful Publishing",
    "MY.GAMES":                    "MY.GAMES",
    "Top Hat Studios":             "Top Hat Studios",
    # B2B-поставщики (исторически шли отдельными инвойсами, теперь в биллинге)
    "KRM Teknoloji":               "КRM",  # имя в R1 'продажи б2б' (русская К — как в эталоне)
}

# Спецсопоставления по подстрокам (применяются раньше префиксного парсинга)
SUPPLIER_SUBSTRING_RULES = [
    # порядок имеет значение: более специфичные правила выше
    ("(Genba)", "Genba"),
    ("Plug-in-Digital", "Plug-in-Digital"),
    ("(PID)",  "Plug-in-Digital"),
    ("(Epay)", "PLN ИГРЫ. (Epay)"),
    # B2B: PLAION приходит как 'EUR GAMES. PLAION (Tier 1/2/3)' — Tier игнорируем
    ("PLAION", "PLAION"),
    # B2B: KRM Teknoloji в R2 — 'TRY/USD GAMES. PlayStation TR (KRM Teknoloji)' и т.п.
    # (русская К — как в эталоне 'КRM')
    ("(KRM Teknoloji)", "КRM"),
    # B2B: Giftcard Pro — 'USD GAMES. Blizzard (Giftcard Pro)'
    ("(Giftcard Pro)", "Giftcard pro LTD"),
    # B2B: Capcom / Embark Studios как Genba-сток
    # (закупка идёт через Genba, в биллинге появляется под брендом продукта)
    ("Capcom (Stock)",        "Genba"),
    ("Embark Studios (Stock)", "Genba"),
    # Embark Studios Tier 1 (Stock) — отдельное имя для USD-Tier 1
    ("Embark Studios Tier",   "Genba"),
]

# Точные совпадения (если имя поставщика — это просто слово без префикса)
SUPPLIER_EXACT_RULES = {
    "Genba": "Genba",
    "Epay":  "PLN ИГРЫ. (Epay)",
}

# ---------------------------------------------------------------------------
# CNY-поставщики: цена = (RUB-сумма из биллинга) / RUB_CNY_RATE
# ---------------------------------------------------------------------------
CNY_SUPPLIERS = {"Kishmish Games", "One More Time", "Callback Games"}
RUB_CNY_RATE = 11

# ---------------------------------------------------------------------------
# Валюты в финальном своде по поставщикам
# ---------------------------------------------------------------------------
SUPPLIER_CURRENCY = {
    "Nacon":           "EUR",
    "Daedalic":        "EUR",
    "Quantic Dream":   "EUR",
    "Kishmish Games":  "CNY",
    "One More Time":   "CNY",
    "Callback Games":  "CNY",
    # B2B (по эталону)
    "PLAION":           "EUR",
    "КRM":              "USD",  # источник в TRY, конвертируется в USD
    "Giftcard pro LTD": "USD",
}
DEFAULT_CURRENCY = "USD"

# ---------------------------------------------------------------------------
# FX-фолбэк: средний курс из R2 по валютам.
# Используется ТОЛЬКО когда у позиции пуст 'Курс фиксации в валюте базового поставщика'
# (так бывает для зоны 'Продажи б2б'). Заполняется движком из загруженного R2.
# Структура: {"TRY": 0.0226, ...} — множитель валюта→USD (1 ед. валюты = X USD).
# ---------------------------------------------------------------------------
FX_FALLBACK_DEFAULT = {
    # запасные значения на случай, если в R2 не нашлось ни одной строки с курсом
    "TRY": 0.0228,  # ≈ март 2026 (USD/TRY ≈ 43.9)
}

# ---------------------------------------------------------------------------
# Имена колонок в сырых отчётах
# ---------------------------------------------------------------------------
# Universal Report (R1) — старый формат. ВАЖНО: "площадка " с пробелом на конце!
COLS_R1 = {
    "ploshadka":   "площадка ",
    "supplier":    "Поставщик",
    "pid":         "Id продукта (Billing)",
    "prod_name":   "Продукт",
    "base_amount": "Закуп в валюте взаиморасчетов с ПО",
    "base_ccy":    "Валюта базового ПО",
    "prod_amount": "Цена закупа в валюте продукта",
    "prod_ccy":    "Валюта продукта",
}

# Universal Report shipped (R2) — новый формат
COLS_R2 = {
    "ploshadka":   "площадка",
    "supplier":    "Поставщик",
    "pid":         "ID продукта",
    "prod_name":   "Продукт",
    "qty":         "Количество",
    "base_amount": "Сумма в валюте базового поставщика",
    "base_ccy":    "Валюта базового поставщика",
    "prod_amount": "Себестоимость позиции заказа",
    "prod_ccy":    "Валюта покупки у поставщика",
    "fx_rate":     "Курс фиксации в валюте базового поставщика",
}

# genbaFile
COLS_GENBA = {
    "ploshadka":   "площадка",
    "pid":         "ID продукта",
    "qty":         "Activation Qty",
    "grand_total": "Grand Total",
}
