# -*- coding: utf-8 -*-
"""S17: فیکس تمدید قفل 429 - تلاش مجدد روی قفل‌های طولانی ممنوع + زمان‌بندی دقیق تلاش نام."""
import io

PATH = "bot.py"
src = io.open(PATH, encoding="utf-8").read()
n0 = len(src)

def rep(old, new, tag):
    global src
    assert src.count(old) == 1, "anchor NOT unique/found: " + tag
    src = src.replace(old, new, 1)

# ۱) tg: قفل طولانی (بیش از ۳۰ ثانیه) = هیچ تلاش مجددی (تمدید قفل تلگرام!) - فقط قفل کوتاه انتظار و یک retry
rep('''                ra = (j.get("parameters") or {}).get("retry_after")
                if ra: time.sleep(min(ra, 10)); continue''',
    '''                ra = (j.get("parameters") or {}).get("retry_after")
                if ra:
                    if ra > 30: return j
                    time.sleep(ra + 0.5); continue''', "tg long-429")

# ۲) feeder: اولین تلاش نام ۱۵ دقیقه بعد از استارت + بعد از 429 دقیقا بعد از پایان قفل (+۱۲۰ ثانیه اطمینان)
rep('''    _name_tried = 0
    _bk = 0.0''',
    '''    _name_tried = time.time() - 900
    _bk = 0.0''', "feeder init")
rep('''                r = tg("setMyName", name=BOT_NAME)
                if r.get("ok"): print("▶ نام ربات تغییر کرد به:", BOT_NAME)''',
    '''                r = tg("setMyName", name=BOT_NAME)
                if r.get("ok"): print("▶ نام ربات تغییر کرد به:", BOT_NAME)
                else:
                    ra2 = (r.get("parameters") or {}).get("retry_after")
                    if ra2:
                        _name_tried = time.time() - 1800 + ra2 + 120
                        print("▶ قفل نام:", fa(ra2), "ثانیه - تلاش بعدی دقیق")''', "feeder precise retry")

io.open(PATH, "w", encoding="utf-8").write(src)
print("S17 applied:", n0, "->", len(src), "chars")
