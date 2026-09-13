# -*- coding: utf-8 -*-
"""S22: گروه‌های تاییدشدهٔ مالک (groups.json) + خروج امنیتی از گروه ناشناس - هیچ لیست سیاهی نیست؛ همه خوب‌اند."""
import io

PATH = "bot.py"
src = io.open(PATH, encoding="utf-8").read()
n0 = len(src)

def rep(old, new, tag):
    global src
    assert src.count(old) == 1, "anchor NOT unique/found: " + tag
    src = src.replace(old, new, 1)

# ۱) فهرست گروه‌های تاییدشده (ماندگار)
rep('''profiles = jload("profiles.json", {})''',
    '''profiles = jload("profiles.json", {})
APPROVED_GROUPS = set(jload("groups.json", []))
OWNER_ID = "8694290031"''', "approved groups")

# ۲) گیت گروه در on_msg - بعد از فلود
rep('''    if flooded(uid): return
    sp = m.get("successful_payment")''',
    '''    if flooded(uid): return
    if ctype in ("group", "supergroup"):
        gid0 = str(chat.get("id"))
        if gid0 not in APPROVED_GROUPS:
            if uid == OWNER_ID:
                APPROVED_GROUPS.add(gid0); jsave("groups.json", sorted(APPROVED_GROUPS))
                tg("sendMessage", chat_id=chat["id"], parse_mode="HTML",
                   text="✅ <b>این گروه توسط مالک تایید شد</b>\\n🌍 دنیای مستقل همین گروه فعال است - «شروع» بزن.")
            else:
                tg("sendMessage", chat_id=chat["id"], parse_mode="HTML",
                   text="🛡 <b>خروج امنیتی</b>\\n❗️ این گروه در فهرست تاییدشدهٔ مالک نیست.\\nربات فقط در گروه‌های تاییدشدهٔ مالک می‌ماند.\\n👈 مالک در همین گروه پیام دهد تا تایید شود.")
                tg("leaveChat", chat_id=chat["id"])
            return
    sp = m.get("successful_payment")''', "group gate")

# ۳) اشاره فارسی به‌جای اسلش
rep('''            tg("sendMessage", chat_id=int(uid), text="🇮🇷 برای فرماندهی کشور /start بزن.", parse_mode="HTML")''',
    '''            tg("sendMessage", chat_id=int(uid), text="🇮🇷 برای فرماندهی کشور کلمه «شروع» را بفرست.", parse_mode="HTML")''', "persian start hint")

io.open(PATH, "w", encoding="utf-8").write(src)
print("S22 applied:", n0, "->", len(src), "chars")
