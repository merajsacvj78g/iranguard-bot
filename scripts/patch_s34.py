# -*- coding: utf-8 -*-
# S34: واریز ساعتی دقیق روی ساعت ایران + سیستم استارز پیشرفته (بسته‌های چندگروهی،
#      حقوق ساعتی سرمایه‌گذاری، بهرهٔ نامحسوس کیف استارز) + سقف ۳ اتحاد نظامی
import io

s = io.open("bot.py", encoding="utf-8").read()
REPS = []


def rep(old, new, tag):
    REPS.append((old, new, tag))


# ── ۱) پیش‌فرض‌های migrate ────────────────────────────────────────────
rep('''                     menu=0, sub=0, pop=89.0, ident=None, relmod={}, incmod=1.0, city=None, cargos=[], exports=[], refines=[], arms={}).items():
        if p.get(k) is None: p[k] = v''',
    '''                     menu=0, sub=0, pop=89.0, ident=None, relmod={}, incmod=1.0, city=None, cargos=[], exports=[], refines=[], arms={},
                     hpay_t=0.0, hpay_tot=0, pay_stash=0.0, hpay_log=None, hpay_inv=0, hpay_inv_t=0.0,
                     pack_multi=0, invest=None).items():
        if p.get(k) is None: p[k] = v
    if p.get("invest") is None: p["invest"] = dict(u=0, t=0)
    if p.get("hpay_log") is None: p["hpay_log"] = []''', "migrate_defaults")

# ── ۲) درآمد ملی به‌جای خزانه، در گلوگاه واریز ساعتی جمع می‌شود ───────
rep('''    if net >= 0:
        mearn(p, net * hrs, "درآمد ملی")
    else:''',
    '''    if net >= 0:
        p["pay_stash"] = round(float(p.get("pay_stash", 0)) + net * hrs, 2)
    else:''', "income_stash")

# ── ۳) موتور واریز ساعتی + بهره + حقوق سرمایه‌گذاری + خزانهٔ چندگروهی ──
rep('''    mr = my_regions(p)
    for k, _, _ in COMMS:''',
    '''    # ⏰ واریز ساعتی - مرز دقیق ساعت ایران (UTC+3:30)
    if p.get("hpay_t", 0) <= 0:
        p["hpay_t"] = now - ((now + 12600) % 3600)
    if now - p["hpay_t"] >= 3600:
        n8 = int((now - p["hpay_t"]) // 3600)
        p["hpay_t"] += n8 * 3600
        dep8 = int(round(p.get("pay_stash", 0)))
        p["pay_stash"] = 0.0
        if dep8 > 0:
            mearn(p, dep8, "واریز ساعتی درآمد")
            p["hpay_tot"] = int(p.get("hpay_tot", 0)) + dep8
        lg8 = p.get("hpay_log") or []
        lg8.append([int(now), dep8])
        del lg8[:-12]
        p["hpay_log"] = lg8
    inv9 = p.get("invest") or {}
    if inv9.get("u"):
        gain9 = int(world.setdefault("stars", {}).get(str(p["uid"]), 0)) * 0.005 * hrs
        if gain9 >= 0.5:
            mearn(p, gain9, "بهره سرمایه")
    if p.get("hpay_inv"):
        if p.get("hpay_inv_t", 0) <= 0:
            p["hpay_inv_t"] = now - ((now + 12600) % 3600)
        if now - p["hpay_inv_t"] >= 3600:
            n9 = int((now - p["hpay_inv_t"]) // 3600)
            p["hpay_inv_t"] += n9 * 3600
            mearn(p, 2500 * n9, "حقوق سرمایه‌گذاری")
    if p.get("pack_multi"):
        base8 = int(p.get("treasury", 0))
        for w8 in worlds.values():
            q8 = (w8.get("pdata") or {}).get(p["uid"])
            if q8 is not None and q8 is not p:
                q8["treasury"] = base8
    mr = my_regions(p)
    for k, _, _ in COMMS:''', "hourly_engine")

# ── ۴) نمایش واریز ساعتی در اقتصاد ────────────────────────────────────
rep('''         f"📈 درآمد ناخالص: {fsm(inc)} - 📊 سود خالص: {fsm(net)}",''',
    '''         f"📈 درآمد ناخالص: {fsm(inc)} - 📊 سود خالص: {fsm(net)}",
         f"⏰ واریز بعدی: {fa(max(0, int((3600 - (time.time() + 12600) % 3600) / 60)))} دقیقه دیگر - در حال جمع‌شدن: {fm(int(p.get('pay_stash', 0)))}",
         f"💵 جمع واریزهای ساعتی تا امروز: {fm(p.get('hpay_tot', 0))}",''', "eco_hourly")

# ── ۵) helper ساعت ایران ──────────────────────────────────────────────
rep('''def tehfull(ts=None):
    return datetime.fromtimestamp(ts or time.time(), TEH).strftime("%Y-%m-%d %H:%M")''',
    '''def tehfull(ts=None):
    return datetime.fromtimestamp(ts or time.time(), TEH).strftime("%Y-%m-%d %H:%M")


def tehhour(ts=None):
    """ساعت ایران HH:MM - مرجع همهٔ واریزهای ساعتی"""
    return datetime.fromtimestamp(ts or time.time(), TEH).strftime("%H:%M")''', "tehhour")

# ── ۶) فروشگاه استارز: کیف + وضعیت + دکمهٔ بسته‌ها ─────────────────────
rep('''    L += ["━" * 20,
          "🔒 پرداخت امن داخل تلگرام - بدون واسطه.",
          "⚡️ شارژ در چند ثانیه - بدون ریسک."]
    return "\\n".join(L)''',
    '''    inv6 = p.get("invest") or {}
    ws6 = int(world.setdefault("stars", {}).get(str(p["uid"]), 0))
    L += [f"⭐️ کیف استارز تو: {fa(ws6)} - 💰 حقوق ساعتی: " + ("فعال ✅" if p.get("hpay_inv") else "خاموش"),
          "📈 بهرهٔ سرمایه: " + ("فعال ✅" if inv6.get("u") else "خاموش"),
          "━" * 20,
          "🔒 پرداخت امن داخل تلگرام - بدون واسطه.",
          "⚡️ شارژ در چند ثانیه - بدون ریسک."]
    return "\\n".join(L)''', "stars_text")

rep('''def stars_kb(p):
    rows = []
    for st, usd in STARS_SHOP:
        rows.append([btn(p["uid"], f"⭐️ {fa(st)} استارز → {fm(usd)}", "byst:" + str(usd))])
    rows.append([btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)''',
    '''def stars_kb(p):
    rows = []
    for st, usd in STARS_SHOP:
        rows.append([btn(p["uid"], f"⭐️ {fa(st)} استارز → {fm(usd)}", "byst:" + str(usd))])
    rows.append([btn(p["uid"], "🛍 بسته‌های ویژه", "packs")])
    rows.append([btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)


PACKS = dict(
    multi=("🌍 بستهٔ چندگروهی", "یک خزانه مشترک در همه گروه‌ها - پولت همه‌جا همراهت است", 800),
    kit=("🏗 بستهٔ ساز و تجهیز", "$12,000 + ۱۲ تجهیزات تصادفی در همه دنیاهایت", 1200))


def packs_text(p):
    inv7 = p.get("invest") or {}
    ws7 = int(world.setdefault("stars", {}).get(str(p["uid"]), 0))
    return "\\n".join([
        "🛍 <b>فروشگاه بسته‌های ویژه</b>", "━" * 20,
        sec("این خریدها اثر در همهٔ گروه‌ها دارند - یک‌بار بخر، همه‌جا داشته باش."),
        f"⭐️ کیف استارز تو: <b>{fa(ws7)}</b>",
        ("✅" if p.get("hpay_inv") else "⭕️") + " حقوق ساعتی: " + ("فعال - ۲٬۵۰۰ هر ساعت" if p.get("hpay_inv") else "فعال نیست"),
        ("✅" if inv7.get("u") else "⭕️") + " بهرهٔ سرمایه: " + ("فعال - ۰٫۵٪ در ساعت" if inv7.get("u") else "خاموش"),
        "━" * 20,
        "🌍 بستهٔ چندگروهی (۸۰۰⭐): خزانهٔ همهٔ گروه‌هایت یکی می‌شود.",
        "🏗 بستهٔ ساز و تجهیز (۱٬۲۰۰⭐): $12,000 + ۱۲ تجهیزات در همهٔ دنیاها.",
        "💰 حقوق ساعتی (۳۰۰⭐): هر ساعت دقیق روی ساعت ایران ۲٬۵۰۰ واریز.",
        "📈 بهرهٔ سرمایه (۱۵۰⭐): ۰٫۵٪ کیف استارزت هر ساعت بی‌صدا بهره می‌دهد.",
        "🎁 سکهٔ تشویقی: با هر شارژ خزانه، ۲۰٪ استارزش هدیه به کیف تو برمی‌گردد.",
        "━" * 20,
        "💡 کیف استارز جدا از خزانه است - منبع بهره و خرید ابزار."])


def packs_kb(p):
    u = p["uid"]
    return kb([[btn(u, "🌍 بستهٔ چندگروهی - ۸۰۰⭐", "bypack:multi")],
               [btn(u, "🏗 بستهٔ ساز و تجهیز - ۱٬۲۰۰⭐", "bypack:kit")],
               [btn(u, "💰 حقوق ساعتی سرمایه‌گذاری - ۳۰۰⭐", "invbuy:l")],
               [btn(u, "📈 بهرهٔ سرمایه ۰٫۵٪ - ۱۵۰⭐", "invbuy:u")],
               [btn(u, "⏸ خاموشی بهرهٔ سرمایه", "invbuy:off")],
               [btn(u, "💳 شارژ خزانه", "stars"), btn(u, "🏠 خانه", "menu")]])''', "packs_panel")

# ── ۷) هندلرهای خرید بسته‌ها ──────────────────────────────────────────
rep('''        tg("sendInvoice", chat_id=cid, title=f"شارژ خزانه {fm(usd)}",
           description="بعد از پرداخت، خزانه فوری شارژ می‌شود",
           payload=f"top:{uid}:{usd}", currency="XTR",
           prices=[{"label": f"{stars} استارز", "amount": stars}])
        return''',
    '''        tg("sendInvoice", chat_id=cid, title=f"شارژ خزانه {fm(usd)}",
           description="بعد از پرداخت، خزانه فوری شارژ می‌شود",
           payload=f"top:{uid}:{usd}", currency="XTR",
           prices=[{"label": f"{stars} استارز", "amount": stars}])
        return
    if act.startswith("bypack:"):
        k7 = act.split(":", 1)[1]
        info7 = PACKS.get(k7)
        if not info7:
            show_sub(cid, p, "این بسته موجود نیست.", packs_kb(p)); return
        tg("sendInvoice", chat_id=cid, title=info7[0], description=info7[1],
           payload=f"pack:{k7}", currency="XTR",
           prices=[{"label": info7[0], "amount": info7[2]}])
        return
    if act == "invbuy:l":
        ws7 = world.setdefault("stars", {})
        w7 = int(ws7.get(str(uid), 0))
        if w7 < 300:
            show_sub(cid, p, f"⭐️ ۳۰۰ استارز در کیف لازم است - کیف تو: {fa(w7)}", packs_kb(p)); return
        ws7[str(uid)] = w7 - 300
        if not p.get("hpay_inv"):
            p["hpay_inv"] = 1
            p["hpay_inv_t"] = now - ((now + 12600) % 3600)
        aud(p, "خرید حقوق سرمایه‌گذاری", "۳۰۰ استارز - ۲٬۵۰۰ هر ساعت")
        show_sub(cid, p, f"✅ حقوق سرمایه‌گذاری فعال شد - {fm(2500)} هر ساعت دقیق روی ساعت ایران واریز می‌شود.", packs_kb(p)); return
    if act == "invbuy:u":
        inv7 = p.setdefault("invest", dict(u=0, t=0))
        if not inv7.get("u"):
            ws7 = world.setdefault("stars", {})
            w7 = int(ws7.get(str(uid), 0))
            if w7 < 150:
                show_sub(cid, p, f"⭐️ ۱۵۰ استارز در کیف لازم است - کیف تو: {fa(w7)}", packs_kb(p)); return
            ws7[str(uid)] = w7 - 150
        inv7["u"] = 1
        inv7["t"] = now
        aud(p, "بهرهٔ سرمایه فعال شد", "۰٫۵٪ در ساعت از کیف استارز")
        show_sub(cid, p, "✅ بهرهٔ سرمایه فعال شد - هر ساعت ۰٫۵٪ کیف استارزت بی‌صدا به خزانه می‌ریزد (در همهٔ گروه‌ها).", packs_kb(p)); return
    if act == "invbuy:off":
        inv7 = p.setdefault("invest", dict(u=0, t=0))
        if inv7.get("u"):
            inv7["u"] = 0
            inv7["t"] = 0
            aud(p, "بهرهٔ سرمایه خاموش شد", "")
            show_sub(cid, p, "⏸ بهرهٔ سرمایه خاموش شد - هر وقت خواستی دوباره روشن کن.", packs_kb(p)); return
        show_sub(cid, p, "بهرهٔ سرمایه فعال نیست.", packs_kb(p)); return
    if act == "packs":
        show_sub(cid, p, packs_text(p), packs_kb(p)); return''', "pack_handlers")

# ── ۸) تحویل بسته‌ها بعد از پرداخت + سکهٔ تشویقی شارژ ──────────────────
rep('''            tg("sendMessage", chat_id=8694290031,
               text=f"💰 واریز استارز: {p.get('name')} ({uid})\\n⭐️ {stars} استارز → {fm(usd)}")
        return''',
    '''            tg("sendMessage", chat_id=8694290031,
               text=f"💰 واریز استارز: {p.get('name')} ({uid})\\n⭐️ {stars} استارز → {fm(usd)}")
            pk9 = sp.get("invoice_payload") or ""
            if pk9.startswith("top:"):
                bonus9 = int(stars * 0.2)
                if bonus9 > 0:
                    ws9 = world.setdefault("stars", {})
                    ws9[str(uid)] = int(ws9.get(str(uid), 0)) + bonus9
            elif pk9 == "pack:multi":
                p["pack_multi"] = 1
                base7 = int(p.get("treasury", 0))
                for w7 in worlds.values():
                    q7 = (w7.get("pdata") or {}).get(uid)
                    if q7 is not None:
                        q7["pack_multi"] = 1
                        q7["treasury"] = base7
                tg("sendMessage", chat_id=int(uid), parse_mode="HTML",
                   text="🌍 <b>بستهٔ چندگروهی فعال شد</b>\\nخزانهٔ تو از این به بعد در همهٔ گروه‌ها یکی است.")
            elif pk9 == "pack:kit":
                p["treasury"] = int(p.get("treasury", 0)) + 12000
                _mlog(p, 12000, "بستهٔ ساز و تجهیز")
                kit7 = random.sample(list(EQUIP), min(12, len(EQUIP)))
                for w7 in worlds.values():
                    q7 = (w7.get("pdata") or {}).get(uid)
                    if q7 is not None:
                        q7["treasury"] = int(q7.get("treasury", 0)) + 12000
                        _mlog(q7, 12000, "بستهٔ ساز و تجهیز")
                        q7.setdefault("equip", []).extend([dict(x) for x in kit7])
                tg("sendMessage", chat_id=int(uid), parse_mode="HTML",
                   text="🏗 <b>بستهٔ ساز و تجهیز تحویل شد</b>\\n+$12,000 و ۱۲ تجهیزات در همهٔ دنیاهایت ثبت شد.")
        return''', "pack_delivery")

# ── ۹) سقف ۳ اتحاد نظامی - پیشنهاددهنده ───────────────────────────────
rep('''        if op2 == "all":
            pmy = p["regions"].get(p.get("city") or "", {}).get("bl", {}).get("base", 0)
            kd0 = (world["pacts"].get(pk(uid, tgt)) or {}).get("kind", "ndq")''',
    '''        if op2 == "all":
            pmy = p["regions"].get(p.get("city") or "", {}).get("bl", {}).get("base", 0)
            kd0 = (world["pacts"].get(pk(uid, tgt)) or {}).get("kind", "ndq")
            _al = [k2 for k2, v2 in world["pacts"].items() if isinstance(v2, dict) and v2.get("kind") == "all" and uid in k2.split("|")]
            if len(_al) >= 3:
                show_sub(cid, p, "🎖 سقف اتحاد نظامی: ۳ نفر - برای اتحاد جدید اول یکی را لغو کن.", cmdr_kb(p)); return''', "alliance_cap_ask")

# ── ۱۰) سقف ۳ اتحاد - هر دو طرف هنگام امضا ────────────────────────────
rep('''            if op2 == "yes" and frm in others and frm != uid:
                if knd == "all" and (profiles.get(frm, {}).get("lvl", 1) < 3 or pr2.get("lvl", 1) < 3):''',
    '''            if op2 == "yes" and frm in others and frm != uid:
                if knd == "all":
                    _al2 = [k2 for k2, v2 in world["pacts"].items() if isinstance(v2, dict) and v2.get("kind") == "all" and uid in k2.split("|")]
                    _al3 = [k2 for k2, v2 in world["pacts"].items() if isinstance(v2, dict) and v2.get("kind") == "all" and str(frm) in k2.split("|")]
                    if len(_al2) >= 3:
                        show_sub(cid, p, "🎖 سقف اتحاد نظامی تو پر است (۳ نفر) - اول یکی را لغو کن.", cmdr_kb(p)); return
                    if len(_al3) >= 3:
                        show_sub(cid, p, "🎖 سقف اتحاد نظامی طرف مقابل پر است (۳ نفر).", cmdr_kb(p)); return
                if knd == "all" and (profiles.get(frm, {}).get("lvl", 1) < 3 or pr2.get("lvl", 1) < 3):''', "alliance_cap_sign")

# ── ۱۱) قانون در پنل فرماندهان ────────────────────────────────────────
rep('''          "پیمان = حمله ممنوع دوطرفه + دفاع +۴٪",''',
    '''          sec("هر فرمانده حداکثر ۳ اتحاد نظامی همزمان می‌تواند داشته باشد."),
          "پیمان = حمله ممنوع دوطرفه + دفاع +۴٪",''', "cmdr_rule")

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
print(f"S34 applied: {len(REPS)} replacements")
