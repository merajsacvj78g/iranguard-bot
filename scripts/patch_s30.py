# -*- coding: utf-8 -*-
# S30: حساب کتاب دقیق پول (mpay/mearn + گردش خزانه) + جمعیت واقعی هر شهر
#      + منوی ۵صفحه‌ای بخش‌بندی‌شده رنگی + اعلان گروهی ریست کامل
import io

s = io.open("bot.py", encoding="utf-8").read()
REPS = []


def rep(old, new, tag):
    REPS.append((old, new, tag))


# ── ۱) توابع mpay/mearn - دفتر گردش خزانه ─────────────────────────────
rep('''def pk(a, b):
    return "|".join(sorted([str(a), str(b)]))''',
    '''def _mlog(wp, amt, why):
    try:
        lg = wp.setdefault("mlog", [])
        lg.append([int(time.time()), int(amt), str(why)[:26]])
        del lg[:-14]
    except Exception:
        pass


def mpay(p, amt, why=""):
    """پرداخت دقیق - همیشه عدد صحیح، خزانه هرگز منفی، ثبت در گردش خزانه"""
    amt = int(round(amt))
    if amt <= 0 or p.get("treasury", 0) < amt:
        return False
    p["treasury"] = int(p["treasury"]) - amt
    _mlog(p, -amt, why or "پرداخت")
    return True


def mearn(p, amt, why=""):
    """درآمد دقیق - همیشه عدد صحیح، ثبت در گردش خزانه"""
    amt = int(round(amt))
    if amt <= 0:
        return False
    p["treasury"] = int(p.get("treasury", 0)) + amt
    _mlog(p, amt, why or "درآمد")
    return True


def pk(a, b):
    return "|".join(sorted([str(a), str(b)]))''', "mpay_mearn")

# ── ۲) تیک درآمد ملی - دقیق و ثبت‌شده ─────────────────────────────────
rep('''    p["treasury"] = max(0, int(round(p["treasury"] + net * hrs)))''',
    '''    if net >= 0:
        mearn(p, net * hrs, "درآمد ملی")
    else:
        _neg = int(round(-net * hrs))
        p["treasury"] = max(0, int(p.get("treasury", 0)) - _neg)
        _mlog(p, -_neg, "هزینه‌های ملی")''', "income_tick")

# ── ۳) باج مستعمره - ثبت دوطرفه ───────────────────────────────────────
rep('''                trib = min(trib, int(p["treasury"]))
                p["treasury"] = int(p.get("treasury", 0)) - trib
                mp2["treasury"] = int(mp2.get("treasury", 0)) + trib''',
    '''                trib = min(trib, int(p["treasury"]))
                p["treasury"] = int(p.get("treasury", 0)) - trib
                mp2["treasury"] = int(mp2.get("treasury", 0)) + trib
                _mlog(p, -trib, "باج به ارباب")
                _mlog(mp2, trib, "باج از مستعمره")''', "tribute")

rep('''        p["treasury"] = int(p.get("treasury", 0)) + int(8 * slv9 * hrs)''',
    '''        mearn(p, int(8 * slv9 * hrs), "کار بردگان")''', "slave_income")

# ── ۴) حقوق نیروی متحد ────────────────────────────────────────────────
rep('''            if p["treasury"] >= pay:
                p["treasury"] -= pay
                fc3["last"] = now''',
    '''            if p["treasury"] >= pay:
                p["treasury"] = int(p["treasury"]) - int(pay)
                _mlog(p, -int(pay), "حقوق نیروی متحد")
                fc3["last"] = now''', "forces_pay")

# ── ۵) تسویه صادرات نفت ───────────────────────────────────────────────
rep('''            pay2 = int(round(world["market"]["oil"] * 20 * 1.08))
            p["treasury"] = int(p.get("treasury", 0)) + pay2''',
    '''            pay2 = int(round(world["market"]["oil"] * 20 * 1.08))
            mearn(p, pay2, "صادرات نفت")''', "oil_export")

# ── ۶) جنگ: خسارت و کمک‌هزینه پیروزی ──────────────────────────────────
rep('''        p["treasury"] = max(0, p["treasury"] - dmg * 150)''',
    '''        _dm = int(round(dmg * 150))
        p["treasury"] = max(0, int(p.get("treasury", 0)) - _dm)
        _mlog(p, -_dm, "خسارت جنگ")''', "war_dmg")

rep('''        p["won_wars"] += 1; p["sat"] = min(100, p["sat"] + 6); p["treasury"] += 1200; addxp(p, 50)''',
    '''        p["won_wars"] += 1; p["sat"] = min(100, p["sat"] + 6); mearn(p, 1200, "کمک‌هزینه پیروزی"); addxp(p, 50)''', "war_win")

# ── ۷) تصمیم‌های ملی ──────────────────────────────────────────────────
rep('''        p["treasury"] -= 800; p["sat"] = min(100, p["sat"] + 5)''',
    '''        mpay(p, 800, "یارانه سوخت"); p["sat"] = min(100, p["sat"] + 5)''', "dec_sub_up")

rep('''        p["treasury"] += 600; p["sat"] = max(5, p["sat"] - 5)''',
    '''        mearn(p, 600, "کاهش یارانه"); p["sat"] = max(5, p["sat"] - 5)''', "dec_sub_dn")

rep('''        p["treasury"] += 1000; p["sanctions"] = max(0, p["sanctions"] - 1)''',
    '''        mearn(p, 1000, "سرمایه‌گذاری خارجی"); p["sanctions"] = max(0, p["sanctions"] - 1)''', "dec_fdi")

rep('''        p["treasury"] -= 1200; p["budget"]["con"] = min(40, p["budget"]["con"] + 2)''',
    '''        mpay(p, 1200, "شهر جدید"); p["budget"]["con"] = min(40, p["budget"]["con"] + 2)''', "dec_newcity")

# ── ۸) تغییر هویت / اتحاد / استقرار / لغو پیمان ───────────────────────
rep('''            p["treasury"] -= 5000; p["sat"] = max(5, p["sat"] - 10); p["stab"] = max(5, p["stab"] - 5)''',
    '''            mpay(p, 5000, "تغییر هویت ملی"); p["sat"] = max(5, p["sat"] - 10); p["stab"] = max(5, p["stab"] - 5)''', "ident_chg")

rep('''            p["treasury"] -= 2500''',
    '''            mpay(p, 2500, "پیشنهاد اتحاد")''', "alliance")

rep('''            p["treasury"] -= 500
            world["forces"][rk0] = dict(frm=tgt, host=uid, de=de2, last=now)''',
    '''            mpay(p, 500, "استقرار نیرو")
            world["forces"][rk0] = dict(frm=tgt, host=uid, de=de2, last=now)''', "deploy")

rep('''            p["treasury"] -= 1000''',
    '''            mpay(p, 1000, "لغو پیمان")''', "pact_cancel")

# ── ۹) بازار - خرید و فروش دوطرفه ─────────────────────────────────────
rep('''        p["treasury"] -= o["price"]
        if fp: fp["treasury"] = int(fp.get("treasury", 0)) + o["price"]''',
    '''        mpay(p, o["price"], "خرید بازار")
        if fp:
            fp["treasury"] = int(fp.get("treasury", 0)) + int(o["price"])
            _mlog(fp, int(o["price"]), "فروش بازار")''', "market")

# ── ۱۰) غنیمت جنگی ────────────────────────────────────────────────────
rep('''        tgt7["treasury"] = int(tgt7.get("treasury", 0)) - pr7
        p["treasury"] = int(p.get("treasury", 0)) + pr7''',
    '''        tgt7["treasury"] = int(tgt7.get("treasury", 0)) - int(pr7)
        _mlog(tgt7, -int(pr7), "غنیمت جنگی")
        mearn(p, pr7, "غنیمت جنگی")''', "loot")

# ── ۱۱) بردگی / هم‌سوسازی (دو خط یکسان ۱۵۰۰ - با بافت) ───────────────
rep('''            show_sub(cid, p, f"بردگی کردن {fm(1500)} دارد - خزانه: {fm(p['treasury'])}", cmdr_kb(p)); return
        p["treasury"] -= 1500''',
    '''            show_sub(cid, p, f"بردگی کردن {fm(1500)} دارد - خزانه: {fm(p['treasury'])}", cmdr_kb(p)); return
        mpay(p, 1500, "بردگی کردن")''', "enslave")

rep('''            show_sub(cid, p, f"هم‌سوسازی حزب {fm(1500)} هزینه دارد - خزانه: {fm(p['treasury'])}.", build_kb(p, rk)); return
        p["treasury"] -= 1500''',
    '''            show_sub(cid, p, f"هم‌سوسازی حزب {fm(1500)} هزینه دارد - خزانه: {fm(p['treasury'])}.", build_kb(p, rk)); return
        mpay(p, 1500, "هم‌سوسازی حزب")''', "party_align")

# ── ۱۲) عملیات اعزامی / ساخت سازه (دو خط یکسان cost - با بافت) ────────
rep('''        p["treasury"] -= cost
        p["stock"]["oil"] = int(round(p["stock"].get("oil", 0))) - fuel''',
    '''        mpay(p, cost, "اعزام عملیات")
        p["stock"]["oil"] = int(round(p["stock"].get("oil", 0))) - fuel''', "ops_deploy")

rep('''            show_sub(cid, p, f"💳 خزانه کافی نیست - این ساخت {fm(cost)} لازم دارد.\\nخزانه: {fm(p['treasury'])}", build_kb(p, rk)); return
        p["treasury"] -= cost''',
    '''            show_sub(cid, p, f"💳 خزانه کافی نیست - این ساخت {fm(cost)} لازم دارد.\\nخزانه: {fm(p['treasury'])}", build_kb(p, rk)); return
        mpay(p, cost, "ساخت سازه")''', "build")

# ── ۱۳) تولید تسلیحات / بهبود روابط (دو خط یکسان ۲۰۰ - با بافت) ───────
rep('''        p["arms"][rk] = time.time()
        p["treasury"] -= 200''',
    '''        p["arms"][rk] = time.time()
        mpay(p, 200, "تولید تسلیحات")''', "arms_cost")

rep('''            show_sub(cid, p, f"بهبود روابط {fm(200)} هزینه دارد - خزانه: {fm(p['treasury'])}", cnt_kb(p, ck)); return
        p["treasury"] -= 200''',
    '''            show_sub(cid, p, f"بهبود روابط {fm(200)} هزینه دارد - خزانه: {fm(p['treasury'])}", cnt_kb(p, ck)); return
        mpay(p, 200, "بهبود روابط")''', "relations")

# ── ۱۴) بازسازی تجهیزات ───────────────────────────────────────────────
rep('''                p["treasury"] = max(0, p["treasury"] - 200)
                extra = " - هزینه بازسازی: $200"''',
    '''                p["treasury"] = max(0, int(p.get("treasury", 0)) - 200)
                _mlog(p, -200, "بازسازی تجهیزات")
                extra = " - هزینه بازسازی: $200"''', "rebuild")

# ── ۱۵) rpop - جمعیت پویا ─────────────────────────────────────────────
rep('''def arms_produce(p, hrs):''',
    '''def rpop(rk, p=None):
    """جمعیت واقعی شهر (میلیون) - با توسعه رشد می‌کند، بی‌طرف عقب می‌ماند"""
    try:
        base = float(REGIONS[rk].get("pop", 2.0))
    except Exception:
        return 0.0
    if p and rk in (p.get("regions") or {}):
        dev = p["regions"][rk].get("dev", 0) or 0
        return round(base * (1.0 + 0.02 * min(20, int(dev))), 2)
    return round(base * 0.92, 2)


def arms_produce(p, hrs):''', "rpop")

# ── ۱۶) جمعیت در انتخاب شهر ───────────────────────────────────────────
rep('''         "در این دنیا هر فرمانده یک شهر از ایران را دارد.",
         "شهر بی‌طرف (⚪) آزاد است - شهر دیگران را فقط با عملیات نظامی می‌گیری.",''',
    '''         "در این دنیا هر فرمانده یک شهر از ایران را دارد.",
         "👥 جمعیت هر شهر با توسعه رشد می‌کند - بی‌طرف عقب می‌ماند.",
         "شهر بی‌طرف (⚪) آزاد است - شهر دیگران را فقط با عملیات نظامی می‌گیری.",''', "cty_header")

rep('''        if rk in own:
            L.append(f"{STAT[own[rk][1]]} {rv['nm']} - فرماندار: {own[rk][2]}")
        elif _fs < max_regions():
            L.append(f"⚪ {rv['nm']} - {rv['tp']} (بی‌طرف - آزاد)"); _fs += 1''',
    '''        if rk in own:
            L.append(f"{STAT[own[rk][1]]} {rv['nm']} - 👥 {fnum(rpop(rk, p) * 1000000)} - فرماندار: {own[rk][2]}")
        elif _fs < max_regions():
            L.append(f"⚪ {rv['nm']} - 👥 {fnum(rpop(rk) * 1000000)} (بی‌طرف - آزاد)"); _fs += 1''', "cty_pop")

# ── ۱۷) جمعیت در شهرها و مناطق - پویا به‌جای عدد ثابت ─────────────────
rep('''        L.append(f"👥 {fnum(r['pop'] * 1000000)} - 📈 توسعه {fa(r['dev'])}٪")''',
    '''        L.append(f"👥 {fnum(rpop(rk, p) * 1000000)} - 📈 توسعه {fa(r['dev'])}٪")''', "regs_pop")

# ── ۱۸) گردش خزانه در حسابرسی ─────────────────────────────────────────
rep('''    for x in items:
        L.append(f"▪ {x['t']} - {x['who']}")
        L.append(f"   {x['what']}" + (f" - {x['det']}" if x.get("det") else ""))
    return "\\n".join(L)''',
    '''    for x in items:
        L.append(f"▪ {x['t']} - {x['who']}")
        L.append(f"   {x['what']}" + (f" - {x['det']}" if x.get("det") else ""))
    lg = (p.get("mlog") or [])[-8:][::-1]
    if lg:
        L += ["━" * 20, "💳 گردش خزانه تو (آخرین حرکت‌ها):"]
        for _t, _a, _w in lg:
            L.append(f"▪ {'+' if _a >= 0 else '−'}{fm(abs(_a))} - {_w}")
    return "\\n".join(L)''', "audit_ledger")

# ── ۱۹) منوی ۵صفحه‌ای بخش‌بندی‌شده رنگی ────────────────────────────────
rep('''def menu_kb(p, page=1):
    """منوی دوصفحه‌ای - رنگ هر بخش در همه صفحات یکسان:
    🟢 اقتصاد/بازار - 🟣 صنعت/توسعه/فناوری - 🟡 منابع/لجستیک
    🔴 دفاع/عملیات/بحران - 🔵 دیپلماسی/فرماندهان/جهان - 🟠 دستیار/رتبه - ⚪ سایر"""
    u = p["uid"]
    rows = []
    if p.get("decision"): rows.append([btn(u, "🗳️ تصمیم ملی در انتظار تو!", "dec")])
    if p.get("war"): rows.append([btn(u, "⚔️ خطر نظامی - فوری!", "war")])
    if page == 2:
        rows += [
            [btn(u, "🔴 دفاع", "de"), btn(u, "🔴 عملیات", "ops")],
            [btn(u, "🔴 بحران", "crisis"), btn(u, "🔵 دیپلماسی", "dip")],
            [btn(u, "🔵 فرماندهان", "cmdr"), btn(u, "🔵 جهان", "world")],
            [btn(u, "🟠 دستیار", "asz"), btn(u, "🟠 رتبه‌بندی", "rank")],
            [btn(u, "⚪ اخبار", "news"), btn(u, "⚙️ تنظیمات", "set")],
            [btn(u, "🌍 دنیاهای من", "wlds")],
            [btn(u, "◀️ مدیریت", "mnu:1"), btn(u, "🏠 خانه", "menu")]]
    else:
        rows += [
            [btn(u, "🇮🇷 کشور", "country"), btn(u, "🟢 اقتصاد", "eco")],
            [btn(u, "🟢 بازار", "mkt"), btn(u, "🟣 صنعت", "ind")],
            [btn(u, "🟡 منابع", "res"), btn(u, "🟡 لجستیک", "log")],
            [btn(u, "🟣 توسعه", "prj"), btn(u, "🟣 فناوری", "tech")],
            [btn(u, "⚙️ قدرت و جهان ▶️", "mnu:2"), btn(u, "🏠 خانه", "menu")]]
    return kb(rows)''',
    '''def menu_kb(p, page=1):
    """منوی ۵صفحه‌ای بخش‌بندی‌شده - رنگ هر بخش ثابت:
    🟢 اقتصاد و پول - 🟣 صنعت/توسعه/فناوری - 🟡 منابع/لجستیک/مناطق
    🔴 نظام/بحران - 🔵 سیاست/دیپلماسی/جهان - 🟠 فرماندهی/رتبه - ⚪ سیستم"""
    u = p["uid"]
    rows = []
    if p.get("decision"): rows.append([btn(u, "🗳️ تصمیم ملی در انتظار تو!", "dec")])
    if p.get("war"): rows.append([btn(u, "⚔️ خطر نظامی - فوری!", "war")])
    if page == 2:      # 🟣 صنعت و توسعه
        rows += [
            [btn(u, "🟣 صنعت", "ind"), btn(u, "🟣 توسعه", "prj")],
            [btn(u, "🟣 فناوری", "tech"), btn(u, "🟡 منابع", "res")],
            [btn(u, "🟡 لجستیک", "log"), btn(u, "🟡 انبار جنگ", "wh")],
            [btn(u, "🟡 مناطق من", "regs"), btn(u, "🗺 نقشه ایران", "map")],
            [btn(u, "◀️ وضعیت", "mnu:1"), btn(u, "🏠 خانه", "menu"), btn(u, "🔴 نظام ▶️", "mnu:3")]]
    elif page == 3:    # 🔴 نظام و بحران
        rows += [
            [btn(u, "🔴 دفاع", "de"), btn(u, "🔴 عملیات", "ops")],
            [btn(u, "🔴 بحران", "crisis"), btn(u, "⚔️ جنگ", "war")],
            [btn(u, "🎒 زرادخانه", "equip"), btn(u, "🗺 نقشه ایران", "map")],
            [btn(u, "◀️ صنعت", "mnu:2"), btn(u, "🏠 خانه", "menu"), btn(u, "🔵 سیاست ▶️", "mnu:4")]]
    elif page == 4:    # 🔵 سیاست و دیپلماسی
        rows += [
            [btn(u, "⚙️ هویت ملی", "ident"), btn(u, "🔵 دیپلماسی", "dip")],
            [btn(u, "🔵 فرماندهان", "cmdr"), btn(u, "🔵 جهان", "world")],
            [btn(u, "🟠 رتبه‌بندی", "rank"), btn(u, "🟠 دستیار", "asz")],
            [btn(u, "◀️ نظام", "mnu:3"), btn(u, "🏠 خانه", "menu"), btn(u, "⚪ سیستم ▶️", "mnu:5")]]
    elif page == 5:    # ⚪ سیستم
        rows += [
            [btn(u, "⚪ اخبار", "news"), btn(u, "⚪ تنظیمات", "set")],
            [btn(u, "🌍 دنیاهای من", "wlds"), btn(u, "📖 راهنما", "help")],
            [btn(u, "🎖 عناوین", "titles"), btn(u, "💚 سلامت سامانه", "health")],
            [btn(u, "🔄 بروزرسانی", "refresh")],
            [btn(u, "◀️ سیاست", "mnu:4"), btn(u, "🏠 خانه", "menu")]]
    else:              # ۱ 🏛 وضعیت و اقتصاد
        rows += [
            [btn(u, "🇮🇷 کشور", "country"), btn(u, "🏙 شهرهای من", "regs")],
            [btn(u, "🟢 اقتصاد", "eco"), btn(u, "🟢 بازار", "mkt")],
            [btn(u, "⚙️ بودجه", "budget"), btn(u, "🔍 حسابرسی", "audit")],
            [btn(u, "💳 فروشگاه استارز", "stars"), btn(u, "🤝 قراردادها", "trd")],
            [btn(u, "🟣 صنعت و توسعه ▶️", "mnu:2"), btn(u, "🏠 خانه", "menu")]]
    return kb(rows)''', "menu5")

# ── ۲۰) هندلر mnu تا صفحه ۵ ───────────────────────────────────────────
rep('''        pg = int(act.split(":")[1]) if act.split(":")[1] in ("1", "2") else 1''',
    '''        pg = int(act.split(":")[1]) if act.split(":")[1] in ("1", "2", "3", "4", "5") else 1''', "mnu_handler")

# ── ۲۱) تنظیمات رنگی ──────────────────────────────────────────────────
rep('''def set_kb(p):
    u = p["uid"]
    return kb([[btn(u, "💳 فروشگاه استارز", "stars")],
               [btn(u, "⚙️ هویت ملی", "ident")],
               [btn(u, "🔍 حسابرسی", "audit"), btn(u, "📖 راهنما", "help")],
               [btn(u, "🎖 عناوین", "titles"), btn(u, "💚 سلامت", "health")],
               [btn(u, "➖ مناطق", "cfgm:-"), btn(u, "🌍 " + fa(max_regions()) + " منطقه", "cfgm:0"), btn(u, "➕ مناطق", "cfgm:+")],
               [btn(u, "♻️ ریست جهان این گروه - مالک", "rst:0")],
               [btn(u, "☠️ ریست کامل همهٔ پلیرها - مالک", "rstp:0")],
               [btn(u, "🔄 بروزرسانی", "refresh"), btn(u, "🏠 خانه", "menu")]])''',
    '''def set_kb(p):
    u = p["uid"]
    return kb([[btn(u, "⚪ اخبار", "news"), btn(u, "📖 راهنما", "help")],
               [btn(u, "⚙️ هویت ملی", "ident"), btn(u, "🔍 حسابرسی", "audit")],
               [btn(u, "🎖 عناوین", "titles"), btn(u, "💚 سلامت", "health")],
               [btn(u, "🟡 ➖ مناطق", "cfgm:-"), btn(u, "🌍 " + fa(max_regions()) + " منطقه", "cfgm:0"), btn(u, "🟡 ➕ مناطق", "cfgm:+")],
               [btn(u, "♻️ ریست جهان این گروه - مالک", "rst:0")],
               [btn(u, "☠️ ریست کامل همهٔ پلیرها - مالک", "rstp:0")],
               [btn(u, "🏠 خانه", "menu")]])''', "set_kb")

# ── ۲۲) اعلان گروهی بعد از ریست کامل ──────────────────────────────────
rep('''        news("☠️ ریست کامل - همهٔ فرماندهان از صفر شروع می‌کنند")
        mark_dirty()''',
    '''        news("☠️ ریست کامل - همهٔ فرماندهان از صفر شروع می‌کنند")
        mark_dirty()
        try:
            if int(gid2):
                tg("sendMessage", chat_id=int(gid2), text="☠️ <b>ریست کامل انجام شد</b>\\n━━━━━━━━━━━━━━━━━━\\n- همهٔ فرماندهان از صفر شروع کردند\\n- خزانه $2,000 - سطح ۱ - زرادخانه خالی\\n- هر ۱۳ منطقه آزاد و بی‌طرف\\n\\nحالا «استارت» بفرست و شهرت را انتخاب کن 🏙", parse_mode="HTML")
        except Exception:
            pass''', "rstp_announce")

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
print(f"S30 applied: {len(REPS)} replacements")
