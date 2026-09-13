# -*- coding: utf-8 -*-
"""S24: مهاجرت کامل به ربات جدید - تایید خودکار گروه توسط ادمین/مالک + خوش‌آمد با my_chat_member + راهنمای Privacy."""
import io

PATH = "bot.py"
src = io.open(PATH, encoding="utf-8").read()
n0 = len(src)

def rep(old, new, tag):
    global src
    assert src.count(old) == 1, "anchor NOT unique/found: " + tag
    src = src.replace(old, new, 1)

# ۱) گیت گروه: ادمین/سازندهٔ گروه هم می‌تواند تایید کند (مهاجرت به هر گروهی بدون فرکشن)
rep('''    if ctype in ("group", "supergroup"):
        gid0 = str(chat.get("id"))
        if gid0 not in APPROVED_GROUPS:
            if uid == OWNER_ID:
                APPROVED_GROUPS.add(gid0); jsave("groups.json", sorted(APPROVED_GROUPS))
                tg("sendMessage", chat_id=chat["id"], parse_mode="HTML",
                   text="✅ <b>این گروه توسط مالک تایید شد</b>\\n🌍 دنیای مستقل همین گروه فعال است - «شروع» بزن.")
            else:''',
    '''    if ctype in ("group", "supergroup"):
        gid0 = str(chat.get("id"))
        if gid0 not in APPROVED_GROUPS:
            _st2 = ((tg("getChatMember", chat_id=chat["id"], user_id=int(uid)).get("result") or {}).get("status") or "")
            if uid == OWNER_ID or _st2 in ("creator", "administrator"):
                APPROVED_GROUPS.add(gid0); jsave("groups.json", sorted(APPROVED_GROUPS))
                tg("sendMessage", chat_id=chat["id"], parse_mode="HTML",
                   text="✅ <b>این گروه تایید شد</b>\\n🌍 دنیای مستقل همین گروه فعال است - «استارت» بفرست.\\n\\n⚠️ اگر پیام‌های معمولی دیده نمی‌شوند: ربات را ادمین گروه کنید یا در BotFather حالت Group Privacy را خاموش کنید.")
            else:''', "group gate admin-approve")

# ۲) خوش‌آمد خودکار هنگام اضافه‌شدن ربات (my_chat_member همیشه به بات می‌رسد)
rep('''                if "message" in u: on_msg(u["message"])
                elif "callback_query" in u: on_cb(u["callback_query"])''',
    '''                if "message" in u: on_msg(u["message"])
                elif "callback_query" in u: on_cb(u["callback_query"])
                elif "my_chat_member" in u:
                    mc = u["my_chat_member"]; ch2 = mc.get("chat") or {}
                    if ch2.get("type") in ("group", "supergroup") and (mc.get("new_chat_member") or {}).get("status") == "member":
                        with _lock:
                            gid2 = str(ch2.get("id")); set_ctx(gid2)
                            ensure_world(gid2, ch2.get("title") or "🌍 دنیای گروه")
                            APPROVED_GROUPS.add(gid2); jsave("groups.json", sorted(APPROVED_GROUPS))
                        tg("sendMessage", chat_id=ch2["id"], parse_mode="HTML",
                           text="🇮🇷 <b>ایران‌کالپس این گروه را فعال کرد</b>\\n«استارت» را بفرست و حزب استانت را انتخاب کن.\\n\\n⚠️ برای دیدن همهٔ پیام‌ها: ربات را ادمین گروه کنید یا در BotFather ← Group Privacy ← خاموش.")''', "my_chat_member welcome")

# ۳) دریافت آپدیت my_chat_member
rep('''    allowed = ["message", "callback_query", "pre_checkout_query"]''',
    '''    allowed = ["message", "callback_query", "pre_checkout_query", "my_chat_member"]''', "allowed updates")

io.open(PATH, "w", encoding="utf-8").write(src)
print("S24 applied:", n0, "->", len(src), "chars")
