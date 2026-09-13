# -*- coding: utf-8 -*-
"""پچ B نسخه ۸: اتحاد نظامی + استقرار نیروهای متحد + پنل - اجرا یک‌بار."""
import io

s = io.open("bot.py", encoding="utf-8").read()

# ═══ ۱) pac:yes - پشتیبانی درخواست اتحاد + سه شاخه جدید ═══
OLD1 = '''        if op2 in ("yes", "no"):
            frm = world["preq"].pop(uid, None)
            if op2 == "yes" and frm in others and frm != uid:
                world["pacts"][pk(frm, uid)] = dict(t=int(now))
                aud(p, "پیمان عدم تعرض", "با " + others[frm].get("name", "؟"))
                news(f"🤝 پیمان عدم تعرض: {others[frm].get('name')} و {p['name']}")
                wbroadcast(f"🤝 <b>پیمان عدم تعرض</b> میان {esc(others[frm].get('name'))} و {esc(p['name'])} امضا شد")
            show_sub(cid, p, cmdr_text(p), cmdr_kb(p)); return'''

NEW1 = '''        if op2 in ("yes", "no"):
            pv = world["preq"].pop(uid, None)
            frm = pv.get("frm") if isinstance(pv, dict) else pv
            knd = (pv.get("kind", "ndq") if isinstance(pv, dict) else "ndq") or "ndq"
            if op2 == "yes" and frm in others and frm != uid:
                if knd == "all" and (profiles.get(frm, {}).get("lvl", 1) < 3 or pr2.get("lvl", 1) < 3):
                    show_sub(cid, p, "🔒 اتحاد نظامی برای دو طرف سطح ۳ لازم است.", cmdr_kb(p)); return
                world["pacts"][pk(frm, uid)] = dict(t=int(now), kind=knd)
                if knd == "all":
                    aud(p, "امضای اتحاد نظامی", "با " + others[frm].get("name", "؟"))
                    news(f"🎖 اتحاد نظامی: {others[frm].get('name')} و {p['name']}")
                    wbroadcast(f"🎖 <b>اتحاد نظامی</b> میان {esc(others[frm].get('name'))} و {esc(p['name'])} امضا شد")
                else:
                    aud(p, "پیمان عدم تعرض", "با " + others[frm].get("name", "؟"))
                    news(f"🤝 پیمان عدم تعرض: {others[frm].get('name')} و {p['name']}")
                    wbroadcast(f"🤝 <b>پیمان عدم تعرض</b> میان {esc(others[frm].get('name'))} و {esc(p['name'])} امضا شد")
            show_sub(cid, p, cmdr_text(p), cmdr_kb(p)); return
        if op2 == "all":
            pmy = p["regions"].get(p.get("city") or "", {}).get("bl", {}).get("base", 0)
            kd0 = (world["pacts"].get(pk(uid, tgt)) or {}).get("kind", "ndq")
            if not has_pact(uid, tgt):
                show_sub(cid, p, "اول پیمان عدم تعرض ببندید - بعد اتحاد نظامی.", cmdr_kb(p)); return
            if kd0 == "all":
                show_sub(cid, p, "همین حالا اتحاد نظامی دارید.", cmdr_kb(p)); return
            if pr2.get("lvl", 1) < 3 or pmy < 1:
                show_sub(cid, p, "🔒 اتحاد نظامی: سطح ۳ + یک پایگاه نظامی در شهر خودت لازم است.", cmdr_kb(p)); return
            if p["treasury"] < 2500:
                show_sub(cid, p, f"پیشنهاد اتحاد {fm(2500)} دارد - خزانه: {fm(p['treasury'])}", cmdr_kb(p)); return
            if cd_left(p, "pac" + tgt) > 0:
                show_sub(cid, p, f"⏳ {fa(cd_left(p, 'pac' + tgt))} ثانیه صبر کن.", cmdr_kb(p)); return
            p["treasury"] -= 2500
            world["preq"][tgt] = dict(frm=uid, kind="all")
            cd_set(p, "pac" + tgt, 3600)
            aud(p, "پیشنهاد اتحاد نظامی", "به " + others[tgt].get("name", "؟") + " - $2,500")
            try:
                tg("sendMessage", chat_id=int(tgt), parse_mode="HTML",
                   text="🎖 <b>پیشنهاد اتحاد نظامی</b> از " + esc(p["name"]) + "\\nدر ربات: 🤝 فرماندهان")
            except Exception:
                pass
            show_sub(cid, p, "✅ پیشنهاد اتحاد ارسال شد.", cmdr_kb(p)); return
        if op2 == "frc":
            rk0 = p.get("city")
            pmy = p["regions"].get(rk0 or "", {}).get("bl", {}).get("base", 0)
            kd0 = (world["pacts"].get(pk(uid, tgt)) or {}).get("kind", "ndq")
            if kd0 != "all":
                show_sub(cid, p, "🎖 فقط با اتحاد نظامی - نه پیمان ساده.", cmdr_kb(p)); return
            if pmy < 1:
                show_sub(cid, p, "🪖 برای پذیرش نیروی متحد، پایگاه نظامی در شهر خودت لازم است.", cmdr_kb(p)); return
            if world["forces"].get(rk0):
                show_sub(cid, p, "در این شهر قبلاً نیرو مستقر است.", cmdr_kb(p)); return
            if cd_left(p, "frc" + tgt) > 0:
                show_sub(cid, p, f"⏳ {fa(cd_left(p, 'frc' + tgt))} ثانیه صبر کن.", cmdr_kb(p)); return
            if p["treasury"] < 500:
                show_sub(cid, p, f"استقرار نیرو {fm(500)} هزینه دارد - خزانه: {fm(p['treasury'])}", cmdr_kb(p)); return
            ap2 = others.get(tgt) or {}
            de2 = min(30, max(6, len(ap2.get("equip", [])) * 2))
            p["treasury"] -= 500
            world["forces"][rk0] = dict(frm=tgt, host=uid, de=de2, last=now)
            cd_set(p, "frc" + tgt, 21600)
            aud(p, "استقرار نیروی متحد", others[tgt].get("name", "؟") + " → " + REGIONS[rk0]["nm"] + " - قدرت " + fa(de2))
            news("🪖 نیروهای متحد " + others[tgt].get("name", "؟") + " در " + REGIONS[rk0]["nm"] + " مستقر شدند - حقوق $300/ساعت با میزبان")
            try:
                tg("sendMessage", chat_id=int(tgt), parse_mode="HTML",
                   text="🪖 ستون کمکی تو در " + esc(REGIONS[rk0]["nm"]) + " مستقر شد - پادگان میزبان: " + esc(p["name"]))
            except Exception:
                pass
            show_sub(cid, p, f"🪖 نیروی متحد مستقر شد - دفاع منطقه +{fa(de2)}\\n💳 {fsm(-500)} + حقوق {fm(300)} هر ساعت", cmdr_kb(p)); return
        if op2 == "wdw":
            rk0 = p.get("city")
            fc = world["forces"].get(rk0)
            if not fc or (fc.get("host") != uid and fc.get("frm") != uid):
                show_sub(cid, p, "نیرویی از این فرمانده مستقر نیست.", cmdr_kb(p)); return
            del world["forces"][rk0]
            aud(p, "خروج نیروی متحد", REGIONS.get(rk0, {}).get("nm", "؟"))
            news("🪖 نیروهای متحد از " + REGIONS.get(rk0, {}).get("nm", "؟") + " خارج شدند")
            show_sub(cid, p, "نیروها خارج شدند - حقوق تمام.", cmdr_kb(p)); return'''

assert s.count(OLD1) == 1, "anchor pac:yes"
s = s.replace(OLD1, NEW1)

# ═══ ۲) لغو پیمان → خروج نیروهای مربوط به همان جفت ═══
OLD2 = '''            p["treasury"] -= 1000
            world["pacts"].pop(pk(uid, tgt), None)
            aud(p, "لغو پیمان", "با " + others[tgt].get("name", "؟") + " - $1,000")'''
NEW2 = OLD2 + '''
            for rk2 in list(world.get("forces", {})):
                fc2 = world["forces"][rk2]
                if uid in (fc2.get("host"), fc2.get("frm")) and tgt in (fc2.get("host"), fc2.get("frm")):
                    del world["forces"][rk2]'''
assert s.count(OLD2) == 1, "anchor brk"
s = s.replace(OLD2, NEW2)

# ═══ ۳) پنل: نمایش نوع پیمان ═══
OLD3 = '''        ph = "🤝 پیمان داری" if has_pact(p["uid"], u2) else ("⏳ درخواست فرستادی" if st["preq"].get(u2) == p["uid"] else "⚔️ بی‌پیمان")'''
NEW3 = '''        kd2 = (st["pacts"].get(pk(p["uid"], u2)) or {}).get("kind", "ndq")
        ph = ("🎖 اتحاد نظامی" if kd2 == "all" else "🤝 پیمان داری") if has_pact(p["uid"], u2) else ("⏳ درخواست فرستادی" if st["preq"].get(u2) == p["uid"] else "⚔️ بی‌پیمان")'''
assert s.count(OLD3) == 1, "anchor ph"
s = s.replace(OLD3, NEW3)

# ═══ ۴) پنل: بنر درخواست رسیده با نوع ═══
OLD4 = '''    inc = st["preq"].get(p["uid"])
    if inc in [u2 for u2, _ in others]:
        nm = (worlds.get(p.get("gid") or "0", {}).get("pdata", {}).get(inc) or {}).get("name", "؟")
        L += ["━" * 20, f"📩 درخواست پیمان از {nm}"]'''
NEW4 = '''    incv = st["preq"].get(p["uid"])
    inc = incv.get("frm") if isinstance(incv, dict) else incv
    if inc in [u2 for u2, _ in others]:
        nm = (worlds.get(p.get("gid") or "0", {}).get("pdata", {}).get(inc) or {}).get("name", "؟")
        kn = "اتحاد نظامی" if (isinstance(incv, dict) and incv.get("kind") == "all") else "پیمان"
        L += ["━" * 20, f"📩 درخواست {kn} از {nm}"]'''
assert s.count(OLD4) == 1, "anchor banner"
s = s.replace(OLD4, NEW4)

# ═══ ۵) متن راهنمای پنل ═══
OLD5 = '''          "پیمان = حمله ممنوع دوطرفه + دفاع +۴٪",
          f"لغو پیمان: {fm(1000)} + ثبت در حسابرسی",'''
NEW5 = '''          "پیمان = حمله ممنوع دوطرفه + دفاع +۴٪",
          "اتحاد نظامی = پیمان + استقرار نیروی متحد (سطح ۳ + پایگاه نظامی)",
          f"لغو پیمان: {fm(1000)} + ثبت در حسابرسی",'''
assert s.count(OLD5) == 1, "anchor footer"
s = s.replace(OLD5, NEW5)

# ═══ ۶) کیبورد: قبول با نوع + دکمه‌های اتحاد/استقرار/بازگشت ═══
OLD6 = '''    inc = st["preq"].get(p["uid"])
    if inc in [u2 for u2, _ in others] and pr.get("lvl", 1) >= 2:
        rows.append([btn(p["uid"], "✅ قبول پیمان", "pac:yes:" + str(inc)), btn(p["uid"], "❌ رد", "pac:no:" + str(inc))])'''
NEW6 = '''    incv = st["preq"].get(p["uid"])
    inc = incv.get("frm") if isinstance(incv, dict) else incv
    if inc in [u2 for u2, _ in others] and pr.get("lvl", 1) >= 2:
        kn = "اتحاد" if (isinstance(incv, dict) and incv.get("kind") == "all") else "پیمان"
        rows.append([btn(p["uid"], f"✅ قبول {kn}", "pac:yes:" + str(inc)), btn(p["uid"], "❌ رد", "pac:no:" + str(inc))])'''
assert s.count(OLD6) == 1, "anchor kb accept"
s = s.replace(OLD6, NEW6)

OLD7 = '''    for u2, w2 in others:
        if has_pact(p["uid"], u2):
            rows.append([btn(p["uid"], f"💔 لغو پیمان با {w2.get('name', '؟')} - $1,000", "pac:brk:" + u2)])
        elif st["preq"].get(u2) != p["uid"] and pr.get("lvl", 1) >= 2 and cd_left(p, "pac" + u2) == 0:
            rows.append([btn(p["uid"], f"🤝 پیشنهاد پیمان به {w2.get('name', '؟')}", "pac:ask:" + u2)])'''
NEW7 = '''    for u2, w2 in others:
        kd2 = (st["pacts"].get(pk(p["uid"], u2)) or {}).get("kind", "ndq")
        myb = p["regions"].get(p.get("city") or "", {}).get("bl", {}).get("base", 0)
        if has_pact(p["uid"], u2):
            rows.append([btn(p["uid"], f"💔 لغو پیمان با {w2.get('name', '؟')} - $1,000", "pac:brk:" + u2)])
            if kd2 != "all" and (pr.get("lvl", 1) or 1) >= 3 and myb >= 1 and cd_left(p, "pac" + u2) == 0:
                rows.append([btn(p["uid"], f"🎖 ارتقا به اتحاد نظامی با {w2.get('name', '؟')} - $2,500", "pac:all:" + u2)])
            if kd2 == "all" and myb >= 1:
                fc0 = world["forces"].get(p.get("city") or "")
                if fc0 and fc0.get("frm") == u2:
                    rows.append([btn(p["uid"], f"↩️ بازگشت نیروهای {w2.get('name', '؟')}", "pac:wdw:" + u2)])
                elif not fc0 and cd_left(p, "frc" + u2) == 0:
                    rows.append([btn(p["uid"], f"🪖 استقرار نیروهای {w2.get('name', '؟')} در شهر من - $500", "pac:frc:" + u2)])
        elif st["preq"].get(u2) != p["uid"] and pr.get("lvl", 1) >= 2 and cd_left(p, "pac" + u2) == 0:
            rows.append([btn(p["uid"], f"🤝 پیشنهاد پیمان به {w2.get('name', '؟')}", "pac:ask:" + u2)])'''
assert s.count(OLD7) == 1, "anchor kb rows"
s = s.replace(OLD7, NEW7)

# ═══ ۷) حقوق نیروها در player_tick (زمان‌محور) ═══
OLD8 = '''    exp_up = sum(BUILDS[b]["up"] * lv for rk, r in p["regions"].items() for b, lv in r["bl"].items())'''
NEW8 = '''    for rk3, fc3 in list(world.get("forces", {}).items()):
        if fc3.get("host") != p["uid"]:
            continue
        pay = int((now - fc3.get("last", now)) / 3600 * 300)
        if pay >= 1:
            if p["treasury"] >= pay:
                p["treasury"] -= pay
                fc3["last"] = now
            else:
                del world["forces"][rk3]
                ap3 = (worlds.get(_CTX[0], {}).get("pdata") or {}).get(fc3.get("frm"))
                if ap3:
                    try:
                        tg("sendMessage", chat_id=int(ap3["uid"]), parse_mode="HTML",
                           text="🪖 ستون کمکی تو در " + esc(REGIONS.get(rk3, {}).get("nm", "؟")) + " به دلیل ندادن حقوق خارج شد.")
                    except Exception:
                        pass
                news("🪖 نیروهای متحد در " + REGIONS.get(rk3, {}).get("nm", "؟") + " به دلیل کمبود بودجه میزبان خارج شدند")
                aud(p, "خروج نیروی متحد", "نپرداختن حقوق")
    exp_up = sum(BUILDS[b]["up"] * lv for rk, r in p["regions"].items() for b, lv in r["bl"].items())'''
assert s.count(OLD8) == 1, "anchor upkeep"
s = s.replace(OLD8, NEW8)

# ═══ ۸) تصرف → پراکندن نیروهای مستقر ═══
OLD9 = '''            aud(p, "تصرف منطقه", REGIONS[rk]["nm"] + (f" از {d.get('name')}" if d else " (بی‌طرف)"))'''
NEW9 = OLD9 + '''
            if world.get("forces", {}).pop(rk, None):
                news(f"🪖 نیروهای مستقر در {REGIONS[rk]['nm']} با سقوط شهر پراکندند")'''
assert s.count(OLD9) == 1, "anchor conquest"
s = s.replace(OLD9, NEW9)

io.open("bot.py", "w", encoding="utf-8").write(s)
print("S8-B OK -", len(s.splitlines()), "lines")
