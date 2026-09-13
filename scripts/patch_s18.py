# -*- coding: utf-8 -*-
"""S18: حزب هر منطقه (جمهوری اسلامی/پهلوی - منطقه به منطقه) + منطقه ۱۳: البرز (کرج) +
تغییر حزب منطقه با پول + اثر حزب بر رضایت در تسویه + نمایش حزب در نقشه/منطقه + هم‌سویی خودکار هویت با cset."""
import io

PATH = "bot.py"
src = io.open(PATH, encoding="utf-8").read()
n0 = len(src)

def rep(old, new, tag):
    global src
    assert src.count(old) == 1, "anchor NOT unique/found: " + tag
    src = src.replace(old, new, 1)

# ── ۱) حزب پیش‌فرض هر منطقه + منطقه جدید البرز (کرج)
party_map = {
    "thr": "rep", "esf": "rep", "khz": "rep", "khr": "rep", "sis": "rep", "krn": "rep",
    "frs": "pah", "msd": "pah", "hrm": "pah", "azb": "pah", "urm": "pah", "gil": "pah",
}
anchors = {
    "thr": 'out=dict(industrial=3, strategic=2), need=dict(food=3, energy=3)),',
    "esf": 'out=dict(industrial=5), need=dict(mineral=3, food=1)),',
    "khz": 'out=dict(energy=4, oil=4), need=dict(food=2, industrial=1)),',
    "frs": 'out=dict(food=6), need=dict(energy=1)),',
    "khr": 'out=dict(mineral=6, strategic=1), need=dict(food=2, energy=1)),',
    "azb": 'out=dict(industrial=4), need=dict(mineral=2, energy=2)),',
    "msd": 'out=dict(oil=5, strategic=1), need=dict(food=2, industrial=1)),',
    "urm": 'out=dict(food=4, mineral=1), need=dict(energy=1, industrial=1)),',
    "sis": 'out=dict(mineral=4, strategic=2), need=dict(food=1)),',
    "gil": 'out=dict(food=5), need=dict(industrial=1)),',
    "krn": 'out=dict(mineral=7), need=dict(food=2, energy=1)),',
    "hrm": 'out=dict(energy=3, industrial=1), need=dict(food=1)),',
}
for rk, anc in anchors.items():
    assert src.count(anc) == 1, "region anchor: " + rk
    src = src.replace(anc, anc[:-2] + f', party="{party_map[rk]}"),', 1)

rep(''' "hrm": dict(nm="هرمزگان", tp="🚢 بندری - صادراتی", pop=1.9, ind=1, mine=2, en=3, ag=0, port=2, air=0, inc=138, sec=52, dev=45, fl="تنگ جهانی و اسکله‌ها",
             out=dict(energy=3, industrial=1), need=dict(food=1), party="pah"),
}''',
    ''' "hrm": dict(nm="هرمزگان", tp="🚢 بندری - صادراتی", pop=1.9, ind=1, mine=2, en=3, ag=0, port=2, air=0, inc=138, sec=52, dev=45, fl="تنگ جهانی و اسکله‌ها",
             out=dict(energy=3, industrial=1), need=dict(food=1), party="pah"),
 "alz": dict(nm="البرز", tp="🏭 صنعتی - حمل‌ونقل", pop=2.1, ind=3, mine=1, en=1, ag=2, port=0, air=0, inc=140, sec=62, dev=56, fl="کرج - کریدور غربی پایتخت",
             out=dict(industrial=3, food=1), need=dict(energy=1, mineral=1), party="pah"),
}''', "alz region")

rep('''ADJ = {  # مرز مشترک مناطق - مبنای عامل «وضعیت مرزها»
 "thr": ["gil", "esf", "azb", "khr"], "gil": ["thr", "azb"],''',
    '''ADJ = {  # مرز مشترک مناطق - مبنای عامل «وضعیت مرزها»
 "thr": ["gil", "esf", "azb", "khr", "alz"], "gil": ["thr", "azb"],''', "ADJ thr")
rep(''' "urm": ["azb"], "msd": ["khz", "frs"],
}''',
    ''' "urm": ["azb"], "msd": ["khz", "frs"], "alz": ["thr"],
}''', "ADJ alz")

rep('''        "khr": "توپخانه رعد-۲", "sis": "پهپاد مجاهد-۶", "krn": "پدافند خرداد-۱۵", "gil": "رادار مطلع‌الفجر"}''',
    '''        "khr": "توپخانه رعد-۲", "sis": "پهپاد مجاهد-۶", "krn": "پدافند خرداد-۱۵", "gil": "رادار مطلع‌الفجر",
        "alz": "موشک قیام-۱"}

PARTY_NM = {"rep": "جمهوری اسلامی", "pah": "پهلوی"}
PARTY_IC = {"rep": "🕌", "pah": "👑"}''', "ARMS + PARTY")

# ── ۲) مهاجرت: حزب ذخیره‌شده برای دنیاهای موجود
rep('''    for rk in REGIONS: st["rs"].setdefault(rk, dict(owner=None, status="neutral", hist=[]))''',
    '''    for rk in REGIONS: st["rs"].setdefault(rk, dict(owner=None, status="neutral", hist=[]))
    for rk in REGIONS: st["rs"][rk].setdefault("party", REGIONS[rk]["party"])''', "ensure_world party seed")

# ── ۳) نمایش حزب در نمای منطقه
rep('''         f"{rv['fl']}" + (f" - فرماندار: {_own[2]}" if _own else " - بی‌طرف"),''',
    '''         f"{rv['fl']}" + (f" - فرماندار: {_own[2]}" if _own else " - بی‌طرف"),
         f"🏛 حزب منطقه: {PARTY_IC[world['rs'][rk].get('party') or rv['party']]} {PARTY_NM[world['rs'][rk].get('party') or rv['party']]}",''', "reg_text party")

# ── ۴) نمایش حزب در نقشه
rep('''        line = f"{icon} {rv['nm']} - {lbl}"
        L.append(line)''',
    '''        pk2 = x.get("party") or rv["party"]
        line = f"{icon} {rv['nm']} {PARTY_IC.get(pk2, '')} - {lbl}"
        L.append(line)''', "map_text party")
rep('''    L += ["━" * 20, "🟢 تحت کنترل تو - 🟡 مورد مناقشه - 🔴 دشمن - ⚪ بی‌طرف",''',
    '''    L += ["━" * 20, "🟢 تحت کنترل تو - 🟡 مناقشه - 🔴 دشمن - ⚪ بی‌طرف - 🕌 جمهوری اسلامی - 👑 پهلوی",''', "map legend")

# ── ۵) اثر حزب بر رضایت در تسویه (هم‌سو +۱ تا سقف ۸۰، مخالف −۲ تا کف ۲۵ - بدون حلقه مرگ)
rep('''    p["income_hour"] = int(net)
    arms_produce(p, hrs)''',
    '''    p["income_hour"] = int(net)
    for rk in my_regions(p):
        pk2 = world.get("rs", {}).get(rk, {}).get("party") or REGIONS[rk]["party"]
        rr = p["regions"][rk]
        rr["sat"] = min(80, int(rr.get("sat", 60)) + 1) if pk2 == p.get("ident") else max(25, int(rr.get("sat", 60)) - 2)
    arms_produce(p, hrs)''', "settle party drift")

# ── ۶) دکمه تغییر حزب منطقه در نمای سازه‌ها (همان kb نمای شهر)
rep('''    if nav: rows.append(nav)
    rows.append([btn(p["uid"], "🏙 شهرها", "regs"), btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)''',
    '''    if nav: rows.append(nav)
    rows.append([btn(p["uid"], "🏛 هم‌سوسازی حزب منطقه - $1,500", "ptf:" + rk)])
    rows.append([btn(p["uid"], "🏙 شهرها", "regs"), btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)''', "build_kb party button")

# ── ۷) هندلر تغییر حزب (قبل از bld:)
rep('''    if act.startswith("bld:"):''',
    '''    if act.startswith("ptf:"):
        rk = act.split(":")[1]
        if rk not in p["regions"]:
            show_sub(cid, p, "این منطقه مال تو نیست.", build_kb(p, rk)); return
        cur = world["rs"].get(rk, {}).get("party") or REGIONS[rk]["party"]
        if cur == p.get("ident"):
            show_sub(cid, p, "🏛 این منطقه از قبل هم‌سوی حزب توست.", build_kb(p, rk)); return
        if cd_left(p, "ptf" + rk) > 0:
            show_sub(cid, p, f"⏳ {fa(cd_left(p, 'ptf' + rk) // 3600)} ساعت صبر کن.", build_kb(p, rk)); return
        if p["treasury"] < 1500:
            show_sub(cid, p, f"هم‌سوسازی حزب {fm(1500)} هزینه دارد - خزانه: {fm(p['treasury'])}.", build_kb(p, rk)); return
        p["treasury"] -= 1500
        world["rs"][rk]["party"] = p["ident"]
        cd_set(p, "ptf" + rk, 21600)
        news(f"🏛 حزب {REGIONS[rk]['nm']} هم‌سوی {PARTY_NM[p['ident']]} شد")
        aud(p, "هم‌سوسازی حزب منطقه", REGIONS[rk]["nm"] + " → " + PARTY_NM[p["ident"]])
        show_sub(cid, p, "🏛 " + REGIONS[rk]["nm"] + " اکنون هم‌سوی " + PARTY_NM[p["ident"]] + " است - رضایت از تسویه بعد اصلاح می‌شود.", build_kb(p, rk)); return
    if act.startswith("bld:"):''', "ptf handler")

# ── ۸) انتخاب شهر = حزب آن منطقه (هویت خودکار هم‌سو می‌شود)
rep('''        p["city"] = rk
        rs_claim(p, rk)
        aud(p, "ادعای شهر", REGIONS[rk]["nm"])
        news(f"🏙 {p['name']} فرمانداری {REGIONS[rk]['nm']} را بر عهده گرفت")
        show_menu(p, cid); return''',
    '''        p["city"] = rk
        rs_claim(p, rk)
        pk3 = world["rs"].get(rk, {}).get("party") or REGIONS[rk]["party"]
        if p.get("ident") != pk3:
            p["ident"] = pk3
            aud(p, "هم‌سویی با حزب منطقه", REGIONS[rk]["nm"] + " → " + PARTY_NM[pk3])
        aud(p, "ادعای شهر", REGIONS[rk]["nm"])
        news(f"🏙 {p['name']} فرمانداری {REGIONS[rk]['nm']} را بر عهده گرفت ({PARTY_NM[pk3]})")
        show_menu(p, cid); return''', "cset party align")

io.open(PATH, "w", encoding="utf-8").write(src)
print("S18 applied:", n0, "->", len(src), "chars")
