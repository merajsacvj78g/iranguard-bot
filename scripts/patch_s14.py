# -*- coding: utf-8 -*-
"""S14: ۸ تسلیحات ایرانی تحقیق‌شده + ۳ سامانه ویژه بیشتر برای هر کشور خارجی + فروش سلاح به متحد."""
import io, sys

PATH = "bot.py"
src = io.open(PATH, encoding="utf-8").read()
n0 = len(src)

def rep(old, new, tag):
    global src
    assert src.count(old) == 1, "anchor NOT unique/found: " + tag
    src = src.replace(old, new, 1)

# ── ۱) تسلیحات ایرانی جدید (تحقیق: خیبرشکن 1450km/سوخت جامد، حاج‌قاسم 1400km/ماخ12،
#        خیبر=خرمشهر-4 2000km/1.5t، سومار 2000+km کروز، صیاد-3 120km،
#        کمان-22 3000km/24h، ابابیل-3 250km، آرش-2 2000km کت) — موشکی‌ها de کم (موتور msl +10×cnt دست‌نخورده)
rep(''' dict(nm="موشک فتح-۱۱۰", ic="🚀", cat="موشکی", price=2400, de=6,  rec=0, lg=2, q=5, mins=70, up=45),
]''',
    ''' dict(nm="موشک فتح-۱۱۰", ic="🚀", cat="موشکی", price=2400, de=6,  rec=0, lg=2, q=5, mins=70, up=45),
 dict(nm="موشک خیبرشکن", ic="🚀", cat="موشکی", price=2600, de=7,  rec=2, lg=1, q=4, mins=90, up=45),
 dict(nm="موشک حاج‌قاسم", ic="🚀", cat="موشکی", price=2400, de=7,  rec=2, lg=1, q=4, mins=85, up=45),
 dict(nm="موشک خیبر-۴", ic="🚀", cat="موشکی", price=3000, de=8,  rec=2, lg=1, q=5, mins=100, up=50),
 dict(nm="کروز سومار", ic="🚀", cat="موشکی", price=2200, de=6,  rec=3, lg=0, q=4, mins=80, up=40),
 dict(nm="کت آرش-۲", ic="🚀", cat="موشکی", price=1300, de=5,  rec=1, lg=0, q=3, mins=50, up=25),
 dict(nm="پدافند صیاد-۳", ic="🗼", cat="دفاعی", price=1800, de=15, rec=4, lg=1, q=4, mins=60, up=30),
 dict(nm="پهپاد کمان-۲۲", ic="🛩️", cat="هواگرد", price=2000, de=8,  rec=9, lg=1, q=4, mins=70, up=35),
 dict(nm="پهپاد ابابیل-۳", ic="🛩️", cat="هواگرد", price=800,  de=4,  rec=5, lg=1, q=3, mins=30, up=15),
]''', "EQUIP")

# ── ۲) سامانه‌های ویژه بیشتر برای هر کشور (ایسکندر-ام، سوخو-۵۷، کا-۵۲ / جی-۲۰، جی-۱۶دی، تایپ-۰۵۵ /
#        اف-۲۲، اف-۱۵ایکس، اسم-۶ / مرکاوا-۴، دیوید اسلینگ، سائار-۶)
rep('''        dict(nm="جت آموزشی یاک-۱۳۰", ic="✈️", cat="هواگرد", price=2600, de=12, rec=5, lg=0, q=4, mins=70, up=40)],''',
    '''        dict(nm="جت آموزشی یاک-۱۳۰", ic="✈️", cat="هواگرد", price=2600, de=12, rec=5, lg=0, q=4, mins=70, up=40),
        dict(nm="موشک ایسکندر-ام", ic="🚀", cat="موشکی", price=4600, de=8,  rec=2, lg=1, q=5, mins=120, up=65),
        dict(nm="جنگنده سوخو-۵۷", ic="✈️", cat="هواگرد", price=5800, de=24, rec=7, lg=0, q=6, mins=140, up=75),
        dict(nm="بالگرد کا-۵۲ آلیگاتور", ic="🚁", cat="بالگرد", price=2900, de=14, rec=5, lg=1, q=4, mins=70, up=40)],''', "FOREIGN ru")
rep('''        dict(nm="پهپاد وینگ‌لانگ-۲", ic="🛩️", cat="هواگرد", price=1700, de=6, rec=8, lg=1, q=3, mins=50, up=25)],''',
    '''        dict(nm="پهپاد وینگ‌لانگ-۲", ic="🛩️", cat="هواگرد", price=1700, de=6, rec=8, lg=1, q=3, mins=50, up=25),
        dict(nm="جنگنده جی-۲۰", ic="✈️", cat="هواگرد", price=5600, de=23, rec=7, lg=0, q=6, mins=140, up=75),
        dict(nm="جنگنده جی-۱۶دی", ic="✈️", cat="هواگرد", price=3600, de=16, rec=7, lg=0, q=5, mins=90, up=50),
        dict(nm="ناوشکن تایپ-۰۵۵", ic="🚢", cat="دریایی", price=4400, de=21, rec=6, lg=2, q=5, mins=120, up=60)],''', "FOREIGN cn")
rep('''        dict(nm="پهپاد ام‌کیو-۹ ریپر", ic="🛩️", cat="هواگرد", price=2600, de=7, rec=9, lg=0, q=4, mins=70, up=35)],''',
    '''        dict(nm="پهپاد ام‌کیو-۹ ریپر", ic="🛩️", cat="هواگرد", price=2600, de=7, rec=9, lg=0, q=4, mins=70, up=35),
        dict(nm="جنگنده اف-۲۲ رپتور", ic="✈️", cat="هواگرد", price=5600, de=24, rec=7, lg=0, q=6, mins=140, up=75),
        dict(nm="جنگنده اف-۱۵ایکس", ic="✈️", cat="هواگرد", price=4400, de=20, rec=5, lg=1, q=5, mins=110, up=60),
        dict(nm="موشک اسم-۶", ic="🚀", cat="موشکی", price=3400, de=7,  rec=3, lg=1, q=4, mins=90, up=50)],''', "FOREIGN us")
rep('''        dict(nm="سامانه باراک-۸", ic="🚀", cat="دفاعی", price=2500, de=14, rec=3, lg=2, q=4, mins=70, up=40)],''',
    '''        dict(nm="سامانه باراک-۸", ic="🚀", cat="دفاعی", price=2500, de=14, rec=3, lg=2, q=4, mins=70, up=40),
        dict(nm="تانک مرکاوا-۴", ic="🛡️", cat="زرهی", price=3100, de=17, rec=3, lg=1, q=4, mins=80, up=45),
        dict(nm="سامانه دیوید اسلینگ", ic="🗼", cat="دفاعی", price=2900, de=17, rec=4, lg=1, q=4, mins=80, up=45),
        dict(nm="ناوچه سائار-۶", ic="🚢", cat="دریایی", price=3600, de=16, rec=6, lg=2, q=5, mins=100, up=55)],''', "FOREIGN il")

# ── ۳) فروش سلاح به متحد (eqs) — پول از خزانهٔ خریدار به فروشنده، بدون چاپ پول
rep('''        show_sub(cid, p, "🎁 " + e7["nm"] + " در راه " + tgt7.get("name", "؟") + " - تحویل ۱۰ دقیقه.", cmdr_kb(p)); return''',
    '''        show_sub(cid, p, "🎁 " + e7["nm"] + " در راه " + tgt7.get("name", "؟") + " - تحویل ۱۰ دقیقه.", cmdr_kb(p)); return
    if act.startswith("eqs:"):
        v7 = act.split(":")[1]
        if not has_pact(uid, v7):
            show_sub(cid, p, "💵 فقط برای پیمان/اتحاد.", cmdr_kb(p)); return
        if not p["equip"]:
            show_sub(cid, p, "زرادخانه خالی است.", cmdr_kb(p)); return
        if cd_left(p, "eqg" + v7) > 0:
            show_sub(cid, p, f"⏳ {fa(cd_left(p, 'eqg' + v7))} ثانیه صبر کن.", cmdr_kb(p)); return
        tgt7 = (worlds.get(p.get("gid") or "0", {}).get("pdata") or {}).get(v7)
        if tgt7 is None:
            show_sub(cid, p, "این فرمانده در دسترس نیست.", cmdr_kb(p)); return
        pe7 = p["equip"][-1]
        base7 = next((x["price"] for x in list(EQUIP) + [x2 for xs in FOREIGN.values() for x2 in xs] if x["nm"] == pe7["nm"]), 400)
        pr7 = int(round(base7 * 0.5 / 10) * 10)
        if int(tgt7.get("treasury", 0)) < pr7:
            show_sub(cid, p, "💵 خزانه فرمانده مقصد کافی نیست (" + fm(pr7) + ").", cmdr_kb(p)); return
        e7 = p["equip"].pop()
        tgt7["treasury"] = int(tgt7.get("treasury", 0)) - pr7
        p["treasury"] = int(p.get("treasury", 0)) + pr7
        tgt7.setdefault("deliveries", []).append(dict(e=dict(e7), at=now + 600))
        cd_set(p, "eqg" + v7, 600)
        aud(p, "فروش سلاح به متحد", e7["ic"] + " " + e7["nm"] + " → " + tgt7.get("name", "؟") + " (+" + fm(pr7) + ")")
        aud(tgt7, "خرید سلاح از متحد", e7["nm"] + " از " + p["name"] + " (-" + fm(pr7) + ")")
        news(f"🤝 {p['name']} یک {e7['nm']} به {tgt7.get('name')} فروخت")
        try:
            tg("sendMessage", chat_id=int(v7), parse_mode="HTML",
               text="💵 " + esc(p["name"]) + " یک " + esc(e7["nm"]) + " به تو فروخت (" + fm(pr7) + "$) - ۱۰ دقیقه دیگر تحویل می‌شود.")
        except Exception:
            pass
        show_sub(cid, p, "💵 " + e7["nm"] + " در راه " + tgt7.get("name", "؟") + " - درآمد: " + fm(pr7), cmdr_kb(p)); return''', "eqs handler")

# ── ۴) دکمه فروش کنار هدیه
rep('''            rows.append([btn(p["uid"], f"🎁 اهدای سلاح به {w2.get('name', '؟')}", "eqg:" + u2)])''',
    '''            rows.append([btn(p["uid"], f"🎁 اهدای سلاح به {w2.get('name', '؟')}", "eqg:" + u2),
                         btn(p["uid"], f"💵 فروش سلاح به {w2.get('name', '؟')}", "eqs:" + u2)])''', "eqs button")

io.open(PATH, "w", encoding="utf-8").write(src)
print("S14 applied:", n0, "->", len(src), "chars")
