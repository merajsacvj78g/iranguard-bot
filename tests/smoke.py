# -*- coding: utf-8 -*-
"""
رگرسیون طلایی GLOBAL WAR: IRAN COLLAPSE - یک فرمان، همه مسیرهای حساس:
آنبردینگ - بازار غیرفوری - قرارداد تجاری - پیمان - تصرف Engine-محور - بحران - بکاپ/ریکاوری
دستیار فقط-تحلیل - سلامت مالک - رتبه چندعاملی - اعلام گروهی - ضد دوبار-ضربه
اجرا: python3 tests/smoke.py   → خروجی PASS/FAIL
"""
import os, sys, shutil, time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)
import bot as B

TMP = "/tmp/smoke"
shutil.rmtree(TMP, ignore_errors=True)
shutil.copytree(B.DATA, TMP)
B.DATA = TMP
shutil.rmtree(os.path.join(TMP, "backup"), ignore_errors=True)  # فقط بکاپ‌های همین اجرا
B.profiles = {}
B.worlds = {"0": dict(title="x", st=B.new_st(), news=[], pdata={})}
B.set_ctx("0")

SENT = []
B.tg = lambda m, **k: (SENT.append((m, k.get("chat_id"), k.get("text") or "", k.get("reply_markup"))),
                       {"ok": True, "result": {"message_id": 1}})[1]
B.joined = lambda *a, **k: True  # گیت در کل بسته باز

def texts(m=None, cid=None):
    return [t for mm, c, t, k in SENT if t and (m is None or mm == m) and (cid is None or c == cid)]

def press(uid, act, chat_id):
    SENT.clear()
    B.on_cb({"data": f"{uid}|{act}", "from": {"id": int(uid)}, "id": "q",
             "message": {"message_id": 5, "chat": {"id": chat_id, "type": "supergroup", "title": "جنگ ایران"}}})
    B.cb_drain()
    ts = texts()
    return ts[-1] if ts else ""

ERRS = []
def check(c, n):
    print(("✓" if c else "✗"), n)
    if not c: ERRS.append(n)

# ── ۰) بدون گیت عضویت + گیت گروه‌های تاییدشده ──
B.joined = lambda *a, **k: True   # عضویت اجباری در بازی حذف شده - همه همیشه مجاز
SENT.clear()
B.on_msg({"message_id": 91, "from": {"id": 901, "first_name": "آ"}, "chat": {"id": 901, "type": "private"}, "date": 1, "text": "/start"})
check(any("خوش آمدی" in t for t in texts()), "بدون عضویت اجباری: /start خصوصی → خوش‌آمد")
SENT.clear()
B.on_msg({"message_id": 92, "from": {"id": 903, "first_name": "غ"}, "chat": {"id": -100977, "type": "supergroup", "title": "نات"}, "date": 1, "text": "سلام"})
check(any(m == "leaveChat" and c == -100977 for m, c, t, k in SENT), "گیت گروه: گروه ناتایید → خروج امنیتی")
B.APPROVED_GROUPS.add("-100910")
B.joined = lambda *a, **k: True

# ── ۱) آنبردینگ گروهی: هر بازیکن یک شهر ──
G = "-100910"
B.on_msg({"message_id": 1, "from": {"id": 901, "first_name": "آ"}, "chat": {"id": int(G), "type": "supergroup", "title": "ج"}, "date": 1, "text": "/start"})
B.on_msg({"message_id": 2, "from": {"id": 902, "first_name": "ب"}, "chat": {"id": int(G), "type": "supergroup", "title": "ج"}, "date": 1, "text": "/start"})
for u in ("901", "902"):
    press(u, "ident:pick:rep", int(G)); press(u, "ident:ok:rep", int(G))
press("901", "cset:thr", int(G)); press("902", "cset:khz", int(G))
B.set_ctx(G)
pa = B.worlds[G]["pdata"]["901"]; pb = B.worlds[G]["pdata"]["902"]
check(pa.get("city") == "thr" and pb.get("city") == "khz", "آنبردینگ: هویت + شهر اختصاصی")
check(B.world["rs"]["thr"]["owner"] == "901", "ثبت دیتابیسی مالکیت منطقه")

# ── ۲) بازار غیرفوری: سفارش → قرارداد → تحویل ──
pa["treasury"] = 50000; pa["stock"] = {k: 0 for k, _, _ in B.COMMS}; pa["last_mkt"] = 0
pr = B.world["market"]["energy"]
press("901", "mbuy:energy", int(G))
check(pa["stock"]["energy"] == 0 and len(pa["cargos"]) == 1, "خرید فوری نیست - محموله در راه")
check(pa["treasury"] == 50000 - (int(pr) * 10 + 50), "هزینه + حمل کسر شد")
pa["cargos"][0]["at"] = time.time() - 1
B.player_tick(pa)
check(pa["stock"]["energy"] == 10, "تحویل زمان‌دار به انبار")

# ── ۳) قرارداد تجاری P2P: اَمانت → قبول → پول + محموله ──
B.profiles["901"]["lvl"] = 2; B.profiles["902"]["lvl"] = 2
pa["stock"]["food"] = 20; pb["treasury"] = 20000; pa["cd"] = {}
press("901", "trk:902:food", int(G))
o = B.world["treq"]["902"][0]
check(pa["stock"]["food"] == 10, "اَمانت کالا از فروشنده")
t0 = pb["treasury"]; pa0 = pa["treasury"]
press("902", "tra:yes:" + o["oid"], int(G))
check(pb["treasury"] == t0 - o["price"] and pa["treasury"] == pa0 + o["price"], "قبول: پول بدون تولید جدید جابه‌جا شد")
check(len(pb["cargos"]) == 1, "تحویل غیرفوری به خریدار")
check(any(m == "sendMessage" and c == int(G) and "قرارداد تجاری" in t for m, c, t, k in SENT), "اعلام قرارداد در گروه")

# ── ۴) پیمان: امضا → گیت حمله → لغو هزینه‌دار ──
press("901", "pac:ask:902", int(G)); press("902", "pac:yes:901", int(G))
check(B.has_pact("901", "902"), "پیمان امضا شد")
B.world["prot"]["khz"] = 0; pa["cd"] = {}
for a in ["wt:khz", "wo:grd", "wc:100", "wp:0", "wr:d", "wn:n"]:
    press("901", a, int(G))
t = press("901", "wgo", int(G))
check("پیمان عدم تعرض" in t and not B.world["wars"], "حمله به پیمانی توسط گیت رد شد")
tr = pa["treasury"]
press("901", "pac:brk:902", int(G))
check(not B.has_pact("901", "902") and pa["treasury"] == tr - 1000, "لغو پیمان با $1,000")

# ── ۵) تصرف Engine-محور: DB + تاریخچه + حسابرسی ──
B.profiles["901"]["xp"] = 2400; B.profiles["901"]["lvl"] = 5; pa["treasury"] = 100000
pa["stock"]["oil"] = 60  # سوخت جنگی ویزارد دوم  # lvl از XP
pa["equip"] = [dict(nm="x", ic="⭐", cat="زرهی", de=5, rec=5, lg=2, q=3, mins=30, up=10) for _ in range(30)]  # براندازی: سطح ۵ + ۳۰ تجهیزات
pa["cd"] = {}; B.world["prot"]["azb"] = 0
for a in ["wt:azb", "wo:grd", "wc:100", "wp:1500", "wr:s", "wn:n"]:
    press("901", a, int(G))
press("901", "wgo", int(G))
op = B.world["wars"][-1]; op["t1"] = time.time() - 1
SENT.clear()
B.war_resolve_loop(G)
check("موفقیت کامل - تصرف" in (texts()[-1] if texts() else ""), "تصرف: نتیجه از Engine")
check(B.world["rs"]["azb"]["owner"] == "901" and B.world["rs"]["azb"]["hist"], "مالکیت + تاریخچه منطقه آپدیت شد")
check(any("تصرف منطقه" in x["what"] for x in B.world["audit"]), "حسابرسی: تصرف ثبت شد")

# ── ۶) بحران مهارنشده: خسارت + اعلام گروه ──
pa["crises"] = [dict(nm="🗣 نارضایتی اجتماعی", rg="thr", cost=450, dl=time.time() - 1)]
s0 = pa["regions"]["thr"]["sat"]
SENT.clear()
B.player_tick(pa)
check(pa["regions"]["thr"]["sat"] <= s0 - 12, "بحران: خسارت واقعی")
check(any(m == "sendMessage" and c == int(G) and "مهار نشد" in t for m, c, t, k in SENT), "اعلام بحران در گروه")

# ── ۷) بکاپ و ریکاوری ──
os.makedirs(os.path.join(TMP, "backup"), exist_ok=True)
B.jsave("backup/worlds.json-T.json", B.worlds)
open(os.path.join(TMP, "worlds.json"), "w").write("{corrupt!!")
B2 = B.jload("worlds.json", {})
check(isinstance(B2, dict) and G in B2, "ریکاوری خودکار از بکاپ سالم")

# ── ۸) دستیار: فقط تحلیل - و اعلام کمبود داده ──
pa["energy"] = 30
t = press("901", "asz", int(G))
check("دستیار تحلیل‌گر" in t and "بدون تأیید" in t, "دستیار: تحلیل از دیتای واقعی")
check("داده کافی" in B.asz_text(B.new_profile({"id": "z"})), "دستیار: کمبود داده صریح (بدون حدس)")

# ── ۹) سلامت: فقط مالک + آمار IO ──
t = press("901", "health", int(G))
check("فقط برای مالک" in t, "سلامت: غیرمالک رد")
B.profiles["8694290031"] = dict(name="م", xp=0, lvl=1, sel=G, titles=[])
B.worlds[G]["pdata"]["8694290031"] = B.new_wp({"id": 8694290031, "first_name": "م"}); B.worlds[G]["pdata"]["8694290031"]["gid"] = G
press("8694290031", "ident:pick:rep", int(G)); press("8694290031", "ident:ok:rep", int(G)); press("8694290031", "cset:hrm", int(G))
t = press("8694290031", "health", int(G))
check("ورودی/خروجی" in t, "سلامت مالک: آمار IO")

# ── ۱۰) رتبه چندعاملی ──
t = press("901", "rank", int(G))
check("رتبه‌بندی" in t, "رتبه‌بندی چندعاملی")

# ── ۱۱) ضد دوبار-ضربه ──
time.sleep(0.8)
pa["cd"] = {}
pa["stock"]["energy"] = max(pa["stock"].get("energy", 0), 10)
r1 = press("901", "trk:902:energy", int(G))
n1 = len(B.world["treq"].get("902", []))
press("901", "trk:902:energy", int(G))
n2 = len(B.world["treq"].get("902", []))
check(n1 == n2 == 1, f"دوبار-ضربه: فقط یک اجرا ({n1},{n2}) | پاسخ: {r1[:60]}")

# ── ۱۱ب) اقتصاد نفت: صادرات قراردادی + پالایش + گیت سوخت ──
B.world["market"]["oil"] = 110
pa["treasury"] = 50000; pa["stock"]["oil"] = 30
tr0 = pa["treasury"]
press("901", "exn", int(G))
check(len(pa.get("exports", [])) == 1 and pa["stock"]["oil"] == 10, "صادرات: ۲۰ تن در امانت")
rt = press("901", "mkt", int(G))
check("🛢 نفت:" in rt, f"متن بازار: راهنمای نفت | {rt[:50]}")
pa["exports"][0]["at"] = time.time() - 1
B.world["market"]["oil"] = 200  # نوسان تا لحظه تحویل
B.player_tick(pa)
pay0 = pa["treasury"] - tr0
check(pay0 == int(round(200 * 20 * 1.08)), f"تسویه به قیمت لحظه تحویل ({pay0}) - ضد سفته‌بازی")
check(pa["stock"]["oil"] == 10, "امانت نفت برگشت نخورد")
r1 = press("901", "rfn", int(G))

check("پالایش لازم" in r1, "پالایش بدون پالایشگاه رد شد")
pa["regions"]["thr"]["bl"]["ref"] = 1
pa["cd"] = {}
time.sleep(0.8)  # گارد دوبار-ضربه بین دو rfn
r2 = press("901", "rfn", int(G))

check(pa["stock"]["oil"] == 0 and len(pa.get("refines", [])) == 1, "پالایش: ۱۰ تن در امانت")
pa["refines"][0]["at"] = time.time() - 1
B.player_tick(pa)
check(pa["stock"]["energy"] == 8 and pa["stock"]["strategic"] == 2, "خروجی پالایش: +۸ انرژی +۲ استراتژیک")
pa["cd"] = {}; pa["treasury"] = 100000; pa["stock"]["oil"] = 0
time.sleep(0.8)
for a in ["wt:khz", "wo:msl", "wc:100", "wp:0", "wr:d", "wn:n"]:
    press("901", a, int(G))
t = press("901", "wgo", int(G))
check("سوخت جنگی" in t and not B.world["wars"], f"بدون نفت: عملیات رد شد | {t[:40]}")
pa["stock"]["oil"] = 10; pa["cd"] = {}
B.world["preq"].pop("902", None)
time.sleep(0.8)
for a in ["wt:khz", "wo:msl", "wc:100", "wp:0", "wr:d", "wn:n"]:
    press("901", a, int(G))
press("901", "wgo", int(G))
check(len(B.world["wars"]) == 1 and pa["stock"]["oil"] == 0, "با نفت: اعزام شد، سوخت کسر شد")
B.world["wars"].clear()  # عملیات تست را پاک کن - ادامه سناریو

# ── ۱۲) ارومیه: منطقه یازدهم ──
check("urm" in B.REGIONS and B.ADJ.get("urm") == ["azb"] and "urm" in B.ADJ["azb"], "ارومیه + مرز با آذربایجان")
check(B.world["rs"].get("urm", {}).get("owner") is None, "ارومیه در rs همان World ثبت شده (مهاجرت)")
B.profiles["909"] = dict(name="خ", xp=0, lvl=1, sel=G, titles=[])
B.worlds[G]["pdata"]["909"] = B.new_wp({"id": 909, "first_name": "خ909"})
B.worlds[G]["pdata"]["909"]["gid"] = G
press("909", "ident:pick:rep", int(G)); press("909", "ident:ok:rep", int(G))
press("909", "cset:urm", int(G))
check(B.world["rs"]["urm"]["owner"] == "909", "ادعای ارومیه کار می‌کند")

# ── ۱۳) پایگاه نظامی: ساخت + فاکتور دفاع ──
B.profiles["901"]["xp"] = max(B.profiles["901"].get("xp", 0), 2400)
B.profiles["901"]["lvl"] = B.profiles["901"]["xp"] // 600 + 1
pa["treasury"] = 200000
press("901", "build", int(G))
SENT.clear()
B.route(pa, "bld:thr:base", {"chat": {"id": int(G), "type": "supergroup", "title": "ج"}})
check(any(b["bk"] == "base" for b in pa["builds"]), "پایگاه نظامی وارد صف ساخت شد")
pa["builds"][0]["done"] = time.time() - 1
B.player_tick(pa)
check(pa["regions"]["thr"]["bl"].get("base", 0) >= 1, "پایگاه نظامی تکمیل شد (حقوق خودکار در exp)")
_, fdf = B.def_calc(pa, "thr", "grd")
check(any("پایگاه نظامی" in x for x, _ in fdf), "فاکتور دفاع پایگاه فعال")

# ── ۱۴) اتحاد نظامی + استقرار نیروهای متحد ──
B.profiles["902"]["xp"] = max(B.profiles["902"].get("xp", 0), 1800)
B.profiles["902"]["lvl"] = B.profiles["902"]["xp"] // 600 + 1
pa["cd"] = {}
press("901", "pac:ask:902", int(G))
press("902", "pac:yes:901", int(G))
pa["cd"] = {}
t = press("901", "pac:all:902", int(G))
check(isinstance(B.world["preq"].get("902"), dict) and B.world["preq"]["902"].get("kind") == "all", f"پیشنهاد اتحاد ثبت شد | {t[:50]}")
time.sleep(0.8)  # گارد دوبار-ضربه عمداً فوری را رد می‌کند
t = press("902", "pac:yes:901", int(G))
check((B.world["pacts"].get(B.pk("901", "902")) or {}).get("kind") == "all", f"اتحاد نظامی امضا شد | {t[:40]}")
t = press("901", "pac:frc:902", int(G))
fc = B.world["forces"].get("thr")
check(fc and fc.get("frm") == "902" and fc["de"] >= 6, f"نیروی متحد مستقر شد (de={fc['de'] if fc else '-'})")
_, fdf = B.def_calc(pa, "thr", "grd")
check(any("نیروهای متحد مستقر" in x for x, _ in fdf), "نیروی متحد در دفاع حساب شد")
t0 = pa["treasury"]
fc["last"] = time.time() - 7200
B.player_tick(pa)
check(pa["treasury"] == t0 - 600 and fc["last"] > time.time() - 60, "حقوق $300/ساعت زمان‌محور کسر شد")
# بی‌پولی → خروج نیرو
pa["treasury"] = 0
fc["last"] = time.time() - 3600
B.player_tick(pa)
check(not B.world["forces"].get("thr"), "ندادن حقوق → خروج خودکار نیرو")
check(any("خارج شدند" in n.get("x", "") for n in B.worlds[G]["news"][-4:]), "خبر خروج نیرو")
# استقرار مجدد + لغو پیمان → پراکندن
time.sleep(0.8)
pa["treasury"] = 5000; pa["cd"] = {}
press("901", "pac:frc:902", int(G))
check(B.world["forces"].get("thr"), "استقرار مجدد")
t = press("901", "pac:brk:902", int(G))
check(not B.world["forces"].get("thr") and not B.has_pact("901", "902"), "لغو پیمان → پراکندن نیروها")

# ── ۱۵) مسجدسلیمان + تسلیحات واقعی ──
check("msd" in B.REGIONS and B.ADJ["msd"] == ["khz", "frs"], "مسجدسلیمان + مرز خوزستان/فارس")
check(B.world["rs"].get("msd", {}).get("owner") is None, "مسجدسلیمان در World موجود seed شد (مهاجرت v3)")
check(len(B.EQUIP) == 35 and any(e["nm"] == "تانک کرار" for e in B.EQUIP) and any(e["nm"] == "کروز پاوه" for e in B.EQUIP), "۳۵ تسلیحات واقعی (کرار/فتح-۱۱۰/پاوه/...)")

# ── جمع‌بندی ──
B.save_all()
print("━" * 40)
print("نتیجه: " + ("PASS ✓ - همه مسیرهای طلایی سبز" if not ERRS else "FAIL ✗ - " + str(len(ERRS)) + " خرابی"))
sys.exit(0 if not ERRS else 1)
