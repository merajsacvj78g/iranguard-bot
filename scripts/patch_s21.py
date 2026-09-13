# -*- coding: utf-8 -*-
"""S21: جمعیت دقیق مناطق (سرشماری ۱۳۹۵ + مسجدسلیمان ۱۴۰۳) + ریست جهان توسط مالک (هر گروه مستقل)."""
import io

PATH = "bot.py"
src = io.open(PATH, encoding="utf-8").read()
n0 = len(src)

def rep(old, new, tag):
    global src
    assert src.count(old) == 1, "anchor NOT unique/found: " + tag
    src = src.replace(old, new, 1)

# ── ۱) جمعیت دقیق (میلیون): البرز ۲.۷ - خراسان ۸.۱ (سه‌تکه) - آذربایجان ۷.۲ (شرقی+غربی)
#        مسجدسلیمان ۰.۱۱۱ (۱۴۰۳) - ارومیه ۰.۷ (شهر) - کرمان ۳.۲ - هرمزگان ۱.۸
for old, new, tag in [
    ('pop=2.1, ind=3', 'pop=2.7, ind=3', 'alz'),
    ('pop=6.7, ind=2', 'pop=8.1, ind=2', 'khr'),
    ('pop=3.9, ind=4', 'pop=7.2, ind=4', 'azb'),
    ('pop=0.4, ind=2', 'pop=0.11, ind=2', 'msd'),
    ('pop=1.6, ind=1', 'pop=0.7, ind=1', 'urm'),
    ('pop=3.4, ind=1', 'pop=3.2, ind=1', 'krn'),
    ('pop=1.9, ind=1', 'pop=1.8, ind=1', 'hrm'),
]:
    rep(old, new, "pop " + tag)

# ── ۲) تابع ریست جهان (بعد از max_regions)
rep('''def max_regions():''',
    '''def reset_world(gid):
    """ریست کامل جهانِ یک گروه: همه مناطق بی‌طرف، جنگ/پیمان/مستعمره/کاروان/زرادخانه از اول - پروفایل شخصی (خزانه/سطح) می‌ماند"""
    st = worlds[gid]["st"]
    st["rs"] = {rk: dict(owner=None, status="neutral", hist=[], party=REGIONS[rk]["party"]) for rk in REGIONS}
    st["wars"] = []; st["pacts"] = {}; st["preq"] = {}; st["forces"] = {}
    st["col"] = {}; st["treq"] = {}; st["wlog"] = []; st["sellmod"] = {}
    for wp in (worlds[gid].get("pdata") or {}).values():
        wp["regions"] = {}; wp["city"] = None
        wp["equip"] = []; wp["deliveries"] = []; wp["cargos"] = []
        wp["builds"] = []; wp["arms"] = {}
        wp["stock"] = {k: 0 for k, _, _ in COMMS}
        wp["stock"] = {k: 0 for k, _, _ in COMMS}
        wp["stock"]["food"] = 20

def max_regions():''', "reset_world fn")

# ── ۳) دکمه ریست در تنظیمات
rep('''               [btn(u, "➖ مناطق", "cfgm:-"), btn(u, "🌍 " + fa(max_regions()) + " منطقه", "cfgm:0"), btn(u, "➕ مناطق", "cfgm:+")],''',
    '''               [btn(u, "➖ مناطق", "cfgm:-"), btn(u, "🌍 " + fa(max_regions()) + " منطقه", "cfgm:0"), btn(u, "➕ مناطق", "cfgm:+")],
               [btn(u, "♻️ ریست جهان این گروه - مالک", "rst:0")],''', "set_kb rst")

# ── ۴) معافیت گیت بدون‌شهر برای rst
rep('''and not act.startswith("cfgm"):''',
    '''and not act.startswith("cfgm") and not act.startswith("rst"):''', "gate rst")

# ── ۵) هندلرها
rep('''    if act.startswith("cfgm:"):''',
    '''    if act == "rst:0":
        if uid != "8694290031":
            show_sub(cid, p, "♻️ ریست جهان فقط برای مالک.", set_kb(p)); return
        show_sub(cid, p, "♻️ <b>ریست کامل جهان این گروه؟</b>\\n━" * 1 + "━━━━━━━━━━━━━━━━━━\\n- همه ۱۳ منطقه بی‌طرف می‌شوند (کسی روی هیچ شهری نیست)\\n- جنگ‌ها، پیمان‌ها، مستعمره‌ها و زرادخانه‌ها پاک می‌شود\\n- خزانه و سطح فرماندهان حفظ می‌شود\\n- بعد از ریست، همه باید منطقه‌شان را دوباره انتخاب کنند\\n\\n⚠️ این کار برگشت ندارد.",
                 kb([[btn(uid, "✅ بله، ریست کامل", "rst:go"), btn(uid, "❌ انصراف", "set")]])); return
    if act == "rst:go":
        if uid != "8694290031":
            show_sub(cid, p, "♻️ ریست جهان فقط برای مالک.", set_kb(p)); return
        reset_world(p.get("gid") or "0")
        news("♻️ جهان این گروه از اول ساخته شد - همه مناطق آزاد است")
        show_sub(cid, p, "♻️ جهان این گروه از اول ساخته شد.\\n\\n🏙 حالا منطقه‌ات را انتخاب کن - هر فرمانده یک منطقه:", cty_kb(p)); return
    if act.startswith("cfgm:"):''', "rst handlers")

io.open(PATH, "w", encoding="utf-8").write(src)
print("S21 applied:", n0, "->", len(src), "chars")
