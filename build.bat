@echo off
chcp 65001 >nul
echo ========================================
echo    Сборка проекта Telegram бота
echo ========================================
echo.

REM --- Проверка зависимостей ---
echo [1/6] Проверка зависимостей...

py --version >nul 2>nul
if errorlevel 1 (
    echo ОШИБКА: Python не найден в PATH!
    echo Установите Python или добавьте его в PATH
    pause
    exit /b 1
)

pyinstaller --version >nul 2>nul
if errorlevel 1 (
    echo ОШИБКА: PyInstaller не установлен!
    echo Установите: pip install pyinstaller
    pause
    exit /b 1
)

REM --- Создание папки dist ---
echo [2/6] Создание структуры папок...

if not exist "dist" (
    mkdir dist
    echo Создана папка: dist
) else (
    echo Папка dist уже существует
)

REM --- Компиляция bot.py в EXE ---
echo [3/6] Компиляция bot.py...

pyinstaller --onefile ^
--name bot ^
--distpath dist ^
--workpath build_temp ^
--clean ^
--noconsole ^
bot.py

if errorlevel 1 (
    echo ОШИБКА: Не удалось скомпилировать bot.py!
    pause
    exit /b 1
)

echo Успешно: dist\bot.exe

REM --- Компиляция script.os в EXE (если oscript есть) ---
echo [4/6] Компиляция script.os...

where oscript >nul 2>nul
if not errorlevel 1 (
    if exist "script.os" (
        oscript -make script.os dist\script.exe
        if errorlevel 0 (
            echo Успешно: dist\script.exe
        ) else (
            echo ПРЕДУПРЕЖДЕНИЕ: Не удалось скомпилировать script.os
        )
    ) else (
        echo ПРЕДУПРЕЖДЕНИЕ: Файл script.os не найден
    )
) else (
    echo ПРЕДУПРЕЖДЕНИЕ: OneScript не найден, пропускаем компиляцию script.os
)

REM --- Создание .env файла с шаблоном ---
echo [5/6] Создание .env файла...

(
    echo TELEGRAM_TOKEN=your_telegram_bot_token_here
    echo.
    echo INFOBASE_NAME=MyInfoBase
    echo SERVER_HOST=localhost
    echo ALLOWED_IDS=all
) > "dist\.env"
echo Создан: dist\.env (шаблон)

REM --- Копирование reg.bat ---
echo [6/6] Копирование вспомогательных файлов...

if exist "reg.bat" (
    copy "reg.bat" "dist\" >nul
    echo Скопирован: reg.bat
)

(
    echo taskkill /im bot.exe /f
    echo pause
) > "dist\stopbot.bat"

REM --- Финальная очистка ---
echo [7/7] Финальная очистка...
if exist "build_temp" (
    rmdir /s /q "build_temp"
    echo Удалена папка build_temp
)
if exist "build" (
    rmdir /s /q "build"
    echo Удалена папка build
)
echo.

echo.
echo ========================================
echo    Сборка завершена успешно!
echo ========================================
echo.
echo Содержимое папки dist:
dir /b dist
echo.
echo Следующие шаги:
echo 1. Перейдите в папку dist
echo 2. Отредактируйте файл .env
echo 3. Запустите bot.exe
pause