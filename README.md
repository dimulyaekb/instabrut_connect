# InstaBrut Connect

Программа для автоматического подключения Instagram-бота к платформе instabrut.ru.

## Как это работает

1. Пользователь скачивает программу с сайта instabrut.ru
2. Запускает — открывается браузер с Instagram
3. Входит в свой аккаунт
4. Программа шифрует сессию и отправляет на сервер
5. Бот автоматически подключается

## Сборка

### Windows (.exe)
Сборка через Docker-образ `cdrx/pyinstaller-windows`:
```bash
docker run --rm -v "$(pwd):/src/" cdrx/pyinstaller-windows
```
Готовый .exe в `dist/windows/`.

### Linux
```bash
pip install pyinstaller playwright
playwright install chromium
pyinstaller --onefile --name instabrut_connect instabrut_connect.py
```
Готовый бинарник в `dist/`.

### macOS (.app)
Сборка через GitHub Actions (`.github/workflows/build_macos.yml`):
- `runs-on: macos-latest`
- Автоматически при пуше в master/main
- Артефакт: `InstabrutConnect_macOS.zip`

Или вручную на Mac:
```bash
pip install pyinstaller playwright
playwright install chromium
pyinstaller --onefile --windowed --name "InstabrutConnect" instabrut_connect.py
```

## Для пользователей macOS

Если приложение не открывается — выполните в терминале:
```bash
xattr -cr /путь/к/InstabrutConnect.app
```

## Лицензия

Проприетарное ПО. Все права защищены.
