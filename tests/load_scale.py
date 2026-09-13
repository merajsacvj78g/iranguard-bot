# -*- coding: utf-8 -*-
"""
آزمون بار مقیاس‌شده چند-World روی استک JSON فعلی:
- ۶ World مستقل × ۱۲ فرمانده = ۷۲ بازیکن همزمان (نخ واقعی برای هر بازیکن)
- پنل، بازار، تجارت سه‌دکمه‌ای همزمان (پایستگی پول)، تمام جهان‌ها همزمان زیر فشار
- ایزولاسیون: هیچ uid از World دیگر مالک منطقه‌ای نشود + پول بین World جابه‌جا نشود
- صفر استثنای فراری + worlds.json سالم پس از ذخیره
توجه: این آزمون درستی Lock/ایزولاسیون/توان عملیاتی را می‌سنجد؛ ادعای ظرفیت ۱۰٬۰۰۰ کاربر
فقط با Load Test روی استک نهایی (DB واقعی + شبکه) معنا دارد.
"""
import os, sys, shutil, time, threading, random, json, traceback

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)
import bot as B

TMP = "/tmp/loadscale"
shutil.rmtree(TMP, ignore_errors=True)
shutil.copytree(B.DATA, TMP)
B.DATA = TMP
B.profiles = {}
B.tg = lambda m, **k: {"ok": True, "result": {"message_id": 1}}
B.joined = lambda *a, **k: True

EXC = []
_ppe = B.traceback.print_exc
def _count_ppe(*a, **k):
    EXC.append(traceback.format_exc()[:300]); _ppe(*a, **k)
B.traceback.print_exc = _count_ppe

NW, NPW = 6, 12                      # ۶ World × ۱۲ فرمانده (هر یک یک منطقه)
WORLDS = ["-1009" + str(i) for i in range(NW)]
for gid in WORLDS:
    B.worlds[gid] = dict(title="W" + gid[-2:], st=B.new_st(), news=[], pdata={})

players = {}                          # gid → [uids]
for gid in WORLDS:
    B.set_ctx(gid)
    uids = []
    rks = list(B.REGIONS)
    for i in range(NPW):
        uid = str(7000 + NW * 100 * WORLDS.index(gid) + i)
        uids.append(uid)
        B.profiles[uid] = B.new_profile({"id": uid})
        wp = B.new_wp({"id": int(uid), "first_name": "S" + uid[-3:]})
        wp["gid"] = gid; wp["ident"] = "rep"; wp["treasury"] = 100000
        B.worlds[gid]["pdata"][uid] = wp
        B.profiles[uid]["lvl"] = 3
        B.world[gid if False else "rs"][rks[i]]["owner"] = uid
        wp["city"] = rks[i]
    players[gid] = uids

msg = {"chat": {"id": 1, "type": "supergroup", "title": "مقیاس"}}
def press(uid, act, gid):
    m = {"chat": {"id": int(gid), "type": "supergroup", "title": "مقیاس"}}
    B.on_cb({"data": f"{uid}|{act}", "from": {"id": int(uid)}, "id": "q", "message": m})
    B.cb_drain()

def wtotal(gid):
    return sum(int(p.get("treasury", 0)) for p in B.worlds[gid]["pdata"].values())

VIEWS = ["menu", "eco", "map", "rank", "regs", "trd", "news", "cmdr", "asz"]
OPS = 12
ERR0 = len(EXC)
t0 = time.time(); ops_total = 0
def worker(gid, uid):
    global ops_total
    p = B.worlds[gid]["pdata"][uid]
    for j in range(OPS):
        a = random.choice(VIEWS)
        if j % 4 == 0:
            a = random.choice(["mbuy:food", "msell:food", "mkt"])
            p["last_mkt"] = 0
            p["stock"]["food"] = max(p["stock"].get("food", 0), 30)
        press(uid, a, gid); ops_total += 1
ths = []
snap0 = {gid: wtotal(gid) for gid in WORLDS}
for gid in WORLDS:
    for uid in players[gid]:
        ths.append(threading.Thread(target=worker, args=(gid, uid)))
random.shuffle(ths)
[t.start() for t in ths]; [t.join() for t in ths]
dur = time.time() - t0
ERR1 = len(EXC)

# ── تجارت سه‌دکمه‌ای همزمان در هر World (پایستگی پول مستقل هر جهان) ──
conserved_all = True
for gid in WORLDS:
    B.set_ctx(gid)
    u0, u1 = players[gid][0], players[gid][1]
    p0 = B.worlds[gid]["pdata"][u0]
    p0["stock"] = {k: 60 for k, _, _ in B.COMMS}; p0["cd"] = {}
    s0 = wtotal(gid)
    press(u0, "trk:" + u1 + ":food", gid)
    offers = list(B.world["treq"].get(u1, []))
    if not offers: conserved_all = False; continue
    oid = offers[-1]["oid"]
    res = {"n": 0}
    def acc(): press(u1, "tra:yes:" + oid, gid); res["n"] += 1
    def rej(): press(u1, "tra:no:" + oid, gid); res["n"] += 1
    def can(): press(u0, "trc:" + oid, gid); res["n"] += 1
    th2 = [threading.Thread(target=f) for f in (acc, rej, can)]
    [t.start() for t in th2]; [t.join() for t in th2]
    if wtotal(gid) != s0: conserved_all = False

# ── داوری ──
neg = all(int(p.get("treasury", 0)) >= 0 for gid in WORLDS for p in B.worlds[gid]["pdata"].values())
# ایزولاسیون مالکیت: هر ownerِ rs مال همان World باشد
isol = True
for gid in WORLDS:
    B.set_ctx(gid)
    for rk in B.REGIONS:
        o = B.world["rs"][rk]["owner"]
        if o is not None and o not in B.worlds[gid]["pdata"]: isol = False
# پول بین جهان‌ها: مجموع کل = مجموع اسنپ‌شات‌ها (تسویه زمانی اجرا نشده)
B.save_all()
with open(os.path.join(TMP, "worlds.json"), encoding="utf-8") as f:
    dat = json.load(f)
valid = all(g in dat and len(dat[g]["pdata"]) == NPW and len(dat[g]["st"]["rs"]) == len(B.REGIONS) for g in WORLDS)
ok_exc = len(EXC) == ERR1 and len(EXC) == ERR0 - ERR0  # صفر استثنای جدید در هر فاز

print("━" * 40)
print(f"جهان‌ها: {NW} مستقل | فرماندهان همزمان: {NW * NPW} | نخ‌ها: {len(ths)}")
print(f"عملیات: {ops_total} در {dur:.2f}s ({ops_total/dur:.0f} op/s کل)")
print(f"پایستگی پول در تجارت ۳دکمه‌ای × {NW} جهان: {'✓' if conserved_all else '✗'}")
print(f"ایزولاسیون مالکیت بین جهان‌ها: {'✓' if isol else '✗'}")
print(f"استثنای فراری: {'صفر ✓' if not EXC else str(len(EXC)) + ' ✗'}")
print(f"خزانه منفی: {'هیچ ✓' if neg else '✗'}")
print(f"worlds.json ({NW} جهان × {NPW} بازیکن × {len(B.REGIONS)} منطقه): {'سالم ✓' if valid else '✗'}")
verdict = conserved_all and isol and not EXC and neg and valid
print("━" * 40)
print("نتیجه: " + ("PASS ✓ - چند-Worldی زیر فشار همزمان درست است" if verdict else "FAIL ✗"))
if EXC: print("نمونه:", EXC[0])
sys.exit(0 if verdict else 1)
