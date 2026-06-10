#!/usr/bin/env python3
"""
InstaBrut Connect — программа для автоматического подключения Instagram-бота.

Использование:
    python instabrut_connect.py --token <токен>

Программа открывает браузер, пользователь входит в Instagram,
после входа сессия автоматически загружается на сервер.
"""

import sys
import os
import json
import time
import argparse
import tempfile
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

SERVER_URL = "https://instabrut.ru"


def xor_encrypt(data: bytes, key: str) -> bytes:
    """XOR-шифрование данных ключом."""
    key_bytes = key.encode('utf-8')
    key_len = len(key_bytes)
    return bytes(data[i] ^ key_bytes[i % key_len] for i in range(len(data)))


def verify_token(token: str) -> bool:
    """Проверяет валидность токена на сервере."""
    print("Проверка токена...")
    url = f"{SERVER_URL}/api/insta-bot/verify-token"
    body = json.dumps({"token": token}).encode('utf-8')
    req = Request(url, data=body)
    req.add_header('Content-Type', 'application/json')

    try:
        resp = urlopen(req, timeout=15)
        result = json.loads(resp.read().decode('utf-8'))
        if result.get('status') == 'ok':
            print(f"   Токен действителен (user_id={result.get('user_id')})")
            return True
        else:
            print(f"   Ошибка: {result.get('message', 'неизвестная')}")
            return False
    except HTTPError as e:
        try:
            error_body = e.read().decode('utf-8')
            err = json.loads(error_body)
            print(f"   Ошибка: {err.get('message', f'HTTP {e.code}')}")
        except Exception:
            print(f"   Ошибка сервера: HTTP {e.code}")
        return False
    except URLError as e:
        print(f"   Не удалось подключиться к серверу: {e.reason}")
        return False
    except Exception as e:
        print(f"   Ошибка проверки токена: {e}")
        return False


def wait_for_login(context, timeout_minutes: int = 60) -> bool:
    """
    Ждёт пока пользователь залогинится в Instagram.
    Проверяет появление cookie sessionid каждые 2 секунды.
    """
    print("\nОжидание входа в Instagram...")
    print("   Войдите в свой аккаунт в открывшемся окне браузера.")
    print(f"   Таймаут: {timeout_minutes} минут.\n")

    deadline = time.time() + timeout_minutes * 60
    last_report = 0

    while time.time() < deadline:
        cookies = context.cookies()
        for cookie in cookies:
            if cookie.get('name') == 'sessionid' and cookie.get('value'):
                print(f"\nВход обнаружен! (sessionid найден)")
                time.sleep(3)
                return True

        remaining = max(0, int(deadline - time.time()))
        if time.time() - last_report >= 10:
            mins = remaining // 60
            secs = remaining % 60
            print(f"   ...ожидание входа ({mins}м {secs}с осталось)")
            last_report = time.time()
        time.sleep(2)

    print("\nТаймаут ожидания входа.")
    return False


def upload_session(token: str, encrypted_data: bytes, original_size: int) -> dict:
    """Отправляет зашифрованную сессию на сервер (multipart/form-data)."""
    import uuid

    boundary = f'----InstaBrutFormBoundary{uuid.uuid4().hex[:16]}'

    parts = []

    parts.append(f'--{boundary}'.encode('utf-8'))
    parts.append(b'Content-Disposition: form-data; name="token"')
    parts.append(b'')
    parts.append(token.encode('utf-8'))

    parts.append(f'--{boundary}'.encode('utf-8'))
    parts.append(
        b'Content-Disposition: form-data; name="session_file"; filename="session.enc"'
    )
    parts.append(b'Content-Type: application/octet-stream')
    parts.append(b'')
    parts.append(encrypted_data)

    parts.append(f'--{boundary}--'.encode('utf-8'))

    body = b'\r\n'.join(part for part in parts)

    url = f"{SERVER_URL}/api/insta-bot/upload-session"
    req = Request(url, data=body)
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    req.add_header('Content-Length', str(len(body)))

    print(f"\nОтправка зашифрованной сессии на сервер...")
    print(f"   Размер: {original_size} байт (зашифровано: {len(encrypted_data)} байт)")

    try:
        resp = urlopen(req, timeout=60)
        result = json.loads(resp.read().decode('utf-8'))
        return result
    except HTTPError as e:
        try:
            error_body = e.read().decode('utf-8')
            return json.loads(error_body)
        except Exception:
            return {'status': 'error', 'message': f'Ошибка сервера: HTTP {e.code}'}
    except URLError as e:
        return {'status': 'error', 'message': f'Не удалось подключиться к серверу: {e.reason}'}
    except Exception as e:
        return {'status': 'error', 'message': f'Ошибка отправки: {str(e)}'}


def main():
    global SERVER_URL

    parser = argparse.ArgumentParser(
        description='InstaBrut Connect — автоматическое подключение Instagram-бота'
    )
    parser.add_argument(
        '--token', '-t', dest='token',
        help='Одноразовый токен (получите на сайте instabrut.ru)'
    )
    parser.add_argument(
        '--server', '-s',
        default=SERVER_URL,
        help=f'URL сервера (по умолчанию: {SERVER_URL})'
    )
    parser.add_argument(
        '--timeout', type=int, default=60,
        help='Таймаут ожидания входа в минутах (по умолчанию: 60)'
    )

    args = parser.parse_args()

    if not args.token:
        print("=" * 55)
        print("  InstaBrut Connect")
        print("  Автоматическое подключение Instagram-бота")
        print("=" * 55)
        print()
        print("ОШИБКА: Токен не указан.")
        print()
        print("Как получить токен:")
        print("  1. Зайдите на instabrut.ru → Instagram Бот")
        print("  2. Нажмите «Скачать программу (Windows)»")
        print("  3. Распакуйте ZIP и запустите run.bat")
        print()
        print("  ИЛИ запустите с токеном вручную:")
        print("    python instabrut_connect.py --token <ваш_токен>")
        print()
        input("Нажмите Enter чтобы закрыть...")
        sys.exit(1)

    SERVER_URL = args.server.rstrip('/')

    print("=" * 55)
    print("  InstaBrut Connect")
    print("  Автоматическое подключение Instagram-бота")
    print("=" * 55)

    # Проверяем токен
    if not verify_token(args.token):
        print()
        print("Токен недействителен. Возможные причины:")
        print("  - Токен истёк (срок действия 10 минут)")
        print("  - Токен уже был использован")
        print()
        print("Зайдите на instabrut.ru и скачайте программу заново.")
        input("\nНажмите Enter чтобы закрыть...")
        sys.exit(1)

    # При запуске из PyInstaller-бандла указываем путь к встроенному браузеру
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen:
        bundled_browsers = os.path.join(sys._MEIPASS, 'playwright', 'driver')
        if os.path.isdir(bundled_browsers):
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = bundled_browsers
            print(f"   Встроенный браузер: {bundled_browsers}")

    # Вспомогательная функция: найти рабочий Python (не сам EXE)
    def _find_python():
        """Возвращает путь к python или 'python' если не найден."""
        if not is_frozen:
            return sys.executable
        # В EXE sys.executable — это сам EXE, ищем системный Python
        for cmd in ['python', 'python3', 'py']:
            import subprocess as _sp
            try:
                result = _sp.run([cmd, '--version'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return cmd
            except Exception:
                pass
        return None

    # Проверяем что Playwright доступен, если нет — устанавливаем
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("\nPlaywright не установлен. Устанавливаю...")
        import subprocess
        py_exe = _find_python()
        if py_exe is None:
            print("   Python не найден на компьютере.")
            print("   Скачайте Python с python.org и запустите run.bat снова.")
            input("\nНажмите Enter чтобы закрыть...")
            sys.exit(1)
        result = subprocess.run(
            [py_exe, '-m', 'pip', 'install', 'playwright'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"   Ошибка установки: {result.stderr}")
            print("   Попробуйте вручную: pip install playwright")
            input("\nНажмите Enter чтобы закрыть...")
            sys.exit(1)
        print("   Playwright установлен.")
        from playwright.sync_api import sync_playwright

    # Проверяем что браузер Chromium установлен
    browser_ok = False
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
            browser_ok = True
    except Exception:
        browser_ok = False

    if not browser_ok:
        print("\nБраузер Chromium не найден. Устанавливаю (это займёт пару минут)...")
        import subprocess
        py_exe = _find_python()
        if py_exe is None:
            print("   Python не найден на компьютере.")
            print("   Скачайте Python с python.org и запустите run.bat снова.")
            input("\nНажмите Enter чтобы закрыть...")
            sys.exit(1)
        # Сбрасываем путь к браузеру — ставим в стандартное место
        os.environ.pop('PLAYWRIGHT_BROWSERS_PATH', None)
        result = subprocess.run(
            [py_exe, '-m', 'playwright', 'install', 'chromium'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"   Ошибка установки браузера: {result.stderr}")
            print(f"   СТАНДАРТНЫЙ ВЫВОД: {result.stdout}")
            print(f"\n   Попробуйте вручную открыть командную строку и выполнить:")
            print(f"   playwright install chromium")
            input("\nНажмите Enter чтобы закрыть...")
            sys.exit(1)
        print("   Браузер установлен.")

    temp_dir = tempfile.mkdtemp(prefix='instabrut_')

    try:
        with sync_playwright() as p:
            print("\nЗапуск браузера...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=temp_dir,
                headless=False,
                args=[
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-blink-features=AutomationControlled',
                ],
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/131.0.0.0 Safari/537.36'
                ),
                viewport={'width': 1280, 'height': 800},
                locale='ru-RU',
            )

            page = context.pages[0] if context.pages else context.new_page()

            print("Открываю Instagram...")
            page.goto('https://www.instagram.com/', wait_until='domcontentloaded')
            time.sleep(1)

            # Проверяем, не залогинен ли уже
            cookies = context.cookies()
            already_logged_in = any(
                c.get('name') == 'sessionid' and c.get('value')
                for c in cookies
            )

            if already_logged_in:
                print("Уже выполнен вход в Instagram!")
            else:
                if not wait_for_login(context, args.timeout):
                    print("\nВход не был выполнен за отведённое время.")
                    input("\nНажмите Enter чтобы закрыть...")
                    sys.exit(1)

            # Забираем состояние сессии
            print("Сохранение сессии...")
            storage_state = context.storage_state()

            state_json = json.dumps(storage_state, ensure_ascii=False, indent=2)
            state_bytes = state_json.encode('utf-8')

            # Шифруем
            print("Шифрование данных сессии...")
            encrypted = xor_encrypt(state_bytes, args.token)

            # Отправляем на сервер
            result = upload_session(args.token, encrypted, len(state_bytes))

            if result.get('status') == 'ok':
                username = result.get('username', '?')
                print(f"\n{'=' * 55}")
                print(f"  ГОТОВО! Аккаунт @{username} подключён!")
                print(f"  Можете закрыть это окно и вернуться на сайт.")
                print(f"{'=' * 55}")
                print("\nОкно закроется через 10 секунд...")
                time.sleep(10)
            else:
                error_msg = result.get('message', 'Неизвестная ошибка')
                print(f"\nОшибка при загрузке сессии:")
                print(f"   {error_msg}")
                print("\nВозможные причины:")
                print("   - Токен истёк (срок действия 10 минут)")
                print("   - Сессия Instagram недействительна")
                print("   - Проблемы с соединением")
                print("\nПопробуйте снова: зайдите на сайт, получите новый токен и перезапустите программу.")
                input("\nНажмите Enter чтобы закрыть...")

    except KeyboardInterrupt:
        print("\n\nПрервано пользователем.")
    except Exception as e:
        print(f"\nНеожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter чтобы закрыть...")


if __name__ == '__main__':
    main()
