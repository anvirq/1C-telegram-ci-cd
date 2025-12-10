"""
Сборка проекта Telegram бота
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path
from typing import Optional, Tuple

class Colors:
    """Цвета для консольного вывода"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header():
    """Вывод заголовка"""
    print(f"{Colors.CYAN}{'='*60}")
    print(f"{Colors.BOLD}   Сборка проекта Telegram бота")
    print(f"{'='*60}{Colors.END}")
    print()

def print_step(step_num: int, total_steps: int, message: str):
    """Вывод шага сборки"""
    print(f"{Colors.BLUE}[{step_num}/{total_steps}]{Colors.END} {message}...")

def print_success(message: str):
    """Вывод успешного сообщения"""
    print(f"{Colors.GREEN}✓ Успешно:{Colors.END} {message}")

def print_warning(message: str):
    """Вывод предупреждения"""
    print(f"{Colors.YELLOW}⚠ ПРЕДУПРЕЖДЕНИЕ:{Colors.END} {message}")

def print_error(message: str):
    """Вывод ошибки"""
    print(f"{Colors.RED}✗ ОШИБКА:{Colors.END} {message}")

def check_dependencies() -> Tuple[bool, Optional[str]]:
    """Проверка необходимых зависимостей"""
    print_step(1, 7, "Проверка зависимостей")

    try:
        python_version = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"  Python: {python_version.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, "Python не найден в PATH!\nУстановите Python или добавьте его в PATH"
    
    try:
        pyinstaller_version = subprocess.run(
            ["pyinstaller", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"  PyInstaller: {pyinstaller_version.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, "PyInstaller не установлен!\nУстановите: pip install pyinstaller"
    
    return True, None

def create_dist_structure() -> bool:
    """Создание структуры папок"""
    print_step(2, 7, "Создание структуры папок")
    
    dist_dir = Path("dist")
    if not dist_dir.exists():
        dist_dir.mkdir(parents=True)
        print_success(f"Создана папка: {dist_dir}")
        return True
    else:
        print(f"  Папка {dist_dir} уже существует")
        return True

def compile_bot() -> Tuple[bool, Optional[str]]:
    """Компиляция bot.py в EXE"""
    print_step(3, 7, "Компиляция bot.py")
    
    args = [
        "pyinstaller",
        "--onefile",
        "--name", "1cbot",
        "--distpath", "dist",
        "--workpath", "build_temp",
        "--icon=icon.ico",
        "--clean",
        "--noconsole",
        "bot.py"
    ]
    
    print(f"  Команда: {' '.join(args)}")
    
    try:
        result = subprocess.run(
            args,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        exe_path = Path("dist") / "1cbot.exe"
        if exe_path.exists():
            print_success(f"{exe_path}")
            return True, None
        else:
            return False, "EXE файл не был создан"
            
    except subprocess.CalledProcessError as e:
        error_msg = f"Не удалось скомпилировать bot.py!\n"
        if e.stderr:
            error_msg += f"Ошибка PyInstaller: {e.stderr[:200]}..."
        return False, error_msg
    except Exception as e:
        return False, f"Неизвестная ошибка: {str(e)}"

def compile_update_db() -> bool:
    """Компиляция update_db.os в EXE (если есть OneScript)"""
    print_step(4, 7, "Компиляция update_db.os")
    
    try:
        subprocess.run(
            ["oscript", "--version"],
            capture_output=True,
            check=True
        )
        has_oscript = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        has_oscript = False
    
    if not has_oscript:
        print_warning("OneScript не найден, пропускаем компиляцию update_db.os")
        return False
    
    update_db_os = Path("update_db.os")
    if not update_db_os.exists():
        print_warning(f"Файл {update_db_os} не найден")
        return False
    
    try:
        result = subprocess.run(
            ["oscript", "-make", "update_db.os", "dist/update_db.exe"],
            check=True,
            capture_output=True,
            text=True
        )
        print_success("dist/update_db.exe")
        return True
        
    except subprocess.CalledProcessError:
        print_warning("Не удалось скомпилировать update_db.os")
        return False

def create_env_template() -> bool:
    """Создание .env файла с шаблоном"""
    print_step(5, 7, "Создание .env файла")
    
    env_content = """TELEGRAM_TOKEN=your_telegram_bot_token_here

INFOBASE_NAME=MyInfoBase
SERVER_HOST=localhost
ALLOWED_IDS=all
"""
    
    env_path = Path("dist") / ".env"
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)
        print_success(f"{env_path} (шаблон)")
        return True
    except Exception as e:
        print_error(f"Не удалось создать .env файл: {str(e)}")
        return False

def copy_auxiliary_files() -> bool:
    """Копирование вспомогательных файлов"""
    print_step(6, 7, "Копирование вспомогательных файлов")
    
    reg_bat = Path("reg.bat")
    if reg_bat.exists():
        try:
            shutil.copy2(reg_bat, "dist/")
            print_success("reg.bat")
        except Exception as e:
            print_warning(f"Не удалось скопировать reg.bat: {str(e)}")
    
    stopbot_content = """@echo off
chcp 65001 >nul    
taskkill /im 1cbot.exe /f >nul 2>nul
if errorlevel 1 (
    echo Бот не запущен или уже остановлен
) else (
    echo Бот успешно остановлен
)
pause
"""
    
    try:
        stopbot_path = Path("dist") / "stopbot.bat"
        with open(stopbot_path, "w", encoding="utf-8") as f:
            f.write(stopbot_content)
        print_success("stopbot.bat")
        return True
    except Exception as e:
        print_error(f"Не удалось создать stopbot.bat: {str(e)}")
        return False

def cleanup() -> bool:
    """Финальная очистка"""
    print_step(7, 7, "Финальная очистка")
    
    dirs_to_remove = ["build_temp", "build", "bot.spec"]
    removed = []
    
    for dir_name in dirs_to_remove:
        dir_path = Path(dir_name)
        if dir_path.exists():
            try:
                if dir_path.is_dir():
                    shutil.rmtree(dir_path)
                else:
                    dir_path.unlink()
                removed.append(dir_name)
            except Exception as e:
                print_warning(f"Не удалось удалить {dir_name}: {str(e)}")
    
    if removed:
        print(f"  Удалено: {', '.join(removed)}")
    
    return True

def show_final_message():
    """Показать финальное сообщение"""
    print()
    print(f"{Colors.GREEN}{'='*60}")
    print(f"{Colors.BOLD}   Сборка завершена успешно!")
    print(f"{'='*60}{Colors.END}")
    print()
    
    # Показать содержимое папки dist
    dist_dir = Path("dist")
    if dist_dir.exists():
        print("Содержимое папки dist:")
        for item in dist_dir.iterdir():
            if item.is_file():
                size = item.stat().st_size
                print(f"  {item.name} ({size:,} байт)")
            else:
                print(f"  {item.name}/")
    
    print()

def main():
    """Основная функция сборки"""
    print_header()
    
    success, error = check_dependencies()
    if not success:
        print_error(error)
        if platform.system() == "Windows":
            input("Нажмите Enter для выхода...")
        sys.exit(1)
    
    steps = [
        create_dist_structure,
        compile_bot,
        compile_update_db,
        create_env_template,
        copy_auxiliary_files,
        cleanup
    ]
    
    failed_steps = []
    
    for i, step_func in enumerate(steps, 2):
        try:
            if not step_func():
                failed_steps.append(i)
        except Exception as e:
            print_error(f"Ошибка на шаге {i}: {str(e)}")
            failed_steps.append(i)
    
    # Показываем результат
    if not failed_steps:
        show_final_message()
        if platform.system() == "Windows":
            input("Нажмите Enter для выхода...")
    else:
        print()
        print_error(f"Сборка завершена с ошибками на шагах: {', '.join(map(str, failed_steps))}")
        if platform.system() == "Windows":
            input("Нажмите Enter для выхода...")
        sys.exit(1)

if __name__ == "__main__":
    try:
        if platform.system() == "Windows":
            os.system("chcp 65001 >nul")
        main()
    except KeyboardInterrupt:
        print("\n\nСборка прервана пользователем")
        sys.exit(130)
    except Exception as e:
        print_error(f"Критическая ошибка: {str(e)}")
        if platform.system() == "Windows":
            input("Нажмите Enter для выхода...")
        sys.exit(1)