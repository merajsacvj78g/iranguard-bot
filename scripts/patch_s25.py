# -*- coding: utf-8 -*-
"""S25: بهبود کلی - فهرست فرمان فارسی کامل + انعطاف نویسه/فاصله + مستعمره/آزادی/دنیاهای من + هشدار نوع اشتباه."""
import io

PATH = "bot.py"
src = io.open(PATH, encoding="utf-8").read()
n0 = len(src)

def rep(old, new, tag):
    global src
    assert src.count(old) == 1, "anchor NOT unique/found: " + tag
    src = src.replace(old, new, 1)

# ── ۱) فرمان‌های بیشتر: مستعمره - آزادم - دنیاهای من - واریز
rep('''"سلام": "salam", "درود": "salam", "هلو": "salam", "راهنما": "help", "کمک": "help"}''',
    '''"مستعمره‌ها": "csl", "مستعمره": "csl", "آزادم": "cfree", "آزادی": "cfree", "دنیاهای من": "wlds", "دنیاها": "wlds",
          "واریز": "stars", "شارژ استارز": "stars", "زرادخانه": "equip", "سلاح": "shop:ru", "جنگ": "war",
          "سلام": "salam", "درود": "salam", "هلو": "salam", "راهنما": "help", "کمک": "help", "دستورها": "help", "دستورات": "help"}''', "cmdmap more")

# ── ۲) norm_cmd انعطاف‌پذیر: چند کلمه‌ای، اعراب، ي/ك، ZWNJ، نقطه‌گذاری انتهایی
rep('''def norm_cmd(txt):
    try:
        t = (txt or "").strip().lstrip("/").strip()
        if not t: return ""
        t = t.split()[0].replace("ي", "ی").replace("ك", "ک").replace("\\u200c", "")
        t = t.split("@")[0]
        return t
    except Exception: return ""''',
    '''def norm_cmd(txt):
    try:
        t = (txt or "").strip().lstrip("/").strip()
        if not t: return ""
        t = t.replace("ي", "ی").replace("ك", "ک").replace("\\u200c", "").replace("\\u064B", "").replace("\\u064C", "").replace("\\u064D", "").replace("\\u064E", "").replace("\\u064F", "").replace("\\u0650", "").replace("\\u0651", "")
        t = t.split("@")[0]
        if t.split()[0] in CMDMAP or t.split()[0].startswith("/"):
            t = t.split()[0]
        else:
            t = " ".join(t.split())   # «دنیاهای من» و مشابه
        return t.strip("!.؟?،,؛:")
    except Exception: return ""''', "norm_cmd flexible")

# ── ۳) نامعلوم → راهنما به‌جای سکوت (هم گروه هم پیوی)
rep('''        if c in ("salam",) or c == "سلام":''',
    '''        if c and c not in ("salam", "سلام") and c not in CMDMAP and not txt.startswith("/"):
            show_sub(int(uid), p, "❓ این کلمه دستور بازی نیست.\\n\\n" + help_text(), kb([[btn(uid, "🏠 خانه", "menu")]])); return
        if c in ("salam",) or c == "سلام":''', "unknown hint")

io.open(PATH, "w", encoding="utf-8").write(src)
print("S25 applied:", n0, "->", len(src), "chars")
