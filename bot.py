from collections.abc import Sequence
import logging
import subprocess
import os
import datetime
from typing import List, Tuple
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

load_dotenv()
telegram_token = os.getenv("TELEGRAM_TOKEN")
infobase_name = os.getenv("INFOBASE_NAME")
server_host = os.getenv("SERVER_HOST")
allowed_ids = os.getenv("ALLOWED_IDS")

def restrict():
    def decorator(handler_func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):          
            if allowed_ids == "all":
                return await handler_func(update, context)
            user_id = update.effective_user.id
            if str(user_id) not in allowed_ids:
                await update.message.reply_text("🚫 Доступ запрещен.")
                return None
            return await handler_func(update, context)
        return wrapper
    return decorator

async def _send_response(chat, text: str) -> None:

    if chat and text and str(text).strip():
        try:
            await chat.send_message(str(text).strip())
        except Exception as e:
            logging.error(f"Ошибка отправки в Telegram: {e}")

async def run_command(
    chat,
    command: List[str],
    description: str = ""
) -> Tuple[bool, str]:

    try:
        if description:
            await _send_response(chat, f"🔄 {description}...")
        
        process = subprocess.Popen(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  
            bufsize=1,
            universal_newlines=True,
            encoding="cp866"
        )
        
        output_lines = []
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
                
            if line:
                cleaned_line = line.rstrip('\n')
                if cleaned_line:  
                    output_lines.append(cleaned_line)
                    await _send_response(chat, f"▸ {cleaned_line}")
        
        return_code = process.wait()

        if return_code == 0:
            await _send_response(chat, f"✅ Готово!")
        else:
            await _send_response(chat, f"❌ Завершено с ошибкой (код: {return_code})")
            
    except FileNotFoundError:
        error = f"❌ Команда не найдена: {command[0]}"
        await _send_response(chat, error)
        return False, error
    except Exception as e:
        error = f"❌ Неожиданная ошибка: {str(e)}"
        await _send_response(chat, error)
        logging.exception(f"Ошибка выполнения команды {command}")
        return False, error

@restrict()
async def regras(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    chat = update.effective_chat
    args = context.args or []
    
    if len(args) != 1:
        help_text = """Устанавливает сервер администрирования RAS как службу Windows
        Использование: /regcas <Версия платформы>"""
        await _send_response(chat, help_text)
        return
    
    v8version = args[0]
    await run_command(
        chat,
        ['reg.bat', v8version],
        description=f"Установка RAS для версии {v8version}"
    )

def get_args(update, context):

    if context.args:
        return context.args
    elif update.callback_query and update.callback_query.data:
        return update.callback_query.data.split()[-2:]
    return []

@restrict()
async def updatedb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    chat = update.effective_chat
    args = get_args(update, context)

    if len(args) != 2:
        help_text = """Обновляет конфигурацию информационной базы
        Использование: /updatedb <Пользователь> <Пароль>"""
        await _send_response(chat, help_text)
        return

    db_user, db_pwd = args
    
    query = update.callback_query

    if not query:
        hour_now = datetime.datetime.now().hour
        if  hour_now < 21 and hour_now > 8:
            await chat.send_message(
                text="😱Кажется сейчас разгар рабочего дня. Точно обновляем?😱",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚠️⚠️Обновить базу⚠️⚠️", callback_data=f"update_db {db_user} {db_pwd}")]
                ])
            )
            return
    
    debug = os.getenv('Debug', 'False').lower() == 'true'
    
    if not debug:
        command = ['update_db.exe', infobase_name, db_user, db_pwd]
        cmd_description = "Обновление базы"
    else:
        command = ['oscript', 'update_db.os', infobase_name, db_user, db_pwd]
        cmd_description = "Обновление базы (dev)"
    
    await run_command(
        chat,
        command,
        cmd_description
    )

    if query:
        await query.edit_message_reply_markup()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    update_info = update.to_dict() if update else 'No update'
    logging.error(f"Ошибка: {context.error}\nОбновление: {update_info}")

    if update and update.message:
        await update.message.reply_text('Произошла ошибка. Пожалуйста, попробуйте позже.')
def main() -> None:

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    
    app = Application.builder().token(telegram_token).build()
    
    app.add_handler(CommandHandler("updatedb", updatedb))
    app.add_handler(CommandHandler("regras", regras))
    
    app.add_handler(CallbackQueryHandler(updatedb, pattern=r"^update_db"))

    app.add_error_handler(error_handler)
    
    logging.info("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
