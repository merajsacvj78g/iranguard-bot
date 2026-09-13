# -*- coding: utf-8 -*-
"""S28: سکوت روی کلمات نامعلوم (گروه + پیوی) - قفل مالکیت دکمه از قبل سخت است."""
import io

PATH = "bot.py"
src = io.open(PATH, encoding="utf-8").read()
n0 = len(src)

def rep(old, new, tag):
    global src
    assert src.count(old) == 1, "anchor NOT unique/found: " + tag
    src = src.replace(old, new, 1)

rep('''            if not txt.startswith("/"):
                tg("sendMessage", chat_id=cid, parse_mode="HTML",
                   text="❓ «" + esc(c) + "» دستور بازی نیست - راهنما در پیوی ربات یا دکمه‌های همین پنل.")''',
    '''            # کلمهٔ نامعلوم = بی‌صدا (نویز گروه)''', "group unknown silent")
rep('''        if c and c not in ("salam", "سلام") and c not in CMDMAP and not txt.startswith("/"):
            show_sub(int(uid), p, "❓ این کلمه دستور بازی نیست.\\n\\n" + help_text(), kb([[btn(uid, "🏠 خانه", "menu")]])); return''',
    '''        # کلمهٔ نامعلوم در پیوی = بی‌صدا''', "private unknown silent")

io.open(PATH, "w", encoding="utf-8").write(src)
print("S28 applied:", n0, "->", len(src), "chars")
