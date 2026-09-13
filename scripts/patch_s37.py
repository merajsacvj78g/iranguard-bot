# -*- coding: utf-8 -*-
# S37: پنل «حساب من» + گارد پرداخت استارز (فقط پیوی) + فرمان‌های تازه
import io

s = io.open("bot.py", encoding="utf-8").read()
REPS = []


def rep(old, new, tag):
    REPS.append((old, new, tag))


# ── ۱) پنل حساب من ────────────────────────────────────────────────────
rep('''def set_kb(p):''',
    '''def acc_text(p):
    """حساب من - همهٔ وضعیت مالی بازیکن یک‌جا"""
    pr = profiles.get(p["uid"]) or {}
    ws = int(world.setdefault("stars", {}).get(p["uid"], 0))
    inv = p.get("invest") or {}
    L = ["👤 <b>حساب من</b>", "━" * 20,
         sec("همهٔ وضعیت مالی تو یک‌جا: خزانه، واریز ساعتی، حقوق، بهره و گردش."),
         f"💳 خزانه: <b>{fm(p['treasury'])}</b>",
         f"⏰ در گلوگاه واریز: {fm(int(p.get('pay_stash', 0)))} - جمع واریزهای ساعتی: {fm(p.get('hpay_tot', 0))}",
         "💰 حقوق سرمایه‌گذاری: " + ("فعال - ۲٬۵۰۰ هر ساعت ✅" if p.get("hpay_inv") else "خاموش"),
         "📈 بهرهٔ سرمایه: " + ("فعال - ۰٫۵٪ هر ساعت ✅" if inv.get("u") else "خاموش"),
         f"⭐️ کیف استارز: {fa(ws)}",
         f"🎖 سطح {fa(pr.get('lvl', 1))} - ⭐️ XP {fa(pr.get('xp', 0))}",
         "━" * 20, "💳 گردش اخیر:"]
    lg = (p.get("mlog") or [])[-8:][::-1]
    if not lg:
        L.append("حرکتی ثبت نشده.")
    for _t, _a, _w in lg:
        L.append(f"▪ {'+' if _a >= 0 else '−'}{fm(abs(_a))} - {_w}")
    return "\\n".join(L)


def set_kb(p):''', "acc_panel")

# ── ۲) هندلر حساب من ──────────────────────────────────────────────────
rep('''    if act == "set": show_sub(cid, p, set_text(p), set_kb(p)); return''',
    '''    if act == "set": show_sub(cid, p, set_text(p), set_kb(p)); return
    if act == "acc": show_sub(cid, p, acc_text(p), kb([[btn(uid, "💳 فروشگاه استارز", "stars"), btn(uid, "🏠 خانه", "menu")]])); return''', "acc_handler")

# ── ۳) دکمهٔ حساب من در منو ────────────────────────────────────────────
rep('''            [btn(u, "⚙️ بودجه", "budget"), btn(u, "🔍 حسابرسی", "audit")],''',
    '''            [btn(u, "⚙️ بودجه", "budget"), btn(u, "🔍 حسابرسی", "audit"), btn(u, "👤 حساب من", "acc")],''', "acc_button")

# ── ۴) گارد پرداخت: فاکتور استارز فقط در پیوی ─────────────────────────
rep('''        if not stars: show_sub(cid, p, "این بسته موجود نیست.", stars_kb(p)); return
        tg("sendInvoice", chat_id=cid, title=f"شارژ خزانه {fm(usd)}",''',
    '''        if not stars: show_sub(cid, p, "این بسته موجود نیست.", stars_kb(p)); return
        if (msg.get("chat") or {}).get("type") != "private":
            show_sub(cid, p, "💳 پرداخت فقط در گفت‌وگوی خصوصی امن است - به پیوی ربات برو و «منو» بزن.", stars_kb(p))
            try: tg("sendMessage", chat_id=int(uid), parse_mode="HTML", text="💳 <b>فروشگاه استارز</b>\\nاز منوی خصوصی → 💳 فروشگاه استارز")
            except Exception: pass
            return
        tg("sendInvoice", chat_id=cid, title=f"شارژ خزانه {fm(usd)}",''', "byst_guard")

rep('''        if not info7:
            show_sub(cid, p, "این بسته موجود نیست.", packs_kb(p)); return
        tg("sendInvoice", chat_id=cid, title=info7[0], description=info7[1],''',
    '''        if not info7:
            show_sub(cid, p, "این بسته موجود نیست.", packs_kb(p)); return
        if (msg.get("chat") or {}).get("type") != "private":
            show_sub(cid, p, "💳 پرداخت فقط در گفت‌وگوی خصوصی امن است - به پیوی ربات برو و «منو» بزن.", packs_kb(p))
            try: tg("sendMessage", chat_id=int(uid), parse_mode="HTML", text="🛍 <b>بسته‌های ویژه</b>\\nاز منوی خصوصی → 💳 فروشگاه استارز → 🛍 بسته‌های ویژه")
            except Exception: pass
            return
        tg("sendInvoice", chat_id=cid, title=info7[0], description=info7[1],''', "bypack_guard")

# ── ۵) فرمان‌های تازه ──────────────────────────────────────────────────
rep('''          "گردش خزانه": "audit", "بسته": "packs", "بسته‌ها": "packs", "سرمایه‌گذاری": "packs",''',
    '''          "گردش خزانه": "audit", "بسته": "packs", "بسته‌ها": "packs", "سرمایه‌گذاری": "packs",
          "منوی بازی": "menu", "حساب من": "acc", "کیف": "packs",''', "cmdmap_v37")

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
print(f"S37 applied: {len(REPS)} replacements")
