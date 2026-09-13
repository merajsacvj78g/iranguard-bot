# -*- coding: utf-8 -*-
# S32: «منو» بدون / در پیوی = بوت‌استرپ کامل + دفتر خزانه برای همهٔ مسیرهای
#      اقتصادی باقی‌مانده (قراردادها/پژوهش/پروژه/خرید خارجی/پالایش/بازار/بحران/
#      غنیمت جنگی دوطرفه) + سخت‌گیری براندازی (سطح ۵ + ۳۰ تجهیزات)
import io

s = io.open("bot.py", encoding="utf-8").read()
REPS = []


def rep(old, new, tag):
    REPS.append((old, new, tag))


# ── ۱) «منو/پنل/بازی/خانه» در پیوی = بالا آمدن پنل حتی برای تازه‌وارد ──
rep('''        is_start = txt.startswith("/start") or (c in ("شروع", "شروع بازی", "استارت", "استارت بازی") and not txt.startswith("/"))''',
    '''        is_start = txt.startswith("/start") or (c in ("شروع", "شروع بازی", "استارت", "استارت بازی", "منو", "پنل", "بازی", "خانه", "منوی بازی") and not txt.startswith("/"))''', "is_start_words")

# ── ۲) قراردادهای دیپلماسی ────────────────────────────────────────────
rep('''        if ty == "joint": p["treasury"] -= 1500
        if ty == "over": p["treasury"] -= 2000''',
    '''        if ty == "joint": mpay(p, 1500, "پروژه مشترک")
        if ty == "over": mpay(p, 2000, "پایگاه لجستیکی")''', "agree_cost")

rep('''        if ty == "fdi": p["treasury"] += 800''',
    '''        if ty == "fdi": mearn(p, 800, "سرمایه‌گذاری خارجی")''', "agree_fdi")

# ── ۳) خرید تجهیزات خارجی ─────────────────────────────────────────────
rep('''        p["treasury"] -= price
        mins = int(e["mins"] * (1.5 if crel(p, ck) < 30 else 1))''',
    '''        mpay(p, price, "خرید تجهیزات")
        mins = int(e["mins"] * (1.5 if crel(p, ck) < 30 else 1))''', "buyeq")

# ── ۴) پژوهش ──────────────────────────────────────────────────────────
rep('''        p["treasury"] -= t["cost"]
        mins = int(t["mins"]''',
    '''        mpay(p, t["cost"], "پژوهش")
        mins = int(t["mins"]''', "tech")

# ── ۵) پروژه ملی ──────────────────────────────────────────────────────
rep('''        p["treasury"] -= cost
        mins = pr["mins"][st]''',
    '''        mpay(p, cost, "پروژه ملی")
        mins = pr["mins"][st]''', "prj")

# ── ۶) خرید خارجی حزبی ────────────────────────────────────────────────
rep('''        p["treasury"] -= pr3
        p["deliveries"].append(dict(e=dict(e3), at=now + (e3["mins"] + 20) * 60))''',
    '''        mpay(p, pr3, "خرید خارجی")
        p["deliveries"].append(dict(e=dict(e3), at=now + (e3["mins"] + 20) * 60))''', "fbuy")

# ── ۷) پالایش ─────────────────────────────────────────────────────────
rep('''        p["stock"]["oil"] = int(round(p["stock"].get("oil", 0))) - 10
        p["treasury"] -= 30''',
    '''        p["stock"]["oil"] = int(round(p["stock"].get("oil", 0))) - 10
        mpay(p, 30, "پالایش نفت")''', "rfn")

# ── ۸) بازار جهانی: خرید و فروش ───────────────────────────────────────
rep('''            p["treasury"] -= cost
            mins = max(6, int(14 - nat_stats(p)["logi"] / 10))''',
    '''            mpay(p, cost, "خرید بازار")
            mins = max(6, int(14 - nat_stats(p)["logi"] / 10))''', "mbuy")

rep('''        p["stock"][k] = int(round(p["stock"][k])) - 10; gain = int(pr * 10)
        p["treasury"] += gain''',
    '''        p["stock"][k] = int(round(p["stock"][k])) - 10; gain = int(pr * 10)
        mearn(p, gain, "فروش بازار")''', "msell")

# ── ۹) مهار بحران ─────────────────────────────────────────────────────
rep('''        p["treasury"] -= c["cost"]; p["ops"][opk] = 1; p["crises"].remove(c)''',
    '''        mpay(p, c["cost"], "مهار بحران"); p["ops"][opk] = 1; p["crises"].remove(c)''', "crs")

# ── ۱۰) غنیمت جنگی - تصرف کامل (دوطرفه) ───────────────────────────────
rep('''                loot = min(2000, int(d.get("treasury", 0) * 0.2))
                d["treasury"] = max(0, d.get("treasury", 0) - loot)''',
    '''                loot = min(2000, int(d.get("treasury", 0) * 0.2))
                d["treasury"] = max(0, int(d.get("treasury", 0)) - int(loot))
                _mlog(d, -int(loot), "غنیمت جنگی")''', "loot_dec_d")

rep('''            p["treasury"] += loot
            addxp(p, 40)''',
    '''            mearn(p, loot, "غنیمت جنگی")
            addxp(p, 40)''', "loot_dec_p")

# ── ۱۱) غنیمت محدود (دوطرفه) ──────────────────────────────────────────
rep('''                loot = min(400, d.get("treasury", 0))
                d["treasury"] = max(0, d.get("treasury", 0) - loot)
                p["treasury"] += loot''',
    '''                loot = min(400, int(d.get("treasury", 0)))
                d["treasury"] = max(0, int(d.get("treasury", 0)) - int(loot))
                _mlog(d, -int(loot), "غنیمت جنگی")
                mearn(p, loot, "غنیمت جنگی")''', "loot_lim")

# ── ۱۲) سخت‌گیری براندازی: آخرین شهر فقط با سطح ۵ + ۳۰ تجهیزات ────────
rep('''        outc = None
        if ratio >= 1.3: outc = "dec"
        elif ratio >= 0.95: outc = "lim"
        else: outc = "rep"''',
    '''        outc = None
        if ratio >= 1.3: outc = "dec"
        elif ratio >= 0.95: outc = "lim"
        else: outc = "rep"
        if outc == "dec" and d is not None and len(my_regions(d)) <= 1:
            _lv5 = int((profiles.get(p["uid"]) or {}).get("lvl", 1))
            if _lv5 < 5 or len(p.get("equip") or []) < 30:
                outc = "lim"
                rep.append("🛡 براندازی کامل نیازمند سطح ۵ + ۳۰ تجهیزات است - این حمله حداکثر موفقیت محدود داشت.")
                news(f"🛡 حمله به آخرین شهر {d.get('name', '؟')} محدود ماند - براندازی سخت شد")''', "coup_bar")

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
print(f"S32 applied: {len(REPS)} replacements")
