# -*- coding: utf-8 -*-
"""S12: حذف کامل شیلدها + سیستم مستعمره/بردگی/سقوط کامل - سخت و قطعی."""
import io

s = io.open("bot.py", encoding="utf-8").read()

# ═══ ۱) حذف شیلدها - ثبت مالکیت بدون سپر ═══
OLD = '''    """ثبت مالکیت در دیتابیس + سپر ۲ ساعته"""
    st = world
    st["rs"][rk] = dict(owner=p["uid"], status="green",
                        hist=(st["rs"][rk].get("hist") or []) + [(int(time.time()), p["uid"], "claim")])
    st["prot"][rk] = time.time() + 2 * 3600'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''    """ثبت مالکیت در دیتابیس"""
    st = world
    st["rs"][rk] = dict(owner=p["uid"], status="green",
                        hist=(st["rs"][rk].get("hist") or []) + [(int(time.time()), p["uid"], "claim")])''')
OLD = '''    st["prot"][rk] = time.time() + 3600
'''
assert s.count(OLD) == 1
s = s.replace(OLD, "")

# ═══ ۲) گیت سپر در wgo - حذف ═══
OLD = '''        sh = world["prot"].get(rk, 0)
        if sh > time.time():
            show_sub(cid, p, f"🔒 این تازه تحت سپر است - {fa(int((sh - time.time()) // 60) + 1)} دقیقه صبر کن.", ops_kb(p)); return
'''
assert s.count(OLD) == 1
s = s.replace(OLD, "")

# ═══ ۳) نمایشگرهای سپر - حذف ═══
OLD = '''        sh = int(st["prot"].get(rk, 0) - time.time())
'''
assert s.count(OLD) == 2
s = s.replace(OLD, "")
OLD = '''        if sh > 0: tag += f" - 🔒 سپر {fa(sh // 60)} دقیقه"
'''
assert s.count(OLD) == 1
s = s.replace(OLD, "")
OLD = '''        if sh > 0: line += f" 🔒{fa(sh // 60)}د"
'''
assert s.count(OLD) == 1
s = s.replace(OLD, "")

# ═══ ۴) seed col + مهاجرت v4 ═══
OLD = '''    if not isinstance(st.get("forces"), dict): st["forces"] = {}
    return w'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''    if not isinstance(st.get("forces"), dict): st["forces"] = {}
    if not isinstance(st.get("col"), dict): st["col"] = {}
    return w''')
OLD = '''        _set_schema_ver("worlds", 3); ch = True
        LOG.info("migration applied: worlds v3 (msd)")'''
assert s.count(OLD) == 1
s = s.replace(OLD, OLD + '''
    if _schema_ver("worlds") < 4:
        for w in worlds.values():
            if not isinstance(w, dict): continue
            st = w.get("st")
            if not isinstance(st, dict): continue
            st.setdefault("col", {})
        _set_schema_ver("worlds", 4); ch = True
        LOG.info("migration applied: worlds v4 (col)")''')

# ═══ ۵) تابع حذف فرمانده (سقوط کامل) - بعد از rs_transfer ═══
OLD = '''def wlog(rec):'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''def eliminate(d):
    """سقوط کامل: براندازی فرمانده - ریست کامل خزانه/ارتش/XP/عنوان (سخت‌ترین رخداد بازی)"""
    uid2 = d.get("uid")
    g2 = _CTX[0]
    w2 = worlds.get(g2) or {}
    st2 = w2.get("st") or {}
    col0 = st2.get("col", {})
    col0.pop(uid2, None)
    for v3 in [v3 for v3, c3 in list(col0.items()) if c3.get("master") == uid2]:
        del col0[v3]
    for tgt2 in list(st2.get("treq", {})):
        keep = []
        for o in st2["treq"][tgt2]:
            if o.get("frm") == uid2:
                fresh0 = w2.get("pdata", {}).get(uid2)
            else:
                keep.append(o)
        if keep:
            st2["treq"][tgt2] = keep
        else:
            st2["treq"].pop(tgt2, None)
    st2.get("preq", {}).pop(uid2, None)
    fresh = new_wp({"id": int(uid2) if str(uid2).isdigit() else 0, "first_name": d.get("name") or "فرمانده"})
    fresh["gid"] = g2
    w2.setdefault("pdata", {})[uid2] = fresh
    pr2 = profiles.get(uid2)
    if pr2:
        pr2["xp"] = 0
        pr2["lvl"] = 1
        pr2["titles"] = []
    news("☠️ " + (d.get("name") or "فرمانده") + " برای همیشه سقوط کرد - فرماندهی برانداخته شد")
    wbroadcast("☠️ <b>سقوط کامل!</b> فرماندهی " + esc(d.get("name") or "؟") + " برانداخته شد - خزانه، ارتش، سطح و عنوان‌ها صفر شد")


def wlog(rec):''')

# ═══ ۶) فتح پایتخت → مستعمره/آزادی/سقوط - در بلوک تصرف ═══
OLD = '''            if world.get("forces", {}).pop(rk, None):
                news(f"🪖 نیروهای مستقر در {REGIONS[rk]['nm']} با سقوط شهر پراکندند")'''
assert s.count(OLD) == 1
s = s.replace(OLD, OLD + '''
            col0 = world.setdefault("col", {})
            if d is not None and rk == d.get("city"):
                if col0.get(uid, {}).get("master") == did and p.get("city") == rk:
                    del col0[uid]
                    aud(p, "آزادسازی", "بازپس‌گیری پایتخت")
                    news(f"🕊 {p['name']} با بازپس‌گیری {REGIONS[rk]['nm']} آزاد شد")
                    wbroadcast(f"🕊 <b>آزادی!</b> {esc(p['name'])} پایتختش را پس گرفت و از سلطه {esc(d.get('name') or '؟')} درآمد")
                else:
                    if col0.get(uid, {}).get("master") == did:
                        del col0[uid]
                    for v3 in [v3 for v3, c3 in list(col0.items()) if c3.get("master") == did]:
                        del col0[v3]
                    col0[did] = dict(master=uid, since=int(now), kind="col")
                    aud(p, "ایجاد مستعمره", d.get("name") or "؟")
                    news(f"👑 {d.get('name')} مستعمره {p['name']} شد - باج ۱۵٪ درآمد")
                    wbroadcast(f"👑 <b>مستعمره جدید:</b> {esc(d.get('name') or '؟')} زیر سلطه {esc(p['name'])} - برای آزادی باید پایتخت را پس بگیرد")''')

# ═══ ۷) سقوط کامل بعد از تصرف ═══
OLD = '''            if d is not None: addxp(d, 5)'''
assert s.count(OLD) == 1
s = s.replace(OLD, OLD + '''
            if d is not None and not my_regions(d):
                eliminate(d)
                aud(p, "سقوط کامل فرمانده", "براندازی کامل")''')

# ═══ ۸) باج مستعمره + درآمد بردگی در settle ═══
OLD = '''    p["income_hour"] = int(net)'''
assert s.count(OLD) == 1
s = s.replace(OLD, OLD + '''
    col9 = world.get("col", {}).get(p["uid"])
    if col9:
        mp2 = (worlds.get(_CTX[0], {}).get("pdata") or {}).get(col9.get("master"))
        if mp2 is None:
            world.get("col", {}).pop(p["uid"], None)
        else:
            rate2 = 0.25 if col9.get("kind") == "slv" else 0.15
            trib = int(net * rate2 * hrs)
            if trib > 0:
                trib = min(trib, int(p["treasury"]))
                p["treasury"] = int(p.get("treasury", 0)) - trib
                mp2["treasury"] = int(mp2.get("treasury", 0)) + trib
    slv9 = sum(1 for c9 in world.get("col", {}).values() if c9.get("master") == p["uid"] and c9.get("kind") == "slv")
    if slv9:
        p["treasury"] = int(p.get("treasury", 0)) + int(8 * slv9 * hrs)''')

# ═══ ۹) گیت بردگی: دیپلماسی/تجارت ممنوع ═══
OLD = '''    if act == "refresh": close_sub(cid, p); show_menu(p, cid); return'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''    c9 = world.get("col", {}).get(uid)
    if c9 and c9.get("kind") == "slv" and act.startswith(("pac:", "trk:", "trd2:")):
        show_sub(cid, p, "⛓ در بردگی هستی - دیپلماسی و تجارت مستقل ممنوع؛ پایتختت را پس بگیر و آزاد شو.", cmdr_kb(p)); return
''' + OLD)

# ═══ ۱۰) پنل فرماندهان: وضعیت مستعمره ═══
OLD = '''    L += ["━" * 20,
          "پیمان = حمله ممنوع دوطرفه + دفاع +۴٪",'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''    col0 = st.get("col", {})
    if p["uid"] in col0:
        c2 = col0[p["uid"]]
        mn2 = (worlds.get(p.get("gid") or "0", {}).get("pdata") or {}).get(c2.get("master"), {}).get("name", "؟")
        L.append(("⛓ در بردگی " + mn2 + " - باج ۲۵٪ - دیپلماسی ممنوع") if c2.get("kind") == "slv"
                 else ("👑 مستعمره " + mn2 + " - باج ۱۵٪ درآمد - آزادی: بازپس‌گیری پایتخت"))
    myc2 = [v for v, c2 in col0.items() if c2.get("master") == p["uid"]]
    if myc2:
        nm3 = [(worlds.get(p.get("gid") or "0", {}).get("pdata") or {}).get(v, {}).get("name", "؟") for v in myc2]
        L.append("👑 مستعمره‌های تو: " + " - ".join(nm3))
''' + OLD)

# ═══ ۱۱) دکمه‌های ارباب ═══
OLD = '''        elif st["preq"].get(u2) != p["uid"] and pr.get("lvl", 1) >= 2 and cd_left(p, "pac" + u2) == 0:
            rows.append([btn(p["uid"], f"🤝 پیشنهاد پیمان به {w2.get('name', '؟')}", "pac:ask:" + u2)])'''
assert s.count(OLD) == 1
s = s.replace(OLD, OLD + '''
    for v4, c4 in st.get("col", {}).items():
        if c4.get("master") != p["uid"]:
            continue
        nm4 = (worlds.get(p.get("gid") or "0", {}).get("pdata") or {}).get(v4, {}).get("name", "؟")
        if c4.get("kind") == "col":
            rows.append([btn(p["uid"], f"⛓ بردگی کردن {nm4} - $1,500", "csl:" + v4),
                         btn(p["uid"], f"🕊 آزادی {nm4}", "cfree:" + v4)])
        else:
            rows.append([btn(p["uid"], f"🕊 آزاد کردن {nm4}", "cfree:" + v4)])''')

# ═══ ۱۲) شاخه‌های csl/cfree ═══
OLD = '''    if act == "ops": show_sub(cid, p, ops_text(p), ops_kb(p)); return'''
assert s.count(OLD) == 1
s = s.replace(OLD, '''    if act.startswith("csl:"):
        v5 = act.split(":")[1]
        c5 = world.get("col", {}).get(v5)
        if not c5 or c5.get("master") != uid or c5.get("kind") == "slv":
            show_sub(cid, p, "این مستعمره در دسترس نیست.", cmdr_kb(p)); return
        if p["treasury"] < 1500:
            show_sub(cid, p, f"بردگی کردن {fm(1500)} دارد - خزانه: {fm(p['treasury'])}", cmdr_kb(p)); return
        p["treasury"] -= 1500
        c5["kind"] = "slv"
        aud(p, "بردگی گرفتن مستعمره", fm(1500))
        news(f"⛓ {c5 and (worlds.get(p.get('gid') or '0', {}).get('pdata') or {}).get(v5, {}).get('name', '؟')} به بردگی گرفته شد")
        try:
            tg("sendMessage", chat_id=int(v5), parse_mode="HTML", text="⛓ تو را به بردگی گرفتند - باج ۲۵٪ و ممنوعیت دیپلماسی/تجارت مستقل. با پس‌گرفتن پایتخت آزاد شو.")
        except Exception:
            pass
        show_sub(cid, p, "⛓ مستعمره به بردگی تبدیل شد - باج ۲۵٪ + کار اجباری (+$8/ساعت برای تو).", cmdr_kb(p)); return
    if act.startswith("cfree:"):
        v6 = act.split(":")[1]
        c6 = world.get("col", {}).get(v6)
        if not c6 or c6.get("master") != uid:
            show_sub(cid, p, "این مستعمره در دسترس نیست.", cmdr_kb(p)); return
        del world["col"][v6]
        aud(p, "آزاد کردن مستعمره", "بخشش")
        news(f"🕊 {p['name']} مستعمره‌اش را آزاد کرد")
        try:
            tg("sendMessage", chat_id=int(v6), parse_mode="HTML", text="🕊 اربابت آزادت کرد - دیپلماسی و تجارت آزاد شد.")
        except Exception:
            pass
        show_sub(cid, p, "🕊 مستعمره آزاد شد.", cmdr_kb(p)); return
''' + OLD)

io.open("bot.py", "w", encoding="utf-8").write(s)
print("S12 OK -", len(s.splitlines()), "lines")
