#!/bin/bash
# نگهبان اجرا - اگر بات به هر دلیل افتاد، ۳ ثانیه بعد برمی‌گردد
cd "$(dirname "$0")"
mkdir -p logs
while true; do
  echo "── $(date '+%F %T') START ──" >> logs/bot.log
  python3 -u bot.py >> logs/bot.log 2>&1
  RC=$?
  echo "── $(date '+%F %T') EXIT($RC) ──" >> logs/bot.log
  sleep 3
done
