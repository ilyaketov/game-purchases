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
    "B2B":        {"r1": None,            "r2": ["закуп b2b", "продажи б2б"], "genba": "b2b"},
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
    # B2B-инвойсы, попавшие в R2 как штатные строки (Продажи б2б)
    "PLAION (Tier 1)":             "PLAION",
    "PLAION (Tier 2)":             "PLAION",
    "PLAION (Tier 3)":             "PLAION",
    "PLAION":                      "PLAION",
    "PlayStation TR (KRM Teknoloji)": "KRM",
    "Xbox TR (KRM Teknoloji)":        "KRM",
    "Xbox (KRM Teknoloji)":           "KRM",
    "KRM Teknoloji":                  "KRM",
    "Blizzard (Giftcard Pro)":     "Giftcard pro LTD",
    "Giftcard Pro":                "Giftcard pro LTD",
}

# Спецсопоставления по подстрокам (применяются раньше префиксного парсинга)
SUPPLIER_SUBSTRING_RULES = [
    # порядок имеет значение: более специфичные правила выше
    ("(Genba)", "Genba"),
    ("Plug-in-Digital", "Plug-in-Digital"),
    ("(PID)",  "Plug-in-Digital"),
    ("(Epay)", "PLN ИГРЫ. (Epay)"),
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
# TRY-поставщики (KRM Teknoloji): в R2 себестоимость лежит в TRY,
# в эталон выводим в USD по фиксированному курсу TRY/USD.
# Курс восстановлен по эталонным инвойсам KRM (FRK2026000000066/68): 43.80
# При смене курса месяца — отредактировать значение ниже.
# ---------------------------------------------------------------------------
TRY_SUPPLIERS = {"KRM"}
TRY_USD_RATE = 43.80

# ---------------------------------------------------------------------------
# Валюты в финальном своде по поставщикам
# ---------------------------------------------------------------------------
SUPPLIER_CURRENCY = {
    "Nacon":           "EUR",
    "Daedalic":        "EUR",
    "Quantic Dream":   "EUR",
    "PLAION":          "EUR",
    "Kishmish Games":  "CNY",
    "One More Time":   "CNY",
    "Callback Games":  "CNY",
    "KRM":              "USD",
    "Giftcard pro LTD": "USD",
}
DEFAULT_CURRENCY = "USD"

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
}

# genbaFile
COLS_GENBA = {
    "ploshadka":   "площадка",
    "pid":         "ID продукта",
    "qty":         "Activation Qty",
    "grand_total": "Grand Total",
}
