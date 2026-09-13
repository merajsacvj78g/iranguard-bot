# -*- coding: utf-8 -*-
"""S17b: سرعت - بازیابی فوری پول در برخورد 409 (کاهش خواب تلاش مجدد + یک تلاش بیشتر)."""
import io

PATH = "bot.py"
src = io.open(PATH, encoding="utf-8").read()
n0 = len(src)

def rep(old, new, tag):
    global src
    assert src.count(old) == 1, "anchor NOT unique/found: " + tag
    src = src.replace(old, new, 1)

rep('''    for _ in range(3):
        try:
            t = (15, 66) if method == "getUpdates" else (15, 30)
            r = requests.post(f"{API}{TOKEN}/{method}", json=kw, timeout=t)
            j = r.json()
            if not j.get("ok"):
                d = str(j.get("description", ""))
                if "message is not modified" in d: return {"ok": True}
                if j.get("error_code") == 409 or "terminated by other getUpdates" in d:
                    time.sleep(1.5); continue''',
    '''    for _ in range(4):
        try:
            t = (15, 66) if method == "getUpdates" else (15, 30)
            r = requests.post(f"{API}{TOKEN}/{method}", json=kw, timeout=t)
            j = r.json()
            if not j.get("ok"):
                d = str(j.get("description", ""))
                if "message is not modified" in d: return {"ok": True}
                if j.get("error_code") == 409 or "terminated by other getUpdates" in d:
                    time.sleep(0.4); continue''', "poll recapture speed")

io.open(PATH, "w", encoding="utf-8").write(src)
print("S17b applied:", n0, "->", len(src), "chars")
