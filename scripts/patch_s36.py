# -*- coding: utf-8 -*-
# S36: آماده‌سازی دیپلوی - بنر نسخه، راهنمای سیستم‌های تازه
import io

s = io.open("bot.py", encoding="utf-8").read()
REPS = []


def rep(old, new, tag):
    REPS.append((old, new, tag))


# ── ۱) بنر نسخه واقعی ─────────────────────────────────────────────────
rep('''    print("▶ Bot: @" + (me["result"].get("username") or "") + " | IRAN-COLLAPSE v1-0")''',
    '''    print("▶ Bot: @" + (me["result"].get("username") or "") + " | IRAN-COLLAPSE v6.33")''', "banner")

# ── ۲) راهنما: سیستم‌های تازه ─────────────────────────────────────────
rep('''        "💳 پول دلاری: شروع $2,000 - درآمد ساعتی − نگهداری",
        "📈 مسیر رشد: $1,000 → $5,000 → $10,000 → $50,000 → $100,000",''',
    '''        "💳 پول دلاری: شروع $2,000 - درآمد ساعتی − نگهداری",
        "🤲 کمک نوپایی: تا سطح ۳ (حداکثر ۲ شهر) درآمدت زیر $150 در ساعت نمی‌رود",
        "⏰ واریز درآمد هر ساعت، دقیقاً روی ساعت ایران - جزئیات: اقتصاد",
        "⭐️ استارز: شارژ خزانه + بسته‌های ویژه (چندگروهی/حقوق/بهره) - فروشگاه",
        "🎖 اتحاد نظامی: حداکثر ۳ نفر - پیمان ساده نامحدود",
        "📈 مسیر رشد: $1,000 → $5,000 → $10,000 → $50,000 → $100,000",''', "help_new")

ok = True
for old, new, tag in REPS:
    c = s.count(old)
    if c != 1:
        print(f"FAIL {tag}: x{c}")
        ok = False
if not ok:
    raise SystemExit("anchors failed - file untouched")
for old, new, tag in REPS:
    s = s.replace(old, new, 1)
io.open("bot.py", "w", encoding="utf-8").write(s)
print(f"S36 applied: {len(REPS)} replacements")
