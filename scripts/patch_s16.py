# -*- coding: utf-8 -*-
"""S16: ۴ تسلیحات ایرانی دیگر (تحقیق: پاوه 1650km، حویز 1350km، ابو مهدی کروز دریایی، مهاجر-10 2000km/24h)."""
import io

PATH = "bot.py"
src = io.open(PATH, encoding="utf-8").read()
n0 = len(src)

def rep(old, new, tag):
    global src
    assert src.count(old) == 1, "anchor NOT unique/found: " + tag
    src = src.replace(old, new, 1)

rep(''' dict(nm="پهپاد گزا", ic="🛩️", cat="هواگرد", price=2100, de=3,  rec=8, lg=0, q=4, mins=60, up=30),
]''',
    ''' dict(nm="پهپاد گزا", ic="🛩️", cat="هواگرد", price=2100, de=3,  rec=8, lg=0, q=4, mins=60, up=30),
 dict(nm="کروز پاوه", ic="🚀", cat="موشکی", price=2300, de=6,  rec=3, lg=0, q=4, mins=80, up=40),
 dict(nm="کروز حویز", ic="🚀", cat="موشکی", price=2100, de=6,  rec=2, lg=0, q=4, mins=75, up=38),
 dict(nm="کروز دریایی ابو مهدی", ic="🚢", cat="دریایی", price=2400, de=12, rec=4, lg=2, q=4, mins=80, up=45),
 dict(nm="پهپاد مهاجر-۱۰", ic="🛩️", cat="هواگرد", price=1900, de=6,  rec=9, lg=1, q=4, mins=65, up=30),
]''', "EQUIP s16")

io.open(PATH, "w", encoding="utf-8").write(src)
print("S16 applied:", n0, "->", len(src), "chars")
