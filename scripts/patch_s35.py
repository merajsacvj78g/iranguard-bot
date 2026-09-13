# -*- coding: utf-8 -*-
# S35: کمک نوپایی (شروع بدون خونریزی خزانه) + کیف استارز در منو + فرمان‌های تازه + نمایش حقوق
import io

s = io.open("bot.py", encoding="utf-8").read()
REPS = []


def rep(old, new, tag):
    REPS.append((old, new, tag))


# ── ۱) کمک نوپایی: تا سطح ۳ و حداکثر ۲ شهر، کف درآمد خالص $150 در ساعت ──
rep('''    for cid, ag in p["agreements"].items():
        if ag == "over": exp_ar += 80
    return int(round(inc)), int(round(inc - exp_up - exp_eq - exp_ar))''',
    '''    for cid, ag in p["agreements"].items():
        if ag == "over": exp_ar += 80
    net = int(round(inc - exp_up - exp_eq - exp_ar))
    try:
        _lv = int((profiles.get(p["uid"]) or {}).get("lvl", 1))
        if _lv <= 3 and len(my_regions(p)) <= 2 and net < 150:
            net = 150  # 🤲 کمک نوپایی - شروع بدون خونریزی خزانه
    except Exception:
        pass
    return int(round(inc)), net''', "subsidy")

# ── ۲) اقتصاد: خط کمک نوپایی + خط حقوق سرمایه‌گذاری ───────────────────
rep('''         f"💵 جمع واریزهای ساعتی تا امروز: {fm(p.get('hpay_tot', 0))}",''',
    '''         f"💵 جمع واریزهای ساعتی تا امروز: {fm(p.get('hpay_tot', 0))}",
         f"💰 حقوق سرمایه‌گذاری: فعال - {fm(2500)} هر ساعت" if p.get("hpay_inv") else "💰 حقوق سرمایه‌گذاری: خاموش - از 🛍 بسته‌های ویژه",
         ("🤲 کمک نوپایی فعال: کف درآمد $150 در ساعت تا سطح ۳ (حداکثر ۲ شهر)"),''', "eco_lines")

# ── ۳) منو: کیف استارز کنار سطح ───────────────────────────────────────
rep('''        f"🌎 {worlds.get(p.get('gid'), worlds.get('0', {})).get('title', '🏠 دنیای اصلی')} - 🎖 سطح {fa((profiles.get(p['uid']) or {}).get('lvl', 1))}",''',
    '''        f"🌎 {worlds.get(p.get('gid'), worlds.get('0', {})).get('title', '🏠 دنیای اصلی')} - 🎖 سطح {fa((profiles.get(p['uid']) or {}).get('lvl', 1))} - ⭐️ {fa(int(world.setdefault('stars', {}).get(p['uid'], 0)))}",''', "menu_wallet")

# ── ۴) فرمان‌های تازه ─────────────────────────────────────────────────
rep('''          "پنل": "menu", "اتحاد": "dip", "اتحادها": "dip", "راهنما": "help", "خزانه": "eco", "قراردادها": "trd", "قرارداد": "trd",''',
    '''          "پنل": "menu", "اتحاد": "dip", "اتحادها": "dip", "راهنما": "help", "خزانه": "eco", "قراردادها": "trd", "قرارداد": "trd",
          "حساب": "eco", "پول": "eco", "درآمد": "eco", "خرید": "mkt", "فروش": "mkt", "سلاح": "equip",
          "گردش خزانه": "audit", "بسته": "packs", "بسته‌ها": "packs", "سرمایه‌گذاری": "packs",''', "cmdmap_v33")

ok = True
for old, new, tag in REPS:
    c = s.count(old)
    if c != 1:
        print(f"FAIL {tag}: x{c}")
        ok = False
if not ok:
    raise SystemExit("anchors failed - file untouched")
for old, new, tag in REPS:
    s = s.replace(old, new, 1)
io.open("bot.py", "w", encoding="utf-8").write(s)
print(f"S35 applied: {len(REPS)} replacements")
