# -*- coding: utf-8 -*-
"""
صحت‌سنجی همروندی بازی روی استک JSON فعلی:
- N فرمانده همزمان (نخ‌های واقعی) پنل می‌زنند، بازار خرید/فروش می‌کنند، قرارداد تجاری می‌بندند
- صفر استثنای فراری + صفر Race + پایستگی پول در چرخه کامل تجارت
توجه: این «تأیید ظرفیت ۱۰٬۰۰۰ کاربر» نیست — آن فقط با Load Test روی استک واقعی
(aiogram 3 + PostgreSQL + Redis + Pool) معنا دارد. این آزمون درستی Lock/دیتا را می‌سنجد.
"""
import os, sys, shutil, time, threading, random, json, traceback

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)
import bot as B

TMP = "/tmp/loadsim"
shutil.rmtree(TMP, ignore_errors=True)
shutil.copytree(B.DATA, TMP)
B.DATA = TMP
B.profiles = {}
B.worlds = {"0": dict(title="x", st=B.new_st(), news=[], pdata={})}
B.tg = lambda m, **k: {"ok": True, "result": {"message_id": 1}}
B.joined = lambda *a, **k: True

# ── شمارش استثناهای فراری (همه از traceback.print_exc رد می‌شوند) ──
EXC = []
_ppe = B.traceback.print_exc
def _count_ppe(*a, **k):
    EXC.append(traceback.format_exc()[:200]); _ppe(*a, **k)
B.traceback.print_exc = _count_ppe

G = "-100900"
B.set_ctx(G)
N = 10                       # ۱۰ فرمانده - هر یک یک شهر
msg = {"chat": {"id": int(G), "type": "supergroup", "title": "لود"}}
uids = [str(6000 + i) for i in range(N)]
for i, uid in enumerate(uids):
    B.profiles[uid] = B.new_profile({"id": uid})
    wp = B.new_wp({"id": int(uid), "first_name": "L" + uid[-2:]})
    wp["gid"] = G; wp["ident"] = "rep"; wp["treasury"] = 100000
    B.worlds[G]["pdata"][uid] = wp
    B.profiles[uid]["lvl"] = 3

def press(uid, act):
    B.on_cb({"data": f"{uid}|{act}", "from": {"id": int(uid)}, "id": "q", "message": msg})
    B.cb_drain()

# ثبت شهرها (زیر همان Lock رویه واقعی)
for i, uid in enumerate(uids):
    press(uid, "ident:ok:rep")
    press(uid, "cset:" + list(B.REGIONS)[i])

def total_money():
    return sum(int(p.get("treasury", 0)) for p in B.worlds[G]["pdata"].values())

# ── فاز ۱: فشار عمومی - ۸ نخ × ۵۰ عملیات ──
VIEWS = ["menu", "eco", "map", "cmdr", "asz", "wh", "rank", "trd", "equip", "news", "regs"]
ERR1 = len(EXC)
t0 = time.time(); ops1 = 0
def worker_phase1(uid):
    global ops1
    my = random.choices(VIEWS, k=50)
    for a in my:
        press(uid, a); ops1 += 1
ths = [threading.Thread(target=worker_phase1, args=(u,)) for u in uids[:8]]
[t.start() for t in ths]; [t.join() for t in ths]
d1 = time.time() - t0

# ── فاز ۲: پایستگی پول فقط با جریان تجارت ──
B.worlds[G]["pdata"][uids[0]]["stock"] = {k: 60 for k, _, _ in B.COMMS}
B.worlds[G]["pdata"][uids[0]]["cd"] = {}
snap0 = total_money()
B.worlds[G]["pdata"][uids[0]]["cd"] = {}
press(uids[0], "trk:" + uids[1] + ":food")
offers = list(B.world["treq"].get(uids[1], []))
assert offers, "پیشنهاد تجاری ثبت نشد"
oid = offers[-1]["oid"]
res = {}
def acc(_): press(uids[1], "tra:yes:" + oid); res["a"] = True
def rej(_): press(uids[1], "tra:no:" + oid); res["r"] = True
def can(_): press(uids[0], "trc:" + oid); res["c"] = True
# هر سه دکمه همزمان - فقط یکی باید اثر کند (Lock + حذف تک‌باره)
ths = [threading.Thread(target=f, args=(i,)) for i, f in enumerate([acc, rej, can])]
[t.start() for t in ths]; [t.join() for t in ths]
snap1 = total_money()
conserved = snap0 == snap1
# تخلیه محموله‌ها برای بررسی نهایی
for p in B.worlds[G]["pdata"].values():
    for c in p.get("cargos", []): c["at"] = time.time() - 1
    B.player_tick(p)

# ── فاز ۳: بازار پرتردد - هر بازیکن خرید/فروش سریع ──
ERR3 = len(EXC)
t2 = time.time(); ops3 = 0
def worker_phase3(uid):
    global ops3
    p = B.worlds[G]["pdata"][uid]; p["last_mkt"] = 0; p["treasury"] += 50000
    for _ in range(30):
        press(uid, random.choice(["mbuy:food", "msell:food", "mkt"])); ops3 += 1
        p["last_mkt"] = 0
        p["stock"]["food"] = max(p["stock"].get("food", 0), 30)
ths = [threading.Thread(target=worker_phase3, args=(u,)) for u in uids]
[t.start() for t in ths]; [t.join() for t in ths]
d3 = time.time() - t2

# ── داوری ──
ok_exc = len(EXC) == ERR1 == ERR3  # هیچ استثنای جدیدی در هیچ فازی
neg = all(int(p.get("treasury", 0)) >= 0 for p in B.worlds[G]["pdata"].values())
B.save_all()
with open(os.path.join(TMP, "worlds.json"), encoding="utf-8") as f:
    json.load(f)
valid = True
# ظرفیت: انبار + محموله در راه ≤ سقف + خوراک دستی تست (۳۰ تن هر کارگر)
csum = all(p["stock"]["food"] >= 0
           and int(round(sum(p["stock"].values()))) + sum(c["qty"] for c in p.get("cargos", []))
           <= p["stockcap"] + 30 * 10
           for p in B.worlds[G]["pdata"].values())

print("━" * 40)
print(f"بازیکنان: {N} همزمان | عملیات پنل: {ops1} در {d1:.2f}s ({ops1/d1:.0f} op/s)")
print(f"بازار: {ops3} عملیات در {d3:.2f}s ({ops3/d3:.0f} op/s)")
print(f"پایستگی پول در ۳ دکمه همزمان تجارت: {'✓' if conserved else '✗'} ({snap0} → {snap1})")
print(f"استثنای فراری: {'صفر ✓' if ok_exc else str(len(EXC)) + ' ✗'}")
print(f"خزانه منفی: {'هیچ ✓' if neg else 'وجود دارد ✗'}")
print(f"worlds.json پس از فشار: {'سالم ✓' if valid else 'خراب ✗'}")
print(f"انبارها منطقی: {'✓' if csum else '✗'}")
verdict = ok_exc and conserved and neg and valid and csum
print("━" * 40)
print("نتیجه: " + ("PASS ✓ - قفل/پایستگی/اعتبار دیتا زیر فشار همزمانی درست است" if verdict else "FAIL ✗"))
if EXC:
    print("نمونه خطا:", EXC[0])
sys.exit(0 if verdict else 1)
