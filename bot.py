# -*- coding: utf-8 -*-
# 👑 CROWN WARS — استراتژی کلان نبرد تاج‌ها
# دائمی - دکمه‌محور - فارسی - بدون فرمان اسلش - زمان تهران، ذخیره UTC
import os, json, time, random, threading, signal, sys, traceback, queue
from datetime import datetime, timezone, timedelta
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

# لاگ ساختاریافته چرخشی (۵ فایل × ۱MB) - کنسول مثل قبل print می‌کند
import logging
from logging.handlers import RotatingFileHandler
LOG = logging.getLogger("iranguard")
try:
    _lh = RotatingFileHandler(os.path.join(DATA, "bot.log"), maxBytes=1_000_000,
                              backupCount=4, encoding="utf-8")
    _lh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    LOG.addHandler(_lh); LOG.setLevel(logging.INFO)
except Exception:
    pass
API = "https://api.telegram.org/bot"
TEH = timezone(timedelta(hours=3, minutes=30))
_lock = threading.RLock()
FQ = queue.Queue()

def load_token():
    if os.environ.get("BOT_TOKEN"): return os.environ["BOT_TOKEN"]
    try:
        for ln in open(os.path.join(BASE, ".env")):
            if ln.startswith("BOT_TOKEN="): return ln.split("=", 1)[1].strip()
    except Exception: pass
    return ""

TOKEN = load_token()

# ───────── ابزارها ─────────
FA = str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹-")
def fa(x):
    if isinstance(x, bool): x = int(x)
    elif isinstance(x, (int, float)):
        try: x = int(round(x))
        except Exception: x = 0
    return str(x if x is not None else 0).translate(FA)
def fnum(x):
    try: x = int(round(float(x)))
    except Exception: x = 0
    s = str(abs(x)); parts = []
    while len(s) > 3: parts.insert(0, s[-3:]); s = s[:-3]
    out = ",".join(([s] if s else []) + parts)
    return ("−" if x < 0 else "") + out.translate(FA)
def esc(s): return str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
def bar(c, m, w=10):
    try:
        c = 0 if c is None else c; m = 1 if not m else m
        f = round(w * max(0, min(c, m)) / max(1, m))
    except Exception: f = 0
    return "█" * f + "░" * (w - f)
def pct(c, m):
    try:
        c = 0 if c is None else c; m = 1 if not m else m
        return fa(int(100 * max(0, min(c, m)) / max(1, m)))
    except Exception: return fa(0)
def teh(ts=None):
    return datetime.fromtimestamp(ts or time.time(), TEH).strftime("%H:%M")
def tehfull(ts=None):
    return datetime.fromtimestamp(ts or time.time(), TEH).strftime("%Y-%m-%d %H:%M")


def tehhour(ts=None):
    """ساعت ایران HH:MM - مرجع همهٔ واریزهای ساعتی"""
    return datetime.fromtimestamp(ts or time.time(), TEH).strftime("%H:%M")

_IO = {"r": 0, "w": 0}
_SESS = requests.Session()          # keep-alive: اتصال TCP/TLS بازیابی می‌شود - هر درخواست خیلی سریع‌تر
_SESS.headers.update({"Connection": "keep-alive"})

def jload(n, d):
    _IO["r"] += 1
    try: return json.load(open(os.path.join(DATA, n)))
    except Exception:
        import glob as _g
        for f in sorted(_g.glob(os.path.join(DATA, "backup", n + "-*.json")), reverse=True):
            try: return json.load(open(f))
            except Exception: continue
        return d
    try: return json.load(open(os.path.join(DATA, n)))
    except Exception: return d
def jsave(n, o):
    _IO["w"] += 1
    p = os.path.join(DATA, n); t = p + ".tmp"
    json.dump(o, open(t, "w"), ensure_ascii=False); os.replace(t, p)

STIME = time.time()
SAVE_T = [time.time()]

_DIRTY = [False]
_SHARD_N = [0]

def mark_dirty():
    """تغییرات در حافظه ثبت شد - ذخیرهٔ دیسک دسته‌ای و زیر قفل (مسیر فرمان هرگز منتظر دیسک نمی‌ماند)"""
    _DIRTY[0] = True

def save_all():
    with _lock:
        jsave("profiles.json", profiles); jsave("worlds.json", worlds)
        SAVE_T[0] = time.time()

def tg(method, **kw):
    global _SESS
    kw = {k: v for k, v in kw.items() if v is not None}
    if not TOKEN: return {"ok": False}
    for _ in range(8):
        try:
            t = (15, 66) if method == "getUpdates" else (15, 30)
            hdr = {"Connection": "close"} if (method == "getUpdates" or _) else None
            r = _SESS.post(f"{API}{TOKEN}/{method}", json=kw, timeout=t, headers=hdr)
            j = r.json()
            if not j.get("ok"):
                d = str(j.get("description", ""))
                if "message is not modified" in d: return {"ok": True}
                if j.get("error_code") == 409 or "terminated by other getUpdates" in d:
                    time.sleep(0.4); continue
                ra = (j.get("parameters") or {}).get("retry_after")
                if ra:
                    if ra > 30: return j
                    time.sleep(ra + 0.5); continue
                print("[tg]", method, d[:140])
            return j
        except Exception as e:
            print("[tg]", method, repr(e))
            try: _SESS.close()
            except Exception: pass
            try: _SESS = requests.Session()
            except Exception: pass
            time.sleep(min(2 ** _, 8))
    return {"ok": False}

def tgf(method, data=None, files=None):
    """ارسال فایل (multipart) - برای عکس"""
    if not TOKEN: return {"ok": False}
    try:
        r = _SESS.post(f"{API}{TOKEN}/{method}", data=data or {}, files=files, timeout=(15, 60))
        return r.json()
    except Exception as e:
        print("[tg]", method, repr(e)); return {"ok": False}

try: COVER = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cover.jpg"), "rb").read()
except Exception: COVER = None

# ───────── مرکز ایموجی (Emoji Registry) - هیچ آیدی داخل هندلرها نیست ─────────
EMOJI = {
 "iran1": ("🇮🇷", "5949420992278303833"), "iran2": ("🇮🇷", "6042111875494187872"),
 "iran3": ("🇮🇷", "5913709984184538340"), "iran4": ("🇮🇷", "5893295931612210061"),
 "iran5": ("🇮🇷", "5839117436024001991"), "iran6": ("🇮🇷", "5839065398200244133"),
 "iran7": ("🇮🇷", "5839018707610774741"), "iran8": ("🇮🇷", "5839002498404194045"),
 "iran9": ("🇮🇷", "5873050181628336601"), "iran10": ("🇮🇷", "5850199005698462596"),
 "pahlavi": ("🦁", "5864156610028378675"),
 "ru1": ("🇷🇺", "5992218004920747903"), "ru2": ("🇷🇺", "5992053529148137634"),
 "cn1": ("🇨🇳", "5769298954466369481"), "iq1": ("🇮🇶", "5951926774983037354"),
 "iq2": ("🇮🇶", "5981172487201758726"), "ps1": ("🇵🇸", "5949602446056624802"),
 "ps2": ("🇵🇸", "5949433121265947610"), "lb1": ("🇱🇧", "5949795320152987526"),
 "lb2": ("🇱🇧", "5895316078069813889"), "ye1": ("🇾🇪", "5891013835099214333"),
 "tool": ("🛠", "5462921117423384478"), "tool2": ("🛠️", "5981136959232286654"),
 "box": ("📦", "5463172695132745432"), "battery": ("🔋", "5454125707300978880"),
 "computer": ("🖥", "5375099322666859339"), "coin": ("🪙", "5463046637842608206"),
 "money": ("💰", "5375312095346704820"), "cash": ("💸", "5373174941095050893"),
 "cart": ("🛒", "5226656353744862682"), "bags": ("🛍", "5453901475648390219"),
 "ambulance": ("🚑", "5453870826761765894"),
 "antenna1": ("📡", "5839401174448478145"), "antenna2": ("📡", "5767420198332144257"),
 "antenna3": ("📡", "5766895005436222898"),
 "anchor1": ("⚓️", "5922403637941769526"), "anchor2": ("⚓️", "5767050079525412513"),
 "anchor3": ("⚓️", "5766974720029236404"),
 "mail": ("✉️", "5454113432284446338"), "timer": ("⏱", "5373236586760651455"),
 "shield1": ("🛡", "5465154440287757794"), "shield2": ("🛡", "5373173798633752502"),
 "helmet1": ("🪖", "5981162471338024162"), "helmet2": ("🪖", "5454168390685965478"),
 "medal1": ("🎖", "5981270841952836583"), "medal2": ("🎖", "5229045747130843073"),
 "target": ("🎯", "5773763207898340332"), "salute": ("🫡", "5780637500624082354"),
 "muscle": ("💪", "5463413771647069835"), "swords": ("⚔️", "5454014806950429357"),
 "plane1": ("✈️", "5976580956708936910"), "plane2": ("✈️", "5767137434865244999"),
 "plane3": ("✈️", "5766903427867089820"), "plane4": ("✈️", "5767303383811628719"),
 "rocket1": ("🚀", "5764796188062653652"), "rocket2": ("🚀", "5766962775725187627"),
 "rocket3": ("🚀", "5767121268608342750"), "rocket4": ("🚀", "5767388969624936602"),
 "rocket5": ("🚀", "5767106558345355176"), "rocket6": ("🚀", "5767307133318078907"),
 "fire1": ("🔥", "5926822463504652601"), "fire2": ("🔥", "5960642277238904258"),
 "fire3": ("🔥", "5961017597251032103"), "fire4": ("🔥", "5963046359413036387"),
 "fire5": ("🔥", "5949329367740980145"), "fire6": ("🔥", "5767184129749686975"),
 "boom": ("💥", "5911089177960650817"), "dizzy": ("😵", "5463274047771000031"),
 "hurt": ("🤕", "5463156928307801722"), "scream": ("😱", "5454182632797521992"),
 "chart": ("📈", "5226928895189598791"), "brain": ("🧠", "5226639745106330551"),
 "people": ("👥", "5453957997418004470"), "eye": ("👁", "5228822494730797152"),
 "top": ("🔝", "5463071033256848094"), "up": ("⬆️", "5463122435425448565"),
 "star": ("⭐️", "5226928895189598791"), "cup": ("🏆", "5226431245918942763"),
 "crown": ("👑", "5229011542011299168"), "refresh": ("🔄", "5226702984204797593"),
 "back": ("🔙", "5253997076169115797"),
 "cross1": ("❌", "5454350746407419714"), "warn": ("❗️", "5373059848856421989"),
 "question": ("❓", "5463139580934892960"), "interrobang": ("⁉️", "5226618356169194833"),
 "cross2": ("❌", "5463358164705489689"), "unlock": ("🔓", "5465443379917629504"),
 "noentry": ("⛔️", "5463358164705489689"), "ok": ("👌", "5463423955014529788"),
 "handshake": ("🤝", "5463256910851546817"), "thumbsup": ("👍", "5465465194056525619"),
 "thumbsdown": ("👎", "5465225015190367274"), "joy": ("😂", "5463121572137022242"),
 "pray": ("🙏", "5228878926306101271"), "devil": ("😈", "5228962845672096235"),
 "hearts": ("🥰", "5465262274031659421"), "joystick": ("🕹", "5453921696354419743"),
 "hour": ("⌛️", "5454415424319931791"),
 # بدون آیدی - فقط fallback معمولی
 "factory": ("🏭", ""), "home": ("🏠", ""), "globe": ("🌍", ""), "gear": ("⚙️", ""),
 "city": ("🏙️", ""), "smile": ("😊", ""), "bolt": ("⚡", ""), "truck": ("🚚", ""),
 "newspaper": ("📰", ""), "pick": ("⛏", ""), "vote": ("🗳️", ""), "dove": ("🕊️", ""),
 "book": ("📖", ""), "house2": ("🏘", ""), "therm": ("🌡", ""), "chartdn": ("📉", ""),
}

def pe(k):
    """از رجیستری بخوان - اگر آیدی نبود یا ساپورت نشد، ایموجی معمولی همان بخش"""
    e, i = EMOJI.get(k, ("⭐️", ""))
    if i: return '<tg-emoji emoji-id="%s">%s</tg-emoji>' % (i, e)
    return e

def cflag(ck):
    """پرچم کشور - پرمیوم برای روسیه/چین/عراق/فلسطین/لبنان/یمن"""
    m = {"ru": "ru1", "cn": "cn1", "iq": "iq1", "ps": "ps1", "lb": "lb1", "ye": "ye1"}
    return pe(m[ck]) if ck in m else COUNTRIES[ck]["fl"]

def kb(rows): return {"inline_keyboard": rows}
def btn(uid, t, d): return {"text": t, "callback_data": f"{uid}|{d}"}
def ubt(t, url): return {"text": t, "url": url}

CHANNEL = -1003854383148
CHANNEL_URL = [""]
_join_cache = {}

def chan_url():
    if CHANNEL_URL[0]: return CHANNEL_URL[0]
    try:
        ch = (tg("getChat", chat_id=CHANNEL).get("result") or {})
        un = ch.get("username")
        if isinstance(un, str) and un:
            CHANNEL_URL[0] = "https://t.me/" + un
        else:
            u2 = (tg("exportChatInviteLink", chat_id=CHANNEL).get("result") or "")
            CHANNEL_URL[0] = u2 if isinstance(u2, str) else ""
    except Exception:
        CHANNEL_URL[0] = ""
    return CHANNEL_URL[0]

def joined(uid, force=False):
    """عضویت اجباری برداشته شد (دستور مالک) - همه همیشه اجازه دارند"""
    return True

def join_text():
    return "\n".join(["👑 <b>به CrownWars خوش آمدی</b>", "━" * 20,
                      "📰 اخبار، آپدیت‌ها و آموزش کامل در کانال:",
                      "📰 اخبار و آپدیت‌ها + آموزش کامل ۹ بخشی", "━" * 20,
                      "«منو» بفرست و بازی را شروع کن!"])

def join_kb(uid):
    return kb([[ubt("✅ عضویت در کانال", chan_url() or "https://t.me/")],
               [btn(uid, "🔄 بررسی عضویت", "jchk")]])

def fm(x):
    """پول: فقط دلار - کامل و گروه‌بندی‌شده: $1,000"""
    try: x = int(round(float(x)))
    except Exception: x = 0
    sg = str(abs(x)); parts = []
    while len(sg) > 3: parts.insert(0, sg[-3:]); sg = sg[:-3]
    return ("−" if x < 0 else "") + "$" + ",".join(([sg] if sg else []) + parts)

def fsm(x):
    """پول علامت‌دار: +$100 / −$50"""
    return ("+" if x >= 0 else "") + fm(x)

# ───────── داده‌های ثابت ─────────
REGIONS = {
 "thr": dict(nm="تهران", tp="🎓 علمی - سیاسی", pop=14.0, ind=5, mine=1, en=2, ag=1, port=0, air=1, inc=285, sec=70, dev=78, fl="قلب سیاسی و فناوری کشور",
             out=dict(industrial=3, strategic=2), need=dict(food=3, energy=3), party="rep"),
 "esf": dict(nm="اصفهان", tp="🏭 صنعتی - تاریخی", pop=5.1, ind=4, mine=2, en=1, ag=2, port=0, air=1, inc=174, sec=72, dev=68, fl="کارگاه صنعتی ایران",
             out=dict(industrial=5), need=dict(mineral=3, food=1), party="rep"),
 "khz": dict(nm="خوزستان", tp="🛢️ انرژی", pop=4.7, ind=3, mine=2, en=5, ag=3, port=1, air=0, inc=210, sec=58, dev=54, fl="نفت و آب",
             out=dict(energy=4, oil=4), need=dict(food=2, industrial=1), party="rep"),
 "frs": dict(nm="فارس", tp="🌾 کشاورزی", pop=4.9, ind=2, mine=2, en=1, ag=4, port=0, air=1, inc=150, sec=70, dev=60, fl="سبد کشاورزی جنوب",
             out=dict(food=6), need=dict(energy=1), party="pah"),
 "khr": dict(nm="خراسان", tp="⛏️ معدنی", pop=8.1, ind=2, mine=3, en=1, ag=3, port=0, air=1, inc=156, sec=66, dev=58, fl="شرق و معادن",
             out=dict(mineral=6, strategic=1), need=dict(food=2, energy=1), party="rep"),
 "azb": dict(nm="آذربایجان", tp="🏭 صنعتی", pop=7.2, ind=4, mine=2, en=1, ag=2, port=0, air=1, inc=162, sec=64, dev=57, fl="ماشین‌کاری و فولاد",
             out=dict(industrial=4), need=dict(mineral=2, energy=2), party="pah"),
 "msd": dict(nm="مسجدسلیمان", tp="🛢️ نفت - تاریخی", pop=0.11, ind=2, mine=1, en=6, ag=1, port=0, air=0, inc=190, sec=58, dev=52, fl="چاه شماره یک ایران و خاورمیانه (۱۹۰۸) - زادگاه صنعت نفت",
             out=dict(oil=5, strategic=1), need=dict(food=2, industrial=1), party="pah"),
 "urm": dict(nm="ارومیه", tp="🍎 کشاورزی - مرزی", pop=0.7, ind=1, mine=1, en=1, ag=4, port=0, air=1, inc=120, sec=55, dev=52, fl="سیب، دریاچه و مرز غربی",
             out=dict(food=4, mineral=1), need=dict(energy=1, industrial=1), party="pah"),
 "sis": dict(nm="سیستان", tp="⛏️ مرزی - معدنی", pop=2.8, ind=0, mine=3, en=2, ag=0, port=1, air=0, inc=66, sec=40, dev=30, fl="مرز، باد و معادن",
             out=dict(mineral=4, strategic=2), need=dict(food=1), party="rep"),
 "gil": dict(nm="گیلان", tp="🌳 کشاورزی - طبیعی", pop=2.5, ind=1, mine=0, en=0, ag=4, port=1, air=0, inc=108, sec=74, dev=62, fl="شالیزار و گردشگری",
             out=dict(food=5), need=dict(industrial=1), party="pah"),
 "krn": dict(nm="کرمان", tp="⛏️ معدنی - مس", pop=3.2, ind=1, mine=5, en=1, ag=1, port=0, air=1, inc=132, sec=55, dev=48, fl="پایتخت مس ایران",
             out=dict(mineral=7), need=dict(food=2, energy=1), party="rep"),
 "hrm": dict(nm="هرمزگان", tp="🚢 بندری - صادراتی", pop=1.8, ind=1, mine=2, en=3, ag=0, port=2, air=0, inc=138, sec=52, dev=45, fl="تنگ جهانی و اسکله‌ها",
             out=dict(energy=3, industrial=1), need=dict(food=1), party="pah"),
 "alz": dict(nm="البرز", tp="🏭 صنعتی - حمل‌ونقل", pop=2.7, ind=3, mine=1, en=1, ag=2, port=0, air=0, inc=140, sec=62, dev=56, fl="کرج - کریدور غربی پایتخت",
             out=dict(industrial=3, food=1), need=dict(energy=1, mineral=1), party="pah"),
}
BUILDS = {
 "fac":  dict(nm="کارخانه", ic="🏭", cost=1200, mins=45, up=20, fx="تولید +۴ - درآمد منطقه +۱۸"),
 "pow":  dict(nm="نیروگاه", ic="⚡", cost=1000, mins=40, up=20, fx="انرژی +۵"),
 "ref":  dict(nm="پالایشگاه", ic="⛽", cost=1800, mins=60, up=30, fx="درآمد +۳۰"),
 "mine": dict(nm="مرکز استخراج", ic="⛏️", cost=900, mins=35, up=20, fx="درآمد +۱۵"),
 "farm": dict(nm="مرکز کشاورزی", ic="🌾", cost=600, mins=30, up=10, fx="غذا + رضایت +۲"),
 "hosp": dict(nm="بیمارستان", ic="🏥", cost=1100, mins=40, up=20, fx="سلامت + رضایت +۳"),
 "uni":  dict(nm="دانشگاه", ic="🏫", cost=1300, mins=50, up=20, fx="پژوهش سریع‌تر - درآمد +۱۸"),
 "road": dict(nm="جاده", ic="🛣️", cost=400, mins=20, up=10, fx="لجستیک +۳"),
 "base": dict(nm="پایگاه نظامی", ic="🪖", cost=2800, mins=150, up=60, fx="دفاع منطقه +۸ هر سطح - پذیرش نیروهای متحد (حقوق $300/ساعت)"),
 "rail": dict(nm="راه‌آهن", ic="🚆", cost=1500, mins=60, up=30, fx="لجستیک +۶ - درآمد +۱۵"),
 "ware": dict(nm="انبار", ic="📦", cost=500, mins=25, up=10, fx="ظرفیت بازار +۵۰"),
 "log":  dict(nm="مرکز لجستیک", ic="🚛", cost=900, mins=35, up=20, fx="لجستیک +۵"),
 "adm":  dict(nm="مرکز اداری", ic="🏢", cost=700, mins=30, up=10, fx="درآمد +۱۸"),
 "comm": dict(nm="مرکز ارتباطات", ic="📡", cost=800, mins=30, up=10, fx="شناسایی + رضایت +۲"),
 "defc": dict(nm="مرکز دفاعی", ic="🛡️", cost=1200, mins=40, up=30, fx="دفاع +۵ - امنیت +۳"),
 "cris": dict(nm="مدیریت بحران", ic="🚨", cost=1000, mins=35, up=20, fx="بحران‌ها ملایم‌تر"),
 "basij":dict(nm="مرکز بسیج", ic="🪖", cost=600, mins=25, up=20, fx="امنیت +۴"),
 "sepah":dict(nm="مرکز سپاه", ic="🎖️", cost=1400, mins=45, up=30, fx="دفاع +۴ - امنیت +۵"),
 "police":dict(nm="مرکز انتظامی", ic="🚔", cost=500, mins=20, up=20, fx="امنیت +۶"),
 "emg":  dict(nm="مرکز امداد", ic="🚑", cost=550, mins=22, up=10, fx="پاسخ بحران سریع‌تر"),
 "trn":  dict(nm="مرکز آموزش", ic="🎯", cost=800, mins=30, up=20, fx="آمادگی +۴"),
}
BORDER = ["fac", "pow", "ref", "mine", "farm", "hosp", "uni", "road", "rail", "ware",
          "log", "adm", "comm", "defc", "cris", "basij", "sepah", "police", "emg", "trn"]

COUNTRIES = {
 "us": dict(nm="آمریکا", fl="🇺🇸", econ=95, ind=90, de=95, st=70, rel=-25),
 "il": dict(nm="اسرائیل", fl="🇮🇱", econ=80, ind=75, de=90, st=65, rel=-30),
 "ru": dict(nm="روسیه", fl="🇷🇺", econ=70, ind=72, de=85, st=60, rel=25),
 "cn": dict(nm="چین", fl="🇨🇳", econ=92, ind=95, de=80, st=78, rel=30),
 "de": dict(nm="آلمان", fl="🇩🇪", econ=88, ind=82, de=60, st=80, rel=-5),
 "fr": dict(nm="فرانسه", fl="🇫🇷", econ=80, ind=70, de=68, st=72, rel=-5),
 "uk": dict(nm="بریتانیا", fl="🇬🇧", econ=82, ind=65, de=72, st=70, rel=-15),
 "tr": dict(nm="ترکیه", fl="🇹🇷", econ=60, ind=58, de=65, st=55, rel=5),
 "ae": dict(nm="امارات", fl="🇦🇪", econ=75, ind=50, de=45, st=74, rel=20),
 "sa": dict(nm="عربستان", fl="🇸🇦", econ=78, ind=45, de=60, st=62, rel=-10),
 "qa": dict(nm="قطر", fl="🇶🇦", econ=85, ind=35, de=35, st=70, rel=10),
 "iq": dict(nm="عراق", fl="🇮🇶", econ=40, ind=30, de=45, st=42, rel=35),
 "in": dict(nm="هند", fl="🇮🇳", econ=72, ind=68, de=70, st=65, rel=25),
 "jp": dict(nm="ژاپن", fl="🇯🇵", econ=85, ind=85, de=55, st=82, rel=0),
 "kr": dict(nm="کره جنوبی", fl="🇰🇷", econ=83, ind=82, de=68, st=75, rel=-5),
 "br": dict(nm="برزیل", fl="🇧🇷", econ=58, ind=52, de=48, st=52, rel=15),
 "za": dict(nm="آفریقای جنوبی", fl="🇿🇦", econ=42, ind=38, de=35, st=45, rel=10),
 "eg": dict(nm="مصر", fl="🇪🇬", econ=45, ind=40, de=58, st=50, rel=8),
 "it": dict(nm="ایتالیا", fl="🇮🇹", econ=72, ind=65, de=52, st=68, rel=0),
 "id": dict(nm="اندونزی", fl="🇮🇩", econ=55, ind=50, de=45, st=58, rel=18),
 "au": dict(nm="استرالیا", fl="🇦🇺", econ=76, ind=55, de=55, st=78, rel=-10),
 "ps": dict(nm="فلسطین", fl="🇵🇸", econ=25, ind=15, de=40, st=35, rel=45),
 "lb": dict(nm="لبنان", fl="🇱🇧", econ=35, ind=25, de=30, st=40, rel=20),
 "ye": dict(nm="یمن", fl="🇾🇪", econ=20, ind=12, de=35, st=30, rel=30),
}
SELLERS = {"ru": [0.85, 0], "cn": [0.9, 0], "tr": [1.0, 10], "br": [1.0, 15], "kr": [1.05, 15],
           "de": [1.15, 25], "fr": [1.15, 25], "it": [1.1, 20], "us": [1.2, 40], "uk": [1.2, 35], "il": [1.3, 40]}
# [ضریب قیمت، حداقل روابط]
EQUIP = [
 dict(nm="خودروی تاکتیکی سراج", ic="🚙", cat="خودرو", price=600,  de=4,  rec=1, lg=3, q=2, mins=20, up=10),
 dict(nm="خودروی سفیر", ic="🚐", cat="خودرو", price=450,  de=2,  rec=1, lg=5, q=2, mins=15, up=10),
 dict(nm="تانک کرار", ic="🛡️", cat="زرهی", price=2200, de=14, rec=2, lg=1, q=4, mins=60, up=40),
 dict(nm="نفربر بوراق", ic="🚛", cat="زرهی", price=1400, de=8,  rec=2, lg=4, q=3, mins=40, up=20),
 dict(nm="جنگنده صاعقه", ic="✈️", cat="هواگرد", price=3000, de=16, rec=6, lg=0, q=5, mins=90, up=60),
 dict(nm="پهپاد مجاهد-۶", ic="🛩️", cat="هواگرد", price=900,  de=2,  rec=8, lg=1, q=3, mins=30, up=10),
 dict(nm="بالگرد طوفان-۲", ic="🚁", cat="بالگرد", price=1800, de=10, rec=4, lg=2, q=4, mins=55, up=30),
 dict(nm="ناوشکن جماران", ic="🚢", cat="دریایی", price=2600, de=12, rec=5, lg=3, q=4, mins=80, up=50),
 dict(nm="شناور تندر ذوالفقار", ic="🛥️", cat="دریایی", price=800,  de=4,  rec=2, lg=2, q=2, mins=25, up=10),
 dict(nm="رادار مطلع‌الفجر", ic="📡", cat="شناسایی", price=1100, de=1,  rec=10, lg=0, q=3, mins=35, up=20),
 dict(nm="سامانه باور-۳۷۳", ic="🗼", cat="دفاعی", price=2800, de=18, rec=4, lg=1, q=5, mins=85, up=50),
 dict(nm="پدافند خرداد-۱۵", ic="🚀", cat="دفاعی", price=2000, de=13, rec=3, lg=1, q=4, mins=65, up=40),
 dict(nm="کاروان امداد و نجات", ic="🏥", cat="امداد", price=500,  de=0,  rec=0, lg=4, q=2, mins=15, up=10),
 dict(nm="تعمیرگاه میدانی", ic="🔧", cat="پشتیبانی", price=650, de=1,  rec=0, lg=6, q=2, mins=18, up=10),
 dict(nm="پهپاد شاهد-۱۲۹", ic="🛩️", cat="هواگرد", price=1600, de=6,  rec=7, lg=1, q=3, mins=50, up=25),
 dict(nm="توپخانه رعد-۲", ic="🎯", cat="زرهی", price=1500, de=9,  rec=1, lg=2, q=3, mins=45, up=25),
 dict(nm="موشک فتح-۱۱۰", ic="🚀", cat="موشکی", price=2400, de=6,  rec=0, lg=2, q=5, mins=70, up=45),
 dict(nm="موشک خیبرشکن", ic="🚀", cat="موشکی", price=2600, de=7,  rec=2, lg=1, q=4, mins=90, up=45),
 dict(nm="موشک حاج‌قاسم", ic="🚀", cat="موشکی", price=2400, de=7,  rec=2, lg=1, q=4, mins=85, up=45),
 dict(nm="موشک خیبر-۴", ic="🚀", cat="موشکی", price=3000, de=8,  rec=2, lg=1, q=5, mins=100, up=50),
 dict(nm="کروز سومار", ic="🚀", cat="موشکی", price=2200, de=6,  rec=3, lg=0, q=4, mins=80, up=40),
 dict(nm="کت آرش-۲", ic="🚀", cat="موشکی", price=1300, de=5,  rec=1, lg=0, q=3, mins=50, up=25),
 dict(nm="پدافند صیاد-۳", ic="🗼", cat="دفاعی", price=1800, de=15, rec=4, lg=1, q=4, mins=60, up=30),
 dict(nm="پهپاد کمان-۲۲", ic="🛩️", cat="هواگرد", price=2000, de=8,  rec=9, lg=1, q=4, mins=70, up=35),
 dict(nm="پهپاد ابابیل-۳", ic="🛩️", cat="هواگرد", price=800,  de=4,  rec=5, lg=1, q=3, mins=30, up=15),
 dict(nm="موشک فتاح-۱", ic="🚀", cat="موشکی", price=3200, de=8,  rec=2, lg=1, q=5, mins=110, up=55),
 dict(nm="موشک عماد", ic="🚀", cat="موشکی", price=2900, de=7,  rec=2, lg=1, q=5, mins=95, up=50),
 dict(nm="موشک سجیل", ic="🚀", cat="موشکی", price=3100, de=8,  rec=1, lg=1, q=5, mins=105, up=55),
 dict(nm="موشک قیام-۱", ic="🚀", cat="موشکی", price=1400, de=5,  rec=0, lg=1, q=3, mins=45, up=25),
 dict(nm="پهپاد شاهد-۱۳۶", ic="🛩️", cat="هواگرد", price=1100, de=6,  rec=1, lg=0, q=4, mins=45, up=20),
 dict(nm="پهپاد گزا", ic="🛩️", cat="هواگرد", price=2100, de=3,  rec=8, lg=0, q=4, mins=60, up=30),
 dict(nm="کروز پاوه", ic="🚀", cat="موشکی", price=2300, de=6,  rec=3, lg=0, q=4, mins=80, up=40),
 dict(nm="کروز حویز", ic="🚀", cat="موشکی", price=2100, de=6,  rec=2, lg=0, q=4, mins=75, up=38),
 dict(nm="کروز دریایی ابو مهدی", ic="🚢", cat="دریایی", price=2400, de=12, rec=4, lg=2, q=4, mins=80, up=45),
 dict(nm="پهپاد مهاجر-۱۰", ic="🛩️", cat="هواگرد", price=1900, de=6,  rec=9, lg=1, q=4, mins=65, up=30),
]
FOREIGN = {
 "ru": [dict(nm="جنگنده سوخو-۳۵اس", ic="✈️", cat="هواگرد", price=4200, de=18, rec=6, lg=0, q=5, mins=100, up=60),
        dict(nm="تانک تی-۹۰ام", ic="🛡️", cat="زرهی", price=3200, de=16, rec=2, lg=1, q=4, mins=75, up=50),
        dict(nm="سامانه اس-۴۰۰", ic="🗼", cat="دفاعی", price=3600, de=20, rec=5, lg=1, q=5, mins=95, up=55),
        dict(nm="پدافند پانتسیر-اس۱", ic="🚛", cat="زرهی", price=1900, de=10, rec=4, lg=3, q=3, mins=55, up=30),
        dict(nm="جت آموزشی یاک-۱۳۰", ic="✈️", cat="هواگرد", price=2600, de=12, rec=5, lg=0, q=4, mins=70, up=40),
        dict(nm="موشک ایسکندر-ام", ic="🚀", cat="موشکی", price=4600, de=8,  rec=2, lg=1, q=5, mins=120, up=65),
        dict(nm="جنگنده سوخو-۵۷", ic="✈️", cat="هواگرد", price=5800, de=24, rec=7, lg=0, q=6, mins=140, up=75),
        dict(nm="بالگرد کا-۵۲ آلیگاتور", ic="🚁", cat="بالگرد", price=2900, de=14, rec=5, lg=1, q=4, mins=70, up=40)],
 "cn": [dict(nm="جنگنده جی-۱۰سی", ic="✈️", cat="هواگرد", price=3800, de=17, rec=6, lg=0, q=5, mins=95, up=55),
        dict(nm="تانک وی‌تی-۴", ic="🛡️", cat="زرهی", price=3000, de=15, rec=2, lg=1, q=4, mins=70, up=45),
        dict(nm="سامانه اچ‌کیو-۹بی‌ای", ic="🗼", cat="دفاعی", price=3300, de=19, rec=4, lg=1, q=5, mins=90, up=50),
        dict(nm="پهپاد چ-۵", ic="🛩️", cat="هواگرد", price=1500, de=5, rec=7, lg=1, q=3, mins=45, up=20),
        dict(nm="پهپاد وینگ‌لانگ-۲", ic="🛩️", cat="هواگرد", price=1700, de=6, rec=8, lg=1, q=3, mins=50, up=25),
        dict(nm="جنگنده جی-۲۰", ic="✈️", cat="هواگرد", price=5600, de=23, rec=7, lg=0, q=6, mins=140, up=75),
        dict(nm="جنگنده جی-۱۶دی", ic="✈️", cat="هواگرد", price=3600, de=16, rec=7, lg=0, q=5, mins=90, up=50),
        dict(nm="ناوشکن تایپ-۰۵۵", ic="🚢", cat="دریایی", price=4400, de=21, rec=6, lg=2, q=5, mins=120, up=60)],
 "us": [dict(nm="تانک ام۱آ۲ آبرامز", ic="🛡️", cat="زرهی", price=3400, de=16, rec=2, lg=1, q=4, mins=75, up=50),
        dict(nm="اف-۱۶ بلوک ۷۰", ic="✈️", cat="هواگرد", price=4000, de=18, rec=6, lg=0, q=5, mins=100, up=60),
        dict(nm="پاتریوت پی‌ای‌سی-۳", ic="🗼", cat="دفاعی", price=3500, de=19, rec=5, lg=1, q=5, mins=95, up=55),
        dict(nm="سامانه ثاد", ic="🗼", cat="دفاعی", price=4200, de=22, rec=5, lg=0, q=5, mins=110, up=65),
        dict(nm="پهپاد ام‌کیو-۹ ریپر", ic="🛩️", cat="هواگرد", price=2600, de=7, rec=9, lg=0, q=4, mins=70, up=35),
        dict(nm="جنگنده اف-۲۲ رپتور", ic="✈️", cat="هواگرد", price=5600, de=24, rec=7, lg=0, q=6, mins=140, up=75),
        dict(nm="جنگنده اف-۱۵ایکس", ic="✈️", cat="هواگرد", price=4400, de=20, rec=5, lg=1, q=5, mins=110, up=60),
        dict(nm="موشک اسم-۶", ic="🚀", cat="موشکی", price=3400, de=7,  rec=3, lg=1, q=4, mins=90, up=50)],
 "il": [dict(nm="اف-۳۵آی ادیر", ic="✈️", cat="هواگرد", price=5200, de=22, rec=8, lg=0, q=5, mins=120, up=70),
        dict(nm="پدافند ارو-۳", ic="🗼", cat="دفاعی", price=4000, de=21, rec=5, lg=0, q=5, mins=100, up=60),
        dict(nm="گنبد آهنین", ic="🗼", cat="دفاعی", price=2800, de=15, rec=3, lg=2, q=4, mins=80, up=45),
        dict(nm="پهپاد هرون-تی‌پی", ic="🛩️", cat="هواگرد", price=2400, de=6, rec=9, lg=1, q=4, mins=65, up=35),
        dict(nm="سامانه باراک-۸", ic="🚀", cat="دفاعی", price=2500, de=14, rec=3, lg=2, q=4, mins=70, up=40),
        dict(nm="تانک مرکاوا-۴", ic="🛡️", cat="زرهی", price=3100, de=17, rec=3, lg=1, q=4, mins=80, up=45),
        dict(nm="سامانه دیوید اسلینگ", ic="🗼", cat="دفاعی", price=2900, de=17, rec=4, lg=1, q=4, mins=80, up=45),
        dict(nm="ناوچه سائار-۶", ic="🚢", cat="دریایی", price=3600, de=16, rec=6, lg=2, q=5, mins=100, up=55)],
}

def fstock(p, ck):
    """سلاح خارجی فقط با حزب درست: جمهوری اسلامی ← روسیه/چین - پهلوی ← آمریکا/اسرائیل"""
    ident = p.get("ident")
    if ident == "rep" and ck in ("ru", "cn"): return FOREIGN[ck]
    if ident == "pah" and ck in ("us", "il"): return FOREIGN[ck]
    return []

COMMS = [("energy", "⛽ انرژی", 100), ("oil", "🛢 نفت خام", 110), ("food", "🌾 غذا", 80), ("mineral", "⛏️ مواد", 120),
         ("industrial", "🏭 کالای صنعتی", 90), ("strategic", "📦 استراتژیک", 150)]
PROJECTS = {
 "cor": dict(nm="کریدور اقتصادی", ic="🏗️", st=[1800, 2600, 3400], mins=[90, 120, 150], fx="درآمد +۸٪"),
 "eng": dict(nm="شبکه انرژی", ic="⚡", st=[1600, 2400, 3200], mins=[80, 110, 140], fx="انرژی +۸"),
 "rail":dict(nm="شبکه ریلی", ic="🚆", st=[1700, 2500, 3300], mins=[85, 115, 145], fx="لجستیک +۸"),
 "ind": dict(nm="شهر صنعتی", ic="🏭", st=[2000, 2800, 3600], mins=[95, 125, 155], fx="تولید +۸"),
 "agr": dict(nm="طرح کشاورزی", ic="🌾", st=[1200, 1800, 2400], mins=[70, 95, 120], fx="رضایت +۵ - غذا"),
 "med": dict(nm="شبکه درمانی", ic="🏥", st=[1400, 2000, 2700], mins=[75, 100, 130], fx="سلامت - رضایت +۶"),
 "tec": dict(nm="پروژه فناوری", ic="🌐", st=[1900, 2700, 3500], mins=[90, 120, 150], fx="پژوهش +۱۵٪"),
}
TECHS = {}
_tiers = [("industry", "🏭 صنعت", ["خط مونتاژ نو", "رباتیک کارخانه", "شبکه تولید هوشمند"]),
          ("energy", "⚡ انرژی", ["توربین پربازده", "خورشیدی مقیاس‌پذیر", "شبکه هوشمند برق"]),
          ("logi", "🚚 لجستیک", ["مسیرهای بهینه", "حمل ترکیبی", "زنجیره تامین دیجیتال"]),
          ("comm", "📡 ارتباطات", ["شبکه ملی داده", "پوشش سراسری", "سایبر مرزها"]),
          ("med", "🏥 پزشکی", ["پوشش درمان روستا", "زنجیره دارو", "پزشکی پیشگیرانه"]),
          ("agr", "🌾 کشاورزی", ["آبیاری نو", "بذر مقاوم", "سردخانه ملی"]),
          ("soft", "💻 فناوری", ["دولت الکترونیک", "پرداخت ملی", "هوش مصنوعی خدمت"]),
          ("def", "🛡️ دفاع", ["پدافند لایه‌ای", "آمادگی پایدار", "پاسخ سریع"]),
          ("urban", "🏙️ شهرسازی", ["مسیر پاک", "بازآفرینی شهری", "شهر ۱۵ دقیقه‌ای"])]
for br, nm, t3 in _tiers:
    for i, t in enumerate(t3):
        TECHS[f"{br}{i}"] = dict(nm=t, br=nm, tier=i + 1, cost=900 + 800 * i, mins=40 + 30 * i,
                                 need=f"{br}{i-1}" if i else "")
CRISESS = [("🔥 آتش‌سوزی", 400), ("🌪️ بلای طبیعی", 700), ("⚡ قطعی انرژی", 350), ("📉 بحران اقتصادی", 500),
           ("🏭 حادثه صنعتی", 450), ("🚚 اختلال لجستیکی", 400), ("🏥 بحران درمانی", 550), ("⚠️ افت امنیت", 450), ("🗣 نارضایتی اجتماعی", 450), ("🚢 تعطیلی مسیر تجاری", 500), ("🛒 رکود تجارت محلی", 400)]
DECISIONS = [
 dict(q="بودجه صنعت را افزایش دهیم؟", a=[("افزایش", "industry_up"), ("کاهش", "industry_dn"), ("بدون تغییر", "none")]),
 dict(q="سیاست باز تجاری اجرا کنیم؟", a=[("بله - درهای باز", "trade_open"), ("خیر - محتاطانه", "trade_close"), ("میانه", "none")]),
 dict(q="ساعات کاری کارخانه‌ها بیشتر شود؟", a=[("بله", "work_more"), ("خیر", "work_less"), ("بدون تغییر", "none")]),
 dict(q="یارانه انرژی خانگی؟", a=[("افزایش", "sub_up"), ("حذف تدریجی", "sub_dn"), ("تثبیت", "none")]),
 dict(q="سرمایه‌گذاری بزرگ خارجی اجازه بدهیم؟", a=[("اجازه", "fdi_yes"), ("محدود", "fdi_no"), ("منطقه‌ای", "none")]),
 dict(q="تمرکززدایی از تهران؟", a=[("انتقال ادارات", "decent"), ("ماندگاری", "none"), ("شهر جدید", "newcity")]),
 dict(q="بازسازی مناطق کم‌توسعه؟", a=[("اولویت سیستان", "sis_focus"), ("اولویت هرمزگان", "hrm_focus"), ("توزیع عادلانه", "none")]),
 dict(q="قانون صرفه‌جویی انرژی صنعتی؟", a=[("سخت‌گیرانه", "eco_hard"), ("تشویقی", "eco_soft"), ("بدون قانون", "none")]),
]

# ───────── دنیاها: هر گروه = یک دنیای مستقل - پروفایل بازیکن مشترک ─────────
# profiles.json: {uid: نام/xp/سطح/دنیای انتخابی} - worlds.json: {gid: دنیای کامل مستقل}
profiles = jload("profiles.json", {})
APPROVED_GROUPS = set(jload("groups.json", []))
OWNER_ID = "8694290031"
worlds = jload("worlds.json", {})

def new_st():
    """وضعیت جهانی تازه برای یک دنیای جدید"""
    return dict(season=1, born=time.time(), last_world=0, tension=30, last_settle=0,
                market={k: b for k, _, b in COMMS},
                countries={k: dict(v) for k, v in COUNTRIES.items()})

def ensure_world(gid, title="🌍 دنیای گروه"):
    w = worlds.get(gid)
    if w is None:
        w = worlds[gid] = dict(title=title, st=new_st(), news=[], pdata={})
    st = w["st"]
    for _k, _v in dict(season=1, born=time.time(), last_world=0, tension=30, last_settle=0).items():
        if st.get(_k) is None: st[_k] = _v
    if not isinstance(st.get("market"), dict): st["market"] = {k: b for k, _, b in COMMS}
    for _ck, _cb, _bb in COMMS:
        if _ck not in st["market"]: st["market"][_ck] = _bb
    st.setdefault("countries", {k: dict(v) for k, v in COUNTRIES.items()})
    for _k, _v in COUNTRIES.items(): st["countries"].setdefault(_k, dict(_v))
    if not isinstance(w.get("news"), list): w["news"] = []
    if not isinstance(w.get("pdata"), dict): w["pdata"] = {}
    # وضعیت کنترل مناطق: هر منطقه world_id (gid) + region_id + owner + status + تاریخچه
    if not isinstance(st.get("rs"), dict) or not st["rs"]:
        st["rs"] = {rk: dict(owner=None, status="neutral", hist=[]) for rk in REGIONS}
    for rk in REGIONS: st["rs"].setdefault(rk, dict(owner=None, status="neutral", hist=[]))
    for rk in REGIONS: st["rs"][rk].setdefault("party", REGIONS[rk]["party"])
    if not isinstance(st.get("prot"), dict): st["prot"] = {}
    if not isinstance(st.get("wlog"), list): st["wlog"] = []
    if not isinstance(st.get("wars"), list): st["wars"] = []
    if not isinstance(st.get("pacts"), dict): st["pacts"] = {}
    if not isinstance(st.get("preq"), dict): st["preq"] = {}
    if not isinstance(st.get("audit"), list): st["audit"] = []
    if not isinstance(st.get("sellmod"), dict): st["sellmod"] = {}
    if not isinstance(st.get("treq"), dict): st["treq"] = {}
    if st.get("tseq") is None: st["tseq"] = 1
    if not isinstance(st.get("forces"), dict): st["forces"] = {}
    if not isinstance(st.get("col"), dict): st["col"] = {}
    if not isinstance(st.get("cfg"), dict): st["cfg"] = {}
    st["cfg"].setdefault("max_regions", len(REGIONS))
    return w

def rs_sync():
    """مالکیت شهرهای فعلی بازیکنان را در وضعیت مناطق ثبت می‌کند"""
    st = world
    for uid2, wp2 in (worlds.get(_CTX[0], {}).get("pdata") or {}).items():
        ck = wp2.get("city")
        if ck and ck in REGIONS and st["rs"][ck]["owner"] is None:
            st["rs"][ck]["owner"] = uid2
            st["rs"][ck]["status"] = "green"

# مهاجرت یک‌باره از فایل‌های قدیمی
if not worlds:
    _ow = jload("world.json", {})
    _on = jload("news.json", [])
    _op = jload("players.json", {})
    worlds["0"] = dict(title="🏠 دنیای اصلی", st=_ow or new_st(), news=_on if isinstance(_on, list) else [], pdata=_op if isinstance(_op, dict) else {})
    jsave("worlds.json", worlds)

# ───────── مهاجرت نسخه‌دار دیتا (Stand-in مهاجرت‌های PostgreSQL) ─────────
def _schema_ver(name):
    d = jload("schema.json", {})
    return int(d.get(name, 0)) if isinstance(d, dict) else 0

def _set_schema_ver(name, v):
    d = jload("schema.json", {})
    if not isinstance(d, dict): d = {}
    d[name] = int(v)
    jsave("schema.json", d)

def migrate_all():
    """هر نسخه فقط یک بار اجرا می‌شود - idempotent"""
    ch = False
    if _schema_ver("worlds") < 1:
        for w in worlds.values():
            if not isinstance(w, dict): continue
            st = w.get("st")
            if not isinstance(st, dict): continue
            for k2, d2 in dict(treq={}, tseq=1, pacts={}, preq={}, audit=[], sellmod={}).items():
                st.setdefault(k2, dict(d2) if isinstance(d2, dict) else (list(d2) if isinstance(d2, list) else d2))
        _set_schema_ver("worlds", 1); ch = True
        LOG.info("migration applied: worlds v1 (treq/tseq/pacts/preq/audit/sellmod)")
    if _schema_ver("profiles") < 1:
        for pr in profiles.values():
            if isinstance(pr, dict): pr.setdefault("titles", [])
        _set_schema_ver("profiles", 1); ch = True
        LOG.info("migration applied: profiles v1 (titles)")
    if _schema_ver("worlds") < 2:
        for w in worlds.values():
            if not isinstance(w, dict): continue
            st = w.get("st")
            if not isinstance(st, dict): continue
            st.setdefault("forces", {})
            for rk in REGIONS:
                st.setdefault("rs", {})
                if rk not in st["rs"]: st["rs"][rk] = dict(owner=None, status="neutral", hist=[])
            for pv in (st.get("pacts") or {}).values():
                if isinstance(pv, dict): pv.setdefault("kind", "ndq")
        _set_schema_ver("worlds", 2); ch = True
        LOG.info("migration applied: worlds v2 (urm/forces/pact-kind)")
    if _schema_ver("worlds") < 3:
        for w in worlds.values():
            if not isinstance(w, dict): continue
            st = w.get("st")
            if not isinstance(st, dict): continue
            st.setdefault("rs", {})
            if "msd" not in st["rs"]:
                st["rs"]["msd"] = dict(owner=None, status="neutral", hist=[])
        _set_schema_ver("worlds", 3); ch = True
        LOG.info("migration applied: worlds v3 (msd)")
    if _schema_ver("worlds") < 4:
        for w in worlds.values():
            if not isinstance(w, dict): continue
            st = w.get("st")
            if not isinstance(st, dict): continue
            st.setdefault("col", {})
        _set_schema_ver("worlds", 4); ch = True
        LOG.info("migration applied: worlds v4 (col)")
    if ch:
        save_all()

migrate_all()
LOG.info("startup: worlds=%d profiles=%d schema=worlds:%d/profiles:%d",
         len(worlds), len(profiles), _schema_ver("worlds"), _schema_ver("profiles"))

world = {}      # بافت فعال - با set_ctx عوض می‌شود
NEWS = []       # بافت فعال
_CTX = ["0"]

def set_ctx(gid):
    """قبل از هر پردازش، دنیای فعال سوار می‌شود - همه پردازش‌ها زیر _lock هستند"""
    global world, NEWS
    _CTX[0] = gid
    w = ensure_world(gid)
    world = w["st"]; NEWS = w["news"]

set_ctx("0")

def news(txt):
    NEWS.append({"t": tehfull(), "x": txt})
    del NEWS[:-200]

def wbroadcast(txt):
    """اعلام رخداد مهم World در گروه همان دنیا - در دنیای خصوصی ارسال نمی‌شود"""
    g = _CTX[0]
    if g and g != "0" and g.lstrip("-").isdigit():
        try: tg("sendMessage", chat_id=int(g), parse_mode="HTML", text=txt)
        except Exception: pass

# ───────── هویت ملی - دو مسیر متوازن ─────────
IDENTS = {
 "rep": dict(nm="جمهوری اسلامی ایران", short="جمهوری اسلامی", title="رئیس‌جمهور", flag="iran1",
             friends=["ru", "cn", "iq"], foes=["us", "uk", "fr"],
             up="ثبات +۵ - مراکز بسیج/سپاه/انتظامی ۱۰٪ ارزان‌تر - روابط روسیه/چین/عراق +۸",
             dn="روابط آمریکا/بریتانیا/فرانسه −۸",
             cheap=dict(basij=0.9, sepah=0.9, police=0.9)),
 "pah": dict(nm="ایران شاهنشاهی", short="پهلوی", title="شاهنشاه", flag="pahlavi",
             friends=["us", "uk", "fr", "de", "il"], foes=["ru", "cn", "iq"],
             up="درآمد ملی +۵٪ - دانشگاه/راه‌آهن/جاده ۱۰٪ ارزان‌تر - روابط آمریکا/بریتانیا/فرانسه/آلمان +۸",
             dn="روابط روسیه/چین/عراق −۸",
             cheap=dict(uni=0.9, rail=0.9, road=0.9)),
}
IDENT_FLAVOR = {
 "rep": ["📣 خطبه نماز جمعه - امت و دولت هم‌صدا", "🍚 طرح حمایتی محلات اجرا شد", "🕌 هیئت‌های مذهبی در تکاپو"],
 "pah": ["🎉 جشن فرهنگ و هنر ایران برگزار شد", "🌆 طرح نوسازی خیابان‌ها آغاز شد", "🦁 شکوه تاریخی ایران جاری است"],
}

def crel(p, ck):
    """روابط ادراکی بازیکن = روابط جهانی + تعدیل هویت ملی"""
    return max(-100, min(100, world["countries"][ck]["rel"] + p.get("relmod", {}).get(ck, 0)))

def ident_apply(p, key):
    d = IDENTS[key]
    p["ident"] = key
    rm = {}
    for f in d["friends"]: rm[f] = 8
    for f in d["foes"]: rm[f] = -8
    p["relmod"] = rm
    if key == "rep": p["stab"] = min(100, p["stab"] + 5)
    else: p["incmod"] = 1.05

def bcost(p, rk, bk):
    """هزینه ساخت با تخفیف هویت ملی - گِرد به ۱۰"""
    lv = p["regions"][rk]["bl"].get(bk, 0)
    dsc = IDENTS.get(p.get("ident") or "", {}).get("cheap", {}).get(bk, 1.0)
    return int(round(BUILDS[bk]["cost"] * (1 + 0.35 * lv) * dsc / 10) * 10)

# ───────── بازیکن ─────────
def new_profile(u):
    """پروفایل مشترک بین همه دنیاها: نام، XP، سطح، دنیای فعال"""
    return dict(name=(u.get("first_name") or "فرمانده")[:20], xp=0, lvl=1, sel="0", titles=[])

def new_wp(u):
    """بازیکن داخل یک دنیا - کاملاً جدا از دنیاهای دیگر"""
    p = dict(uid=str(u.get("id")), name=(u.get("first_name") or "فرمانده")[:20],
             treasury=2000, pop=89.0, sat=60, prod=55, energy=60, logi=40, stab=60,
             income_hour=0, stock={k: 0 for k, _, _ in COMMS}, stockcap=200,
             budget=dict(con=15, health=10, edu=10, ind=15, de=15, log=10, dip=5, cri=10),
             regions={}, builds=[], pending=[], deliveries=[], research=None, research_done=[],
             projects={}, agreements={}, rels_done={}, crises=[], decision=None, dec_cd=0,
             equip=[], cargos=[], ident=None, relmod={}, incmod=1.0, mpage=1, city=None,
             last_settle=time.time(), last_mkt=0, ops={}, score=0,
             won_wars=0, sanctions=0, titles=[], menu=0, sub=0, subs={}, gid="0", born=time.time())
    for rk, rv in REGIONS.items():
        p["regions"][rk] = dict(pop=rv["pop"], ind=rv["ind"], sat=rv["sec"], sec=rv["sec"],
                                dev=rv["dev"], bl={})
    p["regions"]["thr"]["bl"] = {"adm": 1, "police": 1}
    p["regions"]["khz"]["bl"] = {"mine": 1}
    p["regions"]["esf"]["bl"] = {"fac": 1}
    return p

def addxp(p, n):
    """XP مشترک پروفایل - در همه دنیاها جمع می‌شود"""
    pr = profiles.get(p["uid"])
    if not pr: return
    pr["xp"] = int(pr.get("xp", 0)) + n
    pr["lvl"] = pr["xp"] // 600 + 1

def migrate(p):
    for k, v in dict(treasury=0, sat=50, prod=50, energy=50, logi=30, stab=50, income_hour=0,
                     stock={}, stockcap=200, budget={}, regions={}, builds=[], pending=[],
                     deliveries=[], research=None, research_done=[], projects={}, agreements={},
                     rels_done={}, crises=[], decision=None, dec_cd=0, equip=[], last_settle=0.0,
                     last_mkt=0.0, ops={}, score=0, won_wars=0, sanctions=0, titles=[],
                     menu=0, sub=0, pop=89.0, ident=None, relmod={}, incmod=1.0, city=None, cargos=[], exports=[], refines=[], arms={},
                     hpay_t=0.0, hpay_tot=0, pay_stash=0.0, hpay_log=None, hpay_inv=0, hpay_inv_t=0.0,
                     pack_multi=0, invest=None).items():
        if p.get(k) is None: p[k] = v
    if p.get("invest") is None: p["invest"] = dict(u=0, t=0)
    if p.get("hpay_log") is None: p["hpay_log"] = []
    if not isinstance(p.get("budget"), dict) or not p["budget"]:
        p["budget"] = dict(con=15, health=10, edu=10, ind=15, de=15, log=10, dip=5, cri=10)
    for rk, rv in REGIONS.items():
        r = p["regions"].setdefault(rk, dict(pop=rv["pop"], ind=rv["ind"], sat=60, sec=rv["sec"],
                                             dev=rv["dev"], bl={}))
        if not isinstance(r.get("bl"), dict): r["bl"] = {}
        for bk2 in [k for k in r["bl"] if k not in BUILDS or r["bl"][k] is None]:
            del r["bl"][bk2]
        for kk, dv in dict(pop=rv["pop"], ind=rv["ind"], sat=50, sec=rv["sec"], dev=rv["dev"]).items():
            if r.get(kk) is None: r[kk] = dv
    for k, _, _ in COMMS: p["stock"].setdefault(k, 0)
    return p

def my_regions(p):
    """قلمرو بازیکن از دیتابیس مرزها - دنیای اصلی = کل ایران"""
    if (p.get("gid") or "0") == "0":
        return list(REGIONS)
    st = world
    return [rk for rk, x in st["rs"].items() if x["owner"] == p["uid"]]

def owners_of(p):
    """نقشه شهر → (مالک، وضعیت، نام مالک)"""
    st = world
    w = worlds.get(p.get("gid") or "0") or {}
    own = {}
    for rk, x in st["rs"].items():
        if x["owner"]:
            own[rk] = (x["owner"], x.get("status", "green"), (w.get("pdata", {}).get(x["owner"], {}) or {}).get("name") or "فرمانده")
    return own

STAT = {"green": "🟢", "yellow": "🟡", "red": "🔴", "neutral": "⚪"}

def rs_claim(p, rk):
    """ثبت مالکیت در دیتابیس"""
    st = world
    st["rs"][rk] = dict(owner=p["uid"], status="green",
                        hist=(st["rs"][rk].get("hist") or []) + [(int(time.time()), p["uid"], "claim")])

def rs_transfer(p, rk, note):
    """انتقال کنترل منطقه با ثبت کامل در دیتابیس"""
    st = world
    st["rs"][rk]["owner"] = p["uid"]
    st["rs"][rk]["status"] = "green"
    st["rs"][rk]["hist"] = (st["rs"][rk].get("hist") or []) + [(int(time.time()), p["uid"], note)]

def eliminate(d):
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
            if o.get("frm") != uid2:
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


def wlog(rec):
    """تاریخچه جنگ: چه کسی/کجا/چه کاری/وضعیت/نتیجه"""
    st = world
    st["wlog"].append(rec)
    del st["wlog"][:-300]

def aud(p, what, det=""):
    """حسابرسی عملیات مهم - ثبت در دیتابیس World"""
    st = world
    st["audit"].append(dict(who=p.get("name") or "؟", uid=p.get("uid") or "؟", what=what, det=det, t=tehfull()))
    del st["audit"][:-200]

def _mlog(wp, amt, why):
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
    return "|".join(sorted([str(a), str(b)]))

def has_pact(a, b):
    return pk(a, b) in world.get("pacts", {})

def smult(ck):
    """ضریب فروشنده با تعدیل AI اقتصادی جهان"""
    return SELLERS.get(ck, [1.0, 0])[0] + world.get("sellmod", {}).get(ck, 0)

def cd_left(p, k): return max(0, int(p.get("cd", {}).get(k, 0) - time.time()))
def cd_set(p, k, s): p.setdefault("cd", {})[k] = time.time() + s

# ───────── موتور اقتصاد ─────────
def bstat(p, f):
    """جمع اثر ساختمان‌های قلمرو بازیکن به‌تفکیک نوع اثر"""
    out = 0
    for rk in my_regions(p):
        for bk, lv in p["regions"][rk]["bl"].items():
            out += lv * f(bk)
    return out

def nat_stats(p):
    prod = min(100, 40 + bstat(p, lambda b: 4 if b == "fac" else (2 if b in ("ref", "mine") else 0)) * 2
               + sum(v.get("s", 0) for v in p["projects"].values()) + p["budget"].get("ind", 0) * 1.2 - p["sanctions"] * 4)
    energy = min(100, 35 + bstat(p, lambda b: 5 if b == "pow" else (2 if b == "ref" else 0)) * 2
                 + (8 if p["projects"].get("eng", {}).get("s") == 3 else 0) + p["budget"].get("con", 0) // 2)
    logi = min(100, 20 + bstat(p, lambda b: 6 if b == "rail" else (5 if b == "log" else (3 if b == "road" else (2 if b == "ware" else 0))))
               + (8 if p["projects"].get("rail", {}).get("s") == 3 else 0))
    defsc = bstat(p, lambda b: 5 if b == "defc" else (4 if b == "sepah" else (4 if b == "trn" else 0))) * 2
    defsc += sum(e["de"] for e in p["equip"]) + sum(1 for a in p["agreements"].values() if a == "pact") * 10
    defsc += p["budget"].get("de", 0) * 1.5 + (8 if p["research_done"].count("def2") else 0)
    _rs = [p["regions"][rk] for rk in my_regions(p)] or list(p["regions"].values())
    sec_all = sum(r["sec"] for r in _rs) / len(_rs)
    return dict(prod=min(100, prod), energy=energy, logi=logi, de=int(defsc), sec=sec_all)

def nbal(p):
    """تراز ساعتی هر کالا: جمع تولید شهرها − جمع مصرف شهرها"""
    b = {k: 0 for k, _, _ in COMMS}
    for rk, rv in REGIONS.items():
        for k, v in rv.get("out", {}).items(): b[k] += v
        for k, v in rv.get("need", {}).items(): b[k] -= v
    return b

def region_income(p, rk, ns):
    """درآمد ساعتی شهر - جمع عوامل: جمعیت، صنعت، منابع، ساختمان‌ها، زیرساخت، رضایت، امنیت، توسعه، بحران"""
    rv = REGIONS[rk]
    inc = rv["inc"] + sum(lv * {"fac": 18, "ref": 30, "mine": 15, "farm": 9, "rail": 15, "adm": 18}.get(b, 0)
                          for b, lv in p["regions"][rk]["bl"].items())
    m = (0.5 + 0.5 * ns["prod"] / 100) * (0.6 + 0.4 * p["regions"][rk]["sec"] / 100) * (0.7 + 0.3 * p["regions"][rk]["sat"] / 100)
    m *= (0.85 + 0.15 * ns["energy"] / 100)
    if rv["port"] and p["agreements"].get("trade"): m += 0.05 * rv["port"]
    for cid, ag in p["agreements"].items():
        if ag == "joint": m += 0.03
    cr = sum(1 for c in p["crises"] if c["rg"] == rk)
    if cr: m *= max(0.4, 1 - 0.18 * cr)
    nb = nbal(p)
    for k, v in rv.get("need", {}).items():
        if p["stock"].get(k, 0) <= 0 and nb.get(k, 0) < 0: m *= 0.85
    return int(round(inc * m * p.get("incmod", 1.0)))
    rv = REGIONS[rk]; r = p["regions"][rk]
    inc = rv["inc"] + sum(lv * {"fac": 6, "ref": 10, "mine": 5, "farm": 3, "rail": 5, "adm": 6}.get(b, 0)
                          for b, lv in r["bl"].items())
    m = (0.5 + 0.5 * ns["prod"] / 100) * (0.6 + 0.4 * r["sec"] / 100) * (0.7 + 0.3 * r["sat"] / 100)
    m *= (0.85 + 0.15 * ns["energy"] / 100)
    if rv["port"] and p["agreements"].get("trade"): m += 0.05 * rv["port"]
    for cid, ag in p["agreements"].items():
        if ag == "joint": m += 0.03
    cr = sum(1 for c in p["crises"] if c["rg"] == rk)
    if cr: m *= max(0.4, 1 - 0.18 * cr)
    return inc * m

def total_income(p, ns):
    inc = sum(region_income(p, rk, ns) for rk in my_regions(p))
    inc *= 1 + (0.08 if p["projects"].get("cor", {}).get("s") == 3 else 0)
    inc *= 1 + sum(1 for a in p["agreements"].values() if a == "trade") * 0.03
    inc *= 1 + sum(1 for a in p["agreements"].values() if a == "joint") * 0.03
    inc *= 1 + sum(1 for a in p["agreements"].values() if a == "fdi") * 0.015
    inc *= 1 - min(0.30, p["sanctions"] * 0.05)
    inc *= 0.9 + 0.2 * (p["sat"] / 100)
    exp_up = sum(BUILDS[b]["up"] * lv for rk, r in p["regions"].items() for b, lv in r["bl"].items())
    exp_eq = sum(e["up"] for e in p["equip"])
    exp_ar = 30 + p["budget"].get("de", 0) * 4 + p["budget"].get("dip", 0) * 2
    for cid, ag in p["agreements"].items():
        if ag == "over": exp_ar += 80
    net = int(round(inc - exp_up - exp_eq - exp_ar))
    try:
        _lv = int((profiles.get(p["uid"]) or {}).get("lvl", 1))
        if _lv <= 3 and len(my_regions(p)) <= 2 and net < 150:
            net = 150  # 🤲 کمک نوپایی - شروع بدون خونریزی خزانه
    except Exception:
        pass
    return int(round(inc)), net

ARMS = {"thr": "سامانه باور-۳۷۳", "esf": "تانک کرار", "khz": "موشک فتح-۱۱۰", "msd": "پهپاد شاهد-۱۲۹",
        "frs": "ناوشکن جماران", "hrm": "بالگرد طوفان-۲", "azb": "نفربر بوراق", "urm": "خودروی سفیر",
        "khr": "توپخانه رعد-۲", "sis": "پهپاد مجاهد-۶", "krn": "پدافند خرداد-۱۵", "gil": "رادار مطلع‌الفجر",
        "alz": "موشک قیام-۱"}

PARTY_NM = {"rep": "جمهوری اسلامی", "pah": "پهلوی"}
PARTY_IC = {"rep": "🕌", "pah": "👑"}

def reset_world(gid):
    """ریست کامل جهانِ یک گروه: همه مناطق بی‌طرف، جنگ/پیمان/مستعمره/کاروان/زرادخانه از اول - پروفایل شخصی (خزانه/سطح) می‌ماند"""
    st = worlds[gid]["st"]
    st["rs"] = {rk: dict(owner=None, status="neutral", hist=[], party=REGIONS[rk]["party"]) for rk in REGIONS}
    st["wars"] = []; st["pacts"] = {}; st["preq"] = {}; st["forces"] = {}
    st["col"] = {}; st["treq"] = {}; st["wlog"] = []; st["sellmod"] = {}
    for wp in (worlds[gid].get("pdata") or {}).values():
        wp["regions"] = {}; wp["city"] = None
        wp["equip"] = []; wp["deliveries"] = []; wp["cargos"] = []
        wp["builds"] = []; wp["arms"] = {}
        wp["stock"] = {k: 0 for k, _, _ in COMMS}
        wp["stock"]["food"] = 20

def max_regions():
    """سقف مناطق آزاد قابل‌ادعای این World - فقط مالک تغییرش می‌دهد"""
    try: return max(1, min(len(REGIONS), int(world.get("cfg", {}).get("max_regions", len(REGIONS)))))
    except Exception: return len(REGIONS)

def rpop(rk, p=None):
    """جمعیت واقعی شهر (میلیون) - با توسعه رشد می‌کند، بی‌طرف عقب می‌ماند"""
    try:
        base = float(REGIONS[rk].get("pop", 2.0))
    except Exception:
        return 0.0
    if p and rk in (p.get("regions") or {}):
        dev = p["regions"][rk].get("dev", 0) or 0
        return round(base * (1.0 + min(0.40, 0.004 * int(dev))), 2)
    return round(base * 0.92, 2)


def arms_produce(p, hrs):
    """صنایع دفاعی منطقه‌ای: هر منطقه با کارخانه و توسعه، هر ۲ ساعت یک واحد تخصصی می‌سازد"""
    made = []
    for rk, nm3 in ARMS.items():
        if rk not in my_regions(p):
            continue
        r3 = p["regions"][rk]
        if r3.get("bl", {}).get("fac", 0) < 1 or r3.get("dev", 0) < 55:
            continue
        last3 = (p.setdefault("arms", {}).get(rk) or 0)
        steps = int((time.time() - last3) // 7200)
        if steps < 1:
            continue
        e3 = next((x for x in EQUIP if x["nm"] == nm3), None)
        if e3 is None or p["treasury"] < 200:
            continue
        p["arms"][rk] = time.time()
        mpay(p, 200, "تولید تسلیحات")
        p["equip"].append(dict(e3))
        made.append(nm3)
        aud(p, "تولید صنایع دفاعی", f"{nm3} در {REGIONS[rk]['nm']}")
    if made:
        news("🏭 تولیدات این دوره: " + " - ".join(made))
        addxp(p, 8)

def settle(p):
    """تسویه ساعتی - با جبران ساعت‌های غیبت (سقف ۲۴ ساعت)"""
    now = time.time()
    if not p.get("last_settle"): p["last_settle"] = now
    hrs = min(24, (now - p["last_settle"]) / 3600)
    if hrs < 1: return
    ns = nat_stats(p)
    inc, net = total_income(p, ns)
    p["pay_stash"] = round(float(p.get("pay_stash", 0)) + net * hrs, 2)
    p["income_hour"] = int(net)
    for rk in my_regions(p):
        pk2 = world.get("rs", {}).get(rk, {}).get("party") or REGIONS[rk]["party"]
        rr = p["regions"][rk]
        rr["sat"] = min(80, int(rr.get("sat", 60)) + 1) if pk2 == p.get("ident") else max(25, int(rr.get("sat", 60)) - 2)
    arms_produce(p, hrs)
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
                _mlog(p, -trib, "باج به ارباب")
                _mlog(mp2, trib, "باج از مستعمره")
    slv9 = sum(1 for c9 in world.get("col", {}).values() if c9.get("master") == p["uid"] and c9.get("kind") == "slv")
    if slv9:
        mearn(p, int(8 * slv9 * hrs), "کار بردگان")
    # ⏰ واریز ساعتی - مرز دقیق ساعت ایران (UTC+3:30)
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
    for k, _, _ in COMMS:
        b = sum(REGIONS[rk].get("out", {}).get(k, 0) - REGIONS[rk].get("need", {}).get(k, 0) for rk in mr)
        cur = int(round(p["stock"].get(k, 0)))
        if b > 0: p["stock"][k] = min(p["stockcap"], int(round(cur + b * hrs)))
        elif b < 0: p["stock"][k] = max(0, int(round(cur + b * hrs)))
    p["pop"] = min(95.0, p["pop"] + 0.02 * hrs * (p["sat"] / 100))
    for rk, r in p["regions"].items():
        r["dev"] = int(round(min(100, r["dev"] + 0.05 * hrs * (p["budget"].get("con", 15) / 15))))
    p["last_settle"] = now

# ───────── موتور جهان ─────────
def world_tick():
    now = time.time()
    if now - world.get("last_world", 0) < 300: return
    world["last_world"] = now
    mk = world["market"]
    evs = [x for x in NEWS[-40:] if x["x"].startswith(("⛽", "⚔️", "📉", "🌪️"))]
    for k, _, _ in COMMS:
        drift = random.uniform(-0.03, 0.03) + 0.01 * len(evs) * random.choice([-1, 1])
        mk[k] = int(round(max(30, min(400, mk[k] * (1 + drift))) / 5) * 5)
    cs = world["countries"]
    ck = random.choice(list(cs))
    c = cs[ck]
    d = random.randint(-4, 5)
    c["rel"] = max(-100, min(100, c["rel"] + d))
    if d >= 4: news(f"{c['fl']} تنش با تهران کاهش یافت - روابط {fa(c['rel'])}+")
    elif d <= -4: news(f"{c['fl']} تنش با تهران افزایش یافت - روابط {fa(c['rel'])}")
    if random.random() < 0.25:
        a, b = random.sample(list(cs), 2)
        if random.random() < 0.5:
            news(f"{cs[a]['fl']}-{cs[b]['fl']} گفت‌وگوهای تجاری آغاز شد")
            cs[a]["econ"] = min(99, cs[a]["econ"] + 0.3)
        else:
            news(f"🌍 تنش {cs[a]['fl']}-{cs[b]['fl']} در منطقه بالا گرفت")
            world["tension"] = min(100, world["tension"] + 2)
    world["tension"] = max(10, min(100, world["tension"] + random.choice([-2, -1, 0, 1, 2, 3])))
    if random.random() < 0.15:
        ck = random.choice(list(SELLERS))
        d2 = random.choice([-0.05, 0.05])
        sm = world.setdefault("sellmod", {})
        sm[ck] = max(-0.2, min(0.2, sm.get(ck, 0) + d2))
        c2 = cs.get(ck) or dict(fl="", nm=ck)
        news(("📉" if d2 < 0 else "📈") + f" تصمیم اقتصادی {c2.get('nm', ck)}: قیمت تسلیحات {'ارزان' if d2 < 0 else 'گران'}‌تر شد")
    pdw = (worlds.get(_CTX[0], {}).get("pdata") or {})
    for rk4 in list(world.get("forces", {})):
        fc4 = world["forces"][rk4]
        if fc4.get("host") not in pdw or fc4.get("frm") not in pdw:
            del world["forces"][rk4]
    for tgt2, lst in list(world.get("treq", {}).items()):
        keep = []
        for o in lst:
            if o["exp"] < now:
                fp = pdw.get(o["frm"])
                if fp: fp["stock"][o["k"]] = int(round(fp["stock"].get(o["k"], 0))) + o["qty"]
            else:
                keep.append(o)
        if keep: world["treq"][tgt2] = keep
        else: world["treq"].pop(tgt2, None)
    save_all()

def player_tick(p):
    """ساخت‌ها/تحقیق/تحویل/بحران/تصمیم هر بازیکن"""
    now = time.time()
    done = [b for b in p["builds"] if b["done"] <= now]
    for b in done:
        p["builds"].remove(b)
        r = p["regions"][b["rg"]]; r["bl"][b["bk"]] = r["bl"].get(b["bk"], 0) + 1
        r["dev"] = min(100, r["dev"] + 2)
        news(f"🇮🇷 {BUILDS[b['bk']]['ic']} {BUILDS[b['bk']]['nm']} در {REGIONS[b['rg']]['nm']} تکمیل شد")
        addxp(p, 10)
    for d in list(p["deliveries"]):
        if d["at"] <= now:
            p["deliveries"].remove(d); p["equip"].append(d["e"])
            news(f"📦 تحویل تجهیزات {d['e']['ic']} {d['e']['nm']} انجام شد")
    for rk3, fc3 in list(world.get("forces", {}).items()):
        if fc3.get("host") != p["uid"]:
            continue
        pay = int((now - fc3.get("last", now)) / 3600 * 300)
        if pay >= 1:
            if p["treasury"] >= pay:
                p["treasury"] = int(p["treasury"]) - int(pay)
                _mlog(p, -int(pay), "حقوق نیروی متحد")
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
    for c in list(p.get("cargos", [])):
        if c["at"] <= now:
            if sum(p["stock"].values()) + c["qty"] > p["stockcap"]:
                c["at"] = now + 120
                continue
            p["cargos"].remove(c)
            p["stock"][c["k"]] = int(round(p["stock"].get(c["k"], 0))) + c["qty"]
    for ex2 in list(p.get("exports", [])):
        if ex2["at"] <= now:
            p["exports"].remove(ex2)
            pay2 = int(round(world["market"]["oil"] * 20 * 1.08))
            mearn(p, pay2, "صادرات نفت")
            aud(p, "تسویه صادرات نفت", fm(pay2))
            news("🚢 قرارداد صادرات نفت " + p["name"] + " تسویه شد - " + fm(pay2))
    for rf2 in list(p.get("refines", [])):
        if rf2["at"] <= now:
            p["refines"].remove(rf2)
            p["stock"]["energy"] = int(round(p["stock"].get("energy", 0))) + 8
            p["stock"]["strategic"] = int(round(p["stock"].get("strategic", 0))) + 2
            aud(p, "پالایش کامل شد", "+۸ انرژی +۲ استراتژیک")
            news("🏭 پالایشگاه " + p["name"] + " کار کرد: +۸ انرژی +۲ استراتژیک")
            news("🚚 محموله ۱۰ تن تحویل انبار شد")
    for c in list(p["crises"]):
        if now > c["dl"]:
            p["crises"].remove(c)
            r = p["regions"][c["rg"]]
            r["sat"] = max(5, r["sat"] - 8); r["dev"] = max(10, r["dev"] - 4)
            if c["nm"].startswith("🗣"): r["sat"] = max(5, r["sat"] - 6)
            if c["nm"].startswith(("🚢", "🛒")): r["dev"] = max(10, r["dev"] - 3)
            news(f"⚠️ بحران {c['nm']} در {REGIONS[c['rg']]['nm']} مهار نشد - خسارت وارد شد")
            wbroadcast(f"⚠️ بحران {c['nm']} در {REGIONS[c['rg']]['nm']} مهار نشد - خسارت وارد شد")
    for k, pj in p["projects"].items():
        if pj.get("at") and pj["at"] <= now:
            pj["s"] = min(3, pj["s"] + 1); pj["at"] = 0
            if pj["s"] >= 3:
                news(f"🏛️ پروژه ملی «{PROJECTS[k]['nm']}» به‌طور کامل به بهره‌برداری رسید")
                addxp(p, 25)
    if p.get("research") and p["research"].get("at") <= now:
        t = TECHS.pop(p["research"]["tk"], None)
        if t: p["research_done"].append(p["research"]["tk"])
        p["research"] = None
        news(f"🧪 فناوری «{t['nm']}» بومی شد" if t else "🧪 پژوهش پایان یافت")
        addxp(p, 20)
    if now - p.get("dec_cd", 0) > 7200 and p.get("decision") is None and random.random() < 0.35:
        p["decision"] = random.choice(DECISIONS); p["dec_cd"] = now
    if random.random() < 0.06:
        _pool = IDENT_FLAVOR.get(p.get("ident") or "", [])
        if _pool: news(random.choice(_pool))
    if len(p["crises"]) < 2 and random.random() < 0.30:
        nm, cost = random.choice(CRISESS)
        resist = bstat(p, lambda b: 1 if b in ("cris", "emg") else 0)
        if random.random() < max(0.15, 0.5 - 0.06 * resist):
            rg = p.get("city") or random.choice(list(REGIONS))
            p["crises"].append(dict(nm=nm, rg=rg,
                                    cost=int(round(cost * (1 - 0.05 * min(6, resist)) / 5) * 5),
                                    dl=now + 3600))
            news(f"🚨 {nm} در {REGIONS[rg]['nm']} - پاسخ لازم است")
    spawn_chest = False
    return spawn_chest

# ───────── قالب‌ها ─────────
def dstat(p):
    ns = nat_stats(p)
    inc, net = total_income(p, ns)
    return ns, inc, net

# ───────── پنل‌ها ─────────
def sec(t):
    """خط راهنمای بخش - یک جمله که کاربر گیج نشود"""
    return f"💡 {t}"

def show_sub(cid, p, t, k=None):
    """پنل گفت‌وگو - هر (بازیکن، گفت‌وگو) پیام پنل خودش را دارد"""
    key = str(cid)
    mid = (p.get("subs") or {}).get(key) or 0
    if mid:
        r = tg("editMessageText", chat_id=cid, message_id=mid, text=t, parse_mode="HTML",
               reply_markup=k, disable_web_page_preview=True)
        d = str(r.get("description", ""))
        if not r.get("ok") and "can't parse entities" in d:
            r = tg("editMessageText", chat_id=cid, message_id=mid, text=t, parse_mode="HTML",
                   reply_markup=k)
            d = str(r.get("description", ""))
        if r.get("ok"): return
        if "not modified" in d: return
    r = tg("sendMessage", chat_id=cid, text=t, parse_mode="HTML", reply_markup=k,
           disable_web_page_preview=True)
    if r.get("ok"):
        p.setdefault("subs", {})[key] = r["result"]["message_id"]

def close_sub(cid, p):
    mid = (p.get("subs") or {}).get(str(cid))
    if mid:
        tg("deleteMessage", chat_id=cid, message_id=mid)
        p.setdefault("subs", {})[str(cid)] = 0

def menu_text(p):
    ns, inc, net = dstat(p)
    d = IDENTS.get(p.get("ident") or "rep")
    goal = "افزایش درآمد و بازسازی زیرساخت‌ها." if net < 300 else "تثبیت رضایت و آمادگی دفاعی."
    return "\n".join([
        f"{pe(d['flag'])} <b>وضعیت کشور - {d['nm']}</b>",
        "━" * 20,
        f"{pe('money')} خزانه: <b>{fm(p['treasury'])}</b>",
        f"{pe('chart')} درآمد ساعتی: <b>{fsm(net)}</b>",
        f"{pe('people')} جمعیت: {fnum(p['pop'] * 1000000)}",
        sec("مرکز فرماندهی - هر رنگ یک بخش؛ با ▶️ بین صفحات بچرخ."),
        f"🌎 {worlds.get(p.get('gid'), worlds.get('0', {})).get('title', '🏠 دنیای اصلی')} - 🎖 سطح {fa((profiles.get(p['uid']) or {}).get('lvl', 1))} - ⭐️ {fa(int(world.setdefault('stars', {}).get(p['uid'], 0)))}",
        "🏙 شهر تو: <b>{REGIONS[p['city']]['nm']}</b>" if p.get("city") else "🏙 شهر تو: <b>کل ایران</b>",
        f"{pe('tool')} تولید: {fa(ns['prod'])}٪",
        f"{pe('battery')} انرژی: {fa(ns['energy'])}٪",
        f"{pe('shield1')} آمادگی: {fa(ns['de'])}",
        f"{pe('ok')} رضایت: {fa(p['sat'])}٪",
        f"{pe('star')} ثبات: {fa(p['stab'])}٪",
        "━" * 20,
        f"{pe('target')} هدف فعلی",
        goal])

def menu_kb(p, page=1):
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
            [btn(u, "⚙️ بودجه", "budget"), btn(u, "🔍 حسابرسی", "audit"), btn(u, "👤 حساب من", "acc")],
            [btn(u, "💳 فروشگاه استارز", "stars"), btn(u, "🤝 قراردادها", "trd")],
            [btn(u, "🟣 صنعت و توسعه ▶️", "mnu:2"), btn(u, "🏠 خانه", "menu")]]
    return kb(rows)

def show_menu(p, cid):
    show_sub(cid, p, menu_text(p), menu_kb(p))

def country_text(p):
    d = IDENTS.get(p.get("ident") or "rep")
    ns = nat_stats(p)
    L = [f"{pe(d['flag'])} <b>{d['nm']}</b>", "━" * 20,
         sec("شناسنامه کشورت: جمعیت، ثبات و تحریم - وضعیت کلی اینجاست."),
         f"🎖 لقب فرمانده: <b>{d['title']}</b>",
         f"🗓 فصل {fa(world.get('season', 1))} - ⏳ {teh()}",
         f"{pe('people')} جمعیت: {fnum(p['pop'] * 1000000)}",
         f"{pe('star')} ثبات: {fa(p['stab'])}٪ - {pe('warn')} تحریم: {fa(p['sanctions'])} لایه",
         f"{pe('shield1')} آمادگی: {fa(ns['de'])} - 🚚 لجستیک: {fa(ns['logi'])}٪",
         "━" * 20,
         "🏛 ساختار سیاسی:",
         f"✅ {d['up']}",
         f"⚠️ {d['dn']}"]
    return "\n".join(L)

def country_kb(p):
    u = p["uid"]
    return kb([[btn(u, "🏙 شهرها", "regs"), btn(u, "🗳 تصمیم‌ها", "dec")],
               [btn(u, "🎖 عناوین", "titles"), btn(u, "⚙️ هویت ملی", "ident")],
               [btn(u, "↩️ بازگشت", "menu"), btn(u, "🏠 خانه", "menu")]])

def ind_text(p):
    ns = nat_stats(p)
    cnt = {}
    for r in p["regions"].values():
        for b, lv in r["bl"].items(): cnt[b] = cnt.get(b, 0) + lv
    pj = p["projects"].get("ind", {}).get("s", 0)
    L = [f"{pe('tool')} <b>صنعت ملی</b>", "━" * 20,
         sec("کارخانه‌ها موتور درآمد و ساخت تجهیزات‌اند - اول اینجا را بساز."),
         f"🏭 تولید: {fa(ns['prod'])}٪ - {pe('battery')} انرژی: {fa(ns['energy'])}٪",
         f"🏭 کارخانه: {fa(cnt.get('fac', 0))} - ⛽ پالایشگاه: {fa(cnt.get('ref', 0))}",
         f"⛏️ مرکز استخراج: {fa(cnt.get('mine', 0))} - ⚡ نیروگاه: {fa(cnt.get('pow', 0))}",
         f"🏙 شهر صنعتی (پروژه ملی): مرحله {fa(pj)}/۳",
         "━" * 20,
         "💡 کارخانه و شهر صنعتی تولید را بالا می‌برند.",
         "📈 تولید، موتور درآمد همه شهرهاست."]
    return "\n".join(L)

def ind_kb(p):
    u = p["uid"]
    return kb([[btn(u, "🏗 ساخت‌وساز", "build"), btn(u, "🏛 پروژه‌ها", "prj")],
               [btn(u, "⛏ منابع", "res"), btn(u, "🚚 لجستیک", "log")],
               [btn(u, "↩️ بازگشت", "menu"), btn(u, "🏠 خانه", "menu")]])

def res_text(p):
    nb = nbal(p)
    L = [f"{pe('box')} <b>منابع و ذخایر ملی</b>", "━" * 20,
         sec("ذخایر خام شهرهایت - سوخت جنگی و پالایش از همین‌جا تأمین می‌شود.")]
    for k, nm, _ in COMMS:
        b = nb[k]
        sgn = "+" if b > 0 else ("−" if b < 0 else "")
        L.append(f"{nm}: {fa(int(round(p['stock'].get(k, 0))))} تن ({sgn}{fa(abs(b))} در ساعت)")
        L.append(f"   قیمت امروز: {fm(world['market'][k])} هر تن")
    L += ["━" * 20,
          "🏭 مازاد تولید به انبار می‌رود - در بازار بفروش.",
          "⛓ کمبود منابع مصرفی = افت درآمد شهرهای وابسته.",
          "🔌 شهرهای صنعتی به مواد شهرهای معدنی وابسته‌اند."]
    return "\n".join(L)

def res_kb(p):
    u = p["uid"]
    return kb([[btn(u, "📈 بازار جهانی", "mkt"), btn(u, "🏭 صنعت", "ind")],
               [btn(u, "↩️ بازگشت", "menu"), btn(u, "🏠 خانه", "menu")]])

def equip_text(p):
    ns = nat_stats(p)
    L = [f"{pe('plane1')} <b>تجهیزات و نیرو</b>", "━" * 20,
         sec("زرادخانه فعال - در حمله و دفاع مستقیم حساب می‌شود."),
         f"{pe('shield1')} قدرت دفاعی: <b>{fa(ns['de'])}</b> امتیاز",
         f"📦 زرادخانه: {fa(len(p['equip']))} - در مسیر تحویل: {fa(len(p['deliveries']))}",
         "━" * 20]
    if p["equip"]:
        cnt = {}
        for e in p["equip"]: cnt[(e["nm"], e["ic"])] = cnt.get((e["nm"], e["ic"]), 0) + 1
        for (nm, ic), n in list(cnt.items())[:8]: L.append(f"- {ic} {nm} ×{fa(n)}")
    else:
        L.append("زرادخانه خالی است.")
        L.append("از دیپلماسی وارد بازار تجهیزات کشورها شو.")
    return "\n".join(L)

def equip_kb(p):
    u = p["uid"]
    return kb([[btn(u, "🤝 دیپلماسی و خرید", "dip"), btn(u, "🛡 دفاع", "de")],
               [btn(u, "↩️ بازگشت", "menu"), btn(u, "🏠 خانه", "menu")]])

def world_text(p):
    tn = world.get("tension", 30)
    cs = sorted(world["countries"].items(), key=lambda x: -crel(p, x[0]))
    L = [f"{pe('eye')} <b>وضعیت جهان</b>", "━" * 20,
         sec("کشورهای واقعی جهان: قرارداد ببند، سلاح بخر، روابط بساز."),
         f"🌡 تنش جهانی: {fa(tn)}٪ " + ("⚔️ آستانه خطر!" if tn >= 70 else "✅ کنترل‌شده"),
         f"🗓 فصل {fa(world.get('season', 1))} - کشورها: {fa(len(cs))}",
         "━" * 20,
         "🤝 نزدیک‌ترین‌ها:"]
    for ck, c in cs[:3]: L.append(f"- {cflag(ck)} {c['nm']} - روابط {fa(crel(p, ck))}")
    L.append("⚠️ پرتنش‌ترین‌ها:")
    for ck, c in cs[-3:]: L.append(f"- {cflag(ck)} {c['nm']} - روابط {fa(crel(p, ck))}")
    return "\n".join(L)

def world_kb(p):
    u = p["uid"]
    return kb([[btn(u, "🤝 دیپلماسی", "dip"), btn(u, "📰 اخبار", "news")],
               [btn(u, "🏆 رتبه‌بندی", "rank")],
               [btn(u, "↩️ بازگشت", "menu"), btn(u, "🏠 خانه", "menu")]])

def set_text(p):
    d = IDENTS.get(p.get("ident") or "rep")
    return "\n".join([f"{pe('refresh')} <b>تنظیمات</b>", "━" * 20,
                         sec("عناوین، ابزارهای مالک و ریست‌ها - بااحتیاط!"),
                      f"🏛 هویت ملی: {d['nm']}",
                      f"🎖 لقب: {d['title']}",
                      f"⏳ زمان تهران: {tehfull()}",
                      "━" * 20,
                      "مدیریت بازی از این‌جا:"])

STARS_SHOP = [(100, 2500), (250, 7000), (500, 15000)]
STARS_MAP = {2500: 100, 7000: 250, 15000: 500}

def stars_text(p):
    _wt = worlds.get(p.get("gid") or "0", {}).get("title", "🏠 دنیای اصلی")
    L = ["💳 <b>فروشگاه استارز</b>", "━" * 20,
         sec("شارژ فوری خزانه با تلگرام استارز - بسته‌های ویژه هم همین‌جاست."),
         "خزانه ملی را با تلگرام استارز شارژ کن.",
         "بعد از پرداخت، شارژ فوری و خودکار است.",
         f"🌎 مقصد شارژ: <b>{esc(_wt)}</b>",
         "━" * 20]
    for st, usd in STARS_SHOP:
        L.append(f"⭐️ {fa(st)} استارز → 💰 {fm(usd)}")
    inv6 = p.get("invest") or {}
    ws6 = int(world.setdefault("stars", {}).get(str(p["uid"]), 0))
    L += [f"⭐️ کیف استارز تو: {fa(ws6)} - 💰 حقوق ساعتی: " + ("فعال ✅" if p.get("hpay_inv") else "خاموش"),
          "📈 بهرهٔ سرمایه: " + ("فعال ✅" if inv6.get("u") else "خاموش"),
          "━" * 20,
          "🔒 پرداخت امن داخل تلگرام - بدون واسطه.",
          "⚡️ شارژ در چند ثانیه - بدون ریسک."]
    return "\n".join(L)

def stars_kb(p):
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
    return "\n".join([
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
               [btn(u, "💳 شارژ خزانه", "stars"), btn(u, "🏠 خانه", "menu")]])

def acc_text(p):
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
    return "\n".join(L)


def set_kb(p):
    u = p["uid"]
    return kb([[btn(u, "⚪ اخبار", "news"), btn(u, "📖 راهنما", "help")],
               [btn(u, "⚙️ هویت ملی", "ident"), btn(u, "🔍 حسابرسی", "audit")],
               [btn(u, "🎖 عناوین", "titles"), btn(u, "💚 سلامت", "health")],
               [btn(u, "🟡 ➖ مناطق", "cfgm:-"), btn(u, "🌍 " + fa(max_regions()) + " منطقه", "cfgm:0"), btn(u, "🟡 ➕ مناطق", "cfgm:+")],
               [btn(u, "♻️ ریست جهان این گروه - مالک", "rst:0")],
               [btn(u, "☠️ ریست کامل همهٔ پلیرها - مالک", "rstp:0")],
               [btn(u, "🏠 خانه", "menu")]])

def ident_text(p):
    d = IDENTS.get(p.get("ident") or "")
    L = [f"{pe('crown')} <b>هویت ملی ایران</b>", "━" * 20,
         sec("این انتخاب نام، پرچم و قوانین اقتصادی تو را می‌سازد."),
         "مسیر سیاسی کشور را انتخاب کن.",
         "هر مسیر مزایا و هزینه خودش را دارد - هیچ‌کدام برنده از پیش نیستند.",
         "━" * 20]
    for key in ("rep", "pah"):
        x = IDENTS[key]
        L += [f"{pe(x['flag'])} <b>{x['nm']}</b>",
              f"✅ {x['up']}",
              f"⚠️ {x['dn']}", ""]
    if d:
        L += ["━" * 20,
              f"مسیر فعلی: {d['nm']}",
              f"تغییر مسیر: {fm(5000)} + رضایت −۱۰ + ثبات −۵"]
    return "\n".join(L)

def ident_kb(p):
    u = p["uid"]
    rows = []
    if not p.get("ident"):
        rows += [[btn(u, "🇮🇷 جمهوری اسلامی ایران", "ident:pick:rep")],
                 [btn(u, "🦁 ایران شاهنشاهی (پهلوی)", "ident:pick:pah")]]
    else:
        rows += [[btn(u, "🔁 تغییر به جمهوری اسلامی - $5,000", "ident:chg:rep")],
                 [btn(u, "🔁 تغییر به ایران شاهنشاهی - $5,000", "ident:chg:pah")],
                 [btn(u, "🏠 خانه", "menu")]]
    return kb(rows)

def ident_ok_text(p, key):
    x = IDENTS[key]
    cur = p.get("ident")
    L = [f"{pe(x['flag'])} <b>{x['nm']}</b>", "━" * 20,
         f"✅ مزایا: {x['up']}",
         f"⚠️ پیامدها: {x['dn']}",
         "━" * 20]
    if cur:
        L += [f"مسیر فعلی: {IDENTS[cur]['nm']}",
              f"هزینه تغییر: {fm(5000)} - رضایت −۱۰ - ثبات −۵",
              "روابط کشورها جابه‌جا می‌شود."]
    else:
        L += ["این انتخاب نام کشور، پرچم، لقب تو،",
              "روابط اولیه و برخی قوانین اقتصادی را تعیین می‌کند.",
              "بعداً با هزینه قابل تغییر است."]
    return "\n".join(L)

def cty_text(p):
    own = owners_of(p)
    L = [f"{pe('city')} <b>انتخاب شهر</b>", "━" * 20,
         sec("پایهٔ قدرتت را همین‌جا می‌سازی - شهر با توسعه‌ات بزرگ می‌شود."),
         "در این دنیا هر فرمانده یک شهر از ایران را دارد.",
         "👥 جمعیت هر شهر با توسعه رشد می‌کند - بی‌طرف عقب می‌ماند.",
         "شهر بی‌طرف (⚪) آزاد است - شهر دیگران را فقط با عملیات نظامی می‌گیری.",
         "━" * 20]
    _fs = 0
    for rk, rv in REGIONS.items():
        if rk in own:
            L.append(f"{STAT[own[rk][1]]} {rv['nm']} - 👥 {fnum(rpop(rk, p) * 1000000)} - فرماندار: {own[rk][2]}")
        elif _fs < max_regions():
            L.append(f"⚪ {rv['nm']} - 👥 {fnum(rpop(rk) * 1000000)} (بی‌طرف - آزاد)"); _fs += 1
        else:
            L.append(f"⛔️ {rv['nm']} - خارج از سقف این World")
    if p.get("city") and world["rs"].get(p["city"], {}).get("owner") != p["uid"]:
        L.append("━" * 20)
        L.append(f"💔 شهر قبلی تو ({REGIONS[p['city']]['nm']}) از دست رفت.")
        L.append("یک شهر بی‌طرف claim کن یا با عملیات بازپس بگیر.")
    return "\n".join(L)

def cty_kb(p):
    st = world
    rows = []
    free = [rk for rk in REGIONS if st["rs"][rk]["owner"] is None][:max_regions()]
    for i in range(0, len(free), 2):
        row = [btn(p["uid"], "🏙 " + REGIONS[free[i]]["nm"], "cset:" + free[i])]
        if i + 1 < len(free): row.append(btn(p["uid"], "🏙 " + REGIONS[free[i + 1]]["nm"], "cset:" + free[i + 1]))
        rows.append(row)
    return kb(rows)

def regs_text(p, page=0):
    items = list(REGIONS.items())
    per = 3; pages = (len(items) + per - 1) // per
    page = max(0, min(page, pages - 1))
    nmshort = {k: n.split()[0] for k, n, _ in COMMS}
    L = [f"{pe('city')} <b>شهرها و مناطق</b> - صفحه {fa(page + 1)}/{fa(pages)}", "━" * 20,
         sec("سرمایهٔ اصلی تو: جمعیت، توسعه و درآمد ساعتی هر شهر.")]
    ns0 = dstat(p)[0]
    for rk, rv in items[page * per:(page + 1) * per]:
        r = p["regions"][rk]
        _own = owners_of(p).get(rk)
        _stat = world["rs"][rk].get("status", "neutral") if _own else "neutral"
        L.append(f"{STAT[_stat]} <b>{rv['nm']}</b> - {rv['tp']}" + (f" (فرماندار: {_own[2]})" if _own else " (بی‌طرف)"))
        if world["rs"][rk].get("owner") == p["uid"]: L.append("⭐️ شهر تو")
        L.append(f"👥 {fnum(rpop(rk, p) * 1000000)} - 📈 توسعه {fa(r['dev'])}٪")
        outs = " - ".join(f"{nmshort[k]} +{fa(v)}" for k, v in rv.get("out", {}).items())
        needs = " - ".join(f"{nmshort[k]} −{fa(v)}" for k, v in rv.get("need", {}).items())
        if outs: L.append(f"📥 تولید: {outs}")
        if needs: L.append(f"📤 مصرف: {needs}")
        L.append(f"💰 درآمد: {fm(region_income(p, rk, ns0))} در ساعت - 😊 {fa(r['sat'])}٪ - 🔒 {fa(r['sec'])}٪")
        if any(c["rg"] == rk for c in p["crises"]): L.append("🚨 بحران فعال در این شهر!")
        L.append("")
    return "\n".join(L), pages

def regs_kb(p, page=0):
    items = list(REGIONS.items())
    per = 3; pages = (len(items) + per - 1) // per
    page = max(0, min(page, pages - 1))
    rows = [[btn(p["uid"], "🏙 " + REGIONS[rk]["nm"], "reg:" + rk) for rk, _ in items[page * per:(page + 1) * per]]]
    nav = []
    if page > 0: nav.append(btn(p["uid"], "◀️ قبلی", f"rpg:{page - 1}"))
    if page < pages - 1: nav.append(btn(p["uid"], "بعدی ▶️", f"rpg:{page + 1}"))
    if nav: rows.append(nav)
    rows.append([btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)

def reg_text(p, rk):
    rv = REGIONS[rk]; r = p["regions"][rk]
    nmshort = {k: n.split()[0] for k, n, _ in COMMS}
    _own = owners_of(p).get(rk)
    _stat = world["rs"][rk].get("status", "neutral") if _own else "neutral"
    L = [f"{STAT[_stat]} <b>{rv['nm']}</b> - {rv['tp']}", "━" * 20,
         f"{rv['fl']}" + (f" - فرماندار: {_own[2]}" if _own else " - بی‌طرف"),
         f"🏛 حزب منطقه: {PARTY_IC[world['rs'][rk].get('party') or rv['party']]} {PARTY_NM[world['rs'][rk].get('party') or rv['party']]}",
         f"💰 درآمد ساعتی: <b>{fm(region_income(p, rk, dstat(p)[0]) if _own else 0)}</b>",
         f"👥 جمعیت: {fnum(r['pop'] * 1000000)}",
         f"🏭 صنعت {fa(r['ind'])} - 📈 توسعه {fa(r['dev'])}٪",
         f"😊 رضایت {fa(r['sat'])}٪ - 🔒 امنیت {fa(r['sec'])}٪",
         "━" * 20, "📦 اقتصاد منابع:"]
    for k, v in rv.get("out", {}).items(): L.append(f"- تولید {nmshort[k]}: +{fa(v)} در ساعت")
    for k, v in rv.get("need", {}).items(): L.append(f"- مصرف {nmshort[k]}: −{fa(v)} در ساعت")
    if not rv.get("out") and not rv.get("need"): L.append("- بازارمحور")
    L += ["━" * 20, "🏗 سازه‌ها:"]
    if r["bl"]:
        for b, lv in sorted(r["bl"].items()):
            L.append(f"- {BUILDS[b]['ic']} {BUILDS[b]['nm']} سطح {fa(lv)}")
    else:
        L.append("- هنوز چیزی ساخته نشده")
    if any(c["rg"] == rk for c in p["crises"]): L.insert(2, "🚨 <b>بحران فعال در این شهر!</b>")
    return "\n".join(L)

def build_text(p, rk, page=0):
    r = p["regions"][rk]
    L = [f"🏗 <b>ساخت‌وساز در {REGIONS[rk]['nm']}</b>",
         f"{pe('money')} خزانه: {fm(p['treasury'])}", "━" * 20]
    items = [b for b in BORDER if r["bl"].get(b, 0) < 5]
    per = 5; pages = max(1, (len(items) + per - 1) // per)
    page = max(0, min(page, pages - 1))
    for b in items[page * per:(page + 1) * per]:
        lv = r["bl"].get(b, 0); bb = BUILDS[b]
        L.append(f"{bb['ic']} <b>{bb['nm']}</b> (سطح {fa(lv)} → {fa(lv + 1)})")
        L.append(f"   💳 {fm(bcost(p, rk, b))} - ⏳ {fa(bb['mins'])} دقیقه - 🔧 نگهداری {fm(bb['up'])}/ساعت")
        L.append(f"   📈 {bb['fx']}")
    L += ["━" * 20, "در حال ساخت: " + (f"{fa(len(p['builds']))} پروژه" if p["builds"] else "هیچ")]
    return "\n".join(L), pages

def build_kb(p, rk, page=0):
    r = p["regions"][rk]
    items = [b for b in BORDER if r["bl"].get(b, 0) < 5]
    per = 5; pages = max(1, (len(items) + per - 1) // per)
    page = max(0, min(page, pages - 1))
    rows = []
    for b in items[page * per:(page + 1) * per]:
        rows.append([btn(p["uid"], f"{BUILDS[b]['ic']} {BUILDS[b]['nm']} - {fm(bcost(p, rk, b))}", f"bld:{rk}:{b}")])
    nav = []
    if page > 0: nav.append(btn(p["uid"], "◀️ قبلی", f"bpg:{rk}:{page - 1}"))
    if page < pages - 1: nav.append(btn(p["uid"], "بعدی ▶️", f"bpg:{rk}:{page + 1}"))
    if nav: rows.append(nav)
    rows.append([btn(p["uid"], "🏛 هم‌سوسازی حزب منطقه - $1,500", "ptf:" + rk)])
    rows.append([btn(p["uid"], "🏙 شهرها", "regs"), btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)

def eco_text(p):
    ns, inc, net = dstat(p)
    L = [f"{pe('money')} <b>اقتصاد ملی</b>", "━" * 20,
         sec("بودجه هر بخش = سهمش از درآمد ساعتی کشور - نتیجه را زنده می‌بینی."),
         f"💳 خزانه: <b>{fm(p['treasury'])}</b>",
         f"📈 درآمد ناخالص: {fsm(inc)} - 📊 سود خالص: {fsm(net)}",
         f"⏰ واریز بعدی: {fa(max(0, int((3600 - (time.time() + 12600) % 3600) / 60)))} دقیقه دیگر - در حال جمع‌شدن: {fm(int(p.get('pay_stash', 0)))}",
         f"💵 جمع واریزهای ساعتی تا امروز: {fm(p.get('hpay_tot', 0))}",
         f"💰 حقوق سرمایه‌گذاری: فعال - {fm(2500)} هر ساعت" if p.get("hpay_inv") else "💰 حقوق سرمایه‌گذاری: خاموش - از 🛍 بسته‌های ویژه",
         ("🤲 کمک نوپایی فعال: کف درآمد $150 در ساعت تا سطح ۳ (حداکثر ۲ شهر)"),
         f"🏭 تولید {fa(ns['prod'])}٪ - ⚡ انرژی {fa(ns['energy'])}٪",
         f"😤 تحریم فعال: {fa(p['sanctions'])} لایه" if p["sanctions"] else "✅ بدون تحریم فعال",
         "━" * 20, "🏦 بودجه ملی (سهم از صد):"]
    names = dict(con="🏗️ عمران", health="🏥 سلامت", edu="🎓 آموزش", ind="🏭 صنعت",
                 de="🛡️ دفاع", log="🚚 لجستیک", dip="🌍 دیپلماسی", cri="🚨 بحران")
    for k, nm in names.items():
        L.append(f"- {nm}: {fa(p['budget'][k])}٪ {bar(p['budget'][k], 30, 6)}")
    tot = sum(p["budget"].values())
    L.append(f"جمع: {fa(tot)}٪ " + ("✅" if tot <= 100 else "⚠️ بیشتر از ۱۰۰!"))
    return "\n".join(L)

def budget_kb(p):
    rows = []
    names = dict(con="عمران", health="سلامت", edu="آموزش", ind="صنعت", de="دفاع", log="لجستیک", dip="دیپلماسی", cri="بحران")
    ks = list(names)
    for i in range(0, len(ks), 2):
        row = [btn(p["uid"], f"➕ {names[ks[i]]}", "bud+" + ks[i])]
        if i + 1 < len(ks): row.append(btn(p["uid"], f"➕ {names[ks[i + 1]]}", "bud+" + ks[i + 1]))
        rows.append(row)
    rows.append([btn(p["uid"], "↩️ اقتصاد", "eco"), btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)

def dip_text(p, page=0):
    cs = world["countries"]
    items = sorted(cs.items(), key=lambda x: -crel(p, x[0]))
    per = 4; pages = (len(items) + per - 1) // per
    page = max(0, min(page, pages - 1))
    L = [f"🤝 <b>دیپلماسی</b> {pe('handshake')} - صفحه {fa(page + 1)}/{fa(pages)}",
         sec("برای هر قرارداد حداقل رابطه لازم است - اول روابط، بعد امضا."),
         f"📜 روابط فعال: {fa(len(p['agreements']))}", "━" * 20]
    for ck, c in items[page * per:(page + 1) * per]:
        rel = crel(p, ck)
        mood = "❤️" if rel >= 50 else ("🤝" if rel >= 20 else ("😐" if rel >= -10 else "⚠️"))
        ag = p["agreements"].get(ck)
        ags = {"trade": "📜", "fdi": "💵", "joint": "🏗️", "pact": "🛡️", "over": "📦"}.get(ag, "")
        L.append(f"{cflag(ck)} <b>{c['nm']}</b> {mood} {fa(rel)} {ags}")
        L.append(f"   💰{fa(c['econ'])} 🏭{fa(c['ind'])} 🛡️{fa(c['de'])} 📊{fa(c['st'])}")
    return "\n".join(L), pages

def dip_kb(p, page=0):
    cs = world["countries"]
    items = sorted(cs.items(), key=lambda x: -crel(p, x[0]))
    per = 4; pages = (len(items) + per - 1) // per
    page = max(0, min(page, pages - 1))
    rows = [[btn(p["uid"], c["fl"] + " " + c["nm"], "cnt:" + ck) for ck, c in items[page * per:(page + 1) * per]]]
    nav = []
    if page > 0: nav.append(btn(p["uid"], "◀️ قبلی", f"dpg:{page - 1}"))
    if page < pages - 1: nav.append(btn(p["uid"], "بعدی ▶️", f"dpg:{page + 1}"))
    if nav: rows.append(nav)
    rows.append([btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)

def cnt_text(p, ck):
    c = world["countries"][ck]
    rel = crel(p, ck)
    L = [f"{cflag(ck)} <b>{c['nm']}</b>", "━" * 20,
         f"💰 اقتصاد {fa(c['econ'])} - 🏭 صنعت {fa(c['ind'])}",
         f"🛡️ دفاع {fa(c['de'])} - 📊 ثبات {fa(c['st'])}",
         f"🤝 روابط با تهران: <b>{fa(rel)}</b> {bar(rel + 100, 200, 8)}",
         "━" * 20]
    if p["agreements"].get(ck):
        nm = {"trade": "📜 قرارداد تجاری", "fdi": "💵 سرمایه‌گذاری", "joint": "🏗️ پروژه مشترک",
              "pact": "🛡️ پیمان دفاعی", "over": "📦 پایگاه لجستیکی"}[p["agreements"][ck]]
        L.append(f"قرارداد فعال: {nm}")
    else:
        L.append("قراردادی فعال نیست")
    if rel < 0: L.append("⚠️ روابط سرد - خرید گران‌تر و محدودتر")
    return "\n".join(L)

def cnt_kb(p, ck):
    rel = crel(p, ck)
    rows = [[btn(p["uid"], "🤝 بهبود روابط - $200", "dipup:" + ck)]]
    if rel >= 30 and not p["agreements"].get(ck): rows.append([btn(p["uid"], "📜 قرارداد تجاری", "agree:" + ck + ":trade")])
    if rel >= 45 and not p["agreements"].get(ck): rows.append([btn(p["uid"], "💵 جذب سرمایه‌گذاری", "agree:" + ck + ":fdi")])
    if rel >= 55 and not p["agreements"].get(ck): rows.append([btn(p["uid"], "🏗️ پروژه مشترک - $1,500", "agree:" + ck + ":joint")])
    if rel >= 65 and not p["agreements"].get(ck): rows.append([btn(p["uid"], "🛡️ پیمان دفاعی", "agree:" + ck + ":pact")])
    if rel >= 35: rows.append([btn(p["uid"], "🛒 بازار تجهیزات این کشور", "shop:" + ck)])
    if rel >= 70 and not p["agreements"].get(ck): rows.append([btn(p["uid"], "📦 پایگاه لجستیکی - $2,000", "agree:" + ck + ":over")])
    rows.append([btn(p["uid"], "🌍 دیپلماسی", "dip"), btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)

def shop_text(p, ck, page=0):
    c = world["countries"][ck]; mult, minrel = SELLERS.get(ck, [1.0, 0])
    rel = crel(p, ck)
    if rel < minrel:
        return "\n".join([f"🛒 <b>بازار تجهیزات {c['nm']}</b>", "━" * 20,
                          f"⛔️ روابط کافی نیست - حداقل {fa(minrel)} لازم است"]), 1
    pm = max(0.8, min(1.8, smult(ck) - rel / 250))
    def ep(base): return int(round(base * pm / 10) * 10)
    L = [f"{pe('plane1')} <b>بازار تجهیزات {c['nm']}</b>", "━" * 20]
    per = 4; pages = (len(EQUIP) + per - 1) // per
    page = max(0, min(page, pages - 1))
    for e in EQUIP[page * per:(page + 1) * per]:
        L.append(f"{e['ic']} <b>{e['nm']}</b> ({e['cat']}) - ⭐️{fa(e['q'])}")
        L.append(f"   🛡️+{fa(e['de'])} 📡+{fa(e['rec'])} 🚚+{fa(e['lg'])} - 💳 {fm(ep(e['price']))} - ⏳ {fa(e['mins'] if rel >= 30 else int(e['mins'] * 1.5))} دقیقه")
    fs2 = fstock(p, ck)
    if fs2 and rel >= minrel + 20:
        L += ["━" * 20, f"🎖 سامانه‌های ویژه {c['nm']} - فقط برای حزب تو"]
        for j2, e2 in enumerate(fs2):
            pr2 = int(round(e2["price"] * pm * 1.15 / 10) * 10)
            L.append(f"{e2['ic']} <b>{e2['nm']}</b> - 💳 {fm(pr2)} - ⏳ {fa(e2['mins'] + 20)} دقیقه")
    elif ck in FOREIGN:
        L += ["━" * 20, "🎖 این کشور سامانه ویژه فقط به حزب متحدش می‌فروشد." +
              ("حزب تو هم‌سو نیست ✋" if not fs2 else "روابط بیشتر لازم (+20).")]
    L += ["━" * 20, "در مسیر تحویل: " + fa(len(p["deliveries"]))]
    return "\n".join(L), pages

def shop_kb(p, ck, page=0):
    c = world["countries"][ck]; mult, minrel = SELLERS.get(ck, [1.0, 0])
    rel = crel(p, ck)
    pm = max(0.8, min(1.8, smult(ck) - rel / 250))
    def ep(base): return int(round(base * pm / 10) * 10)
    per = 4; pages = (len(EQUIP) + per - 1) // per
    page = max(0, min(page, pages - 1))
    rows = []
    for e in EQUIP[page * per:(page + 1) * per]:
        rows.append([btn(p["uid"], f"{e['ic']} {e['nm']} - {fm(ep(e['price']))}", f"buyeq:{ck}:{EQUIP.index(e)}")])
    nav = []
    if page > 0: nav.append(btn(p["uid"], "◀️ قبلی", f"epg:{ck}:{page - 1}"))
    if page < pages - 1: nav.append(btn(p["uid"], "بعدی ▶️", f"epg:{ck}:{page + 1}"))
    if nav: rows.append(nav)
    rows.append([btn(p["uid"], "↩️ " + c["nm"], "cnt:" + ck), btn(p["uid"], "🏠 خانه", "menu")])
    
    fs3 = fstock(p, ck)
    if fs3:
        rel3 = crel(p, ck)
        minrel3 = SELLERS.get(ck, [1.0, 0])[1]
        if rel3 >= minrel3 + 20:
            cur = []
            for j3 in range(len(fs3)):
                cur.append(btn(p["uid"], FOREIGN[ck][j3]["ic"], f"fbuy:{ck}:{j3}"))
                if len(cur) == 3:
                    rows.append(cur); cur = []
            if cur: rows.append(cur)


def def_text(p):
    ns = nat_stats(p)
    tn = world.get("tension", 30)
    pacts = sum(1 for a in p["agreements"].values() if a == "pact")
    L = [f"{pe('shield1')} <b>دفاع و آمادگی ملی</b>", "━" * 20,
         sec("قدرت دفاع تو در برابر حمله - تجهیزات و پیمان‌ها اینجا حساب می‌شوند."),
         f"💪 آمادگی دفاعی: <b>{fa(ns['de'])}</b> امتیاز",
         f"🎖 بودجه دفاع: {fa(p['budget']['de'])}٪ - پیمان دفاعی: {fa(pacts)}",
         f"🌡 تنش جهانی: {fa(tn)}٪ " + ("⚔️ خطر بالاست!" if tn > 65 else "✅ آرام"),
         "━" * 20,
         "💡 مراکز آموزش و دفاعی بساز؛ پیمان ببند؛ تجهیزات بخر."]
    return "\n".join(L)

def def_kb(p):
    u = p["uid"]
    return kb([[btn(u, "✈️ تجهیزات", "equip"), btn(u, "🌍 جهان", "world")],
               [btn(u, "⚔️ وضعیت نظامی", "war")],
               [btn(u, "↩️ بازگشت", "menu"), btn(u, "🏠 خانه", "menu")]])

def log_text(p):
    ns = nat_stats(p)
    L = [f"🚚 <b>لجستیک و زیرساخت</b> {pe('anchor1')}", "━" * 20,
         sec("جاده و حمل‌ونقل: لجستیک بالا = بازار سریع‌تر و ارزان‌تر."),
         f"🛣️ ظرفیت لجستیک: {bar(ns['logi'], 100, 10)} {fa(ns['logi'])}٪",
         f"📦 ظرفیت انبار ملی: {fa(p['stockcap'])} تن",
         "━" * 20,
         "💡 راه‌آهن و مرکز لجستیک بساز؛ پروژه شبکه ریلی را کامل کن.",
         "🚛 نقل منابع بین شهرها خودکار است - جاده‌های بهتر یعنی سریع‌تر."]
    return "\n".join(L)

def log_kb(p):
    u = p["uid"]
    return kb([[btn(u, "🏗 ساخت‌وساز", "build"), btn(u, "⛏ منابع", "res")],
               [btn(u, "↩️ بازگشت", "menu"), btn(u, "🏠 خانه", "menu")]])

def tech_text(p):
    L = [f"🧠 <b>فناوری و پژوهش</b> {pe('brain')}", "━" * 20,
         sec("هر پژوهش یک اثر دائمی دارد - همیشه یکی در جریان باشد.")]
    if p["research"]:
        t = TECHS.get(p["research"]["tk"])
        if t: L.append(f"⏳ در حال تحقیق: {t['nm']} - تا {teh(p['research']['at'])}")
        else: p["research"] = None
    if not p.get("research"): L.append("پژوهش فعالی نیست.")
    done = [TECHS[k]["nm"] for k in p["research_done"] if k in TECHS]
    L.append(f"✅ بومی‌شده: {fa(len(done))} فناوری")
    if done: L.append("، ".join(done[:6]))
    return "\n".join(L)

def tech_kb(p):
    rows = []
    items = [(k, t) for k, t in TECHS.items() if k not in p["research_done"]
             and (not t["need"] or t["need"] in p["research_done"])]
    for k, t in items[:5]:
        act = " ✅ در حال" if p["research"] and p["research"]["tk"] == k else ""
        rows.append([btn(p["uid"], f"{t['nm']} - {fm(t['cost'])}{act}", "tech:" + k)])
    rows.append([btn(p["uid"], "🔄 بروزرسانی", "tech"), btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)

def prj_text(p):
    L = [f"{pe('crown')} <b>توسعه - پروژه‌های ملی</b>", "━" * 20,
         sec("پروژه‌های بزرگ چندمرحله‌ای - هر مرحله جایزه دائمی می‌دهد.")]
    for k, pr in PROJECTS.items():
        st = p["projects"].get(k, {}).get("s", 0)
        act = p["projects"].get(k, {}).get("at")
        tail = ""
        if act:
            if act <= time.time(): tail = " - ✅ آماده تحویل!"
            else: tail = f" - ⏳ تا {teh(act)}"
        L.append(f"{pr['ic']} <b>{pr['nm']}</b> - مرحله {fa(st)}/۳{tail}")
        L.append(f"   🎯 اثر نهایی: {pr['fx']}")
    return "\n".join(L)

def prj_kb(p):
    rows = []
    for k, pr in PROJECTS.items():
        st = p["projects"].get(k, {}).get("s", 0)
        if st >= 3: continue
        cost = pr["st"][st]
        rows.append([btn(p["uid"], f"{pr['ic']} {pr['nm']} مرحله {fa(st + 1)} - {fm(cost)}", "prj:" + k)])
    rows.append([btn(p["uid"], "🔄 بروزرسانی", "prj"), btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)

def mkt_text(p):
    L = [f"{pe('cart')} <b>بازار جهانی کالا</b> - قیمت‌ها زنده‌اند", "━" * 20,
         sec("ارزان بخر، گران بفروش - قراردادها با تأخیر واقعی تحویل می‌شوند.")]
    for k, nm, base in COMMS:
        pr = world["market"][k]
        trend = "🟢" if pr >= base else "🔴"
        have = int(round(p["stock"].get(k, 0)))
        L.append(f"{nm}: {fm(pr)} هر تن {trend}")
        L.append(f"   موجودی انبار: {fa(have)} تن")
    cg = p.get("cargos", [])
    L += ["━" * 20,
          f"📦 ظرفیت انبار: {fa(int(round(sum(p['stock'].values()))))}/{fa(p['stockcap'])} تن" + (f" - 🚚 در راه: {fa(len(cg))} محموله" if cg else ""),
          "🛢 نفت: صادرات قراردادی (+۸٪ به قیمت لحظه تحویل) - پالایش به انرژی/استراتژیک (پالایشگاه لازم) - سوخت عملیات جنگی",
          "خرید = قرارداد و تحویل چند دقیقه‌ای - فروش فوری به قیمت نمایشی"]
    return "\n".join(L)

def mkt_kb(p):
    rows = []
    for k, nm, _ in COMMS:
        rows.append([btn(p["uid"], f"🛒 خرید ۱۰ {nm}", "mbuy:" + k), btn(p["uid"], f"💰 فروش ۱۰ {nm}", "msell:" + k)])
    rows.append([btn(p["uid"], "🚢 صادرات ۲۰ تن نفت", "exn"), btn(p["uid"], "🏭 پالایش ۱۰ تن", "rfn")])
    rows.append([btn(p["uid"], "🔄 نوسان‌گیری", "mkt"), btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)

def news_text():
    L = [f"{pe('newspaper')} <b>اخبار جهان</b> {pe('antenna1')}", "━" * 20,
         sec("هر اتفاق واقعی همین دنیا اینجا اعلام می‌شود.")]
    for n in NEWS[-10:][::-1]:
        L.append(f"🗓 {n['t'].split()[1]} - {n['x']}")
    if not NEWS: L.append("خبری نیست - جهان آرام است.")
    return "\n".join(L)

def crisis_text(p):
    L = [f"{pe('scream')} <b>مدیریت بحران</b>", "━" * 20,
         sec("بحران مهارنشده خسارت می‌زند - سریع تصمیم بگیر.")]
    if not p["crises"]: L.append("بحران فعالی نداریم ✅")
    for c in p["crises"]:
        L.append(f"{c['nm']} در {REGIONS[c['rg']]['nm']}")
        L.append(f"   💳 هزینه مهار: {fm(c['cost'])} - ⏳ مهلت تا {teh(c['dl'])}")
    return "\n".join(L)

def crisis_kb(p):
    rows = []
    for i, c in enumerate(p["crises"][:4]):
        rows.append([btn(p["uid"], f"🧯 مهار {c['nm']} ({fm(c['cost'])})", f"crs:{i}")])
    rows.append([btn(p["uid"], "🔄 بروزرسانی", "crisis"), btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)

def dec_text(p):
    d = p.get("decision")
    if not d:
        return "\n".join([f"🗳️ <b>تصمیم ملی</b> {pe('vote')}", "━" * 20,
                          "فعلاً تصمیمی در دستور نیست.",
                          "تصمیم‌ها هر چند ساعت یک بار به میز می‌آیند."])
    return "\n".join(["🗳️ <b>تصمیم ملی</b>", "━" * 20, f"❓ {d['q']}", "━" * 20,
                      "هوشمندانه انتخاب کن - پیامد واقعی دارد:"])

def dec_kb(p):
    d = p.get("decision")
    if not d: return kb([[btn(p["uid"], "🏠 خانه", "menu")]])
    rows = [[btn(p["uid"], a[0], "dec:" + a[1]) for a in d["a"][:2]]]
    if len(d["a"]) > 2: rows.append([btn(p["uid"], d["a"][2][0], "dec:" + d["a"][2][1])])
    rows.append([btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)

def rank_text(p):
    # رتبه = جمع قدرت اقتصادی + دفاعی + توسعهٔ واقعی
    def pscore(pl):
        ns, inc, net = dstat(pl)
        rels = sorted([crel(pl, ck) for ck in world["countries"]], reverse=True)[:5]
        return (pl["treasury"] + inc * 10 + ns["de"] * 2 + ns["prod"] * 3
                + sum(r["dev"] for r in pl["regions"].values()) + sum(rels) * 1.5
                + len(pl["agreements"]) * 200 + sum(v.get("s", 0) for v in pl["projects"].values()) * 250)
    pn = f"{p['name']}" + (f" - {REGIONS[p['city']]['nm']}" if p.get("city") else " - کل ایران")
    rows = [(pn, pscore(p))]
    for uid2, wp2 in (worlds.get(p.get("gid") or "0", {}).get("pdata") or {}).items():
        if uid2 != p["uid"]:
            pn2 = f"{wp2.get('name')}" + (f" - {REGIONS.get(wp2.get('city'), {}).get('nm', '؟')}" if wp2.get("city") else " - کل ایران")
            rows.append((pn2, pscore(wp2)))
    for ck, c in world["countries"].items():
        rows.append((f"{c['fl']} {c['nm']}", c["econ"] * 12 + c["ind"] * 8 + c["de"] * 5 + c["st"] * 4))
    rows.sort(key=lambda x: -x[1])
    L = [f"{pe('cup')} <b>رتبه‌بندی جهانی</b>", "━" * 20]
    myrank = next(i for i, (nm, sc) in enumerate(rows, 1) if nm == pn)
    for i, (nm, sc) in enumerate(rows[:12], 1):
        mark = " ◀️ تو" if nm == pn else ""
        L.append(f"{fa(i)}. {nm} - {fnum(sc)}{mark}")
    L += ["━" * 20, f"جایگاه ایران: {fa(myrank)} از {fa(len(rows))}"]
    return "\n".join(L)

def rank_kb(p):
    return kb([[btn(p["uid"], "🌍 جهان", "world")], [btn(p["uid"], "🏠 خانه", "menu")]])

def titles_text(p):
    T = earned_titles(p)
    L = [f"{pe('medal1')} <b>عناوین تو</b> - فقط با عملکرد واقعی", "━" * 20]
    if not T: L.append("هنوز عنوانی نگرفتی - بساز، تجارت کن، مدافع باش!")
    for t in T: L.append(f"✅ {t}")
    return "\n".join(L)

def earned_titles(p):
    ns, inc, net = dstat(p)
    nbuild = sum(sum(r["bl"].values()) for r in p["regions"].values())
    rels = [crel(p, ck) for ck in world["countries"]]
    T = []
    if nbuild >= 25: T.append("🏆 سازنده بزرگ")
    if inc >= 800: T.append("💰 اقتصاددان برتر")
    if sum(1 for r in rels if r >= 40) >= 8: T.append("🌍 دیپلمات برتر")
    if sum(v.get("s", 0) for v in p["projects"].values()) >= 9: T.append("🏗️ معمار ایران")
    if ns["logi"] >= 75: T.append("📦 استاد لجستیک")
    if ns["de"] >= 200 and p["won_wars"] >= 1: T.append("🛡️ مدافع کشور")
    if p["treasury"] >= 50000 and inc >= 2500: T.append("🌐 قدرت جهانی")
    p["titles"] = T
    return T

TYPNM = {"air": "✈️ هوایی", "msl": "🚀 موشکی", "grd": "🪖 زمینی"}

def wforces(p):
    """قدرت پدافندی در سه محور - از تجهیزات و آمادگی"""
    cnt = {}
    for e in p["equip"]: cnt[e["cat"]] = cnt.get(e["cat"], 0) + 1
    ns = nat_stats(p)
    air = cnt.get("هواگرد", 0) * 9 + cnt.get("دفاعی", 0) * 7 + ns["de"] * 0.25 + cnt.get("شناسایی", 0) * 3
    msl = cnt.get("دفاعی", 0) * 11 + ns["de"] * 0.3 + cnt.get("شناسایی", 0) * 4
    grd = (cnt.get("زرهی", 0) + cnt.get("خودرو", 0)) * 8 + cnt.get("بالگرد", 0) * 7 + ns["de"] * 0.35 + ns["logi"] * 0.3
    return dict(air=int(air), msl=int(msl), grd=int(grd))

def radar_n(p):
    """رادار = پیش‌بینی موج حمله؛ دکل رادار بیشتر = دید بیشتر"""
    r = sum(1 for e in p["equip"] if e["cat"] == "شناسایی")
    return 3 if r >= 3 else (2 if r >= 1 else 1)

def war_check(p):
    """حمله دشمن - سه موج: هوایی، موشکی، زمینی - پدافند تاکتیکی"""
    if world.get("tension", 0) < 70 or p.get("war"): return None
    enemy = random.choice(["us", "uk", "fr"])
    c = world["countries"].get(enemy)
    if not c or crel(p, enemy) > -5: return None
    target = p.get("city") or (my_regions(p) or ["thr"])[0]
    base = 10 + int(c["de"] * 0.35)
    waves = [dict(typ=random.choice(["air", "msl", "grd"]), pow=base + i * 10) for i in range(3)]
    p["war"] = dict(enemy=enemy, target=target, stage=0, waves=waves,
                    revealed=radar_n(p), repelled=0, log=[])
    return p["war"]

def war_text(p):
    w = p.get("war")
    if not w:
        return "\n".join([f"{pe('swords')} <b>وضعیت نظامی</b>", "━" * 20,
                          "درگیری فعالی نیست - آماده باش.",
                          "تنش جهانی بالای ۷۰٪ ممکن است حمله شروع شود."])
    c = world["countries"][w["enemy"]]
    f = wforces(p)
    rv = REGIONS[w["target"]]
    L = [f"{pe('swords')} <b>نبرد دفاعی - موج {fa(w['stage'] + 1)}/۳</b>", "━" * 20,
         f"{c['fl']} {c['nm']} به <b>{rv['nm']}</b> حمله می‌کند.",
         "━" * 20,
         "📡 شناسایی رادار:"]
    for i, wv in enumerate(w["waves"]):
        if i < w["revealed"]:
            mark = "◀️ موج فعلی" if i == w["stage"] else ""
            L.append(f"موج {fa(i + 1)}: {TYPNM[wv['typ']]} (قدرت {fa(wv['pow'])}) {mark}")
        else:
            L.append(f"موج {fa(i + 1)}: ❓ نامشخص {'' if i != w['stage'] else '◀️'}")
    L += ["━" * 20,
          f"💪 پدافند تو: ✈️ {fa(f['air'])} | 🚀 {fa(f['msl'])} | 🪖 {fa(f['grd'])}",
          "━" * 20]
    if w["log"]:
        L += ["📋 گزارش:"]
        L += ["- " + x for x in w["log"]]
        L.append("━" * 20)
    L.append("💡 پدافند درست مقابل حمله، ۲-۸ برابر مؤثرتر است.")
    L.append("💡 تجهیزات بخر تا قدرت پدافند بالا برود.")
    return "\n".join(L)

def war_kb(p):
    w = p.get("war")
    if not w or w["stage"] >= 3:
        return kb([[btn(p["uid"], "🏠 خانه", "menu")]])
    return kb([[btn(p["uid"], "✈️ پدافند هوایی", "wd:air")],
               [btn(p["uid"], "🚀 پدافند موشکی", "wd:msl")],
               [btn(p["uid"], "🪖 خط دفاع زمینی", "wd:grd")],
               [btn(p["uid"], "🔄 وضعیت نبرد", "war")]])

def war_deploy(p, typ):
    """یک موج را با پدافند انتخابی پاسخ بده - کاملاً تاکتیکی و بدون شانس"""
    w = p.get("war")
    if not w or w["stage"] >= 3: return war_text(p)
    wave = w["waves"][w["stage"]]
    f = wforces(p)
    eff = int(f[typ] * (1.4 if typ == wave["typ"] else 0.5))
    if eff >= wave["pow"]:
        w["repelled"] += 1
        w["log"].append(f"✅ موج {fa(w['stage'] + 1)}: {TYPNM[typ]} جلوی {TYPNM[wave['typ']]} را گرفت - دفع شد")
    else:
        dmg = max(1, min(8, (wave["pow"] - eff) // 25))
        _dm = int(round(dmg * 150))
        p["treasury"] = max(0, int(p.get("treasury", 0)) - _dm)
        _mlog(p, -_dm, "خسارت جنگ")
        r = p["regions"][w["target"]]
        r["dev"] = max(10, r["dev"] - dmg)
        r["sat"] = max(5, r["sat"] - dmg)
        w["log"].append(f"❌ موج {fa(w['stage'] + 1)}: {TYPNM[typ]} جواب نداد - خسارت {fa(dmg)} (خزانه −{fm(dmg * 150)})")
    w["stage"] += 1
    if w["stage"] < 3:
        return war_text(p)
    win = w["repelled"] >= 2
    c = world["countries"][w["enemy"]]
    city = REGIONS[w["target"]]["nm"]
    world["tension"] = max(15, world["tension"] - 15)
    p["war"] = None
    if win:
        p["won_wars"] += 1; p["sat"] = min(100, p["sat"] + 6); mearn(p, 1200, "کمک‌هزینه پیروزی"); addxp(p, 50)
        news(f"⚔️ پدافند {city} در برابر {c['nm']} پیروز شد - تنش کم شد")
        return "\n".join(["🏆 <b>دفاع پیروز شد!</b>", "━" * 20,
                          f"{fa(w['repelled'])} از ۳ موج دفع شد.",
                          f"😊 روحیه ملی +۶ - 💳 کمک هزینه: {fsm(1200)} - ⭐️ +۵۰ XP",
                          "━" * 20,
                          "💡 تاکتیک درست + تجهیزات = پیروزی قطعی"])
    p["sat"] = max(5, p["sat"] - 5); addxp(p, 5)
    news(f"🛡 دفاع {city} در برابر {c['nm']} پرهزینه تمام شد - بازسازی ممکن است")
    return "\n".join(["🛡 <b>دفاع پرهزینه بود</b>", "━" * 20,
                      f"فقط {fa(w['repelled'])} از ۳ موج دفع شد.",
                      "شهر آسیب دید اما کاملاً بازسازی‌پذیر است.",
                      "━" * 20,
                      "💡 دفعه بعد: رادار بخر (شناسایی موج‌ها) + پدافند متناسب"])

def apply_decision(p, key):
    p["decision"] = None; p["dec_cd"] = time.time()
    if key == "industry_up":
        p["budget"]["ind"] = min(40, p["budget"]["ind"] + 5); p["budget"]["health"] = max(2, p["budget"]["health"] - 3)
        p["sat"] = max(5, p["sat"] - 2); news("🗳️ بودجه صنعت افزایش یافت - سلامت کمی فشرده شد")
        return "🏭 بودجه صنعت +۵ - تولید به‌مرور بالا می‌رود؛ رضایت کمی افت کرد."
    if key == "industry_dn":
        p["budget"]["ind"] = max(2, p["budget"]["ind"] - 5); p["budget"]["health"] = min(40, p["budget"]["health"] + 3)
        p["sat"] = min(100, p["sat"] + 2); news("🗳️ بودجه صنعت کم شد - سلامت تقویت شد")
        return "🏥 بودجه سلامت +۳ - مردم راضی‌تر؛ تولید آهسته می‌شود."
    if key == "trade_open":
        p["sanctions"] = max(0, p["sanctions"] - 1); p["sat"] = min(100, p["sat"] + 3)
        news("🗳️ ایران درهای تجاری را باز کرد")
        return "📈 تجارت باز شد - فشار تحریم کم شد؛ ریسک نوسان جهانی بیشتر."
    if key == "trade_close":
        p["sanctions"] += 1; p["stockcap"] = max(100, p["stockcap"] - 20)
        return "🔒 سیاست محتاطانه - حجم تجارت کم شد؛ اتکا به بازار داخلی بیشتر."
    if key == "work_more":
        p["prod"] = min(100, p["prod"] + 5); p["sat"] = max(5, p["sat"] - 3)
        return "🏭 شیفت‌ها بیشتر شد - تولید فوری بالا؛ رضایت افت کرد."
    if key == "work_less":
        p["sat"] = min(100, p["sat"] + 4); p["prod"] = max(10, p["prod"] - 3)
        return "😌 تولید ملایم‌تر شد - مردم راضی‌تر."
    if key == "sub_up":
        if p["treasury"] < 800: return "خزانه برای یارانه کافی نیست - تصمیم اجرا نشد."
        mpay(p, 800, "یارانه سوخت"); p["sat"] = min(100, p["sat"] + 5)
        return f"⛽ یارانه پرداخت شد - رضایت +۵؛ خزانه {fsm(-800)}."
    if key == "sub_dn":
        mearn(p, 600, "کاهش یارانه"); p["sat"] = max(5, p["sat"] - 5)
        return f"💸 یارانه کم شد - خزانه {fsm(600)}؛ نارضایتی موقت."
    if key == "fdi_yes":
        mearn(p, 1000, "سرمایه‌گذاری خارجی"); p["sanctions"] = max(0, p["sanctions"] - 1)
        news("🗳️ سرمایه‌گذاری خارجی بزرگ تصویب شد")
        return f"💵 سرمایه خارجی جذب شد - خزانه {fsm(1000)}؛ تحریم کمتر."
    if key == "fdi_no":
        p["sat"] = max(5, p["sat"] - 2)
        return "🔒 محدودسازی - اتکای داخلی بیشتر؛ رشد سرمایه‌گذاری کند."
    if key == "decent":
        p["budget"]["con"] = min(40, p["budget"]["con"] + 3); p["sat"] = min(100, p["sat"] + 3)
        news("🗳️ انتقال ادارات از تهران آغاز شد")
        return "🏗️ تمرکززدایی - عمران مناطق تقویت شد."
    if key == "newcity":
        if p["treasury"] < 1200: return "خزانه برای شهر جدید کافی نیست - تصمیم اجرا نشد."
        mpay(p, 1200, "شهر جدید"); p["budget"]["con"] = min(40, p["budget"]["con"] + 2)
        news("🗳️ طرح شهر جدید تصویب شد")
        return f"🏙 شهر جدید در نقشه - هزینه {fsm(-1200)}، آینده روشن."
    if key == "sis_focus":
        p["regions"]["sis"]["dev"] = min(100, p["regions"]["sis"]["dev"] + 10)
        p["regions"]["sis"]["sec"] = min(100, p["regions"]["sis"]["sec"] + 8)
        return "🌵 سیستان در اولویت - توسعه +۱۰ و امنیت +۸."
    if key == "hrm_focus":
        p["regions"]["hrm"]["dev"] = min(100, p["regions"]["hrm"]["dev"] + 10)
        p["regions"]["hrm"]["sec"] = min(100, p["regions"]["hrm"]["sec"] + 6)
        return "⚓️ هرمزگان در اولویت - توسعه +۱۰ و امنیت +۶."
    if key == "eco_hard":
        p["energy"] = min(100, nat_stats(p)["energy"] + 6); p["sat"] = max(5, p["sat"] - 2)
        return "⚡ صرفه‌جویی سخت - انرژی ملی +۶؛ صنایع ناراضی."
    if key == "eco_soft":
        p["sat"] = min(100, p["sat"] + 2)
        return "🎯 بسته تشویقی - فضای صنعت نرم‌تر شد."
    return "به همان صورت ماند."

OPN = {"air": "حمله هوایی", "msl": "حمله موشکی", "grd": "حمله زمینی"}
ADJ = {  # مرز مشترک مناطق - مبنای عامل «وضعیت مرزها»
 "thr": ["gil", "esf", "azb", "khr", "alz"], "gil": ["thr", "azb"],
 "azb": ["thr", "gil", "esf", "khr", "urm"], "esf": ["thr", "azb", "frs", "khz", "krn"],
 "khz": ["esf", "frs", "msd"], "frs": ["esf", "khz", "krn", "hrm", "msd"],
 "khr": ["thr", "azb", "sis", "krn"], "sis": ["khr", "krn", "hrm"],
 "krn": ["esf", "frs", "khr", "sis", "hrm"], "hrm": ["frs", "sis", "krn"],
 "urm": ["azb"], "msd": ["khz", "frs"], "alz": ["thr"],
}
MOB = {"air": 750, "msl": 600, "grd": 500}
DUR = {"air": 12, "msl": 8, "grd": 15}
FUEL = {"air": 15, "msl": 10, "grd": 12}
COMM = {"50": ("۵۰٪ - پرهیز از ریسک", 0.6), "75": ("۷۵٪ - فشار بالا", 0.8), "100": ("۱۰۰٪ - همه‌چیز", 1.0)}
SUPP = {"0": ("بدون پشتیبانی", 0, 0), "500": ("توپخانه - $500", 0.12, 500), "1500": ("پشتیبانی کامل - $1,500", 0.28, 1500)}

def atk_calc(p, typ, com, sup, route, prep, tg=None):
    """قدرت حمله - محاسبه قطعی از وضعیت واقعی بازیکن"""
    ns = nat_stats(p)
    cnt = {}
    for e in p["equip"]: cnt[e["cat"]] = cnt.get(e["cat"], 0) + 1
    if typ == "air": forces = cnt.get("هواگرد", 0) * 9 + cnt.get("شناسایی", 0) * 4
    elif typ == "msl": forces = cnt.get("دفاعی", 0) * 12 + cnt.get("شناسایی", 0) * 5 + cnt.get("موشکی", 0) * 10
    else: forces = (cnt.get("زرهی", 0) + cnt.get("خودرو", 0)) * 8 + cnt.get("بالگرد", 0) * 7
    f = []
    base = forces * COMM[com][1]
    f.append(("نیروی عملیاتی", base))
    supv = int(base * SUPP[sup][1])
    if supv: f.append((SUPP[sup][0], supv))
    lg = base * (0.7 + 0.5 * ns["logi"] / 100) * (1.1 if route == "s" else 1.0)
    f.append(("لجستیک", int(lg - base - supv)))
    tot = base + supv + (lg - base - supv)
    if prep:
        b = int(tot * 0.10); f.append(("آماده‌سازی ۱۰ دقیقه‌ای", b)); tot += b
    r = sum(1 for e in p["equip"] if e["cat"] == "شناسایی")
    if r >= 2:
        b = int(tot * 0.08); f.append(("برتری اطلاعاتی (رادار)", b)); tot += b
    if tg:
        # عامل وضعیت مرزها: حمله از مرز مشترک راحت‌تر است
        if any(a in ADJ.get(tg, []) for a in my_regions(p)):
            b = int(tot * 0.08); f.append(("بستر مرزی همسایه", b)); tot += b
        else:
            b = -int(tot * 0.12); f.append(("عملیات عمق خاک - بدون مرز مشترک", b)); tot += b
        # عامل منابع موجود: انبار عملیاتی
        res = sum(int(round(p.get("stock", {}).get(k, 0))) for k, _, _ in COMMS)
        if res >= 50:
            b = int(tot * 0.05); f.append(("پشتیبانی منابع انبار", b)); tot += b
        elif res == 0:
            b = -int(tot * 0.05); f.append(("انبار خالی - کمبود منابع", b)); tot += b
    if p.get("sanctions"):
        b = -int(tot * min(0.15, 0.03 * p["sanctions"])); f.append(("فشار تحریم", b)); tot += b
    if p.get("income_hour", 0) < 0:
        b = -int(tot * 0.10); f.append(("اقتصاد در کسری", b)); tot += b
    pc = sum(1 for a in p.get("agreements", {}).values() if a == "pact")
    if pc:
        b = int(tot * 0.06 * pc); f.append((f"پیمان دفاعی ×{fa(pc)}", b)); tot += b
    return max(0, int(tot)), f

def def_calc(d, rk, typ, neutral=False, aid=None):
    """قدرت دفاع - برتری خانه‌خانماد"""
    f = []
    if neutral:
        base = int(REGIONS[rk]["sec"] * 0.9 + 15)
        f.append(("شبه‌نظام‌های بی‌طرف", base))
        return base, f
    cnt = {}
    for e in d["equip"]: cnt[e["cat"]] = cnt.get(e["cat"], 0) + 1
    if typ == "air": ars = cnt.get("دفاعی", 0) * 10 + cnt.get("شناسایی", 0) * 3
    elif typ == "msl": ars = cnt.get("دفاعی", 0) * 13 + cnt.get("شناسایی", 0) * 4
    else: ars = (cnt.get("زرهی", 0) + cnt.get("خودرو", 0)) * 9 + cnt.get("بالگرد", 0) * 8
    home = int(ars * 0.2)
    tot = ars + home
    f.append(("تجهیزات دفاعی", ars))
    f.append(("برتری خانه‌خانماد", home))
    bl = d["regions"].get(rk, {}).get("bl", {})
    fort = (bl.get("defc", 0) * 5 + bl.get("sepah", 0) * 4 + bl.get("trn", 0) * 4) * 2
    if fort: f.append(("استحکامات شهری", fort)); tot += fort
    mb = bl.get("base", 0) * 8
    if mb: f.append(("پایگاه نظامی", mb)); tot += mb
    sec = int(d["regions"].get(rk, {}).get("sec", 50) / 2)
    f.append(("امنیت منطقه", sec)); tot += sec
    pc = sum(1 for a in d.get("agreements", {}).values() if a == "pact")
    if pc:
        b = 8 * pc; f.append((f"متحدان دفاعی ×{fa(pc)}", b)); tot += b
    if world.get("tension", 30) > 60:
        b = int(tot * 0.10); f.append(("سیاهی احضار عمومی", b)); tot += b
    if aid and d is not None and has_pact(aid, d.get("uid", "")):
        b = int(tot * 0.04); f.append(("پیمان عدم تعرض", b)); tot += b
    fc = world.get("forces", {}).get(rk)
    if fc and d is not None and fc.get("host") == d.get("uid"):
        f.append(("نیروهای متحد مستقر", fc["de"])); tot += fc["de"]
    return int(tot), f

def ops_kb(p):
    u = p["uid"]
    return kb([[btn(u, "⚔️ عملیات جدید", "ops")],
               [btn(u, "📋 گزارش‌ها", "wh"), btn(u, "🗺 نقشه", "map")],
               [btn(u, "🛡 دفاع", "war"), btn(u, "🏠 خانه", "menu")]])

def ops_text(p):
    st = world
    f = {k: fa(wforces(p)[k]) for k in ("air", "msl", "grd")}
    r = sum(1 for e in p["equip"] if e["cat"] == "شناسایی")
    mine = [rk for rk, x in st["rs"].items() if x["owner"] == p["uid"]]
    act = [o for o in st["wars"] if o["aid"] == p["uid"]]
    L = ["⚔️ <b>مرکز عملیات نظامی</b>", "━" * 20,
         sec("هدف را انتخاب کن، نیرو و سوخت بچین و اعزام بزن - گزارش زنده می‌آید."),
         f"✈️ هوایی {f['air']} | 🚀 موشکی {f['msl']} | 🪖 زمینی {f['grd']}",
         f"📡 رادار: {fa(r)} {'(شناسایی کامل)' if r >= 2 else '(برای شناسایی دشمن ≥۲)'}",
         f"🚚 لجستیک: {fa(nat_stats(p)['logi'])}٪",
         f"🏙 قلمرو تو: {' و '.join(REGIONS[rk]['nm'] for rk in mine) if mine else 'نداری!'}",
         "━" * 20]
    if act:
        for o in act:
            L.append(f"🎯 عملیات فعال: {OPN[o['typ']]} روی {REGIONS[o['rk']]['nm']} - ⏳ {fa(max(0, int((o['t1'] - time.time()) // 60)) + 1)} دقیقه")
    else:
        L.append("عملیات فعالی نداری.")
    L += ["━" * 20,
          "💡 نتیجه از تجهیزات، لجستیک، پشتیبانی، اطلاعات،",
          "   پیمان‌ها و اقتصاد حساب می‌شود - نه شانس.",
          "💡 هرچه قوی‌تر حمله کنی، خسارت و هزینه بیشتر."]
    return "\n".join(L)

def wiz_ops(p):
    w = p.get("wiz") or {}
    return w

def wtg_text(p):
    st = world
    L = ["🎯 <b>انتخاب هدف</b>", "━" * 20,
         "شهرهای بی‌طرف ضعیف‌اند؛ شهر فرماندهان با پدافند کامل.", "━" * 20]
    for rk, rv in REGIONS.items():
        x = st["rs"][rk]
        if x["owner"] == p["uid"]: continue
        nm = (worlds.get(p.get("gid") or "0", {}).get("pdata", {}).get(x["owner"], {}) or {}).get("name") if x["owner"] else None
        tag = STAT[x.get("status", "neutral")] + " "
        tag += (f"فرماندار: {nm}" if nm else "بی‌طرف")
        L.append(f"{tag} - {rv['nm']} ({rv['tp']})")
    return "\n".join(L)

def wtg_kb(p):
    st = world
    rows = []
    tgts = [rk for rk in REGIONS if st["rs"][rk]["owner"] != p["uid"]]
    for i in range(0, len(tgts), 2):
        row = [btn(p["uid"], "🎯 " + REGIONS[tgts[i]]["nm"], "wt:" + tgts[i])]
        if i + 1 < len(tgts): row.append(btn(p["uid"], "🎯 " + REGIONS[tgts[i + 1]]["nm"], "wt:" + tgts[i + 1]))
        rows.append(row)
    rows.append([btn(p["uid"], "↩️ بازگشت", "ops"), btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)

def wiz_line(w):
    if not w.get("tg"): return "۱. هدف: ❓"
    z = [f"۱. هدف: {REGIONS[w['tg']]['nm']}"]
    z.append(f"۲. نوع: {OPN[w['typ']] if w.get('typ') else '❓'}")
    z.append(f"۳. نیرو: {COMM[w['com']][0] if w.get('com') else '❓'}")
    z.append(f"۴. پشتیبانی: {SUPP[w['sup']][0] if w.get('sup') else '❓'}")
    z.append(f"۵. مسیر: {'امن (+$400)' if w.get('route') == 's' else ('مستقیم' if w.get('route') else '❓')}")
    z.append(f"۶. زمان: {'آماده‌سازی +۱۰ دقیقه' if w.get('prep') else ('فوری' if w.get('prep') is not None else '❓')}")
    return "\n".join(z)

def wiz_kb(p, need):
    u = p["uid"]
    rows = []
    if need == "typ":
        rows += [[btn(u, "✈️ هوایی", "wo:air"), btn(u, "🚀 موشکی", "wo:msl")],
                 [btn(u, "🪖 زمینی", "wo:grd")]]
    elif need == "com":
        rows += [[btn(u, "۵۰٪", "wc:50"), btn(u, "۷۵٪", "wc:75"), btn(u, "۱۰۰٪", "wc:100")]]
    elif need == "sup":
        rows += [[btn(u, "بدون", "wp:0"), btn(u, "توپخانه $500", "wp:500")],
                 [btn(u, "کامل $1,500", "wp:1500")]]
    elif need == "route":
        rows += [[btn(u, "🛣 مستقیم", "wr:d"), btn(u, "🛡 مسیر امن +$400", "wr:s")]]
    elif need == "prep":
        rows += [[btn(u, "⚡ فوری", "wn:n"), btn(u, "⏳ آماده‌سازی +۱۰ دقیقه", "wn:p")]]
    rows.append([btn(u, "❌ لغو عملیات", "wcan")])
    return kb(rows)

def wiz_text(p, need):
    w = wiz_ops(p)
    hint = {"typ": "نوع عملیات را انتخاب کن - هر نوع با پدافند متناسب دشمن سنجیده می‌شود.",
            "com": "چقدر از توان نظامی‌ات را درگیر می‌کنی؟ درگیری کمتر = قدرت کمتر و ریسک کمتر.",
            "sup": "پشتیبانی آتش، قدرت حمله را درصد مشخصی بالا می‌برد - هزینه دارد.",
            "route": "مسیر امن لجستیک را ۱۰٪ قوی‌تر می‌کند ولی هزینه دارد.",
            "prep": "آماده‌سازی ۱۰ دقیقه‌ای، قدرت حمله را ۱۰٪ بالا می‌برد."}
    return "\n".join(["⚔️ <b>طراحی عملیات</b>", "━" * 20, wiz_line(w), "━" * 20, hint[need]])

def wrev_text(p):
    """بررسی نهایی - پیش‌بینی از اطلاعات واقعی"""
    w = wiz_ops(p)
    st = world
    did = st["rs"][w["tg"]]["owner"]
    d = worlds[p["gid"]]["pdata"].get(did) if did else None
    atk, af = atk_calc(p, w["typ"], w["com"], w["sup"], w["route"], w["prep"], tg=w["tg"])
    r = sum(1 for e in p["equip"] if e["cat"] == "شناسایی")
    L = ["📋 <b>بررسی نهایی عملیات</b>", "━" * 20,
         wiz_line(w),
         f"📍 منطقه: {REGIONS[w['tg']]['nm']}",
         f"⏱ مدت: {fa(DUR[w['typ']] + (10 if w['prep'] else 0))} دقیقه",
         f"💳 هزینه اعزام: {fm(MOB[w['typ']] + SUPP[w['sup']][2] + (400 if w['route'] == 's' else 0))}",
         f"⛽ سوخت جنگی: {fa(FUEL[w['typ']])} تن نفت - انبار: {fa(int(round(p['stock'].get('oil', 0))))}",
         "━" * 20,
         f"💪 قدرت حمله تو: <b>{fa(atk)}</b>"]
    if d is None:
        dfn, _ = def_calc(None, w["tg"], w["typ"], neutral=True)
        L.append(f"🛡 دفاع هدف (بی‌طرف): <b>{fa(dfn)}</b>")
        est = "برتری تو" if atk >= dfn * 1.3 else ("برابری" if atk >= dfn * 0.95 else "ضعیف‌تری")
    elif r >= 2:
        dfn, _ = def_calc(d, w["tg"], w["typ"], aid=p["uid"])
        L.append(f"🛡 دفاع دشمن (رادار کامل): <b>{fa(dfn)}</b>")
        est = "برتری تو" if atk >= dfn * 1.3 else ("برابری" if atk >= dfn * 0.95 else "ضعیف‌تری")
    else:
        dfn = None
        L.append("🛡 دفاع دشمن: ≈ نامشخص (رادار کافی نداری)")
        est = "نامشخص"
    L += [f"📊 پیش‌بینی: <b>{est}</b>",
          "━" * 20,
          "بعد از اعزام، لغو ممکن نیست.",
          "نتیجه فقط از وضعیت واقعی لحظه برخورد حساب می‌شود."]
    return "\n".join(L)

def wrev_kb(p):
    return kb([[btn(p["uid"], "✅ تأیید و اعزام", "wgo")],
               [btn(p["uid"], "❌ لغو", "wcan")]])

def map_text(p):
    st = world
    L = ["🗺 <b>نقشه کنترل مناطق</b>", "━" * 20,
         sec("رنگ هر شهر = مالکش - هدف بعدی‌ات را از همین نقشه انتخاب کن.")]
    for rk, rv in REGIONS.items():
        x = st["rs"][rk]
        nm = (worlds.get(p.get("gid") or "0", {}).get("pdata", {}).get(x["owner"], {}) or {}).get("name") if x["owner"] else None
        own = x.get("owner")
        if own is None: icon, lbl = "⚪", "بی‌طرف"
        elif own == p["uid"]: icon, lbl = "🟢", "⭐️ تحت کنترل تو"
        elif x.get("status") == "yellow": icon, lbl = "🟡", "مورد مناقشه - " + (nm or "؟")
        else: icon, lbl = "🔴", "دشمن: " + (nm or "؟")
        pk2 = x.get("party") or rv["party"]
        line = f"{icon} {rv['nm']} {PARTY_IC.get(pk2, '')} - {lbl}"
        L.append(line)
    L += ["━" * 20, "🟢 تحت کنترل تو - 🟡 مناقشه - 🔴 دشمن - ⚪ بی‌طرف - 🕌 جمهوری اسلامی - 👑 پهلوی",
          f"🗓 فصل {fa(st.get('season', 1))} - مرزها در دیتابیس ثبت می‌شوند"]
    return "\n".join(L)

def wh_text(p):
    st = world
    L = ["📋 <b>تاریخچه عملیات‌ها</b>", "━" * 20,
         sec("گزارش همهٔ عملیات‌های گذشته تو - درس بگیر و تکرار نکن.")]
    items = [x for x in st["wlog"] if True][-8:][::-1]
    if not items: L.append("هنوز عملیاتی ثبت نشده.")
    for x in items:
        L.append(f"⚔️ {x['what']} - {REGIONS.get(x['where'], {}).get('nm', '؟')}")
        L.append(f"   👤 {x['who']} - 🕒 {x['when']}")
        L.append(f"   📊 {x['status']} - {x['result']}")
    return "\n".join(L)

def wlds_text(p):
    uid = p["uid"]
    pr = profiles.get(uid) or {}
    L = [f"{pe('globe')} <b>دنیاهای من</b>", "━" * 20,
         "هر گروه یک دنیای کاملاً مستقل دارد.",
         "پروفایل، XP و عناوین بین دنیاها مشترک است؛",
         "پول، شهرها، ارتش و تاریخچه هر دنیا جداست.",
         "━" * 20]
    n = 0
    for gid, w in worlds.items():
        if uid not in w["pdata"]: continue
        n += 1
        wp = w["pdata"][uid]
        mark = "⭐️" if gid == pr.get("sel") else "🌎"
        ident = IDENTS.get(wp.get("ident") or "", {}).get("short", "بدون مسیر")
        L.append(f"{mark} <b>{esc(w.get('title') or 'دنیا')}</b>")
        L.append(f"   💰 {fm(wp.get('treasury', 0))} - 🏛 {ident} - 🗓 فصل {fa(w['st'].get('season', 1))}")
    if n <= 1:
        L.append("💡 برای دنیای جدید، ربات را به یک گروه اضافه کن و /start بزن.")
    L.append("━" * 20)
    L.append(f"🎖 سطح تو: {fa(pr.get('lvl', 1))} - ⭐️ XP: {fa(pr.get('xp', 0))}")
    return "\n".join(L)

def wlds_kb(p):
    uid = p["uid"]
    pr = profiles.get(uid) or {}
    rows = []
    for gid, w in worlds.items():
        if uid not in w["pdata"]: continue
        rows.append([btn(uid, ("⭐️ " if gid == pr.get("sel") else "🎮 ") + (w.get("title") or "دنیا"), "wsel:" + gid)])
    rows.append([btn(uid, "🏠 خانه", "menu")])
    return kb(rows)

def asz_text(p):
    if not p.get("regions"):
        return "\n".join(["🧠 <b>دستیار تحلیل‌گر</b>", "━" * 20,
                          "⚠️ هنوز داده کافی برای تحلیل وجود ندارد.",
                          "اول شهر خودت را بساز - بعد تحلیل واقعی می‌دهم.",
                          "(تحلیل فقط از دیتای ثبت‌شده همین World - بدون حدس)"])
    ns, inc, net = dstat(p)
    sug = []
    if ns["energy"] < 45: sug.append((3, f"انرژی {fa(ns['energy'])}٪ پایین است - درآمد شهرها می‌سوزد.", "build"))
    if ns["prod"] < 45: sug.append((2, "تولید کم است - کارخانه و پروژه صنعتی.", "ind"))
    if net < 0: sug.append((3, "درآمد خالص منفی است - بودجه یا بازار.", "eco"))
    myr = my_regions(p)
    secmin = min([p["regions"][rk]["sec"] for rk in myr], default=100)
    if secmin < 45: sug.append((2, f"امنیت شهر تو {fa(secmin)}٪ - ریسک بحران و سقوط.", "de"))
    eqc = sum(1 for e in p["equip"] if e["cat"] in ("دفاعی", "شناسایی"))
    if eqc < 2: sug.append((2, "پدافند و رادار کم - رادار موج‌ها را لو می‌دهد.", "equip"))
    if sum(int(round(p["stock"].get(k, 0))) for k, _, _ in COMMS) > p["stockcap"] * 0.8:
        sug.append((1, "انبار پر است - بفروش تا پول شود.", "mkt"))
    if p["crises"]: sug.append((3, f"{fa(len(p['crises']))} بحران فعال - مهلت محدود!", "crisis"))
    if p["treasury"] < 500: sug.append((2, "خزانه بحرانی - منابع را بفروش.", "mkt"))
    if not sug: sug.append((1, "وضعیت پایدار است - برای رشد: پروژه ملی و فناوری.", "prj"))
    sug.sort(key=lambda x: -x[0])
    pr = profiles.get(p["uid"]) or {}
    L = ["🧠 <b>دستیار تحلیل‌گر</b>", "━" * 20,
         sec("تحلیل خودکار از داده‌های واقعی خودت - توصیهٔ بعدی را اینجا بگیر."),
         f"🎖 سطح {fa(pr.get('lvl', 1))} - ⭐️ XP {fa(pr.get('xp', 0))}",
         "تحلیل فقط از داده‌های واقعی همین World.",
         "هیچ اقدامی بدون تأیید تو انجام نمی‌شود.",
         "━" * 20]
    for i, (sv, msg, _) in enumerate(sug[:3], 1):
        L.append(f"{fa(i)}. {msg}")
    return "\n".join(L)

def asz_kb(p):
    ns, inc, net = dstat(p)
    myr = my_regions(p)
    secmin = min([p["regions"][rk]["sec"] for rk in myr], default=100)
    eqc = sum(1 for e in p["equip"] if e["cat"] in ("دفاعی", "شناسایی"))
    res = sum(int(round(p["stock"].get(k, 0))) for k, _, _ in COMMS)
    rows = []
    if ns["energy"] < 45 or ns["prod"] < 45: rows.append([btn(p["uid"], "🏗 ساخت‌وساز", "build")])
    if net < 0 or res > p["stockcap"] * 0.8: rows.append([btn(p["uid"], "📈 بازار", "mkt"), btn(p["uid"], "💰 اقتصاد", "eco")])
    if secmin < 45 or eqc < 2: rows.append([btn(p["uid"], "🛡 دفاع", "de"), btn(p["uid"], "✈️ تجهیزات", "equip")])
    if p["crises"]: rows.append([btn(p["uid"], "⚠️ بحران‌ها", "crisis")])
    rows.append([btn(p["uid"], "🔄 تحلیل دوباره", "asz"), btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)

def cmdr_text(p):
    st = world
    pr = profiles.get(p["uid"]) or {}
    L = ["🤝 <b>فرماندهان این World</b>", "━" * 20,
         sec("از اینجا پیمان و اتحاد ببند - حداکثر ۳ اتحاد نظامی برای هر فرمانده.")]
    others = [(u2, w2) for u2, w2 in (worlds.get(p.get("gid") or "0", {}).get("pdata") or {}).items() if u2 != p["uid"]]
    if not others: L.append("فعلاً فرمانده دیگری نیست - گروه را دعوت کن!")
    for u2, w2 in others:
        city = REGIONS.get(w2.get("city"), {}).get("nm", "؟")
        kd2 = (st["pacts"].get(pk(p["uid"], u2)) or {}).get("kind", "ndq")
        ph = ("🎖 اتحاد نظامی" if kd2 == "all" else "🤝 پیمان داری") if has_pact(p["uid"], u2) else ("⏳ درخواست فرستادی" if st["preq"].get(u2) == p["uid"] else "⚔️ بی‌پیمان")
        L.append(f"👤 {w2.get('name', '؟')} - 🏙 {city} - {ph}")
    incv = st["preq"].get(p["uid"])
    inc = incv.get("frm") if isinstance(incv, dict) else incv
    if inc in [u2 for u2, _ in others]:
        nm = (worlds.get(p.get("gid") or "0", {}).get("pdata", {}).get(inc) or {}).get("name", "؟")
        kn = "اتحاد نظامی" if (isinstance(incv, dict) and incv.get("kind") == "all") else "پیمان"
        L += ["━" * 20, f"📩 درخواست {kn} از {nm}"]
    col0 = st.get("col", {})
    if p["uid"] in col0:
        c2 = col0[p["uid"]]
        mn2 = (worlds.get(p.get("gid") or "0", {}).get("pdata") or {}).get(c2.get("master"), {}).get("name", "؟")
        L.append(("⛓ در بردگی " + mn2 + " - باج ۲۵٪ - دیپلماسی ممنوع") if c2.get("kind") == "slv"
                 else ("👑 مستعمره " + mn2 + " - باج ۱۵٪ درآمد - آزادی: بازپس‌گیری پایتخت"))
    myc2 = [v for v, c2 in col0.items() if c2.get("master") == p["uid"]]
    if myc2:
        nm3 = [(worlds.get(p.get("gid") or "0", {}).get("pdata") or {}).get(v, {}).get("name", "؟") for v in myc2]
        L.append("👑 مستعمره‌های تو: " + " - ".join(nm3))
    L += ["━" * 20,
          sec("هر فرمانده حداکثر ۳ اتحاد نظامی همزمان می‌تواند داشته باشد."),
          "پیمان = حمله ممنوع دوطرفه + دفاع +۴٪",
          "اتحاد نظامی = پیمان + استقرار نیروی متحد (سطح ۳ + پایگاه نظامی)",
          f"لغو پیمان: {fm(1000)} + ثبت در حسابرسی",
          "📜 تجارت: قرارداد مستقیم کالا - هر دو طرف سود"]
    if (pr.get("lvl", 1) or 1) < 2:
        L.append(f"🔒 پیمان از سطح ۲ (XP {fa(600)}) - تو سطح {fa(pr.get('lvl', 1))}")
    return "\n".join(L)

def cmdr_kb(p):
    st = world
    pr = profiles.get(p["uid"]) or {}
    rows = []
    others = [(u2, w2) for u2, w2 in (worlds.get(p.get("gid") or "0", {}).get("pdata") or {}).items() if u2 != p["uid"]]
    incv = st["preq"].get(p["uid"])
    inc = incv.get("frm") if isinstance(incv, dict) else incv
    if inc in [u2 for u2, _ in others] and pr.get("lvl", 1) >= 2:
        kn = "اتحاد" if (isinstance(incv, dict) and incv.get("kind") == "all") else "پیمان"
        rows.append([btn(p["uid"], f"✅ قبول {kn}", "pac:yes:" + str(inc)), btn(p["uid"], "❌ رد", "pac:no:" + str(inc))])
    for u2, w2 in others:
        kd2 = (st["pacts"].get(pk(p["uid"], u2)) or {}).get("kind", "ndq")
        myb = p["regions"].get(p.get("city") or "", {}).get("bl", {}).get("base", 0)
        if has_pact(p["uid"], u2):
            rows.append([btn(p["uid"], f"💔 لغو پیمان با {w2.get('name', '؟')} - $1,000", "pac:brk:" + u2)])
            rows.append([btn(p["uid"], f"🎁 اهدای سلاح به {w2.get('name', '؟')}", "eqg:" + u2),
                         btn(p["uid"], f"💵 فروش سلاح به {w2.get('name', '؟')}", "eqs:" + u2)])
            if kd2 != "all" and (pr.get("lvl", 1) or 1) >= 3 and myb >= 1 and cd_left(p, "pac" + u2) == 0:
                rows.append([btn(p["uid"], f"🎖 ارتقا به اتحاد نظامی با {w2.get('name', '؟')} - $2,500", "pac:all:" + u2)])
            if kd2 == "all" and myb >= 1:
                fc0 = world["forces"].get(p.get("city") or "")
                if fc0 and fc0.get("frm") == u2:
                    rows.append([btn(p["uid"], f"↩️ بازگشت نیروهای {w2.get('name', '؟')}", "pac:wdw:" + u2)])
                elif not fc0 and cd_left(p, "frc" + u2) == 0:
                    rows.append([btn(p["uid"], f"🪖 استقرار نیروهای {w2.get('name', '؟')} در شهر من - $500", "pac:frc:" + u2)])
        elif st["preq"].get(u2) != p["uid"] and pr.get("lvl", 1) >= 2 and cd_left(p, "pac" + u2) == 0:
            rows.append([btn(p["uid"], f"🤝 پیشنهاد پیمان به {w2.get('name', '؟')}", "pac:ask:" + u2)])
    for v4, c4 in st.get("col", {}).items():
        if c4.get("master") != p["uid"]:
            continue
        nm4 = (worlds.get(p.get("gid") or "0", {}).get("pdata") or {}).get(v4, {}).get("name", "؟")
        if c4.get("kind") == "col":
            rows.append([btn(p["uid"], f"⛓ بردگی کردن {nm4} - $1,500", "csl:" + v4),
                         btn(p["uid"], f"🕊 آزادی {nm4}", "cfree:" + v4)])
        else:
            rows.append([btn(p["uid"], f"🕊 آزاد کردن {nm4}", "cfree:" + v4)])
    rows.append([btn(p["uid"], "📜 تجارت", "trd")])
    rows.append([btn(p["uid"], "⚔️ عملیات", "ops"), btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)

CNAM = {k: nm for k, nm, _ in COMMS}

def trd_text(p):
    st = world
    L = ["📜 <b>قرارداد تجاری فرماندهان</b>", "━" * 20,
         sec("معاملهٔ مستقیم با بازیکنان: مناطق و کالا در ازای پول."),
         "معامله مستقیم کالا: خریدار بدون هزینه حمل و ارزان‌تر، فروشنده بیشتر از فروش بازار", "━" * 20]
    inc = st["treq"].get(p["uid"], [])
    if inc:
        L.append("📩 پیشنهادهای رسیده:")
        for o in inc[:4]:
            lm = max(0, int((o["exp"] - time.time()) // 60))
            L.append(f"▪ {CNAM.get(o['k'], o['k'])} ×{fa(o['qty'])} - {fm(o['price'])} از {o['fn']} - ⏳ {fa(lm)} دقیقه")
    out = [o for lst in st["treq"].values() for o in lst if o["frm"] == p["uid"]]
    if out:
        L.append("📤 پیشنهادهای فرستاده (کالا در امانت):")
        for o in out[:4]:
            L.append(f"▪ {CNAM.get(o['k'], o['k'])} ×{fa(o['qty'])} - {fm(o['price'])} → {o['tn']}")
    good = [f"{nm} {fa(int(round(p['stock'].get(k, 0))))}" for k, nm, _ in COMMS if int(round(p["stock"].get(k, 0))) >= 10]
    L += ["━" * 20, "📦 انبار: " + (" - ".join(good) if good else "برای پیشنهاد، حداقل ۱۰ تن از یک کالا لازم است")]
    return "\n".join(L)

def trd_kb(p):
    st = world
    pr = profiles.get(p["uid"]) or {}
    rows = []
    for o in st["treq"].get(p["uid"], [])[:2]:
        nm2 = CNAM.get(o["k"], o["k"]).split(" ", 1)[-1]
        rows.append([btn(p["uid"], f"✅ قبول {nm2} از {o['fn']}", "tra:yes:" + o["oid"]),
                     btn(p["uid"], "❌", "tra:no:" + o["oid"])])
    for o in [x for lst in st["treq"].values() for x in lst if x["frm"] == p["uid"]][:2]:
        nm2 = CNAM.get(o["k"], o["k"]).split(" ", 1)[-1]
        rows.append([btn(p["uid"], f"↩️ لغو {nm2} به {o['tn']}", "trc:" + o["oid"])])
    if (pr.get("lvl", 1) or 1) >= 2:
        others = (worlds.get(p.get("gid") or "0", {}).get("pdata") or {})
        for u2, w2 in others.items():
            if u2 == p["uid"]: continue
            mine = [x for x in st["treq"].get(u2, []) if x["frm"] == p["uid"]]
            if not mine and cd_left(p, "trd" + u2) == 0:
                rows.append([btn(p["uid"], f"📜 پیشنهاد به {w2.get('name', '؟')}", "trd2:" + u2)])
    else:
        rows.append([btn(p["uid"], f"🔒 تجارت از سطح ۲ (XP {fa(600)})", "cmdr")])
    rows.append([btn(p["uid"], "🤝 فرماندهان", "cmdr"), btn(p["uid"], "🏠 خانه", "menu")])
    return kb(rows)

def trd2_text(p, tn):
    L = [f"📜 <b>پیشنهاد ۱۰ تن به {esc(tn)}</b>", "━" * 20,
         "قیمت از بازار همین World + سود دوطرفه",
         f"📦 ظرفیت انبار: {fa(int(round(sum(p['stock'].values()))))}/{fa(p['stockcap'])} تن",
         "کالا تا پاسخ (حداکثر ۳۰ دقیقه) در امانت می‌ماند.", "━" * 20,
         "کدام کالا؟"]
    return "\n".join(L)

def trd2_kb(p, tgt):
    rows = []
    cur = []
    for k, nm, _ in COMMS:
        if int(round(p["stock"].get(k, 0))) >= 10:
            cur.append(btn(p["uid"], nm, f"trk:{tgt}:{k}"))
            if len(cur) == 2: rows.append(cur); cur = []
    if cur: rows.append(cur)
    if not rows: rows.append([btn(p["uid"], "❌ هیچ کالایی ۱۰ تن نیست", "trd")])
    rows.append([btn(p["uid"], "↩️ بازگشت", "trd")])
    return kb(rows)

def audit_text(p):
    st = world
    L = ["🔍 <b>حسابرسی World</b>", "━" * 20,
         sec("دفتر رسمی دنیا + گردش خزانه تو - همه‌چیز شفاف و ثبت‌شده."),
         f"🗓 فصل {fa(st.get('season', 1))} - ثبت واقعی دیتابیس همین دنیا", "━" * 20]
    items = st["audit"][-10:][::-1]
    if not items: L.append("ثبتی نیست.")
    for x in items:
        L.append(f"▪ {x['t']} - {x['who']}")
        L.append(f"   {x['what']}" + (f" - {x['det']}" if x.get("det") else ""))
    lg = (p.get("mlog") or [])[-8:][::-1]
    if lg:
        L += ["━" * 20, "💳 گردش خزانه تو (آخرین حرکت‌ها):"]
        for _t, _a, _w in lg:
            L.append(f"▪ {'+' if _a >= 0 else '−'}{fm(abs(_a))} - {_w}")
    return "\n".join(L)

def health_text(p):
    import resource
    up = int(time.time() - STIME)
    npl = sum(len(w.get("pdata", {})) for w in worlds.values())
    nops = sum(len(w.get("st", {}).get("wars", [])) for w in worlds.values())
    bdir = os.path.join(DATA, "backup")
    nbk = len(os.listdir(bdir)) if os.path.isdir(bdir) else 0
    L = ["💚 <b>سلامت سامانه</b>", "━" * 20,
         f"⏱ روشن: {fa(up // 3600)} ساعت و {fa((up % 3600) // 60)} دقیقه",
         f"🌍 Worldها: {fa(len(worlds))} - 👤 بازیکنان: {fa(npl)}",
         f"⚔️ عملیات فعال: {fa(nops)}",
         f"💾 آخرین ذخیره: {fa(int(time.time() - SAVE_T[0]))} ثانیه پیش",
         f"🗂 بکاپ‌ها: {fa(nbk)}",
         f"🧠 حافظه: {fa(int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024))} MB",
         f"🔄 ورودی/خروجی: {fa(_IO['r'])} خواندن - {fa(_IO['w'])} نوشتن",
         "📈 ظرفیت واقعی فقط با Load Test تأیید می‌شود."]
    return "\n".join(L)

def route(p, act, msg):
    uid = p["uid"]
    now = time.time()
    cid = (msg.get("chat") or {}).get("id") or int(uid)
    # دروازه هویت ملی - تا انتخاب نکند هیچ پنلی باز نمی‌شود
    if not p.get("ident") and not act.startswith("ident"):
        show_sub(cid, p, ident_text(p), ident_kb(p)); return
    if (p.get("gid") or "0") != "0" and not my_regions(p) and not act.startswith("ident") and not act.startswith("cset") and not act.startswith("ops") and not act.startswith("wt:") and not act.startswith("wgo") and not act.startswith("wf") and not act.startswith("wo:") and not act.startswith("wc:") and not act.startswith("wp:") and not act.startswith("wr:") and not act.startswith("wn:") and act != "wcan" and not act.startswith("map") and not act.startswith("wh") and not act.startswith("cfgm") and not act.startswith("rst") and act != "csl" and act != "cfree" and act != "wlds" and act != "help" and not act.startswith("rstp"):
        if any(world["rs"][rk]["owner"] is None for rk in REGIONS):
            show_sub(cid, p, cty_text(p), cty_kb(p)); return
        show_sub(cid, p, "همه شهرها مالک دارند - برای ورود به بازی باید عملیات نظامی انجام دهی ⚔️", ops_kb(p)); return
    c9 = world.get("col", {}).get(uid)
    if c9 and c9.get("kind") == "slv" and act.startswith(("pac:", "trk:", "trd2:")):
        show_sub(cid, p, "⛓ در بردگی هستی - دیپلماسی و تجارت مستقل ممنوع؛ پایتختت را پس بگیر و آزاد شو.", cmdr_kb(p)); return
    if act == "refresh": close_sub(cid, p); show_menu(p, cid); return
    if act == "menu": show_menu(p, cid); return
    if act.startswith("mnu:"):
        pg = int(act.split(":")[1]) if act.split(":")[1] in ("1", "2", "3", "4", "5") else 1
        show_sub(cid, p, menu_text(p), menu_kb(p, pg)); return
    if act == "help": show_sub(cid, p, help_text(), kb([[btn(uid, "🏠 خانه", "menu")]])); return
    if act == "ident": show_sub(cid, p, ident_text(p), ident_kb(p)); return
    if act.startswith("ident:pick:") or act.startswith("ident:chg:"):
        key = act.split(":")[2]
        if p.get("ident") == key:
            show_sub(cid, p, "همین مسیر فعلاً فعال است ✅", ident_kb(p)); return
        show_sub(cid, p, ident_ok_text(p, key), kb([[btn(uid, "✅ تأیید", "ident:ok:" + key)],
                                                 [btn(uid, "❌ انصراف", "ident")]])); return
    if act.startswith("ident:ok:"):
        key = act.split(":")[2]
        if p.get("ident") == key: show_sub(cid, p, "همین مسیر فعلاً فعال است ✅", ident_kb(p)); return
        if p.get("ident"):
            if p["treasury"] < 5000:
                show_sub(cid, p, f"تغییر هویت {fm(5000)} هزینه دارد - خزانه: {fm(p['treasury'])}", ident_kb(p)); return
            mpay(p, 5000, "تغییر هویت ملی"); p["sat"] = max(5, p["sat"] - 10); p["stab"] = max(5, p["stab"] - 5)
            p["incmod"] = 1.0
        ident_apply(p, key)
        news("⚑ مسیر سیاسی ایران: " + IDENTS[key]["nm"])
        aud(p, "تغییر هویت ملی", IDENTS[key]["nm"])
        if (p.get("gid") or "0") != "0" and not p.get("city"):
            show_sub(cid, p, cty_text(p), cty_kb(p)); return
        show_menu(p, cid); return
        show_sub(cid, p, cty_text(p), cty_kb(p)); return
    if act.startswith("cset:"):
        rk = act.split(":")[1]
        if rk not in REGIONS: show_sub(cid, p, "این شهر وجود ندارد.", cty_kb(p)); return
        own = owners_of(p)
        if my_regions(p): show_menu(p, cid); return
        if rk in own: show_sub(cid, p, f"این شهر قبلاً به {own[rk][2]} رسیده - یکی دیگر انتخاب کن.", cty_kb(p)); return
        if world["rs"][rk]["owner"] is None and [x for x in REGIONS if world["rs"][x]["owner"] is None].index(rk) >= max_regions():
            show_sub(cid, p, "⛔️ این منطقه خارج از سقف این World است - مالک می‌تواند سقف را بالا ببرد.", cty_kb(p)); return
        p["city"] = rk
        rs_claim(p, rk)
        pk3 = world["rs"].get(rk, {}).get("party") or REGIONS[rk]["party"]
        if p.get("ident") != pk3:
            p["ident"] = pk3
            aud(p, "هم‌سویی با حزب منطقه", REGIONS[rk]["nm"] + " → " + PARTY_NM[pk3])
        aud(p, "ادعای شهر", REGIONS[rk]["nm"])
        news(f"🏙 {p['name']} فرمانداری {REGIONS[rk]['nm']} را بر عهده گرفت ({PARTY_NM[pk3]})")
        show_menu(p, cid); return
    if act == "asz": show_sub(cid, p, asz_text(p), asz_kb(p)); return
    if act == "cmdr": show_sub(cid, p, cmdr_text(p), cmdr_kb(p)); return
    if act == "audit": show_sub(cid, p, audit_text(p), kb([[btn(uid, "⚙️ تنظیمات", "set"), btn(uid, "🏠 خانه", "menu")]])); return
    if act == "health":
        if uid != "8694290031":
            show_sub(cid, p, "💚 سلامت سامانه فقط برای مالک.", menu_kb(p)); return
        show_sub(cid, p, health_text(p), kb([[btn(uid, "🏠 خانه", "menu")]])); return
    if act.startswith("pac:"):
        pr2 = profiles.setdefault(uid, new_profile({"id": uid}))
        others = (worlds.get(p.get("gid") or "0", {}).get("pdata") or {})
        _, op2, tgt = act.split(":")
        if op2 != "brk" and pr2.get("lvl", 1) < 2:
            show_sub(cid, p, f"🔒 پیمان‌ها از سطح ۲ باز می‌شود - تو سطح {fa(pr2.get('lvl', 1))}.", cmdr_kb(p)); return
        if tgt not in others:
            show_sub(cid, p, "این فرمانده در دسترس نیست.", cmdr_kb(p)); return
        if op2 == "ask":
            if has_pact(uid, tgt): show_sub(cid, p, "پیمان دارید.", cmdr_kb(p)); return
            if world["preq"].get(tgt) == uid: show_sub(cid, p, "درخواست قبلاً رفته است.", cmdr_kb(p)); return
            world["preq"][tgt] = uid
            cd_set(p, "pac" + tgt, 3600)
            aud(p, "پیشنهاد پیمان", "به " + others[tgt].get("name", "؟"))
            try: tg("sendMessage", chat_id=int(tgt), parse_mode="HTML", text=f"📩 <b>پیشنهاد پیمان عدم تعرض</b> از {esc(p['name'])}\nدر ربات: 🤝 فرماندهان")
            except Exception: pass
            show_sub(cid, p, "✅ پیشنهاد ارسال شد - منتظر پاسخ.", cmdr_kb(p)); return
        if op2 in ("yes", "no"):
            pv = world["preq"].pop(uid, None)
            frm = pv.get("frm") if isinstance(pv, dict) else pv
            knd = (pv.get("kind", "ndq") if isinstance(pv, dict) else "ndq") or "ndq"
            if op2 == "yes" and frm in others and frm != uid:
                if knd == "all":
                    _al2 = [k2 for k2, v2 in world["pacts"].items() if isinstance(v2, dict) and v2.get("kind") == "all" and uid in k2.split("|")]
                    _al3 = [k2 for k2, v2 in world["pacts"].items() if isinstance(v2, dict) and v2.get("kind") == "all" and str(frm) in k2.split("|")]
                    if len(_al2) >= 3:
                        show_sub(cid, p, "🎖 سقف اتحاد نظامی تو پر است (۳ نفر) - اول یکی را لغو کن.", cmdr_kb(p)); return
                    if len(_al3) >= 3:
                        show_sub(cid, p, "🎖 سقف اتحاد نظامی طرف مقابل پر است (۳ نفر).", cmdr_kb(p)); return
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
            _al = [k2 for k2, v2 in world["pacts"].items() if isinstance(v2, dict) and v2.get("kind") == "all" and uid in k2.split("|")]
            if len(_al) >= 3:
                show_sub(cid, p, "🎖 سقف اتحاد نظامی: ۳ نفر - برای اتحاد جدید اول یکی را لغو کن.", cmdr_kb(p)); return
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
            mpay(p, 2500, "پیشنهاد اتحاد")
            world["preq"][tgt] = dict(frm=uid, kind="all")
            cd_set(p, "pac" + tgt, 3600)
            aud(p, "پیشنهاد اتحاد نظامی", "به " + others[tgt].get("name", "؟") + " - $2,500")
            try:
                tg("sendMessage", chat_id=int(tgt), parse_mode="HTML",
                   text="🎖 <b>پیشنهاد اتحاد نظامی</b> از " + esc(p["name"]) + "\nدر ربات: 🤝 فرماندهان")
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
            mpay(p, 500, "استقرار نیرو")
            world["forces"][rk0] = dict(frm=tgt, host=uid, de=de2, last=now)
            cd_set(p, "frc" + tgt, 21600)
            aud(p, "استقرار نیروی متحد", others[tgt].get("name", "؟") + " → " + REGIONS[rk0]["nm"] + " - قدرت " + fa(de2))
            news("🪖 نیروهای متحد " + others[tgt].get("name", "؟") + " در " + REGIONS[rk0]["nm"] + " مستقر شدند - حقوق $300/ساعت با میزبان")
            try:
                tg("sendMessage", chat_id=int(tgt), parse_mode="HTML",
                   text="🪖 ستون کمکی تو در " + esc(REGIONS[rk0]["nm"]) + " مستقر شد - پادگان میزبان: " + esc(p["name"]))
            except Exception:
                pass
            show_sub(cid, p, f"🪖 نیروی متحد مستقر شد - دفاع منطقه +{fa(de2)}\n💳 {fsm(-500)} + حقوق {fm(300)} هر ساعت", cmdr_kb(p)); return
        if op2 == "wdw":
            rk0 = p.get("city")
            fc = world["forces"].get(rk0)
            if not fc or (fc.get("host") != uid and fc.get("frm") != uid):
                show_sub(cid, p, "نیرویی از این فرمانده مستقر نیست.", cmdr_kb(p)); return
            del world["forces"][rk0]
            aud(p, "خروج نیروی متحد", REGIONS.get(rk0, {}).get("nm", "؟"))
            news("🪖 نیروهای متحد از " + REGIONS.get(rk0, {}).get("nm", "؟") + " خارج شدند")
            show_sub(cid, p, "نیروها خارج شدند - حقوق تمام.", cmdr_kb(p)); return
        if op2 == "brk":
            if not has_pact(uid, tgt): show_sub(cid, p, "پیمانی در کار نیست.", cmdr_kb(p)); return
            if p["treasury"] < 1000: show_sub(cid, p, f"لغو پیمان {fm(1000)} دارد - خزانه: {fm(p['treasury'])}", cmdr_kb(p)); return
            mpay(p, 1000, "لغو پیمان")
            world["pacts"].pop(pk(uid, tgt), None)
            aud(p, "لغو پیمان", "با " + others[tgt].get("name", "؟") + " - $1,000")
            for rk2 in list(world.get("forces", {})):
                fc2 = world["forces"][rk2]
                if uid in (fc2.get("host"), fc2.get("frm")) and tgt in (fc2.get("host"), fc2.get("frm")):
                    del world["forces"][rk2]
            news(f"💔 {p['name']} پیمان با {others[tgt].get('name')} را لغو کرد")
            show_sub(cid, p, "پیمان لغو شد - از این‌پس حمله ممکن است.", cmdr_kb(p)); return
    if act == "trd": show_sub(cid, p, trd_text(p), trd_kb(p)); return
    if act.startswith("trd2:"):
        tgt = act.split(":")[1]
        others = (worlds.get(p.get("gid") or "0", {}).get("pdata") or {})
        if tgt not in others or tgt == uid:
            show_sub(cid, p, "این فرمانده در دسترس نیست.", trd_kb(p)); return
        show_sub(cid, p, trd2_text(p, others[tgt].get("name", "؟")), trd2_kb(p, tgt)); return
    if act.startswith("trk:"):
        _, tgt, k = act.split(":")
        pr2 = profiles.get(uid) or {}
        others = (worlds.get(p.get("gid") or "0", {}).get("pdata") or {})
        if (pr2.get("lvl", 1) or 1) < 2:
            show_sub(cid, p, f"🔒 تجارت از سطح ۲ باز می‌شود - تو سطح {fa(pr2.get('lvl', 1))}.", trd_kb(p)); return
        if tgt not in others or tgt == uid or k not in CNAM:
            show_sub(cid, p, "این معامله معتبر نیست.", trd_kb(p)); return
        lst = world["treq"].setdefault(tgt, [])
        if len([o for o in lst if o["frm"] == uid]) >= 2:
            show_sub(cid, p, "حداکثر ۲ پیشنهاد باز به هر فرمانده.", trd_kb(p)); return
        cd = cd_left(p, "trd" + tgt)
        if cd > 0:
            show_sub(cid, p, f"⏳ {fa(cd)} ثانیه صبر کن.", trd_kb(p)); return
        if int(round(p["stock"].get(k, 0))) < 10:
            show_sub(cid, p, f"{CNAM[k]} کمتر از ۱۰ تن است.", trd_kb(p)); return
        price = int(round((world["market"][k] * 10 + 25) / 10) * 10)
        mins = max(6, int(14 - nat_stats(p)["logi"] / 10))
        p["stock"][k] = int(round(p["stock"].get(k, 0))) - 10
        oid = "o" + str(int(world.get("tseq", 1))); world["tseq"] = int(world.get("tseq", 1)) + 1
        lst.append(dict(oid=oid, frm=uid, fn=p["name"], tn=others[tgt].get("name", "؟"),
                        k=k, qty=10, price=price, mins=mins, exp=now + 1800))
        cd_set(p, "trd" + tgt, 600)
        aud(p, "پیشنهاد تجاری", f"{CNAM.get(k, k)} ×۱۰ → {others[tgt].get('name')} - {fm(price)}")
        try: tg("sendMessage", chat_id=int(tgt), parse_mode="HTML",
                text=f"📜 <b>پیشنهاد تجاری</b> از {esc(p['name'])}: {CNAM.get(k, k)} ×۱۰ - {fm(price)}\nدر ربات: 📜 تجارت")
        except Exception: pass
        show_sub(cid, p, f"✅ پیشنهاد ثبت شد - {CNAM.get(k, k)} ×۱۰ تا پاسخ در امانت می‌ماند (۳۰ دقیقه).\n💵 در قبولی: {fm(price)}", trd_kb(p)); return
    if act.startswith("tra:"):
        _, op3, oid = act.split(":")
        lst = world["treq"].setdefault(uid, [])
        o = next((x for x in lst if x["oid"] == oid), None)
        others = (worlds.get(p.get("gid") or "0", {}).get("pdata") or {})
        if not o or o["frm"] == uid:
            show_sub(cid, p, "این پیشنهاد معتبر نیست.", trd_kb(p)); return
        fp = others.get(o["frm"])
        if op3 == "no":
            lst.remove(o)
            if fp: fp["stock"][o["k"]] = int(round(fp["stock"].get(o["k"], 0))) + o["qty"]
            aud(p, "رد پیشنهاد تجاری", f"از {o['fn']} - {CNAM.get(o['k'], o['k'])} برگشت خورد")
            show_sub(cid, p, "پیشنهاد رد شد - کالا به فرستنده برگشت.", trd_kb(p)); return
        if o["exp"] < now:
            lst.remove(o)
            if fp: fp["stock"][o["k"]] = int(round(fp["stock"].get(o["k"], 0))) + o["qty"]
            show_sub(cid, p, "⌛️ این پیشنهاد منقضی شده - کالا برگشت.", trd_kb(p)); return
        if p["treasury"] < o["price"]:
            show_sub(cid, p, f"💳 {fm(o['price'])} لازم است - خزانه: {fm(p['treasury'])}", trd_kb(p)); return
        if sum(p["stock"].values()) + o["qty"] + sum(c["qty"] for c in p.get("cargos", [])) > p["stockcap"]:
            show_sub(cid, p, "📦 ظرفیت انبار و محموله‌ها پر است.", trd_kb(p)); return
        mpay(p, o["price"], "خرید بازار")
        if fp:
            fp["treasury"] = int(fp.get("treasury", 0)) + int(o["price"])
            _mlog(fp, int(o["price"]), "فروش بازار")
        p.setdefault("cargos", []).append(dict(k=o["k"], qty=o["qty"], at=now + o["mins"] * 60, pr=o["price"] // o["qty"]))
        lst.remove(o)
        aud(p, "قبول قرارداد تجاری", f"{CNAM.get(o['k'], o['k'])} ×{fa(o['qty'])} از {o['fn']} - {fm(o['price'])}")
        if fp: aud(fp, "قرارداد تجاری بسته شد", f"{CNAM.get(o['k'], o['k'])} → {p['name']} - {fm(o['price'])}")
        news(f"📜 قرارداد تجاری: {o['fn']} → {p['name']} ({CNAM.get(o['k'], o['k'])} ×{fa(o['qty'])})")
        wbroadcast(f"📜 <b>قرارداد تجاری</b>: {esc(o['fn'])} → {esc(p['name'])} - {CNAM.get(o['k'], o['k'])} ×{fa(o['qty'])} - {fm(o['price'])}")
        if fp:
            try: tg("sendMessage", chat_id=int(o["frm"]), parse_mode="HTML",
                    text=f"📜 {esc(p['name'])} قرارداد تو را قبول کرد - {fm(o['price'])} به خزانه‌ات واریز شد.")
            except Exception: pass
        show_sub(cid, p, f"📜 قرارداد بسته شد - تحویل {fa(o['mins'])} دقیقه‌ای به انبار.\n💳 {fsm(-o['price'])}", trd_kb(p)); return
    if act.startswith("trc:"):
        oid = act.split(":")[1]
        for tgt2, lst in list(world["treq"].items()):
            o = next((x for x in lst if x["oid"] == oid and x["frm"] == uid), None)
            if o:
                lst.remove(o)
                p["stock"][o["k"]] = int(round(p["stock"].get(o["k"], 0))) + o["qty"]
                aud(p, "لغو پیشنهاد تجاری", CNAM.get(o["k"], o["k"]))
                break
        show_sub(cid, p, trd_text(p), trd_kb(p)); return
    if act.startswith("eqg:"):
        v7 = act.split(":")[1]
        if not has_pact(uid, v7):
            show_sub(cid, p, "🎁 فقط برای پیمان/اتحاد.", cmdr_kb(p)); return
        if not p["equip"]:
            show_sub(cid, p, "زرادخانه خالی است.", cmdr_kb(p)); return
        if cd_left(p, "eqg" + v7) > 0:
            show_sub(cid, p, f"⏳ {fa(cd_left(p, 'eqg' + v7))} ثانیه صبر کن.", cmdr_kb(p)); return
        tgt7 = (worlds.get(p.get("gid") or "0", {}).get("pdata") or {}).get(v7)
        if tgt7 is None:
            show_sub(cid, p, "این فرمانده در دسترس نیست.", cmdr_kb(p)); return
        e7 = p["equip"].pop()
        tgt7.setdefault("deliveries", []).append(dict(e=dict(e7), at=now + 600))
        cd_set(p, "eqg" + v7, 600)
        aud(p, "اهدای سلاح به متحد", e7["ic"] + " " + e7["nm"] + " → " + tgt7.get("name", "؟"))
        aud(tgt7, "دریافت سلاح از متحد", e7["nm"] + " از " + p["name"])
        news(f"🎁 {p['name']} یک {e7['nm']} به {tgt7.get('name')} هدیه داد")
        try:
            tg("sendMessage", chat_id=int(v7), parse_mode="HTML",
               text="🎁 " + esc(p["name"]) + " یک " + esc(e7["nm"]) + " برایت فرستاد - ۱۰ دقیقه دیگر تحویل می‌شود.")
        except Exception:
            pass
        show_sub(cid, p, "🎁 " + e7["nm"] + " در راه " + tgt7.get("name", "؟") + " - تحویل ۱۰ دقیقه.", cmdr_kb(p)); return
    if act.startswith("eqs:"):
        v7 = act.split(":")[1]
        if not has_pact(uid, v7):
            show_sub(cid, p, "💵 فقط برای پیمان/اتحاد.", cmdr_kb(p)); return
        if not p["equip"]:
            show_sub(cid, p, "زرادخانه خالی است.", cmdr_kb(p)); return
        if cd_left(p, "eqg" + v7) > 0:
            show_sub(cid, p, f"⏳ {fa(cd_left(p, 'eqg' + v7))} ثانیه صبر کن.", cmdr_kb(p)); return
        tgt7 = (worlds.get(p.get("gid") or "0", {}).get("pdata") or {}).get(v7)
        if tgt7 is None:
            show_sub(cid, p, "این فرمانده در دسترس نیست.", cmdr_kb(p)); return
        pe7 = p["equip"][-1]
        base7 = next((x["price"] for x in list(EQUIP) + [x2 for xs in FOREIGN.values() for x2 in xs] if x["nm"] == pe7["nm"]), 400)
        pr7 = int(round(base7 * 0.5 / 10) * 10)
        if int(tgt7.get("treasury", 0)) < pr7:
            show_sub(cid, p, "💵 خزانه فرمانده مقصد کافی نیست (" + fm(pr7) + ").", cmdr_kb(p)); return
        e7 = p["equip"].pop()
        tgt7["treasury"] = int(tgt7.get("treasury", 0)) - int(pr7)
        _mlog(tgt7, -int(pr7), "غنیمت جنگی")
        mearn(p, pr7, "غنیمت جنگی")
        tgt7.setdefault("deliveries", []).append(dict(e=dict(e7), at=now + 600))
        cd_set(p, "eqg" + v7, 600)
        aud(p, "فروش سلاح به متحد", e7["ic"] + " " + e7["nm"] + " → " + tgt7.get("name", "؟") + " (+" + fm(pr7) + ")")
        aud(tgt7, "خرید سلاح از متحد", e7["nm"] + " از " + p["name"] + " (-" + fm(pr7) + ")")
        news(f"🤝 {p['name']} یک {e7['nm']} به {tgt7.get('name')} فروخت")
        try:
            tg("sendMessage", chat_id=int(v7), parse_mode="HTML",
               text="💵 " + esc(p["name"]) + " یک " + esc(e7["nm"]) + " به تو فروخت (" + fm(pr7) + "$) - ۱۰ دقیقه دیگر تحویل می‌شود.")
        except Exception:
            pass
        show_sub(cid, p, "💵 " + e7["nm"] + " در راه " + tgt7.get("name", "؟") + " - درآمد: " + fm(pr7), cmdr_kb(p)); return
    if act.startswith("csl:"):
        v5 = act.split(":")[1]
        c5 = world.get("col", {}).get(v5)
        if not c5 or c5.get("master") != uid or c5.get("kind") == "slv":
            show_sub(cid, p, "این مستعمره در دسترس نیست.", cmdr_kb(p)); return
        if p["treasury"] < 1500:
            show_sub(cid, p, f"بردگی کردن {fm(1500)} دارد - خزانه: {fm(p['treasury'])}", cmdr_kb(p)); return
        mpay(p, 1500, "بردگی کردن")
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
    if act == "ops": show_sub(cid, p, ops_text(p), ops_kb(p)); return
    if act == "map": show_sub(cid, p, map_text(p), kb([[btn(uid, "⚔️ عملیات", "ops"), btn(uid, "🏠 خانه", "menu")]])); return
    if act == "wh": show_sub(cid, p, wh_text(p), ops_kb(p)); return
    if act == "wcan": p["wiz"] = None; show_sub(cid, p, ops_text(p), ops_kb(p)); return
    if act.startswith("wt:"):
        rk = act.split(":")[1]
        if rk not in REGIONS or world["rs"][rk]["owner"] == uid:
            show_sub(cid, p, "هدف نامعتبر.", wtg_kb(p)); return
        p["wiz"] = dict(tg=rk)
        show_sub(cid, p, wiz_text(p, "typ"), wiz_kb(p, "typ")); return
    if act.startswith("wo:"):
        w = wiz_ops(p)
        if not w.get("tg"): show_sub(cid, p, "اول هدف را انتخاب کن.", wtg_kb(p)); return
        w["typ"] = act.split(":")[1]; p["wiz"] = w
        show_sub(cid, p, wiz_text(p, "com"), wiz_kb(p, "com")); return
    if act.startswith("wc:"):
        w = wiz_ops(p)
        if not w.get("typ"): show_sub(cid, p, "اول نوع عملیات.", wiz_kb(p, "typ")); return
        w["com"] = act.split(":")[1]; p["wiz"] = w
        show_sub(cid, p, wiz_text(p, "sup"), wiz_kb(p, "sup")); return
    if act.startswith("wp:"):
        w = wiz_ops(p)
        if not w.get("com"): show_sub(cid, p, "اول سطح نیرو.", wiz_kb(p, "com")); return
        w["sup"] = act.split(":")[1]; p["wiz"] = w
        show_sub(cid, p, wiz_text(p, "route"), wiz_kb(p, "route")); return
    if act.startswith("wr:"):
        w = wiz_ops(p)
        if not w.get("sup"): show_sub(cid, p, "اول پشتیبانی.", wiz_kb(p, "sup")); return
        w["route"] = act.split(":")[1]; p["wiz"] = w
        show_sub(cid, p, wiz_text(p, "prep"), wiz_kb(p, "prep")); return
    if act.startswith("wn:"):
        w = wiz_ops(p)
        if not w.get("route"): show_sub(cid, p, "اول مسیر لجستیک.", wiz_kb(p, "route")); return
        w["prep"] = (act.split(":")[1] == "p"); p["wiz"] = w
        show_sub(cid, p, wrev_text(p), wrev_kb(p)); return
    if act == "wgo":
        w = wiz_ops(p)
        st = world
        if not w or not w.get("tg") or not w.get("typ") or not w.get("com") or not w.get("sup") or not w.get("route") or w.get("prep") is None:
            show_sub(cid, p, "عملیات ناقص - از اول طراحی کن.", ops_kb(p)); return
        rk = w["tg"]
        if world["rs"][rk]["owner"] == uid:
            show_sub(cid, p, "این شهر خودت است!", ops_kb(p)); return
        did0 = world["rs"][rk]["owner"]
        if did0 and has_pact(uid, did0):
            show_sub(cid, p, "🤝 با فرمانده این شهر پیمان عدم تعرض داری - اول از «🤝 فرماندهان» لغو کن.", ops_kb(p)); return
        if cd_left(p, "atk" + rk) > 0:
            show_sub(cid, p, f"⏳ حمله اخیر به این شهر - {fa(cd_left(p, 'atk' + rk) // 60)} دقیقه صبر.", ops_kb(p)); return
        if any(o["aid"] == uid for o in world["wars"]):
            show_sub(cid, p, "یک عملیات فعال داری - اول تمامش کن.", ops_kb(p)); return
        cost = MOB[w["typ"]] + SUPP[w["sup"]][2] + (400 if w["route"] == "s" else 0)
        if p["treasury"] < cost:
            show_sub(cid, p, f"💳 اعزام {fm(cost)} لازم دارد - خزانه: {fm(p['treasury'])}", ops_kb(p)); return
        fuel = FUEL[w["typ"]]
        if int(round(p["stock"].get("oil", 0))) < fuel:
            show_sub(cid, p, f"⛽ سوخت جنگی کافی نیست - {fa(fuel)} تن نفت لازم است - انبار: {fa(int(round(p['stock'].get('oil', 0))))}\nاز بازار بخر یا مسجدسلیمان/خوزستان داشته باش.", ops_kb(p)); return
        mpay(p, cost, "اعزام عملیات")
        p["stock"]["oil"] = int(round(p["stock"].get("oil", 0))) - fuel
        aud(p, "سوخت عملیات", f"{fa(fuel)} تن نفت برای {OPN[w['typ']]}")
        dur = DUR[w["typ"]] + (10 if w["prep"] else 0)
        did = world["rs"][rk]["owner"]
        op = dict(aid=uid, aname=p["name"], did=did, rk=rk, typ=w["typ"], com=w["com"],
                  sup=w["sup"], route=w["route"], prep=w["prep"], cost=cost,
                  t0=now, t1=now + dur * 60, dur=dur)
        world["wars"].append(op)
        cd_set(p, "atk" + rk, 3600)
        p["wiz"] = None
        wlog(dict(who=p["name"], where=rk, what=OPN[w["typ"]], status="در حال اجرا",
                  when=tehfull(), result=f"اعزام - مدت {fa(dur)} دقیقه"))
        aud(p, "اعزام عملیات", f"{OPN[w['typ']]} → {REGIONS[rk]['nm']} - {fm(cost)}")
        news(f"⚔️ {p['name']} عملیات {OPN[w['typ']]} علیه {REGIONS[rk]['nm']} آغاز کرد")
        tg("sendMessage", chat_id=cid, parse_mode="HTML",
           text=f"⚔️ <b>عملیات آغاز شد!</b>\n{OPN[w['typ']]} روی {REGIONS[rk]['nm']} - نتیجه تا {fa(dur)} دقیقه دیگر")
        show_sub(cid, p, ops_text(p), ops_kb(p)); return
    if act == "country": show_sub(cid, p, country_text(p), country_kb(p)); return
    if act == "ind": show_sub(cid, p, ind_text(p), ind_kb(p)); return
    if act == "res": show_sub(cid, p, res_text(p), res_kb(p)); return
    if act == "equip": show_sub(cid, p, equip_text(p), equip_kb(p)); return
    if act == "world": show_sub(cid, p, world_text(p), world_kb(p)); return
    if act == "set": show_sub(cid, p, set_text(p), set_kb(p)); return
    if act == "acc": show_sub(cid, p, acc_text(p), kb([[btn(uid, "💳 فروشگاه استارز", "stars"), btn(uid, "🏠 خانه", "menu")]])); return
    if act == "rstp:0":
        if uid != "8694290031":
            show_sub(cid, p, "☠️ فقط مالک.", set_kb(p)); return
        show_sub(cid, p, "☠️ <b>ریست کامل همهٔ پلیرهای این گروه؟</b>\n━━━━━━━━━━━━━━━━━━\n- خزانه همه به $۲٬۰۰۰ برمی‌گردد\n- سطح و تجربه و عناوین صفر می‌شود\n- زرادخانه و قراردادها و مستعمره‌ها پاک\n- همهٔ مناطق بی‌طرف\n\n⚠️ برگشت ندارد.",
                 kb([[btn(uid, "☠️ بله، ریست کامل پلیرها", "rstp:go"), btn(uid, "❌ انصراف", "set")]])); return
    if act == "rstp:go":
        if uid != "8694290031":
            show_sub(cid, p, "☠️ فقط مالک.", set_kb(p)); return
        gid2 = p.get("gid") or "0"
        set_ctx(gid2)
        reset_world(gid2)
        for uid2 in list(worlds[gid2]["pdata"]):
            wp2 = new_wp({"id": int(uid2), "first_name": worlds[gid2]["pdata"][uid2].get("name", "فرمانده")})
            wp2["gid"] = gid2
            worlds[gid2]["pdata"][uid2] = wp2
        for uid2 in [u for u in profiles if (profiles[u].get("sel") or "0") == gid2]:
            profiles.pop(uid2, None)
        news("☠️ ریست کامل - همهٔ فرماندهان از صفر شروع می‌کنند")
        mark_dirty()
        try:
            if int(gid2):
                tg("sendMessage", chat_id=int(gid2), text="☠️ <b>ریست کامل انجام شد</b>\n━━━━━━━━━━━━━━━━━━\n- همهٔ فرماندهان از صفر شروع کردند\n- خزانه $2,000 - سطح ۱ - زرادخانه خالی\n- هر ۱۳ منطقه آزاد و بی‌طرف\n\nحالا «استارت» بفرست و شهرت را انتخاب کن 🏙", parse_mode="HTML")
        except Exception:
            pass
        show_sub(cid, p, "☠️ همهٔ پلیرهای این گروه از صفر شروع کردند - «استارت» بفرستید.", cty_kb(p)); return
    if act == "rst:0":
        if uid != "8694290031":
            show_sub(cid, p, "♻️ ریست جهان فقط برای مالک.", set_kb(p)); return
        show_sub(cid, p, "♻️ <b>ریست کامل جهان این گروه؟</b>\n━" * 1 + "━━━━━━━━━━━━━━━━━━\n- همه ۱۳ منطقه بی‌طرف می‌شوند (کسی روی هیچ شهری نیست)\n- جنگ‌ها، پیمان‌ها، مستعمره‌ها و زرادخانه‌ها پاک می‌شود\n- خزانه و سطح فرماندهان حفظ می‌شود\n- بعد از ریست، همه باید منطقه‌شان را دوباره انتخاب کنند\n\n⚠️ این کار برگشت ندارد.",
                 kb([[btn(uid, "✅ بله، ریست کامل", "rst:go"), btn(uid, "❌ انصراف", "set")]])); return
    if act == "rst:go":
        if uid != "8694290031":
            show_sub(cid, p, "♻️ ریست جهان فقط برای مالک.", set_kb(p)); return
        reset_world(p.get("gid") or "0")
        news("♻️ جهان این گروه از اول ساخته شد - همه مناطق آزاد است")
        show_sub(cid, p, "♻️ جهان این گروه از اول ساخته شد.\n\n🏙 حالا منطقه‌ات را انتخاب کن - هر فرمانده یک منطقه:", cty_kb(p)); return
    if act.startswith("cfgm:"):
        if uid != "8694290031":
            show_sub(cid, p, "⛔️ تنظیم World فقط برای مالک.", set_kb(p)); return
        d1 = -1 if act.endswith("-") else (1 if act.endswith("+") else 0)
        world.setdefault("cfg", {})["max_regions"] = max(1, min(len(REGIONS), max_regions() + d1))
        aud(p, "تنظیم World", "سقف مناطق آزاد: " + fa(max_regions()))
        show_sub(cid, p, "🌍 سقف مناطق آزاد این World: " + fa(max_regions()) + " - فقط برای ادعای بازیکن جدید؛ مناطق بی‌طرفِ بیرون سقف با جنگ قابل‌تصرف‌اند.", set_kb(p)); return
    if act == "stars": show_sub(cid, p, stars_text(p), stars_kb(p)); return
    if act.startswith("byst:"):
        try: usd = int(act.split(":")[1])
        except Exception: usd = 0
        stars = STARS_MAP.get(usd)
        if not stars: show_sub(cid, p, "این بسته موجود نیست.", stars_kb(p)); return
        if (msg.get("chat") or {}).get("type") != "private":
            show_sub(cid, p, "💳 پرداخت فقط در گفت‌وگوی خصوصی امن است - به پیوی ربات برو و «منو» بزن.", stars_kb(p))
            try: tg("sendMessage", chat_id=int(uid), parse_mode="HTML", text="💳 <b>فروشگاه استارز</b>\nاز منوی خصوصی → 💳 فروشگاه استارز")
            except Exception: pass
            return
        tg("sendInvoice", chat_id=cid, title=f"شارژ خزانه {fm(usd)}",
           description="بعد از پرداخت، خزانه فوری شارژ می‌شود",
           payload=f"top:{uid}:{usd}", currency="XTR",
           prices=[{"label": f"{stars} استارز", "amount": stars}])
        return
    if act.startswith("bypack:"):
        k7 = act.split(":", 1)[1]
        info7 = PACKS.get(k7)
        if not info7:
            show_sub(cid, p, "این بسته موجود نیست.", packs_kb(p)); return
        if (msg.get("chat") or {}).get("type") != "private":
            show_sub(cid, p, "💳 پرداخت فقط در گفت‌وگوی خصوصی امن است - به پیوی ربات برو و «منو» بزن.", packs_kb(p))
            try: tg("sendMessage", chat_id=int(uid), parse_mode="HTML", text="🛍 <b>بسته‌های ویژه</b>\nاز منوی خصوصی → 💳 فروشگاه استارز → 🛍 بسته‌های ویژه")
            except Exception: pass
            return
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
        show_sub(cid, p, packs_text(p), packs_kb(p)); return
    if act == "wlds":
        if (msg.get("chat") or {}).get("type") != "private":
            show_sub(cid, p, "انتخاب دنیا فقط در گفت‌وگوی خصوصی با ربات است.", menu_kb(p)); return
        show_sub(cid, p, wlds_text(p), wlds_kb(p)); return
    if act.startswith("wsel:"):
        gid = act.split(":")[1]
        pr = profiles.setdefault(uid, new_profile({"id": uid}))
        if gid in worlds and uid in worlds[gid]["pdata"]:
            pr["sel"] = gid; set_ctx(gid)
            p2 = worlds[gid]["pdata"][uid]; migrate(p2)
            show_menu(p2, int(uid)); return
        show_sub(cid, p, "این دنیا در دسترس نیست.", menu_kb(p)); return
    if act == "regs":
        t, _ = regs_text(p); show_sub(cid, p, t, regs_kb(p)); return
    if act.startswith("rpg:"):
        pg = int(act.split(":")[1]); t, _ = regs_text(p, pg); show_sub(cid, p, t, regs_kb(p, pg)); return
    if act.startswith("reg:"):
        rk = act.split(":")[1]; show_sub(cid, p, reg_text(p, rk), build_kb(p, rk)); return
    if act == "build":
        rk = "thr"; t, _ = build_text(p, rk); show_sub(cid, p, t, build_kb(p, rk)); return
    if act.startswith("bpg:"):
        _, rk, pg = act.split(":"); t, _ = build_text(p, rk, int(pg)); show_sub(cid, p, t, build_kb(p, rk, int(pg))); return
    if act.startswith("ptf:"):
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
        mpay(p, 1500, "هم‌سوسازی حزب")
        world["rs"][rk]["party"] = p["ident"]
        cd_set(p, "ptf" + rk, 21600)
        news(f"🏛 حزب {REGIONS[rk]['nm']} هم‌سوی {PARTY_NM[p['ident']]} شد")
        aud(p, "هم‌سوسازی حزب منطقه", REGIONS[rk]["nm"] + " → " + PARTY_NM[p["ident"]])
        show_sub(cid, p, "🏛 " + REGIONS[rk]["nm"] + " اکنون هم‌سوی " + PARTY_NM[p["ident"]] + " است - رضایت از تسویه بعد اصلاح می‌شود.", build_kb(p, rk)); return
    if act.startswith("bld:"):
        _, rk, bk = act.split(":")
        if rk not in my_regions(p):
            show_sub(cid, p, "⛔️ این شهر در قلمرو تو نیست - فقط شهر خودت را بساز.", build_kb(p, rk)); return
        cost = bcost(p, rk, bk)
        if len(p["builds"]) >= 4:
            show_sub(cid, p, "صف ساخت شلوغ است - اول صبر کن کارها تمام شوند.", build_kb(p, rk)); return
        if p["treasury"] < cost:
            show_sub(cid, p, f"💳 خزانه کافی نیست - این ساخت {fm(cost)} لازم دارد.\nخزانه: {fm(p['treasury'])}", build_kb(p, rk)); return
        mpay(p, cost, "ساخت سازه")
        p["builds"].append(dict(rg=rk, bk=bk, done=now + BUILDS[bk]["mins"] * 60))
        news(f"🏗️ ساخت {BUILDS[bk]['nm']} در {REGIONS[rk]['nm']} آغاز شد")
        show_sub(cid, p, f"🏗️ ساخت {BUILDS[bk]['ic']} {BUILDS[bk]['nm']} شروع شد!\n⏳ {fa(BUILDS[bk]['mins'])} دقیقه - 💳 {fsm(-cost)}", build_kb(p, rk))
        return
    if act == "eco": show_sub(cid, p, eco_text(p), kb([[btn(uid, "🏦 بودجه", "budget"), btn(uid, "📈 بازار", "mkt")], [btn(uid, "🏠 خانه", "menu")]])); return
    if act == "budget": show_sub(cid, p, eco_text(p), budget_kb(p)); return
    if act.startswith("bud+"):
        k = act[4:]
        if sum(p["budget"].values()) < 100 and p["budget"][k] < 40: p["budget"][k] += 1
        show_sub(cid, p, eco_text(p), budget_kb(p)); return
    if act == "dip":
        t, pg = dip_text(p); show_sub(cid, p, t, dip_kb(p)); return
    if act.startswith("dpg:"):
        pg = int(act.split(":")[1]); t, _ = dip_text(p, pg); show_sub(cid, p, t, dip_kb(p, pg)); return
    if act.startswith("cnt:"):
        ck = act.split(":")[1]; show_sub(cid, p, cnt_text(p, ck), cnt_kb(p, ck)); return
    if act.startswith("dipup:"):
        ck = act.split(":")[1]; c = world["countries"][ck]
        if cd_left(p, "dip" + ck) > 0:
            show_sub(cid, p, f"⏳ {fa(cd_left(p, 'dip' + ck) // 60)} دقیقه صبر کن.", cnt_kb(p, ck)); return
        if p["treasury"] < 200:
            show_sub(cid, p, f"بهبود روابط {fm(200)} هزینه دارد - خزانه: {fm(p['treasury'])}", cnt_kb(p, ck)); return
        mpay(p, 200, "بهبود روابط")
        gain = 6 if crel(p, ck) < 50 else (3 if crel(p, ck) < 75 else 1)
        c["rel"] = max(-100, min(100, c["rel"] + gain))
        cd_set(p, "dip" + ck, 1800)
        show_sub(cid, p, f"🤝 گفت‌وگوی مثبت با {c['nm']} - روابط +{fa(gain)} → {fa(crel(p, ck))}", cnt_kb(p, ck)); return
    if act.startswith("agree:"):
        _, ck, ty = act.split(":"); c = world["countries"][ck]; rel = crel(p, ck)
        need = dict(trade=30, fdi=45, joint=55, pact=65, over=70)[ty]
        if p["agreements"].get(ck): show_sub(cid, p, "قبلاً قرارداد داری - ابتدا لغو لازم است.", cnt_kb(p, ck)); return
        if rel < need: show_sub(cid, p, f"روابط کافی نیست ({fa(rel)} از {fa(need)}).", cnt_kb(p, ck)); return
        if ty == "joint" and p["treasury"] < 1500: show_sub(cid, p, f"پروژه مشترک {fm(1500)} لازم دارد.", cnt_kb(p, ck)); return
        if ty == "over" and p["treasury"] < 2000: show_sub(cid, p, f"پایگاه لجستیکی {fm(2000)} لازم دارد.", cnt_kb(p, ck)); return
        if ty == "joint": mpay(p, 1500, "پروژه مشترک")
        if ty == "over": mpay(p, 2000, "پایگاه لجستیکی")
        p["agreements"][ck] = ty
        nm = {"trade": "📜 قرارداد تجاری", "fdi": "💵 سرمایه‌گذاری خارجی", "joint": "🏗️ پروژه مشترک",
              "pact": "🛡️ پیمان دفاعی", "over": "📦 پایگاه لجستیکی"}[ty]
        if ty == "fdi": mearn(p, 800, "سرمایه‌گذاری خارجی")
        news(f"🤝 ایران و {c['nm']}: {nm} امضا شد")
        addxp(p, 20)
        extra = f"\n💵 ورودی خزانه: {fsm(800)}" if ty == "fdi" else ""
        show_sub(cid, p, f"✅ {nm} با {c['nm']} امضا شد!{extra}", cnt_kb(p, ck)); return
    if act.startswith("shop:"):
        ck = act.split(":")[1]; t, pg = shop_text(p, ck); show_sub(cid, p, t, shop_kb(p, ck)); return
    if act.startswith("epg:"):
        _, ck, pg = act.split(":"); t, _ = shop_text(p, ck, int(pg)); show_sub(cid, p, t, shop_kb(p, ck, int(pg))); return
    if act.startswith("buyeq:"):
        _, ck, ix = act.split(":"); e = EQUIP[int(ix)]; c = world["countries"][ck]
        mult, minrel = SELLERS.get(ck, [1.0, 0])
        if crel(p, ck) < minrel: show_sub(cid, p, "⛔️ روابط کافی نیست.", shop_kb(p, ck)); return
        pm = max(0.8, min(1.8, smult(ck) - crel(p, ck) / 250))
        price = int(round(e["price"] * pm / 10) * 10)
        if p["treasury"] < price: show_sub(cid, p, f"💳 {fm(price)} لازم است - خزانه: {fm(p['treasury'])}", shop_kb(p, ck)); return
        mpay(p, price, "خرید تجهیزات")
        mins = int(e["mins"] * (1.5 if crel(p, ck) < 30 else 1))
        p["deliveries"].append(dict(e=dict(e), at=now + mins * 60))
        news(f"🛒 خرید {e['nm']} از {c['nm']} - تحویل {fa(mins)} دقیقه‌ای")
        show_sub(cid, p, f"✅ سفارش ثبت شد: {e['ic']} {e['nm']}\n💳 {fsm(-price)} - ⏳ تحویل {fa(mins)} دقیقه", shop_kb(p, ck)); return
    if act == "de": show_sub(cid, p, def_text(p), def_kb(p)); return
    if act == "log": show_sub(cid, p, log_text(p), log_kb(p)); return
    if act == "tech": show_sub(cid, p, tech_text(p), tech_kb(p)); return
    if act.startswith("tech:"):
        k = act.split(":")[1]; t = TECHS.get(k)
        if not t: show_sub(cid, p, "این فناوری موجود نیست.", tech_kb(p)); return
        if p["research"]: show_sub(cid, p, "یک پژوهش در جریان است.", tech_kb(p)); return
        if p["treasury"] < t["cost"]: show_sub(cid, p, f"💳 {fm(t['cost'])} لازم است - خزانه: {fm(p['treasury'])}", tech_kb(p)); return
        mpay(p, t["cost"], "پژوهش")
        mins = int(t["mins"] * (0.85 if any(b == "uni" for r in p["regions"].values() for b in r["bl"]) else 1))
        p["research"] = dict(tk=k, at=now + mins * 60)
        show_sub(cid, p, f"🧠 پژوهش «{t['nm']}» شروع شد - ⏳ {fa(mins)} دقیقه - 💳 {fsm(-t['cost'])}", tech_kb(p)); return
    if act == "prj": show_sub(cid, p, prj_text(p), prj_kb(p)); return
    if act.startswith("prj:"):
        k = act.split(":")[1]; pr = PROJECTS[k]
        st = p["projects"].get(k, {}).get("s", 0)
        if st >= 3: show_sub(cid, p, "این پروژه کامل است ✅", prj_kb(p)); return
        if p["projects"].get(k, {}).get("at"): show_sub(cid, p, "مرحله فعلی در حال ساخت است ⏳", prj_kb(p)); return
        cost = pr["st"][st]
        if p["treasury"] < cost: show_sub(cid, p, f"💳 {fm(cost)} لازم است - خزانه: {fm(p['treasury'])}", prj_kb(p)); return
        mpay(p, cost, "پروژه ملی")
        mins = pr["mins"][st]
        pj = p["projects"].setdefault(k, dict(s=st, at=0))
        pj["at"] = now + mins * 60
        show_sub(cid, p, f"🏛 مرحله {fa(st + 1)} {pr['nm']} آغاز شد - ⏳ {fa(mins)} دقیقه - 💳 {fsm(-cost)}", prj_kb(p)); return
    if act == "mkt": show_sub(cid, p, mkt_text(p), mkt_kb(p)); return
    if act.startswith("fbuy:"):
        _, ck3, j3 = act.split(":")
        fs3 = fstock(p, ck3)
        if not fs3 or ck3 not in FOREIGN:
            show_sub(cid, p, "✋ این کشور به حزب تو سلاح نمی‌فروشد - حزب درست را انتخاب کن.", shop_kb(p, ck3)); return
        if int(j3) >= len(fs3): show_sub(cid, p, "این سامانه موجود نیست.", shop_kb(p, ck3)); return
        e3 = fs3[int(j3)]
        mult3, minrel3 = SELLERS.get(ck3, [1.0, 0])
        if crel(p, ck3) < minrel3 + 20:
            show_sub(cid, p, f"⛔️ روابط بیشتر لازم: حداقل {fa(minrel3 + 20)}", shop_kb(p, ck3)); return
        pm3 = max(0.8, min(1.8, smult(ck3) - crel(p, ck3) / 250))
        pr3 = int(round(e3["price"] * pm3 * 1.15 / 10) * 10)
        if p["treasury"] < pr3:
            show_sub(cid, p, f"💳 {fm(pr3)} لازم است - خزانه: {fm(p['treasury'])}", shop_kb(p, ck3)); return
        if cd_left(p, "fbuy" + ck3) > 0:
            show_sub(cid, p, f"⏳ {fa(cd_left(p, 'fbuy' + ck3))} ثانیه صبر کن.", shop_kb(p, ck3)); return
        mpay(p, pr3, "خرید خارجی")
        p["deliveries"].append(dict(e=dict(e3), at=now + (e3["mins"] + 20) * 60))
        cd_set(p, "fbuy" + ck3, 900)
        aud(p, "خرید تسلیحات خارجی", e3["nm"] + " از " + world["countries"][ck3]["nm"] + " - " + fm(pr3))
        news("🛒 خرید سامانه خارجی: " + e3["nm"] + " از " + world["countries"][ck3]["nm"])
        show_sub(cid, p, "✅ سفارش خارجی ثبت شد: " + e3["ic"] + " " + e3["nm"] + "\n⏳ تحویل " + fa(e3["mins"] + 20) + " دقیقه\n💳 " + fsm(-pr3), shop_kb(p, ck3)); return
    if act == "rfn":
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
        mpay(p, 30, "پالایش نفت")
        p.setdefault("refines", []).append(dict(at=now + 15 * 60))
        cd_set(p, "rfn", 300)
        aud(p, "سفارش پالایش", "۱۰ تن نفت → ۸ انرژی + ۲ استراتژیک - ۱۵ دقیقه")
        show_sub(cid, p, "🏭 پالایش آغاز شد: ۱۰ تن نفت خام در امانت\n⏳ ۱۵ دقیقه بعد: +۸ انرژی +۲ استراتژیک\n💳 " + fsm(-30), mkt_kb(p)); return
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
        show_sub(cid, p, f"🚢 قرارداد صادرات ۲۰ تن بسته شد - نفت در امانت\n⏳ تسویه: {fa(mins)} دقیقه دیگر به قیمت بازار همان لحظه +۸٪\n📌 ریسک و سود با تو - قیمت تثبیت نمی‌شود", mkt_kb(p)); return
    if act.startswith("mbuy:") or act.startswith("msell:"):
        k = act.split(":")[1]; pr = world["market"][k]
        p["last_mkt"] = p.get("last_mkt", 0)
        if now - p["last_mkt"] < 5: show_sub(cid, p, "⏳ کمی آهسته - بازار را بجوشان!", mkt_kb(p)); return
        p["last_mkt"] = now
        if act.startswith("mbuy:"):
            if sum(p["stock"].values()) + 10 + sum(c["qty"] for c in p.get("cargos", [])) > p["stockcap"]:
                show_sub(cid, p, "📦 ظرفیت انبار و محموله‌ها پر است - انبار بساز.", mkt_kb(p)); return
            cost = int(pr * 10) + 50
            if p["treasury"] < cost: show_sub(cid, p, f"💳 {fm(cost)} لازم است (شامل حمل) - خزانه: {fm(p['treasury'])}", mkt_kb(p)); return
            mpay(p, cost, "خرید بازار")
            mins = max(6, int(14 - nat_stats(p)["logi"] / 10))
            p.setdefault("cargos", []).append(dict(k=k, qty=10, at=now + mins * 60, pr=int(pr)))
            show_sub(cid, p, f"📄 قرارداد خرید ۱۰ تن بسته شد - {fm(pr)} هر تن + {fm(50)} حمل\n⏳ تأمین و انتقال: {fa(mins)} دقیقه\n💳 {fsm(-cost)}", mkt_kb(p)); return
        if p["stock"].get(k, 0) < 10: show_sub(cid, p, "۱۰ تن نداری - اول بخر یا صبر کن انبار پر شود.", mkt_kb(p)); return
        p["stock"][k] = int(round(p["stock"][k])) - 10; gain = int(pr * 10)
        mearn(p, gain, "فروش بازار")
        show_sub(cid, p, f"💰 فروش ۱۰ تن - {fm(pr)} هر تن\n💳 {fsm(gain)}", mkt_kb(p)); return
    if act == "news": show_sub(cid, p, news_text(), kb([[btn(uid, "🔄 بروزرسانی", "news"), btn(uid, "🏠 خانه", "menu")]])); return
    if act == "crisis": show_sub(cid, p, crisis_text(p), crisis_kb(p)); return
    if act.startswith("crs:"):
        i = int(act.split(":")[1])
        if i >= len(p["crises"]): show_sub(cid, p, "این بحران بسته شده ✅", crisis_kb(p)); return
        c = p["crises"][i]
        opk = "crs" + c["rg"] + str(int(c["dl"]))
        if p["ops"].get(opk): show_sub(cid, p, "این بحران قبلاً مهار شد ✅", crisis_kb(p)); return
        if p["treasury"] < c["cost"]: show_sub(cid, p, f"💳 {fm(c['cost'])} لازم است - خزانه: {fm(p['treasury'])}", crisis_kb(p)); return
        mpay(p, c["cost"], "مهار بحران"); p["ops"][opk] = 1; p["crises"].remove(c)
        p["sat"] = min(100, p["sat"] + 2); addxp(p, 15)
        news(f"✅ {c['nm']} در {REGIONS[c['rg']]['nm']} مهار شد")
        show_sub(cid, p, "✅ بحران مهار شد! مردم خوشحال‌اند (+۲ رضایت)", crisis_kb(p)); return
    if act == "dec": show_sub(cid, p, dec_text(p), dec_kb(p)); return
    if act.startswith("dec:"):
        if not p.get("decision"): show_sub(cid, p, "تصمیمی در کار نیست.", kb([[btn(uid, "🏠 خانه", "menu")]])); return
        out = apply_decision(p, act.split(":")[1])
        show_sub(cid, p, "🗳️ " + out, kb([[btn(uid, "🏠 خانه", "menu")]])); return
    if act == "rank": show_sub(cid, p, rank_text(p), rank_kb(p)); return
    if act == "titles": show_sub(cid, p, titles_text(p), kb([[btn(uid, "🏠 خانه", "menu")]])); return
    if act == "war":
        if not p.get("war"): war_check(p)
        show_sub(cid, p, war_text(p), war_kb(p)); return
    if act.startswith("wd:"):
        typ = act.split(":")[1]
        if not p.get("war") or typ not in TYPNM:
            show_sub(cid, p, "عملیات فعالی نیست.", war_kb(p)); return
        show_sub(cid, p, war_deploy(p, typ), war_kb(p)); return
    show_menu(p, cid)

CMDMAP = {"آموزش": "help", "کمک": "help", "start": "menu", "menu": "menu", "کشور": "country", "منو": "menu", "شروع": "menu", "استارت": "menu", "وضعیت": "menu", "بازی": "menu", "خانه": "menu",
          "شهرها": "regs", "شهر": "regs", "مناطق": "regs", "استان": "regs", "استان‌ها": "regs",
          "ساخت": "build", "ساخت‌وساز": "build", "توسعه": "prj", "پروژه": "prj", "پروژه‌ها": "prj",
          "اقتصاد": "eco", "بودجه": "budget", "صنعت": "ind", "منابع": "res",
          "دفاع": "de", "تجهیزات": "equip", "زرادخانه": "equip",
          "دیپلماسی": "dip", "جهان": "world", "لجستیک": "log",
          "بازار": "mkt", "فناوری": "tech", "پژوهش": "tech",
          "بحران": "crisis", "بحران‌ها": "crisis", "اخبار": "news", "خبر": "news",
          "تصمیم": "dec", "تصمیم‌ها": "dec", "رتبه": "rank", "رتبه‌بندی": "rank", "برترین": "rank",
          "عناوین": "titles", "تنظیمات": "set", "هویت": "ident", "فروشگاه": "stars", "استارز": "stars", "شارژ": "stars",
          "پنل": "menu", "اتحاد": "dip", "اتحادها": "dip", "راهنما": "help", "خزانه": "eco", "قراردادها": "trd", "قرارداد": "trd",
          "حساب": "eco", "پول": "eco", "درآمد": "eco", "خرید": "mkt", "فروش": "mkt",
          "گردش خزانه": "audit", "بسته": "packs", "بسته‌ها": "packs", "سرمایه‌گذاری": "packs",
          "منوی بازی": "menu", "حساب من": "acc", "کیف": "packs",
          "جنگ": "war", "عملیات": "ops", "حمله": "ops", "نقشه": "map", "تاریخچه": "wh", "گزارش‌ها": "wh", "دستیار": "asz", "تحلیل": "asz", "فرماندهان": "cmdr", "پیمان": "cmdr", "سلامت": "health", "حسابرسی": "audit", "تجارت": "trd", "بودجه": "budget", "مستعمرهها": "csl", "مستعمره": "csl", "آزادم": "cfree", "آزادی": "cfree", "دنیاهای من": "wlds", "دنیاها": "wlds",
          "واریز": "stars", "شارژ استارز": "stars", "زرادخانه": "equip", "سلاح": "shop:ru", "جنگ": "war",
          "سلام": "salam", "درود": "salam", "هلو": "salam", "راهنما": "help", "کمک": "help", "دستورها": "help", "دستورات": "help"}

def norm_cmd(txt):
    try:
        t = (txt or "").strip().lstrip("/").strip()
        if not t: return ""
        t = t.replace("ي", "ی").replace("ك", "ک").replace("\u200c", "").replace("\u064B", "").replace("\u064C", "").replace("\u064D", "").replace("\u064E", "").replace("\u064F", "").replace("\u0650", "").replace("\u0651", "")
        t = t.split("@")[0]
        _full = " ".join(t.split())
        _w = t.split()[0].strip("!؟?.,،:؛+ ")
        if _full in CMDMAP:
            t = _full   # «حساب من»، «دنیاهای من»، «گردش خزانه» - عبارت کامل مقدم است
        elif _w in CMDMAP or _w.startswith("/"):
            t = _w
        return t.strip("!.؟?،,؛:")
    except Exception: return ""

def help_text():
    return "\n".join([
        f"📖 <b>راهنمای فرماندهی</b> {pe('book')}",
        "━" * 20,
        "همه‌چیز دکمه‌ای است - از خانه به همه بخش‌ها می‌رسی.",
        "کلمه‌های میان‌بر بدون / :",
        "کشور - شهرها - صنعت - منابع - اقتصاد - بازار",
        "دیپلماسی - جهان - دفاع - تجهیزات - فناوری - بحران",
        "اخبار - رتبه - عملیات - نقشه - تاریخچه - راهنما",
        "دستیار - فرماندهان - تجارت - حسابرسی",
        "━" * 20,
        "💳 پول دلاری: شروع $2,000 - درآمد ساعتی − نگهداری",
        "🤲 کمک نوپایی: تا سطح ۳ (حداکثر ۲ شهر) درآمدت زیر $150 در ساعت نمی‌رود",
        "⏰ واریز درآمد هر ساعت، دقیقاً روی ساعت ایران - جزئیات: اقتصاد",
        "⭐️ استارز: شارژ خزانه + بسته‌های ویژه (چندگروهی/حقوق/بهره) - فروشگاه",
        "🎖 اتحاد نظامی: حداکثر ۳ نفر - پیمان ساده نامحدود",
        "📈 مسیر رشد: $1,000 → $5,000 → $10,000 → $50,000 → $100,000",
        "⛏ منابع: شهرها تولید و مصرف دارند - مازاد به انبار و بازار می‌رود",
        "🏛 هویت ملی: دو مسیر متوازن - تغییر با هزینه $5,000",
        "🏘 گروه: ربات را اضافه کن و /start بزن - هر گروه یک دنیای مستقل",
        "⏳ زمان تهران: " + teh()])

_cb_last = {}
_cb_pool = queue.Queue()
_cb_warm = {"on": False}
_cb_busy = [0]


def _cb_answer(cqid, t="", a=False):
    tg("answerCallbackQuery", callback_query_id=cqid, text=(t or None), show_alert=a)


def _cb_worker():
    """⚡ دکمه‌ها: پاسخ فوری در on_cb، کار سنگین اینجا در نخ پس‌زمینه"""
    while True:
        q = _cb_pool.get()
        _cb_busy[0] = 1
        try:
            _cb_run(q)
        except Exception:
            traceback.print_exc()
            LOG.exception("خطای دکمه")
        finally:
            _cb_busy[0] = 0


def cb_drain(timeout=3.0):
    """تست/همگام‌سازی: تا صف دکمه‌ها خالی شود صبر کن"""
    t0 = time.time()
    while (not _cb_pool.empty() or _cb_busy[0]) and time.time() - t0 < timeout:
        time.sleep(0.01)


def on_cb(q):
    data = q.get("data", ""); frm = q["from"]; cqid = q["id"]
    uid, _, act = data.partition("|")
    if str(frm.get("id")) != uid:
        _cb_answer(cqid, "این پنل مال تو نیست - شروع کن: /start", True)
        return
    _t0 = time.time()
    _a1, _t1 = _cb_last.get(uid, ("", 0.0))
    if _a1 == act and _t0 - _t1 < 0.7:
        _cb_answer(cqid, "⏳ آهسته - همین حالا زدی"); return
    _cb_last[uid] = (act, _t0)
    if len(_cb_last) > 800:
        for _k in list(_cb_last)[:400]: _cb_last.pop(_k, None)
    _cb_answer(cqid)          # ⚡ دکمه فوری روشن می‌شود - کار در پس‌زمینه ادامه دارد
    if not _cb_warm["on"]:
        _cb_warm["on"] = True
        threading.Thread(target=_cb_worker, daemon=True).start()
    _cb_pool.put(q)

def _cb_run(q):
    uid, _, act = q.get("data", "").partition("|")
    cqid = q["id"]
    msg = q.get("message") or {}
    chat = msg.get("chat") or {}

    def ans(t="", a=False):
        _cb_answer(cqid, t, a)
    print("[cb]", uid, act)
    if act != "jchk" and not joined(uid):
        ans("🔒 اول عضو کانال شو ✅", True)
        if chat.get("type") == "private":
            tg("sendMessage", chat_id=int(uid), parse_mode="HTML", text=join_text(), reply_markup=join_kb(uid))
        return
    if act == "jchk":
        if joined(uid, force=True):
            ans("✅ عضویت تأیید شد", True)
            tg("sendMessage", chat_id=(chat.get("id") or int(uid)), parse_mode="HTML",
               text="✅ عضویت تأیید شد - حالا /start بزن و بازی را ادامه بده.")
        else:
            ans("هنوز عضو نشدی ✅😝", True)
        return
    try:
        with _lock:
            # دنیا از محل دکمه مشخص می‌شود: گروه = دنیای خود گروه، خصوصی = دنیای انتخابی
            if chat.get("type") == "private":
                gid = (profiles.get(uid) or {}).get("sel") or "0"
                if gid not in worlds: gid = "0"
            else:
                gid = str(chat.get("id"))
            w = ensure_world(gid, chat.get("title") or ("🏠 دنیای اصلی" if gid == "0" else "🌍 دنیای گروه"))
            p = w["pdata"].get(uid)
            if not p:
                ans("اول در ربات /start بزن.", True); return
            set_ctx(gid); p["gid"] = gid
            migrate(p); route(p, act, msg)
    except Exception:
        traceback.print_exc()
        LOG.exception("خطای پردازش")
        ans("خطای موقت - یک بار دیگر بزن", True)
    else:
        ans()
    finally:
        mark_dirty()   # ذخیرهٔ خودکار ۸ ثانیه‌ای؛ نخ کارگر دیسک منتظر نمی‌ماند


_RL = {}
def flooded(uid):
    if not uid: return False
    now = time.time(); w = _RL.get(uid)
    if not w or now - w[0] > 60:
        _RL[uid] = [now, 1]; return False
    w[1] += 1
    return w[1] > 40

def on_msg(m):
    chat = m.get("chat", {}); uid = str(m.get("from", {}).get("id", "")); txt = (m.get("text") or "").strip()
    if not uid or uid == "None": return
    ctype = chat.get("type")
    if ctype not in ("private", "group", "supergroup"): return
    if flooded(uid):
        if ctype == "private":
            tg("sendMessage", chat_id=int(uid), text="⏳ کمی آهسته‌تر — پیام‌ها پشت‌سرهم است.")
        return
    if ctype == "private" and not txt.startswith("/"):
        c0 = norm_cmd(txt)
        if c0 not in CMDMAP and c0 not in ("salam", "سلام", "درود", "هلو"):
            tg("sendMessage", chat_id=int(uid), parse_mode="HTML",
               text="👑 دستور نامفهوم بود.\nکلمه‌های جادویی: <b>منو</b> · <b>کشور</b> · <b>شهرها</b> · <b>آموزش</b> · <b>راهنما</b>")
            return
    if ctype in ("group", "supergroup"):
        gid0 = str(chat.get("id"))
        if gid0 not in APPROVED_GROUPS:
            _st2 = ((tg("getChatMember", chat_id=chat["id"], user_id=int(uid)).get("result") or {}).get("status") or "")
            if uid == OWNER_ID or _st2 in ("creator", "administrator"):
                APPROVED_GROUPS.add(gid0); jsave("groups.json", sorted(APPROVED_GROUPS))
                tg("sendMessage", chat_id=chat["id"], parse_mode="HTML",
                   text="✅ <b>این گروه تایید شد</b>\n🌍 دنیای مستقل همین گروه فعال است - «استارت» بفرست.\n\n⚠️ اگر پیام‌های معمولی دیده نمی‌شوند: ربات را ادمین گروه کنید یا در BotFather حالت Group Privacy را خاموش کنید.")
            else:
                tg("sendMessage", chat_id=chat["id"], parse_mode="HTML",
                   text="🛡 <b>خروج امنیتی</b>\n❗️ این گروه در فهرست تاییدشدهٔ مالک نیست.\nربات فقط در گروه‌های تاییدشدهٔ مالک می‌ماند.\n👈 مالک در همین گروه پیام دهد تا تایید شود.")
                tg("leaveChat", chat_id=chat["id"])
            return
    sp = m.get("successful_payment")
    if sp:
        with _lock:
            prof = profiles.get(uid) or profiles.setdefault(uid, new_profile(m.get("from", {})))
            gid = prof.get("sel") if prof.get("sel") in worlds else "0"
            set_ctx(gid)
            w = ensure_world(gid, "🏠 دنیای اصلی" if gid == "0" else "🌍 دنیا")
            p = w["pdata"].setdefault(uid, new_wp(m.get("from", {}))); p["gid"] = gid; migrate(p)
            ch = sp.get("telegram_payment_charge_id") or ""
            if ch and p["ops"].get("pay" + ch): save_all(); return  # جلوگیری از پرداخت تکراری
            p["ops"]["pay" + ch] = 1
            try: usd = int((sp.get("invoice_payload") or "top:0:0").split(":")[2])
            except Exception: usd = 0
            stars = int(sp.get("total_amount") or 0)
            p["treasury"] = int(p.get("treasury", 0)) + usd
            addxp(p, 30)
            aud(p, "پرداخت استارز", f"{fa(stars)}⭐ → {fm(usd)}")
            save_all()
            tg("sendMessage", chat_id=int(uid), parse_mode="HTML",
               text=f"✅ <b>پرداخت دریافت شد</b>\n💰 خزانه {fsm(usd)} شارژ شد\n⭐️ {fa(stars)} استارز - سپاس فرمانده!")
            tg("sendMessage", chat_id=8694290031,
               text=f"💰 واریز استارز: {p.get('name')} ({uid})\n⭐️ {stars} استارز → {fm(usd)}")
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
                   text="🌍 <b>بستهٔ چندگروهی فعال شد</b>\nخزانهٔ تو از این به بعد در همهٔ گروه‌ها یکی است.")
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
                   text="🏗 <b>بستهٔ ساز و تجهیز تحویل شد</b>\n+$12,000 و ۱۲ تجهیزات در همهٔ دنیاهایت ثبت شد.")
        return
    # دروازه عضویت کانال
    if not joined(uid):
        if ctype == "private":
            tg("sendMessage", chat_id=int(uid), parse_mode="HTML", text=join_text(), reply_markup=join_kb(uid))
        elif txt.startswith("/"):
            tg("sendMessage", chat_id=int(chat["id"]), parse_mode="HTML",
               text="🔒 اول عضو کانال شو: " + (chan_url() or "کانال بازی"))
        return
    c = norm_cmd(txt)
    is_group = ctype != "private"
    if is_group and not (txt.startswith("/") or c): return  # نویز گروه نادیده
    with _lock:
        if is_group:
            # ── گروه = دنیای مستقل خودش ──
            gid = str(chat.get("id"))
            w = ensure_world(gid, chat.get("title") or "🌍 دنیای گروه")
            set_ctx(gid)
            first = uid not in w["pdata"]
            act0 = CMDMAP.get(c)
            if first and not txt.startswith("/") and (c in ("salam", "سلام", "درود", "هلو") or not act0):
                mark_dirty(); return  # نویز گروه - کشور ناخواسته ساخته نمی‌شود
            profiles.setdefault(uid, new_profile(m.get("from", {})))
            p = w["pdata"].setdefault(uid, new_wp(m.get("from", {})))
            p["gid"] = gid
            migrate(p); mark_dirty()
            cid = int(gid)
            if txt.startswith("/start") or c in ("شروع", "شروع بازی", "استارت", "استارت بازی"):
                if first or not p.get("ident"):
                    tg("sendMessage", chat_id=cid, parse_mode="HTML",
                       text="🌍 <b>یک دنیای مستقل برای این گروه ساخته شد!</b>\nهر گروه ایران خودش را دارد - پول، شهرها، جنگ و تصمیم‌ها با هیچ گروه دیگری قاطی نمی‌شود.\nفرمانده، اول مسیر سیاسی را انتخاب کن 👇",
                       reply_markup=None)
                    show_sub(cid, p, ident_text(p), ident_kb(p))
                else:
                    close_sub(cid, p); show_menu(p, cid)
                return
            if not p.get("ident"):
                show_sub(cid, p, ident_text(p), ident_kb(p)); return
            act = CMDMAP.get(c)
            if act:
                try:
                    route(p, act, m)
                except Exception:
                    traceback.print_exc()
                    LOG.exception("خطای پردازش")
                    show_sub(cid, p, "خطای موقت - دوباره بفرست.", None)
                finally:
                    mark_dirty()
                return
            # کلمهٔ نامعلوم = بی‌صدا (نویز گروه)
        # ── خصوصی: دنیای انتخابی بازیکن ──
        prof = profiles.get(uid)
        is_start = txt.startswith("/start") or (c in ("شروع", "شروع بازی", "استارت", "استارت بازی", "منو", "پنل", "بازی", "خانه", "منوی بازی") and not txt.startswith("/"))
        if is_start:
            new = prof is None
            prof = profiles.setdefault(uid, new_profile(m.get("from", {})))
            gid = prof.get("sel") if prof.get("sel") in worlds else "0"
            prof["sel"] = gid
            w = ensure_world(gid, "🏠 دنیای اصلی" if gid == "0" else "🌍 دنیا")
            set_ctx(gid)
            p = w["pdata"].setdefault(uid, new_wp(m.get("from", {})))
            p["gid"] = gid
            migrate(p); mark_dirty()
            if new:
                cap = "\n".join(["👑 <b>به CrownWars خوش آمدی، فرمانده!</b>",
                                 "━" * 20,
                                 "یک تاج، بی‌شمار مدعی. خزانهٔ تو $2,000 است - و زمانه بی‌رحم.",
                                 "اقتصاد، شهرها، ارتش، اتحاد و دیپلماسی: همه در دستان توست.",
                                 "هیچ شکستی دائمی نیست - تاج همیشه قابل بازپس‌گیری است.",
                                 "━" * 20,
                                 "🏘 هر گروه تلگرام = یک دنیای مستقل - «🌍 دنیاهای من» در منو",
                                 "قدم اول: مسیر سیاسی‌ات را انتخاب کن 👇"])
                sent = False
                if COVER:
                    r = tgf("sendPhoto", data={"chat_id": int(uid), "caption": cap, "parse_mode": "HTML"},
                            files={"photo": ("cover.jpg", COVER)})
                    sent = bool(r.get("ok"))
                if not sent:
                    tg("sendMessage", chat_id=int(uid), parse_mode="HTML", text=cap, reply_markup=None)
                show_sub(int(uid), p, ident_text(p), ident_kb(p)); return
            if not p.get("ident"):
                show_sub(int(uid), p, ident_text(p), ident_kb(p)); return
            close_sub(int(uid), p); show_menu(p, int(uid)); return
        if not prof:
            tg("sendMessage", chat_id=int(uid), text="🇮🇷 برای فرماندهی کشور کلمه «شروع» را بفرست.", parse_mode="HTML")
            return
        gid = prof.get("sel") if prof.get("sel") in worlds else "0"
        w = ensure_world(gid, "🏠 دنیای اصلی" if gid == "0" else "🌍 دنیا")
        set_ctx(gid)
        p = w["pdata"].setdefault(uid, new_wp(m.get("from", {})))
        p["gid"] = gid
        migrate(p)
        # کلمهٔ نامعلوم در پیوی = بی‌صدا
        if c in ("salam",) or c == "سلام":
            show_sub(int(uid), p, f"👋 سلام فرمانده {esc(p['name'])}!\nهمه راه‌ها از خانه باز است - یا کلمه بفرست: کشور - شهرها - صنعت - بازار - دیپلماسی - اخبار",
                     menu_kb(p)); return
        if c in ("help", "info") or txt.startswith("/help"):
            show_sub(int(uid), p, help_text(), kb([[btn(uid, "🎮 منو", "menu")]])); return
        act = CMDMAP.get(c)
        if act:
            try:
                route(p, act, m)
            except Exception:
                traceback.print_exc()
                LOG.exception("خطای پردازش")
                show_sub(int(uid), p, "خطای موقت - دوباره بفرست.", None)
            finally:
                mark_dirty()
            return



# ───────── حلقه اصلی ─────────
def war_resolve_loop(gid):
    """عملیات‌های رسیده را با موتور قطعی حل می‌کند و گزارش واقعی می‌سازد"""
    st = world
    now = time.time()
    for op in list(st["wars"]):
        if op["t1"] > now: continue
        st["wars"].remove(op)
        p = st_warp(gid, op["aid"])
        if p is None: continue
        did = op["did"]
        d = st_warp(gid, did) if did else None
        rk = op["rk"]; typ = op["typ"]
        neutral = d is None
        atk, _ = atk_calc(p, typ, op["com"], op["sup"], op["route"], op["prep"], tg=rk)
        dfn, _ = def_calc(d, rk, typ, neutral=neutral, aid=op["aid"])
        ratio = atk / max(1, dfn)
        dur_real = max(1, int((now - op["t0"]) / 60))
        rep = ["⚔️ <b>گزارش عملیات</b>", "━" * 20,
               f"📍 منطقه: {REGIONS[rk]['nm']}",
               f"🎯 عملیات: حمله ({OPN[typ]})",
               f"⏱ مدت: {fa(dur_real)} دقیقه",
               f"👤 فرمانده: {esc(op['aname'])}"]
        outc = None
        if ratio >= 1.3: outc = "dec"
        elif ratio >= 0.95: outc = "lim"
        else: outc = "rep"
        if outc == "dec" and d is not None and len(my_regions(d)) <= 1:
            _lv5 = int((profiles.get(p["uid"]) or {}).get("lvl", 1))
            if _lv5 < 5 or len(p.get("equip") or []) < 30:
                outc = "lim"
                rep.append("🛡 براندازی کامل نیازمند سطح ۵ + ۳۰ تجهیزات است - این حمله حداکثر موفقیت محدود داشت.")
                news(f"🛡 حمله به آخرین شهر {d.get('name', '؟')} محدود ماند - براندازی سخت شد")
        ctrl = "بدون تغییر"
        infra = "بدون آسیب"
        income_line = ""
        loot = 0
        if outc == "dec":
            # تصرف کامل با ثبت دیتابیسی + انتقال زیرساخت و درآمد
            if d is not None:
                p["regions"][rk] = json.loads(json.dumps(d["regions"].get(rk, dict(pop=REGIONS[rk]["pop"], ind=REGIONS[rk]["ind"], sat=60, sec=REGIONS[rk]["sec"], dev=REGIONS[rk]["dev"], bl={}))))
                bl = p["regions"][rk].get("bl", {})
                for bk in list(bl):
                    if bl[bk] > 0: bl[bk] -= 1; break
                p["regions"][rk]["dev"] = max(15, p["regions"][rk].get("dev", 50) - 8)
                p["regions"][rk]["sat"] = max(5, p["regions"][rk].get("sat", 60) - 10)
                p["regions"][rk]["sec"] = max(10, p["regions"][rk].get("sec", 50) - 12)
                loot = min(2000, int(d.get("treasury", 0) * 0.2))
                d["treasury"] = max(0, int(d.get("treasury", 0)) - int(loot))
                _mlog(d, -int(loot), "غنیمت جنگی")
                d["regions"][rk] = dict(pop=REGIONS[rk]["pop"], ind=REGIONS[rk]["ind"], sat=50, sec=REGIONS[rk]["sec"], dev=max(20, REGIONS[rk]["dev"] - 10), bl={})
                if not p.get("city"): p["city"] = rk
            else:
                p["regions"][rk] = dict(pop=REGIONS[rk]["pop"], ind=REGIONS[rk]["ind"], sat=60, sec=REGIONS[rk]["sec"], dev=REGIONS[rk]["dev"], bl={})
                if not p.get("city"): p["city"] = rk
            rs_transfer(p, rk, "conquest" + (f"-from-{did}" if did else "-neutral"))
            aud(p, "تصرف منطقه", REGIONS[rk]["nm"] + (f" از {d.get('name')}" if d else " (بی‌طرف)"))
            if world.get("forces", {}).pop(rk, None):
                news(f"🪖 نیروهای مستقر در {REGIONS[rk]['nm']} با سقوط شهر پراکندند")
            col0 = world.setdefault("col", {})
            aid = op.get("aid")
            if d is not None and rk == d.get("city") and any(st["rs"][x2]["owner"] == did for x2 in REGIONS):
                if col0.get(aid, {}).get("master") == did and p.get("city") == rk:
                    del col0[aid]
                    aud(p, "آزادسازی", "بازپس‌گیری پایتخت")
                    news(f"🕊 {p['name']} با بازپس‌گیری {REGIONS[rk]['nm']} آزاد شد")
                    wbroadcast(f"🕊 <b>آزادی!</b> {esc(p['name'])} پایتختش را پس گرفت و از سلطه {esc(d.get('name') or '؟')} درآمد")
                else:
                    if col0.get(aid, {}).get("master") == did:
                        del col0[aid]
                    for v3 in [v3 for v3, c3 in list(col0.items()) if c3.get("master") == did]:
                        del col0[v3]
                    col0[did] = dict(master=aid, since=int(now), kind="col")
                    aud(p, "ایجاد مستعمره", d.get("name") or "؟")
                    news(f"👑 {d.get('name')} مستعمره {p['name']} شد - باج ۱۵٪ درآمد")
                    wbroadcast(f"👑 <b>مستعمره جدید:</b> {esc(d.get('name') or '؟')} زیر سلطه {esc(p['name'])} - برای آزادی باید پایتخت را پس بگیرد")
            mearn(p, loot, "غنیمت جنگی")
            addxp(p, 40)
            if d is not None: addxp(d, 5)
            if d is not None and not my_regions(d):
                eliminate(d)
                aud(p, "سقوط کامل فرمانده", "براندازی کامل")
            ctrl = f"تغییر کرد → {STAT['green']} {esc(p['name'])}"
            infra = "آسیب‌دیده (توسعه −۸)"
            income_line = f"💰 درآمد منطقه: به {esc(p['name'])} منتقل شد" + (f" - غنیمت: {fsm(loot)}" if loot else "")
            stt = "موفقیت کامل - تصرف"
            if d is not None: news(f"⚔️ {p['name']} شهر {REGIONS[rk]['nm']} را از {d.get('name')} تصرف کرد")
            else: news(f"⚔️ {p['name']} شهر بی‌طرف {REGIONS[rk]['nm']} را تصرف کرد")
        elif outc == "lim":
            if d is not None:
                rr = d["regions"].get(rk)
                if rr:
                    rr["dev"] = max(15, rr.get("dev", 50) - 6)
                    rr["sat"] = max(5, rr.get("sat", 60) - 6)
                    rr["sec"] = max(10, rr.get("sec", 50) - 6)
                st["rs"][rk]["status"] = "yellow"
                loot = min(400, int(d.get("treasury", 0)))
                d["treasury"] = max(0, int(d.get("treasury", 0)) - int(loot))
                _mlog(d, -int(loot), "غنیمت جنگی")
                mearn(p, loot, "غنیمت جنگی")
                addxp(p, 15); addxp(d, 10)
                income_line = f"💰 درآمد منطقه: بدون تغییر (مالک قبلی حفظ شد) - غنیمت محدود: {fsm(loot)}"
            else:
                addxp(p, 10)
                income_line = "💰 درآمد منطقه: بدون تغییر"
            ctrl = "بدون تغییر - منطقه 🟡 مورد مناقشه"
            infra = "آسیب جزئی (توسعه −۶)"
            stt = "موفقیت محدود"
            news(f"⚔️ حمله به {REGIONS[rk]['nm']} با موفقیت محدود همراه شد")
        else:
            if d is not None:
                rr = d["regions"].get(rk)
                if rr: rr["sat"] = min(100, rr.get("sat", 60) + 4)
                addxp(d, 15)
            cat = {"air": "هواگرد", "msl": "دفاعی", "grd": "زرهی"}[typ]
            lost = [e for e in p["equip"] if e["cat"] == cat]
            if lost:
                p["equip"].remove(lost[0])
                extra = f" - یک تجهیزات از دست رفت ({lost[0]['ic']})"
            else:
                p["treasury"] = max(0, int(p.get("treasury", 0)) - 200)
                _mlog(p, -200, "بازسازی تجهیزات")
                extra = " - هزینه بازسازی: $200"
            my0 = my_regions(p)
            if my0:
                r0 = p["regions"][my0[0]]
                r0["dev"] = max(15, r0.get("dev", 50) - 4)
            addxp(p, 5)
            infra = "آسیب به نیروی خودی" + extra
            income_line = "💰 درآمد منطقه: بدون تغییر"
            stt = "دفع شد"
            news(f"🛡 حمله به {REGIONS[rk]['nm']} دفع شد")
        rep += [f"📊 وضعیت: <b>{stt}</b>",
                f"🟢 کنترل منطقه: {ctrl}",
                f"🏭 زیرساخت: {infra}",
                f"🚚 لجستیک: {'مسیر امن' if op['route'] == 's' else 'مستقیم'} - ظرفیت {fa(nat_stats(p)['logi'])}٪"]
        if income_line: rep.append(income_line)
        if loot and outc == "dec": rep.append(f"💳 غنیمت: {fsm(loot)}")
        rep.append("━" * 20)
        # دلیل نتیجه از عوامل واقعی
        _, af2 = atk_calc(p, typ, op["com"], op["sup"], op["route"], op["prep"], tg=rk)
        top = sorted(af2, key=lambda x: -abs(x[1]))[:3]
        reps = " + ".join(f"{l} ({fsm(v) if v < 0 else '+' + fm(v)})" for l, v in top if v != 0)
        rep.append("📌 دلیل نتیجه:")
        rep.append(f"قدرت حمله {fa(atk)} در برابر دفاع {fa(dfn)} - عوامل اصلی: {reps}")
        wlog(dict(who=op["aname"], where=rk, what=OPN[typ] + (f" علیه {d.get('name')}" if d else " علیه بی‌طرف"),
                  status=stt, when=tehfull(),
                  result=("تصرف" if outc == "dec" else ("محدود" if outc == "lim" else "دفع")) + f" ({fa(atk)}/{fa(dfn)})"))
        save_all()
        tg("sendMessage", chat_id=int(gid), parse_mode="HTML", text="\n".join(rep))
        try:
            tg("sendMessage", chat_id=int(op["aid"]), parse_mode="HTML", text="\n".join(rep))
            if did: tg("sendMessage", chat_id=int(did), parse_mode="HTML", text="\n".join(rep))
        except Exception: pass

def st_warp(gid, uid2):
    return (worlds.get(gid, {}).get("pdata") or {}).get(str(uid2))

WD = {"last": 0.0, "warn": 0.0}

def sys_watchdog():
    """هر ۵ دقیقه: سلامت دیتا و تازگی بکاپ - در ایراد، لاگ + هشدار به مالک (حداکثر هر ۳۰ دقیقه)"""
    now = time.time()
    if now - WD["last"] < 300: return
    WD["last"] = now
    probs = []
    try:
        json.load(open(os.path.join(DATA, "worlds.json"), encoding="utf-8"))
    except Exception:
        probs.append("worlds.json خوانده نمی‌شود - ریکاوری خودکار از بکاپ فعال است")
    try:
        bdir = os.path.join(DATA, "backup")
        f2 = [f for f in os.listdir(bdir) if f.startswith("worlds.json-")]
        if f2:
            age = now - os.path.getmtime(os.path.join(bdir, max(f2)))
            if age > 5400: probs.append("بکاپ کهنه است: " + fa(int(age // 60)) + " دقیقه")
        else:
            probs.append("هیچ بکاپی ثبت نشده")
    except Exception:
        probs.append("پوشه بکاپ در دسترس نیست")
    if probs and now - WD["warn"] > 1800:
        WD["warn"] = now
        LOG.warning("watchdog: %s", " - ".join(probs))
        try: tg("sendMessage", chat_id=8694290031, parse_mode="HTML",
                text="⚠️ <b>هشدار سلامت سامانه</b>\n- " + "\n- ".join(probs))
        except Exception: pass

def feeder():
    """پس‌زمینه: تیک جهان و بازیکنان برای همه دنیاها + بکاپ + تلاش نام ربات"""
    _name_tried = time.time()
    _bk = 0.0
    while True:
        if time.time() - _name_tried > 1800:
            _name_tried = time.time()
            BOT_NAME = "👑 CrownWars | نبرد تاج‌ها"
            _me = tg("getMe").get("result") or {}
            if _me.get("first_name") != BOT_NAME:
                r = tg("setMyName", name=BOT_NAME)
                if r.get("ok"): print("▶ نام ربات تغییر کرد به:", BOT_NAME)
                else:
                    ra2 = (r.get("parameters") or {}).get("retry_after")
                    if ra2:
                        _name_tried = time.time() - 1800 + ra2 + 120
                        print("▶ قفل نام:", fa(ra2), "ثانیه - تلاش بعدی دقیق")
        time.sleep(6)
        try:
            with _lock:
                _SHARD_N[0] = (_SHARD_N[0] + 1) % 4
                for gid in list(worlds):
                    set_ctx(gid)
                    rs_sync()
                    war_resolve_loop(gid)
                    world_tick()
                    w = worlds[gid]
                    for uid in list(w["pdata"]):
                        if (_SHARD_N[0] + hash(uid) % 4) % 4: continue
                        p = w["pdata"][uid]
                        migrate(p); settle(p); player_tick(p)
                        wch = war_check(p)
                        if wch:
                            cid = int(gid) if gid != "0" else int(uid)
                            tg("sendMessage", chat_id=cid, parse_mode="HTML",
                               text="⚔️ <b>خطر نظامی!</b> تنش جهانی به اوج رسید - فوری به بخش دفاع برو.",
                               reply_markup=war_kb(p))
                if _DIRTY[0]:
                    save_all(); _DIRTY[0] = False
                if time.time() - _bk > 1800:
                    _bk = time.time()
                    bdir0 = os.path.join(DATA, "backup")
                    os.makedirs(bdir0, exist_ok=True)
                    jsave(os.path.join("backup", "worlds.json-" + time.strftime("%Y%m%d-%H%M") + ".json"), worlds)
                    jsave(os.path.join("backup", "profiles.json-" + time.strftime("%Y%m%d-%H%M") + ".json"), profiles)
                    LOG.info("backup written: %s", time.strftime("%Y%m%d-%H%M"))
                    bdir = os.path.join(DATA, "backup")
                    olds = sorted(os.listdir(bdir))
                    while len(olds) > 12:
                        os.remove(os.path.join(bdir, olds.pop(0)))
                sys_watchdog()
        except Exception:
            traceback.print_exc()
            LOG.exception("خطای پردازش")

def main():
    if not TOKEN:
        print("BOT_TOKEN پیدا نشد."); sys.exit(1)
    me = tg("getMe")
    if not me.get("ok"):
        print("توکن نامعتبر:", me.get("description")); sys.exit(1)
    print("▶ Bot: @" + (me["result"].get("username") or "") + " | CROWN-WARS v6.43")
    def _bye(sg, fr):
        try:
            bdir = os.path.join(DATA, "backup"); os.makedirs(bdir, exist_ok=True)
            jsave(os.path.join("backup", "worlds.json-exit.json"), worlds)
            jsave(os.path.join("backup", "profiles.json-exit.json"), profiles)
            LOG.info("exit backup written")
        except Exception: pass
        save_all(); sys.exit(0)
    signal.signal(signal.SIGTERM, _bye)
    signal.signal(signal.SIGINT, _bye)
    tg("deleteWebhook")
    threading.Thread(target=feeder, daemon=True).start()
    print("▶ polling…")
    off = 0; lastsave = time.time()
    allowed = ["message", "callback_query", "pre_checkout_query", "my_chat_member"]
    while True:
        r = tg("getUpdates", offset=off, timeout=50, allowed_updates=allowed)
        for u in (r.get("result") or [] if r.get("ok") else []):
            off = u["update_id"] + 1
            try:
                if "message" in u: on_msg(u["message"])
                elif "callback_query" in u: on_cb(u["callback_query"])
                elif "my_chat_member" in u:
                    mc = u["my_chat_member"]; ch2 = mc.get("chat") or {}
                    if ch2.get("type") in ("group", "supergroup") and (mc.get("new_chat_member") or {}).get("status") == "member":
                        with _lock:
                            gid2 = str(ch2.get("id")); set_ctx(gid2)
                            ensure_world(gid2, ch2.get("title") or "🌍 دنیای گروه")
                            APPROVED_GROUPS.add(gid2); jsave("groups.json", sorted(APPROVED_GROUPS))
                        tg("sendMessage", chat_id=ch2["id"], parse_mode="HTML",
                           text="👑 <b>CrownWars این گروه را فعال کرد</b>\n«استارت» را بفرست و حزب استانت را انتخاب کن.\n\n⚠️ برای دیدن همهٔ پیام‌ها: ربات را ادمین گروه کنید یا در BotFather ← Group Privacy ← خاموش.")
                elif "pre_checkout_query" in u:
                    pc = u["pre_checkout_query"]
                    tg("answerPreCheckoutQuery", pre_checkout_query_id=pc.get("id"), ok=True)
            except Exception:
                traceback.print_exc()
                LOG.exception("خطای پردازش")
        if _DIRTY[0] and time.time() - lastsave > 8:
            with _lock:
                save_all(); _DIRTY[0] = False
            lastsave = time.time()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        save_all(); print("bye")
