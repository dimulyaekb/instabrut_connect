#!/bin/bash
# Скрипт сборки instabrut_connect.exe через PyInstaller
# Запускать на Windows с установленным Python 3.8+
#
# Установка зависимостей (один раз):
#   pip install pyinstaller playwright
#   playwright install chromium
#
# Сборка:
#   bash build.sh

set -e

echo "=== Сборка instabrut_connect.exe ==="
echo ""

# Проверяем PyInstaller
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo "Установка PyInstaller..."
    pip install pyinstaller
fi

echo "Сборка .exe..."
pyinstaller \
    --onefile \
    --name instabrut_connect \
    --hidden-import playwright \
    --hidden-import playwright.sync_api \
    --hidden-import urllib.request \
    --noconsole \
    instabrut_connect.py

echo ""
echo "Готово! .exe в папке dist/"
ls -la dist/instabrut_connect.exe 2>/dev/null || echo "(.exe создаётся только при сборке на Windows)"
