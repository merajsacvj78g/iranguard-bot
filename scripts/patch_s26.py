# -*- coding: utf-8 -*-
"""S26: موتور سرعت - ذخیرهٔ کثیف‌پرچم (خروج از مسیر فرمان)، ذخیرهٔ اصلی زیر قفل هر ۸ ثانیه، تیک شاردینگ‌شدهٔ بازیکنان (÷۴)."""
import io

PATH = "bot.py"
src = io.open(PATH, encoding="utf-8").read()
n0 = len(src)

def rep(old, new, tag, cnt=1):
    global src
    assert src.count(old) == cnt, f"anchor {tag}: {src.count(old)} != {cnt}"
    src = src.replace(old, new, cnt)

# ── ۱) پرچم کثیف سراسری
rep('''def save_all():''',
    '''_DIRTY = [False]
_SHARD_N = [0]

def mark_dirty():
    """تغییرات در حافظه ثبت شد - ذخیرهٔ دیسک دسته‌ای و زیر قفل (مسیر فرمان هرگز منتظر دیسک نمی‌ماند)"""
    _DIRTY[0] = True

def save_all():''', "dirty flag")

# ── ۲) مسیر فرمان: هیچ ذخیرهٔ دیسکی هم‌زمان با پاسخ بازیکن
rep('''                save_all(); return  # نویز گروه - کشور ناخواسته ساخته نمی‌شود''',
    '''                mark_dirty(); return  # نویز گروه - کشور ناخواسته ساخته نمی‌شود''', "noise path")
rep('''            migrate(p); save_all()
            cid = int(gid)''',
    '''            migrate(p); mark_dirty()
            cid = int(gid)''', "group join")
rep('''                finally:
                    save_all()
                return
            if not txt.startswith("/"):
                tg("sendMessage", chat_id=cid, parse_mode="HTML",''',
    '''                finally:
                    mark_dirty()
                return
            if not txt.startswith("/"):
                tg("sendMessage", chat_id=cid, parse_mode="HTML",''', "group cmd finally")
rep('''            migrate(p); save_all()
            if new:''',
    '''            migrate(p); mark_dirty()
            if new:''', "private join")
rep('''            finally:
                save_all()
            return
        tg("sendMessage", chat_id=int(uid), parse_mode="HTML",
           text="🤔 این را نمی‌شناسم.''',
    '''            finally:
                mark_dirty()
            return
        tg("sendMessage", chat_id=int(uid), parse_mode="HTML",
           text="🤔 این را نمی‌شناسم.''', "private cmd finally")

# ── ۳) فیدر: تیک شاردینگ‌شده (۱/۴ بازیکنان در هر گذر - درآمد زمان‌محور دقیق می‌ماند) + ذخیرهٔ شرطی
rep('''                for gid in list(worlds):
                    set_ctx(gid)
                    rs_sync()
                    war_resolve_loop(gid)
                    world_tick()
                    w = worlds[gid]
                    for uid in list(w["pdata"]):
                        p = w["pdata"][uid]''',
    '''                _SHARD_N[0] = (_SHARD_N[0] + 1) % 4
                for gid in list(worlds):
                    set_ctx(gid)
                    rs_sync()
                    war_resolve_loop(gid)
                    world_tick()
                    w = worlds[gid]
                    for uid in list(w["pdata"]):
                        if (_SHARD_N[0] + hash(uid) % 4) % 4: continue
                        p = w["pdata"][uid]''', "shard tick")
rep('''                save_all()
                if time.time() - _bk > 1800:''',
    '''                if _DIRTY[0]:
                    save_all(); _DIRTY[0] = False
                if time.time() - _bk > 1800:''', "feeder conditional save")

# ── ۴) ذخیرهٔ خودکار حلقهٔ اصلی: فقط وقتی کثیف، هر ۸ ثانیه، زیر قفل
rep('''        if time.time() - lastsave > 45:
            save_all(); lastsave = time.time()''',
    '''        if _DIRTY[0] and time.time() - lastsave > 8:
            with _lock:
                save_all(); _DIRTY[0] = False
            lastsave = time.time()''', "main autosave dirty")

io.open(PATH, "w", encoding="utf-8").write(src)
print("S26 applied:", n0, "->", len(src), "chars")
