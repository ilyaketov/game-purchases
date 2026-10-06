"""
Конфигурация автоматизации отчётов закупа для QuickBooks.

Все справочники и константы вынесены сюда для удобства поддержки
без правки кода движка.
"""

# ---------------------------------------------------------------------------
# Маппинг площадок: имя → фильтры в сырых отчётах
# ---------------------------------------------------------------------------
# r1, r2, genba — могут быть строкой ИЛИ списком строк (для комбинированных площадок)
# Имя синтетической колонки с вычисленной площадкой
# (добавляется к R1/R2 в pipeline после загрузки; ручную 'площадка' игнорируем — она была вручную проставляемой меткой,
# а с апреля 2026 в выгрузке вообще исчезла)
SYNTH_PLOSHADKA = "_ploshadka"

# ---------------------------------------------------------------------------
# Правила вычисления площадки по колонкам Партнёр + Ключ куплен в сток + Поставщик
# ---------------------------------------------------------------------------
# Партнёр → (zone_zakup, zone_peremeshchenie).
# Если 'Ключ куплен в сток' = ДА → берётся zone_peremeshchenie, иначе zone_zakup.
#
# Cost*-партнёры — это технические счета для учёта стоковых расходов, эквивалентные
# Stock*-партнёрам (см. v13). По апрельской разметке: CostGB ↔ StockGB, CostChinaplay ↔ StockChinaPlay.
PARTNER_TO_ZONE = {
    "MP_Plati":           ("закуп плати",   "перемещение на плати"),
    "MP_Kinguin":         ("закуп кингвин", "перемещение кингвин"),
    "MP_Eneba":           ("закуп энеба",   "перемещение енеба"),
    "MP_G2A":             ("закуп г2а",     "перемещение на г2а"),
    "MP_Driffle":         ("закуп дриффл",  "перемещение дриффл"),
    # GGSel — с августа 2026 отдельное подразделение 41.12 (раньше входил в Плати 41.06)
    "MP_GGSel":           ("закуп ггсел",   "перемещение на ггсел"),
    "ChinaSteamPY":       ("закуп тао",     "перемещение на тао"),
    "ChinaPlayTaoBao":    ("закуп тао",     "перемещение на тао"),
    "StockB2B":           ("закуп b2b",     "закуп b2b"),
    "CostB2B":            ("закуп b2b",     "cost b2b"),       # появился в апреле
    "StockGB":            ("закуп гб",      "перемещение на гб"),
    "CostGB":             ("закуп гб",      "перемещение на гб"),
    "StockChinaPlay":     ("закуп чайна",   "закуп чайна"),
    "CostChinaplay":      ("закуп чайна",   "costchinaplay"),
    "Gamersbase_WW":      ("продажи гб",    "продажи гб"),
}

# Партнёр Rokky Platform / (CN) yueshangshuma может попадать в три зоны
# в зависимости от поставщика:
#   - содержит '(GB_Stock)' или 'Enaza-Games' (RUB) → продажи гб
#   - валюта CNY и поставщик стоковый/CNY-Team17 → продажи на чайнаплей
#   - всё прочее → Продажи б2б
DUAL_USE_PARTNERS = {"Rokky Platform", "(CN) yueshangshuma"}
GB_SUPPLIER_MARKERS = ["(GB_Stock)", "GamersBase", "Enaza-Games"]
CHINAPLAY_SUPPLIER_MARKERS = ["(Stock)", "Team17"]
DEFAULT_B2B_ZONE = "Продажи б2б"

# ---------------------------------------------------------------------------
# Маппинг площадок: имя → фильтры в сырых отчётах
# ---------------------------------------------------------------------------
# r1, r2, genba — могут быть строкой ИЛИ списком строк (для комбинированных площадок)
PLOSHADKA_MAP = {
    # genba: в genbaFile колонку 'площадка' заполняют по-разному от месяца к месяцу
    # ('plati' в мае/июле, 'MP_Plati' в июне/августе) — перечисляем все варианты.
    "Plati":      {"r1": "закуп плати",   "r2": "закуп плати",                    "genba": ["плати", "plati", "mp_plati"]},
    "GGSel":      {"r1": "закуп ггсел",   "r2": "закуп ггсел",                    "genba": ["ggsel", "mp_ggsel"]},
    "Kinguin":    {"r1": "закуп кингвин", "r2": "закуп кингвин",                  "genba": ["кингвин", "kinguin", "mp_kinguin"]},
    "Eneba":      {"r1": "закуп энеба",   "r2": "закуп энеба",                    "genba": ["eneba", "mp_eneba"]},
    # G2A: в марте было 'закуп г2а' (русские буквы), с апреля — 'Закуп G2A' (английские G2A).
    # Поддерживаем оба варианта, чтобы исторические выгрузки тоже работали.
    "G2A":        {"r1": None,            "r2": ["закуп г2а", "закуп g2a"],       "genba": ["g2a", "mp_g2a"]},
    # Driffle: с августа 2026 часть закупа приходит в R1 (Универсальный отчёт)
    "Driffle":    {"r1": "закуп дриффл",  "r2": "закуп дриффл",                   "genba": ["driffle", "mp_driffle"]},
    "Tao":        {"r1": None,            "r2": "закуп тао",                      "genba": ["тао", "tao"]},
    "ChinaPlay":  {"r1": None,            "r2": ["закуп чайна", "costchinaplay"], "genba": ["chinaplay", "costchinaplay"]},
    "B2B":        {"r1": "продажи б2б",   "r2": ["закуп b2b", "Продажи б2б"],     "genba": "b2b",
                   # Закуп PLAION учитывается весь, даже если ключи передали на другие площадки:
                   # эталон агрегирует PLAION по всем зонам, не только по продажам б2б.
                   "extra_supplier_substrings": ["PLAION"],
                   # B2B: свод по замыслу частичный — неизвестные поставщики не включаются
                   "keep_unknown": False},
    "GamersBase": {"r1": None,            "r2": ["закуп гб", "costgb"],           "genba": ["gb", "costgb"],
                   "keep_unknown": False},
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
    # Новые поставщики, появившиеся в апреле 2026
    "Fireshine Games":             "Fireshine Games",
    "FOR-GAMES CR LTD":            "FOR-GAMES CR LTD",
    "Polden Publishing":           "Polden Publishing",
    "CURVE GAMES":                 "CURVE GAMES",
    "Techland":                    "Techland",
    "Strategy First":              "Strategy First",
    "Frontier Developments":       "Frontier Developments",
    "Incenti":                     "Incenti",
    # Новые поставщики, появившиеся в августе 2026 (раньше молча выпадали из свода)
    "HOUND13 Inc.":                "Hound13 Inc.",
    "Hound13 Inc.":                "Hound13 Inc.",
    "Red Hook Studios":            "Red Hook Studios",
    "Brightika, Inc.":             "Brightika, Inc.",
    "Digital Sky":                 "Digital Sky Entertainment Limited",
    "Digisky":                     "Digital Sky Entertainment Limited",
    "Azura Interactive":           "Azura Interactive",
    "Ustwo Games":                 "Ustwo Games",
    "Boltray Games":               "Boltray Games",
    "Indie.io":                    "Indie.io",
    "SoloGame":                    "HONG KONG SOLO NETWORK TECHNOLOGY",
    "HONG KONG SOLO NETWORK TECHNOLOGY": "HONG KONG SOLO NETWORK TECHNOLOGY",
    "Stardock Entertainment":      "Stardock Entertainment",
    "APPWILL COMPANY LTD":         "APPWILL COMPANY LTD",
    "Forever-Entertainment":       "Forever-Entertainment",
    "Cyber Temple Games LLC":      "Cyber Temple Games LLC",
    "Astragon":                    "Astragon Entertainment GmbH",
    # TOPHOUSE GAMES закупается через Rokky Limited — в эталоне и QuickBooks поставщик Rokky Limited
    "TOPHOUSE GAMES":              "Rokky Limited",
    "Mindscape":                   "Mindscape",
    "Soviet Games":                "Soviet Games",
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
    # Incenti (Bamboo): 'USD GAMES. PlayStation USA (Incenti)', 'EUR GAMES. Blizzard (Incenti)'
    ("(Incenti)", "Incenti"),
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
CNY_SUPPLIERS = {"Kishmish Games", "One More Time", "Callback Games", "Soviet Games"}
# Значение по умолчанию; в приложении курс задаётся на экране перед сборкой.
# Бухгалтерия берёт кросс-курс на конец месяца: (RUB за USD) × (USD за CNY).
# Март 2026 — 11; август 2026 — 86,299298 × 0,14866 = 12,83.
RUB_CNY_RATE = 12.83

# ---------------------------------------------------------------------------
# Валюты в финальном своде по поставщикам
# ---------------------------------------------------------------------------
SUPPLIER_CURRENCY = {
    "Nacon":           "EUR",
    "Daedalic":        "EUR",
    "Quantic Dream":   "EUR",
    "Mindscape":       "EUR",
    "Kishmish Games":  "CNY",
    "One More Time":   "CNY",
    "Callback Games":  "CNY",
    "Soviet Games":    "CNY",
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
# Universal Report (R1). До апреля 2026 здесь была ручная колонка 'площадка ' (с пробелом),
# с апреля её нет. Площадка теперь ВЫЧИСЛЯЕТСЯ из 'Партнер' + 'Ключ куплен в сток'.
COLS_R1 = {
    "supplier":    "Поставщик",
    "pid":         "Id продукта (Billing)",
    "prod_name":   "Продукт",
    "base_amount": "Закуп в валюте взаиморасчетов с ПО",
    "base_ccy":    "Валюта базового ПО",
    "prod_amount": "Цена закупа в валюте продукта",
    "prod_ccy":    "Валюта продукта",
    "partner":     "Партнер",                # обязательно для вычисления площадки
    "in_stock":    "Ключ куплен в сток",     # появилась с апреля 2026; до — отсутствует
}

# Universal Report shipped (R2). Аналогично — 'площадка' вычисляется.
COLS_R2 = {
    "supplier":    "Поставщик",
    "pid":         "ID продукта",
    "prod_name":   "Продукт",
    "qty":         "Количество",
    "base_amount": "Сумма в валюте базового поставщика",
    "base_ccy":    "Валюта базового поставщика",
    "prod_amount": "Себестоимость позиции заказа",
    "prod_ccy":    "Валюта покупки у поставщика",
    "fx_rate":     "Курс фиксации в валюте базового поставщика",
    "partner":     "Партнёр",
    "in_stock":    "Ключ куплен в сток",
}

# genbaFile
COLS_GENBA = {
    "ploshadka":   "площадка",
    "pid":         "ID продукта",
    "qty":         "Activation Qty",
    "grand_total": "Grand Total",
}
