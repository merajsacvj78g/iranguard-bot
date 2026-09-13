# -*- coding: utf-8 -*-
"""S13: تسلیحات خارجی حزبی + اسرائیل + تولید منطقه‌ای سلاح + اهدای سلاح + فیکس مستعمره/سقوط."""
import io

s = io.open("bot.py", encoding="utf-8").read()

# ═══ ۱) فیکس برخورد مستعمره/سقوط: مستعمره فقط اگر مدافع هنوز منطقه‌ای داشته باشد ═══
OLD = '''            if d is not None and rk == d.get("city"):
                if col0.get(aid, {}).get("master") == did and p.get("city") == rk:'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''            if d is not None and rk == d.get("city") and any(st["rs"][x2]["owner"] == did for x2 in REGIONS):
                if col0.get(aid, {}).get("master") == did and p.get("city") == rk:''')

# ═══ ۲) اسرائیل ═══
OLD = ''' "us": dict(nm="آمریکا", fl="🇺🇸", econ=95, ind=90, de=95, st=70, rel=-25),'''
assert s.count(OLD) == 1
s = s.replace(OLD, OLD + '''
 "il": dict(nm="اسرائیل", fl="🇮🇱", econ=80, ind=75, de=90, st=65, rel=-30),''')
OLD = '''SELLERS = {"ru": [0.85, 0], "cn": [0.9, 0], "tr": [1.0, 10], "br": [1.0, 15], "kr": [1.05, 15],
           "de": [1.15, 25], "fr": [1.15, 25], "it": [1.1, 20], "us": [1.2, 40], "uk": [1.2, 35]}'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''SELLERS = {"ru": [0.85, 0], "cn": [0.9, 0], "tr": [1.0, 10], "br": [1.0, 15], "kr": [1.05, 15],
           "de": [1.15, 25], "fr": [1.15, 25], "it": [1.1, 20], "us": [1.2, 40], "uk": [1.2, 35], "il": [1.3, 40]}''')
OLD = '''friends=["us", "uk", "fr", "de"], foes=["ru", "cn", "iq"],'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''friends=["us", "uk", "fr", "de", "il"], foes=["ru", "cn", "iq"],''')

# ═══ ۳) کاتالوگ خارجی - فقط با حزب درست ═══
OLD = '''COMMS = [("energy", "⛽ انرژی", 100),'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''FOREIGN = {
 "ru": [dict(nm="جنگنده سوخو-۳۵اس", ic="✈️", cat="هواگرد", price=4200, de=18, rec=6, lg=0, q=5, mins=100, up=60),
        dict(nm="تانک تی-۹۰ام", ic="🛡️", cat="زرهی", price=3200, de=16, rec=2, lg=1, q=4, mins=75, up=50),
        dict(nm="سامانه اس-۴۰۰", ic="🗼", cat="دفاعی", price=3600, de=20, rec=5, lg=1, q=5, mins=95, up=55),
        dict(nm="پدافند پانتسیر-اس۱", ic="🚛", cat="زرهی", price=1900, de=10, rec=4, lg=3, q=3, mins=55, up=30),
        dict(nm="جت آموزشی یاک-۱۳۰", ic="✈️", cat="هواگرد", price=2600, de=12, rec=5, lg=0, q=4, mins=70, up=40)],
 "cn": [dict(nm="جنگنده جی-۱۰سی", ic="✈️", cat="هواگرد", price=3800, de=17, rec=6, lg=0, q=5, mins=95, up=55),
        dict(nm="تانک وی‌تی-۴", ic="🛡️", cat="زرهی", price=3000, de=15, rec=2, lg=1, q=4, mins=70, up=45),
        dict(nm="سامانه اچ‌کیو-۹بی‌ای", ic="🗼", cat="دفاعی", price=3300, de=19, rec=4, lg=1, q=5, mins=90, up=50),
        dict(nm="پهپاد چ-۵", ic="🛩️", cat="هواگرد", price=1500, de=5, rec=7, lg=1, q=3, mins=45, up=20),
        dict(nm="پهپاد وینگ‌لانگ-۲", ic="🛩️", cat="هواگرد", price=1700, de=6, rec=8, lg=1, q=3, mins=50, up=25)],
 "us": [dict(nm="تانک ام۱آ۲ آبرامز", ic="🛡️", cat="زرهی", price=3400, de=16, rec=2, lg=1, q=4, mins=75, up=50),
        dict(nm="اف-۱۶ بلوک ۷۰", ic="✈️", cat="هواگرد", price=4000, de=18, rec=6, lg=0, q=5, mins=100, up=60),
        dict(nm="پاتریوت پی‌ای‌سی-۳", ic="🗼", cat="دفاعی", price=3500, de=19, rec=5, lg=1, q=5, mins=95, up=55),
        dict(nm="سامانه ثاد", ic="🗼", cat="دفاعی", price=4200, de=22, rec=5, lg=0, q=5, mins=110, up=65),
        dict(nm="پهپاد ام‌کیو-۹ ریپر", ic="🛩️", cat="هواگرد", price=2600, de=7, rec=9, lg=0, q=4, mins=70, up=35)],
 "il": [dict(nm="اف-۳۵آی ادیر", ic="✈️", cat="هواگرد", price=5200, de=22, rec=8, lg=0, q=5, mins=120, up=70),
        dict(nm="پدافند ارو-۳", ic="🗼", cat="دفاعی", price=4000, de=21, rec=5, lg=0, q=5, mins=100, up=60),
        dict(nm="گنبد آهنین", ic="🗼", cat="دفاعی", price=2800, de=15, rec=3, lg=2, q=4, mins=80, up=45),
        dict(nm="پهپاد هرون-تی‌پی", ic="🛩️", cat="هواگرد", price=2400, de=6, rec=9, lg=1, q=4, mins=65, up=35),
        dict(nm="سامانه باراک-۸", ic="🚀", cat="دفاعی", price=2500, de=14, rec=3, lg=2, q=4, mins=70, up=40)],
}

def fstock(p, ck):
    """سلاح خارجی فقط با حزب درست: جمهوری اسلامی ← روسیه/چین - پهلوی ← آمریکا/اسرائیل"""
    ident = p.get("ident")
    if ident == "rep" and ck in ("ru", "cn"): return FOREIGN[ck]
    if ident == "pah" and ck in ("us", "il"): return FOREIGN[ck]
    return []

COMMS = [("energy", "⛽ انرژی", 100),''')

# ═══ ۴) بخش ویژه در فروشگاه ═══
OLD = '''    L += ["━" * 20, "در مسیر تحویل: " + fa(len(p["deliveries"]))]
    return "\\n".join(L), pages'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''    fs2 = fstock(p, ck)
    if fs2 and rel >= minrel + 20:
        L += ["━" * 20, f"🎖 سامانه‌های ویژه {c['nm']} - فقط برای حزب تو"]
        for j2, e2 in enumerate(fs2):
            pr2 = int(round(e2["price"] * pm * 1.15 / 10) * 10)
            L.append(f"{e2['ic']} <b>{e2['nm']}</b> - 💳 {fm(pr2)} - ⏳ {fa(e2['mins'] + 20)} دقیقه")
    elif ck in FOREIGN:
        L += ["━" * 20, "🎖 این کشور سامانه ویژه فقط به حزب متحدش می‌فروشد." +
              ("حزب تو هم‌سو نیست ✋" if not fs2 else "روابط بیشتر لازم (+20).")]
    L += ["━" * 20, "در مسیر تحویل: " + fa(len(p["deliveries"]))]
    return "\\n".join(L), pages''')

# ═══ ۵) مسیر fbuy ═══
OLD = '''    if act == "rfn":'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''    if act.startswith("fbuy:"):
        _, ck3, j3 = act.split(":")
        fs3 = fstock(p, ck3)
        if not fs3 or ck3 not in FOREIGN:
            show_sub(cid, p, "✋ این کشور به حزب تو سلاح نمی‌فروشد - حزب درست را انتخاب کن.", shop_kb(p, ck3)); return
        if int(j3) >= len(fs3): show_sub(cid, p, "این سامانه موجود نیست.", shop_kb(p, ck3)); return
        e3 = fs3[int(j3)]
        mult3, minrel3 = SELLERS.get(ck3, [1.0, 0])
        if crel(p, ck3) < minrel3 + 20:
            show_sub(cid, p, f"⛔️ روابط بیشتر لازم: حداقل {fa(minrel3 + 20)}", shop_kb(p, ck3)); return
        pm3 = max(0.8, min(1.8, smult(ck3) - crel(p, ck3) / 250))
        pr3 = int(round(e3["price"] * pm3 * 1.15 / 10) * 10)
        if p["treasury"] < pr3:
            show_sub(cid, p, f"💳 {fm(pr3)} لازم است - خزانه: {fm(p['treasury'])}", shop_kb(p, ck3)); return
        if cd_left(p, "fbuy" + ck3) > 0:
            show_sub(cid, p, f"⏳ {fa(cd_left(p, 'fbuy' + ck3))} ثانیه صبر کن.", shop_kb(p, ck3)); return
        p["treasury"] -= pr3
        p["deliveries"].append(dict(e=dict(e3), at=now + (e3["mins"] + 20) * 60))
        cd_set(p, "fbuy" + ck3, 900)
        aud(p, "خرید تسلیحات خارجی", e3["nm"] + " از " + world["countries"][ck3]["nm"] + " - " + fm(pr3))
        news("🛒 خرید سامانه خارجی: " + e3["nm"] + " از " + world["countries"][ck3]["nm"])
        show_sub(cid, p, "✅ سفارش خارجی ثبت شد: " + e3["ic"] + " " + e3["nm"] + "\\n⏳ تحویل " + fa(e3["mins"] + 20) + " دقیقه\\n💳 " + fsm(-pr3), shop_kb(p, ck3)); return
''' + OLD)

# ═══ ۶) دکمه‌های فروشگاه ویژه ═══
OLD = '''def shop_kb(p, ck, page=0):'''
i = s.find(OLD)
assert i > 0
j = s.find("return kb(rows)", i)
assert j > 0
seg_end = j + len("return kb(rows)")
seg = s[i:j]
NEWSEG = seg + '''
    fs3 = fstock(p, ck)
    if fs3:
        rel3 = crel(p, ck)
        minrel3 = SELLERS.get(ck, [1.0, 0])[1]
        if rel3 >= minrel3 + 20:
            cur = []
            for j3 in range(len(fs3)):
                cur.append(btn(p["uid"], FOREIGN[ck][j3]["ic"], f"fbuy:{ck}:{j3}"))
                if len(cur) == 3:
                    rows.append(cur); cur = []
            if cur: rows.append(cur)
'''
s = s[:i] + NEWSEG + s[seg_end:]

# ═══ ۷) تولید منطقه‌ای سلاح - هر منطقه یک تخصص ═══
OLD = '''def settle(p):'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''ARMS = {"thr": "سامانه باور-۳۷۳", "esf": "تانک کرار", "khz": "موشک فتح-۱۱۰", "msd": "پهپاد شاهد-۱۲۹",
        "frs": "ناوشکن جماران", "hrm": "بالگرد طوفان-۲", "azb": "نفربر بوراق", "urm": "خودروی سفیر",
        "khr": "توپخانه رعد-۲", "sis": "پهپاد مجاهد-۶", "krn": "پدافند خرداد-۱۵", "gil": "رادار مطلع‌الفجر"}

def arms_produce(p, hrs):
    """صنایع دفاعی منطقه‌ای: هر منطقه با کارخانه و توسعه، هر ۲ ساعت یک واحد تخصصی می‌سازد"""
    made = []
    for rk, nm3 in ARMS.items():
        if rk not in my_regions(p):
            continue
        r3 = p["regions"][rk]
        if r3.get("bl", {}).get("fac", 0) < 1 or r3.get("dev", 0) < 55:
            continue
        last3 = (p.setdefault("arms", {}).get(rk) or 0)
        steps = int((time.time() - last3) // 7200)
        if steps < 1:
            continue
        e3 = next((x for x in EQUIP if x["nm"] == nm3), None)
        if e3 is None or p["treasury"] < 200:
            continue
        p["arms"][rk] = time.time()
        p["treasury"] -= 200
        p["equip"].append(dict(e3))
        made.append(nm3)
        aud(p, "تولید صنایع دفاعی", f"{nm3} در {REGIONS[rk]['nm']}")
    if made:
        news("🏭 تولیدات این دوره: " + " - ".join(made))
        addxp(p, 8)

def settle(p):''')

# ═══ ۸) اجرا در settle ═══
OLD = '''    col9 = world.get("col", {}).get(p["uid"])'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''    arms_produce(p, hrs)
''' + OLD)

# ═══ ۹) اهدای سلاح به متحد (ترید سلاح) ═══
OLD = '''    if act.startswith("csl:"):'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''    if act.startswith("eqg:"):
        v7 = act.split(":")[1]
        if not has_pact(uid, v7):
            show_sub(cid, p, "🎁 فقط برای پیمان/اتحاد.", cmdr_kb(p)); return
        if not p["equip"]:
            show_sub(cid, p, "زرادخانه خالی است.", cmdr_kb(p)); return
        if cd_left(p, "eqg" + v7) > 0:
            show_sub(cid, p, f"⏳ {fa(cd_left(p, 'eqg' + v7))} ثانیه صبر کن.", cmdr_kb(p)); return
        tgt7 = (worlds.get(p.get("gid") or "0", {}).get("pdata") or {}).get(v7)
        if tgt7 is None:
            show_sub(cid, p, "این فرمانده در دسترس نیست.", cmdr_kb(p)); return
        e7 = p["equip"].pop()
        tgt7.setdefault("deliveries", []).append(dict(e=dict(e7), at=now + 600))
        cd_set(p, "eqg" + v7, 600)
        aud(p, "اهدای سلاح به متحد", e7["ic"] + " " + e7["nm"] + " → " + tgt7.get("name", "؟"))
        aud(tgt7, "دریافت سلاح از متحد", e7["nm"] + " از " + p["name"])
        news(f"🎁 {p['name']} یک {e7['nm']} به {tgt7.get('name')} هدیه داد")
        try:
            tg("sendMessage", chat_id=int(v7), parse_mode="HTML",
               text="🎁 " + esc(p["name"]) + " یک " + esc(e7["nm"]) + " برایت فرستاد - ۱۰ دقیقه دیگر تحویل می‌شود.")
        except Exception:
            pass
        show_sub(cid, p, "🎁 " + e7["nm"] + " در راه " + tgt7.get("name", "؟") + " - تحویل ۱۰ دقیقه.", cmdr_kb(p)); return
''' + OLD)

# ═══ ۱۰) دکمه هدیه در پنل ═══
OLD = '''        if has_pact(p["uid"], u2):
            rows.append([btn(p["uid"], f"💔 لغو پیمان با {w2.get('name', '؟')} - $1,000", "pac:brk:" + u2)])'''
assert s.count(OLD) == 1
s = s.replace(OLD, OLD + '''
            rows.append([btn(p["uid"], f"🎁 اهدای سلاح به {w2.get('name', '؟')}", "eqg:" + u2)])''')

# ═══ ۱۱) فیلد arms در migrate ═══
OLD = '''city=None, cargos=[], exports=[], refines=[]).items():'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''city=None, cargos=[], exports=[], refines=[], arms={}).items():''')

io.open("bot.py", "w", encoding="utf-8").write(s)
print("S13 OK -", len(s.splitlines()), "lines")
