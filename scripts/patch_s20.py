# -*- coding: utf-8 -*-
"""S20: منوی اصلی دوصفحه‌ای با رنگ‌بندی یکدست بخش‌ها (دایره‌های استاندارد - تلگرام در دکمه فقط ایموجی استاندارد رندر می‌کند؛ پرمیوم‌ها در متن‌ها با pe() حفظ شد)."""
import io

PATH = "bot.py"
src = io.open(PATH, encoding="utf-8").read()
n0 = len(src)

def rep(old, new, tag):
    global src
    assert src.count(old) == 1, "anchor NOT unique/found: " + tag
    src = src.replace(old, new, 1)

rep('''def menu_kb(p, page=1):
    u = p["uid"]
    rows = []
    if p.get("decision"): rows.append([btn(u, "🗳️ تصمیم ملی در انتظار تو!", "dec")])
    if p.get("war"): rows.append([btn(u, "⚔️ خطر نظامی - فوری!", "war")])
    rows += [
        [btn(u, "🇮🇷 کشور", "country"), btn(u, "💰 اقتصاد", "eco")],
        [btn(u, "🏭 صنعت", "ind"), btn(u, "⛏ منابع", "res")],
        [btn(u, "🏗 توسعه", "prj"), btn(u, "🚚 لجستیک", "log")],
        [btn(u, "🛡 دفاع", "de"), btn(u, "⚔️ عملیات", "ops")],
        [btn(u, "🤝 دیپلماسی", "dip"), btn(u, "🌍 جهان", "world")],
        [btn(u, "📈 بازار", "mkt"), btn(u, "🧠 فناوری", "tech")],
        [btn(u, "⚠️ بحران", "crisis"), btn(u, "📰 اخبار", "news")],
        [btn(u, "🏆 رتبه‌بندی", "rank"), btn(u, "⚙️ تنظیمات", "set")],
        [btn(u, "🧠 دستیار", "asz"), btn(u, "🤝 فرماندهان", "cmdr")],
        [btn(u, "🌍 دنیاهای من", "wlds")]]
    return kb(rows)''',
    '''def menu_kb(p, page=1):
    """منوی دوصفحه‌ای - رنگ هر بخش در همه صفحات یکسان:
    🟢 اقتصاد/بازار - 🟣 صنعت/توسعه/فناوری - 🟡 منابع/لجستیک
    🔴 دفاع/عملیات/بحران - 🔵 دیپلماسی/فرماندهان/جهان - 🟠 دستیار/رتبه - ⚪ سایر"""
    u = p["uid"]
    rows = []
    if p.get("decision"): rows.append([btn(u, "🗳️ تصمیم ملی در انتظار تو!", "dec")])
    if p.get("war"): rows.append([btn(u, "⚔️ خطر نظامی - فوری!", "war")])
    if page == 2:
        rows += [
            [btn(u, "🔴 دفاع", "de"), btn(u, "🔴 عملیات", "ops")],
            [btn(u, "🔴 بحران", "crisis"), btn(u, "🔵 دیپلماسی", "dip")],
            [btn(u, "🔵 فرماندهان", "cmdr"), btn(u, "🔵 جهان", "world")],
            [btn(u, "🟠 دستیار", "asz"), btn(u, "🟠 رتبه‌بندی", "rank")],
            [btn(u, "⚪ اخبار", "news"), btn(u, "⚙️ تنظیمات", "set")],
            [btn(u, "🌍 دنیاهای من", "wlds")],
            [btn(u, "◀️ مدیریت", "mnu:1"), btn(u, "🏠 خانه", "menu")]]
    else:
        rows += [
            [btn(u, "🇮🇷 کشور", "country"), btn(u, "🟢 اقتصاد", "eco")],
            [btn(u, "🟢 بازار", "mkt"), btn(u, "🟣 صنعت", "ind")],
            [btn(u, "🟡 منابع", "res"), btn(u, "🟡 لجستیک", "log")],
            [btn(u, "🟣 توسعه", "prj"), btn(u, "🟣 فناوری", "tech")],
            [btn(u, "⚙️ قدرت و جهان ▶️", "mnu:2"), btn(u, "🏠 خانه", "menu")]]
    return kb(rows)''', "menu_kb pages")

rep('''    if act == "menu": show_menu(p, cid); return''',
    '''    if act == "menu": show_menu(p, cid); return
    if act.startswith("mnu:"):
        pg = int(act.split(":")[1]) if act.split(":")[1] in ("1", "2") else 1
        show_sub(cid, p, menu_text(p), menu_kb(p, pg)); return''', "mnu handler")

io.open(PATH, "w", encoding="utf-8").write(src)
print("S20 applied:", n0, "->", len(src), "chars")
