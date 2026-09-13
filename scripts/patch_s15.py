# -*- coding: utf-8 -*-
"""S15: ۶ تسلیحات ایرانی دیگر (تحقیق: فتاح-۱ هایپرسونیک، عماد 1700km، سجیل جامد 2000-2500km،
قیام-1 700-800km، شاهد-136 انتحاری بال دلتا، گزا 2000km)."""
import io

PATH = "bot.py"
src = io.open(PATH, encoding="utf-8").read()
n0 = len(src)

def rep(old, new, tag):
    global src
    assert src.count(old) == 1, "anchor NOT unique/found: " + tag
    src = src.replace(old, new, 1)

rep(''' dict(nm="پهپاد ابابیل-۳", ic="🛩️", cat="هواگرد", price=800,  de=4,  rec=5, lg=1, q=3, mins=30, up=15),
]''',
    ''' dict(nm="پهپاد ابابیل-۳", ic="🛩️", cat="هواگرد", price=800,  de=4,  rec=5, lg=1, q=3, mins=30, up=15),
 dict(nm="موشک فتاح-۱", ic="🚀", cat="موشکی", price=3200, de=8,  rec=2, lg=1, q=5, mins=110, up=55),
 dict(nm="موشک عماد", ic="🚀", cat="موشکی", price=2900, de=7,  rec=2, lg=1, q=5, mins=95, up=50),
 dict(nm="موشک سجیل", ic="🚀", cat="موشکی", price=3100, de=8,  rec=1, lg=1, q=5, mins=105, up=55),
 dict(nm="موشک قیام-۱", ic="🚀", cat="موشکی", price=1400, de=5,  rec=0, lg=1, q=3, mins=45, up=25),
 dict(nm="پهپاد شاهد-۱۳۶", ic="🛩️", cat="هواگرد", price=1100, de=6,  rec=1, lg=0, q=4, mins=45, up=20),
 dict(nm="پهپاد گزا", ic="🛩️", cat="هواگرد", price=2100, de=3,  rec=8, lg=0, q=4, mins=60, up=30),
]''', "EQUIP s15")

io.open(PATH, "w", encoding="utf-8").write(src)
print("S15 applied:", n0, "->", len(src), "chars")
