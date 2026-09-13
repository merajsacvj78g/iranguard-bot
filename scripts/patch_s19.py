# -*- coding: utf-8 -*-
"""S19: سقف مناطق آزاد قابل‌بازی هر World - قابل تنظیم فقط توسط مالک (درخواست صریح سند طراحی)."""
import io

PATH = "bot.py"
src = io.open(PATH, encoding="utf-8").read()
n0 = len(src)

def rep(old, new, tag):
    global src
    assert src.count(old) == 1, "anchor NOT unique/found: " + tag
    src = src.replace(old, new, 1)

# ۱) پیکربندی World در ensure_world
rep('''    if not isinstance(st.get("col"), dict): st["col"] = {}
    return w''',
    '''    if not isinstance(st.get("col"), dict): st["col"] = {}
    if not isinstance(st.get("cfg"), dict): st["cfg"] = {}
    st["cfg"].setdefault("max_regions", len(REGIONS))
    return w''', "ensure_world cfg")

# ۲) هلپر سقف مناطق
rep('''PARTY_NM = {"rep": "جمهوری اسلامی", "pah": "پهلوی"}
PARTY_IC = {"rep": "🕌", "pah": "👑"}''',
    '''PARTY_NM = {"rep": "جمهوری اسلامی", "pah": "پهلوی"}
PARTY_IC = {"rep": "🕌", "pah": "👑"}

def max_regions():
    """سقف مناطق آزاد قابل‌ادعای این World - فقط مالک تغییرش می‌دهد"""
    try: return max(1, min(len(REGIONS), int(world.get("cfg", {}).get("max_regions", len(REGIONS)))))
    except Exception: return len(REGIONS)''', "max_regions helper")

# ۳) فهرست آزادها در cty_kb با سقف
rep('''    free = [rk for rk in REGIONS if st["rs"][rk]["owner"] is None]
    for i in range(0, len(free), 2):''',
    '''    free = [rk for rk in REGIONS if st["rs"][rk]["owner"] is None][:max_regions()]
    for i in range(0, len(free), 2):''', "cty_kb cap")

# ۴) متن انتخاب شهر: نمایش مناطق خارج از سقف
rep('''    for rk, rv in REGIONS.items():
        if rk in own:
            L.append(f"{STAT[own[rk][1]]} {rv['nm']} - فرماندار: {own[rk][2]}")
        else:
            L.append(f"⚪ {rv['nm']} - {rv['tp']} (بی‌طرف - آزاد)")''',
    '''    _fs = 0
    for rk, rv in REGIONS.items():
        if rk in own:
            L.append(f"{STAT[own[rk][1]]} {rv['nm']} - فرماندار: {own[rk][2]}")
        elif _fs < max_regions():
            L.append(f"⚪ {rv['nm']} - {rv['tp']} (بی‌طرف - آزاد)"); _fs += 1
        else:
            L.append(f"⛔️ {rv['nm']} - خارج از سقف این World")''', "cty_text cap")

# ۵) گارد cset
rep('''        own = owners_of(p)
        if my_regions(p): show_menu(p, cid); return
        if rk in own: show_sub(cid, p, f"این شهر قبلاً به {own[rk][2]} رسیده - یکی دیگر انتخاب کن.", cty_kb(p)); return''',
    '''        own = owners_of(p)
        if my_regions(p): show_menu(p, cid); return
        if rk in own: show_sub(cid, p, f"این شهر قبلاً به {own[rk][2]} رسیده - یکی دیگر انتخاب کن.", cty_kb(p)); return
        if world["rs"][rk]["owner"] is None and [x for x in REGIONS if world["rs"][x]["owner"] is None].index(rk) >= max_regions():
            show_sub(cid, p, "⛔️ این منطقه خارج از سقف این World است - مالک می‌تواند سقف را بالا ببرد.", cty_kb(p)); return''', "cset cap guard")

# ۶) ردیف مالک در منوی تنظیمات
rep('''               [btn(u, "🎖 عناوین", "titles"), btn(u, "💚 سلامت", "health")],
               [btn(u, "🔄 بروزرسانی", "refresh"), btn(u, "🏠 خانه", "menu")]])''',
    '''               [btn(u, "🎖 عناوین", "titles"), btn(u, "💚 سلامت", "health")],
               [btn(u, "➖ مناطق", "cfgm:-"), btn(u, "🌍 " + fa(max_regions()) + " منطقه", "cfgm:0"), btn(u, "➕ مناطق", "cfgm:+")],
               [btn(u, "🔄 بروزرسانی", "refresh"), btn(u, "🏠 خانه", "menu")]])''', "set_kb owner row")

# ۷) هندلر
rep('''    if act == "set": show_sub(cid, p, set_text(p), set_kb(p)); return''',
    '''    if act == "set": show_sub(cid, p, set_text(p), set_kb(p)); return
    if act.startswith("cfgm:"):
        if uid != "8694290031":
            show_sub(cid, p, "⛔️ تنظیم World فقط برای مالک.", set_kb(p)); return
        d1 = -1 if act.endswith("-") else (1 if act.endswith("+") else 0)
        world.setdefault("cfg", {})["max_regions"] = max(1, min(len(REGIONS), max_regions() + d1))
        aud(p, "تنظیم World", "سقف مناطق آزاد: " + fa(max_regions()))
        show_sub(cid, p, "🌍 سقف مناطق آزاد این World: " + fa(max_regions()) + " - فقط برای ادعای بازیکن جدید؛ مناطق بی‌طرفِ بیرون سقف با جنگ قابل‌تصرف‌اند.", set_kb(p)); return''', "cfgm handler")

io.open(PATH, "w", encoding="utf-8").write(src)
print("S19 applied:", n0, "->", len(src), "chars")
