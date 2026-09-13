# -*- coding: utf-8 -*-
"""S27: فیکس KeyError 'tr' - سازه‌های نامعتبر از دیتای قدیمی (ربات قبلی) در migrate حذف می‌شوند."""
import io

PATH = "bot.py"
src = io.open(PATH, encoding="utf-8").read()
n0 = len(src)

def rep(old, new, tag):
    global src
    assert src.count(old) == 1, "anchor NOT unique/found: " + tag
    src = src.replace(old, new, 1)

rep('''        r = p["regions"].setdefault(rk, dict(pop=rv["pop"], ind=rv["ind"], sat=60, sec=rv["sec"],
                                             dev=rv["dev"], bl={}))
        if not isinstance(r.get("bl"), dict): r["bl"] = {}''',
    '''        r = p["regions"].setdefault(rk, dict(pop=rv["pop"], ind=rv["ind"], sat=60, sec=rv["sec"],
                                             dev=rv["dev"], bl={}))
        if not isinstance(r.get("bl"), dict): r["bl"] = {}
        for bk2 in [k for k in r["bl"] if k not in BUILDS or r["bl"][k] is None]:
            del r["bl"][bk2]''', "migrate bl sanitize")

io.open(PATH, "w", encoding="utf-8").write(src)
print("S27 applied:", n0, "->", len(src), "chars")
