# -*- coding: utf-8 -*-
# S38: بگ‌هانت کامل - کلید تکراری «سلاح» + همهٔ متغیرهای مرده و f-stringهای بی‌اثر
import io

s = io.open("bot.py", encoding="utf-8").read()
REPS = []


def rep(old, new, tag):
    REPS.append((old, new, tag))


# ── ۱) باگ واقعی: «سلاح» دو مقصد داشت (equip در خط تازه، shop:ru در خط اصلی - دومی می‌بُرد) ──
rep('''          "حساب": "eco", "پول": "eco", "درآمد": "eco", "خرید": "mkt", "فروش": "mkt", "سلاح": "equip",''',
    '''          "حساب": "eco", "پول": "eco", "درآمد": "eco", "خرید": "mkt", "فروش": "mkt",''', "salah_dup")
# نتیجه: «سلاح» → فروشگاه سلاح (shop:ru) مثل قبل؛ «زرادخانه» → تجهیزات

# ── ۲) eliminate: متغیر مرده fresh0 (باقی‌ماندهٔ اعلان نیمه‌کاره) ──
rep('''        for o in st2["treq"][tgt2]:
            if o.get("frm") == uid2:
                fresh0 = w2.get("pdata", {}).get(uid2)
            else:
                keep.append(o)''',
    '''        for o in st2["treq"][tgt2]:
            if o.get("frm") != uid2:
                keep.append(o)''', "fresh0")

# ── ۳) nat_stats: متغیر مرده con ──
rep('''def nat_stats(p):
    con = p["budget"].get("con", 15) / 100
    prod = min(100,''',
    '''def nat_stats(p):
    prod = min(100,''', "con_dead")

# ── ۴) cty_text: st بی‌استفاده / cty_kb: own بی‌استفاده ──
rep('''def cty_text(p):
    own = owners_of(p)
    st = world
    L = [f"{pe('city')} <b>انتخاب شهر</b>", "━" * 20,
         sec("پایهٔ قدرتت را همین‌جا می‌سازی - شهر با توسعه‌ات بزرگ می‌شود."),''',
    '''def cty_text(p):
    own = owners_of(p)
    L = [f"{pe('city')} <b>انتخاب شهر</b>", "━" * 20,
         sec("پایهٔ قدرتت را همین‌جا می‌سازی - شهر با توسعه‌ات بزرگ می‌شود."),''', "cty_text_st")

rep('''def cty_kb(p):
    own = owners_of(p)
    st = world
    rows = []''',
    '''def cty_kb(p):
    st = world
    rows = []''', "cty_kb_own")

# ── ۵) apply_decision: d بی‌استفاده (مصرف تصمیم حفظ شود) ──
rep('''def apply_decision(p, key):
    d = p.get("decision"); p["decision"] = None; p["dec_cd"] = time.time()''',
    '''def apply_decision(p, key):
    p["decision"] = None; p["dec_cd"] = time.time()''', "dec_dead")

# ── ۶) wlds_kb: act بی‌استفاده ──
rep('''    for gid, w in worlds.items():
        if uid not in w["pdata"]: continue
        act = gid if gid != pr.get("sel") else "wlds"
        rows.append([btn(uid, ("⭐️ " if gid == pr.get("sel") else "🎮 ") + (w.get("title") or "دنیا"), "wsel:" + gid)])''',
    '''    for gid, w in worlds.items():
        if uid not in w["pdata"]: continue
        rows.append([btn(uid, ("⭐️ " if gid == pr.get("sel") else "🎮 ") + (w.get("title") or "دنیا"), "wsel:" + gid)])''', "wlds_dead")

# ── ۷) bld: lv بی‌استفاده (bcost خودش حساب می‌کند) ──
rep('''        r = p["regions"][rk]; lv = r["bl"].get(bk, 0)
        cost = bcost(p, rk, bk)''',
    '''        cost = bcost(p, rk, bk)''', "bld_dead")

# ── ۸) main: global TOKEN بدون انتساب ──
rep('''def main():
    global TOKEN
    if not TOKEN:''',
    '''def main():
    if not TOKEN:''', "global_token")

# ── ۹) reset_world: خط تکراری stock ──
rep('''        wp["stock"] = {k: 0 for k, _, _ in COMMS}
        wp["stock"] = {k: 0 for k, _, _ in COMMS}
        wp["stock"]["food"] = 20''',
    '''        wp["stock"] = {k: 0 for k, _, _ in COMMS}
        wp["stock"]["food"] = 20''', "stock_dup")

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
print(f"S38 applied: {len(REPS)} replacements")
