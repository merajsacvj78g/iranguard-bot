# -*- coding: utf-8 -*-
"""S11: اقتصاد نفت - صادرات قراردادی + پالایش + سوخت عملیات - ضد سفته‌بازی/پیشرفت رایگان."""
import io

s = io.open("bot.py", encoding="utf-8").read()

# ═══ ۱) کالای نفت خام ═══
OLD = '''COMMS = [("energy", "⛽ انرژی", 100), ("food", "🌾 غذا", 80), ("mineral", "⛏️ مواد", 120),'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''COMMS = [("energy", "⛽ انرژی", 100), ("oil", "🛢 نفت خام", 110), ("food", "🌾 غذا", 80), ("mineral", "⛏️ مواد", 120),''')

# ═══ ۲) تولید نفت: خوزستان و مسجدسلیمان ═══
OLD = ''' "khz": dict(nm="خوزستان", tp="🛢️ انرژی", pop=4.7, ind=3, mine=2, en=5, ag=3, port=1, air=0, inc=210, sec=58, dev=54, fl="نفت و آب",
             out=dict(energy=7), need=dict(food=2, industrial=1)),'''
assert s.count(OLD) == 1
s = s.replace(OLD, ''' "khz": dict(nm="خوزستان", tp="🛢️ انرژی", pop=4.7, ind=3, mine=2, en=5, ag=3, port=1, air=0, inc=210, sec=58, dev=54, fl="نفت و آب",
             out=dict(energy=4, oil=4), need=dict(food=2, industrial=1)),''')
OLD = '''out=dict(energy=6, strategic=1), need=dict(food=2, industrial=1)),'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''out=dict(oil=5, strategic=1), need=dict(food=2, industrial=1)),''')

# ═══ ۳) فیلدهای جدید بازیکن ═══
OLD = '''city=None, cargos=[]).items():'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''city=None, cargos=[], exports=[], refines=[]).items():''')

# ═══ ۴) سوخت عملیات - گیت + کسر در wgo ═══
OLD = '''        cost = MOB[w["typ"]] + SUPP[w["sup"]][2] + (400 if w["route"] == "s" else 0)
        if p["treasury"] < cost:
            show_sub(cid, p, f"💳 اعزام {fm(cost)} لازم دارد - خزانه: {fm(p['treasury'])}", ops_kb(p)); return
        p["treasury"] -= cost'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''        cost = MOB[w["typ"]] + SUPP[w["sup"]][2] + (400 if w["route"] == "s" else 0)
        if p["treasury"] < cost:
            show_sub(cid, p, f"💳 اعزام {fm(cost)} لازم دارد - خزانه: {fm(p['treasury'])}", ops_kb(p)); return
        fuel = FUEL[w["typ"]]
        if int(round(p["stock"].get("oil", 0))) < fuel:
            show_sub(cid, p, f"⛽ سوخت جنگی کافی نیست - {fa(fuel)} تن نفت لازم است - انبار: {fa(int(round(p['stock'].get('oil', 0))))}\\nاز بازار بخر یا مسجدسلیمان/خوزستان داشته باش.", ops_kb(p)); return
        p["treasury"] -= cost
        p["stock"]["oil"] = int(round(p["stock"].get("oil", 0))) - fuel
        aud(p, "سوخت عملیات", f"{fa(fuel)} تن نفت برای {OPN[w['typ']]}")''')

# ═══ ۵) ثابت سوخت - کنار DUR ═══
OLD = '''DUR = {"air": 12, "msl": 8, "grd": 15}'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''DUR = {"air": 12, "msl": 8, "grd": 15}
FUEL = {"air": 15, "msl": 10, "grd": 12}''')

# ═══ ۶) سوخت در صفحه بررسی نهایی ═══
OLD = """         f"💳 هزینه اعزام: {fm(MOB[w['typ']] + SUPP[w['sup']][2] + (400 if w['route'] == 's' else 0))}",\n"""
assert s.count(OLD) == 1, "review cost line"
NEW = OLD + """         f"⛽ سوخت جنگی: {fa(FUEL[w['typ']])} تن نفت - انبار: {fa(int(round(p['stock'].get('oil', 0))))}",\n"""
s = s.replace(OLD, NEW)

# ═══ ۷) پالایش و صادرات - شاخه‌های route (قبل از mbuy) ═══
OLD = '''    if act.startswith("mbuy:") or act.startswith("msell:"):'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''    if act == "rfn":
        has_ref = any(r["bl"].get("ref", 0) >= 1 for r in p["regions"].values())
        if not has_ref:
            show_sub(cid, p, "🏭 پالایش لازم است - اول یک پالایشگاه در شهر خودت بساز.", mkt_kb(p)); return
        if len([x for x in p.get("refines", []) if x.get("at") > now]) >= 2:
            show_sub(cid, p, "پالایشگاه مشغول است - بعداً دوباره.", mkt_kb(p)); return
        if int(round(p["stock"].get("oil", 0))) < 10:
            show_sub(cid, p, "🛢 ۱۰ تن نفت خام لازم است - انبار کافی نیست.", mkt_kb(p)); return
        if p["treasury"] < 30:
            show_sub(cid, p, f"هزینه پالایش {fm(30)} است - خزانه: {fm(p['treasury'])}", mkt_kb(p)); return
        if cd_left(p, "rfn") > 0:
            show_sub(cid, p, f"⏳ {fa(cd_left(p, 'rfn'))} ثانیه صبر کن.", mkt_kb(p)); return
        p["stock"]["oil"] = int(round(p["stock"].get("oil", 0))) - 10
        p["treasury"] -= 30
        p.setdefault("refines", []).append(dict(at=now + 15 * 60))
        cd_set(p, "rfn", 300)
        aud(p, "سفارش پالایش", "۱۰ تن نفت → ۸ انرژی + ۲ استراتژیک - ۱۵ دقیقه")
        show_sub(cid, p, "🏭 پالایش آغاز شد: ۱۰ تن نفت خام در امانت\\n⏳ ۱۵ دقیقه بعد: +۸ انرژی +۲ استراتژیک\\n💳 " + fsm(-30), mkt_kb(p)); return
    if act == "exn":
        if len([x for x in p.get("exports", []) if x.get("at") > now]) >= 2:
            show_sub(cid, p, "حداکثر ۲ قرارداد صادرات باز.", mkt_kb(p)); return
        if int(round(p["stock"].get("oil", 0))) < 20:
            show_sub(cid, p, "🛢 صادرات ۲۰ تن نفت خام است - انبار کافی نیست.", mkt_kb(p)); return
        if cd_left(p, "exn") > 0:
            show_sub(cid, p, f"⏳ {fa(cd_left(p, 'exn'))} ثانیه صبر کن.", mkt_kb(p)); return
        mins = max(15, 25 - nat_stats(p)["logi"] // 10)
        p["stock"]["oil"] = int(round(p["stock"].get("oil", 0))) - 20
        p.setdefault("exports", []).append(dict(at=now + mins * 60))
        cd_set(p, "exn", 600)
        aud(p, "قرارداد صادرات نفت", f"۲۰ تن - تسویه به قیمت لحظه تحویل +۸٪ - {fa(mins)} دقیقه")
        show_sub(cid, p, f"🚢 قرارداد صادرات ۲۰ تن بسته شد - نفت در امانت\\n⏳ تسویه: {fa(mins)} دقیقه دیگر به قیمت بازار همان لحظه +۸٪\\n📌 ریسک و سود با تو - قیمت تثبیت نمی‌شود", mkt_kb(p)); return
''' + OLD)

# ═══ ۸) مatur شدن صادرات/پالایش در player_tick (بعد از محموله‌ها) ═══
OLD = '''            p["stock"][c["k"]] = int(round(p["stock"].get(c["k"], 0))) + c["qty"]'''
assert s.count(OLD) == 1
s = s.replace(OLD, OLD + '''
    for ex2 in list(p.get("exports", [])):
        if ex2["at"] <= now:
            p["exports"].remove(ex2)
            pay2 = int(round(world["market"]["oil"] * 20 * 1.08))
            p["treasury"] = int(p.get("treasury", 0)) + pay2
            aud(p, "تسویه صادرات نفت", fm(pay2))
            news("🚢 قرارداد صادرات نفت " + p["name"] + " تسویه شد - " + fm(pay2))
    for rf2 in list(p.get("refines", [])):
        if rf2["at"] <= now:
            p["refines"].remove(rf2)
            p["stock"]["energy"] = int(round(p["stock"].get("energy", 0))) + 8
            p["stock"]["strategic"] = int(round(p["stock"].get("strategic", 0))) + 2
            aud(p, "پالایش کامل شد", "+۸ انرژی +۲ استراتژیک")
            news("🏭 پالایشگاه " + p["name"] + " کار کرد: +۸ انرژی +۲ استراتژیک")''')

# ═══ ۹) دکمه‌های بازار ═══
OLD = '''    rows.append([btn(p["uid"], "🔄 نوسان‌گیری", "mkt"), btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''    rows.append([btn(p["uid"], "🚢 صادرات ۲۰ تن نفت", "exn"), btn(p["uid"], "🏭 پالایش ۱۰ تن", "rfn")])
    rows.append([btn(p["uid"], "🔄 نوسان‌گیری", "mkt"), btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)''')

# ═══ ۱۰) راهنمای بازار: نفت ═══
OLD = '''          f"📦 ظرفیت انبار: {fa(int(round(sum(p['stock'].values()))))}/{fa(p['stockcap'])} تن" + (f" - 🚚 در راه: {fa(len(cg))} محموله" if cg else ""),'''
assert s.count(OLD) == 1
s = s.replace(OLD, OLD + '''
          "🛢 نفت: صادرات قراردادی (+۸٪ به قیمت لحظه تحویل) - پالایش به انرژی/استراتژیک (پالایشگاه لازم) - سوخت عملیات جنگی",''')

io.open("bot.py", "w", encoding="utf-8").write(s)
print("S11 OK -", len(s.splitlines()), "lines")
