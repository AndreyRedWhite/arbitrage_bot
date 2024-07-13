import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters.command import Command
from dotenv import load_dotenv
import requests

load_dotenv()

# Получение токена Telegram бота из переменной окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Создание экземпляров бота и диспетчера
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание кнопок
status_button = KeyboardButton(text='Статус')
opportunities_button = KeyboardButton(text='Найденные возможности')

kb = [[status_button, opportunities_button]]

# Создание клавиатуры
keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=keyboard)


@dp.message(Command('Статус'))
async def check_status(message: types.Message):
    try:
        with open('logs/arbitrage_bot.log', 'r') as log_file:
            lines = log_file.readlines()
            # Берем последние 5 строк логов
            last_logs = lines[-5:]
            last_logs_str = "\n".join(last_logs)
            await message.answer(f"Последние лог-события:\n{last_logs_str}")
    except Exception as e:
        await message.answer(f"Ошибка при чтении логов: {e}")


@dp.message(Command('Найденные возможности'))
async def get_opportunities(message: types.Message):
    try:
        with open('arbitrage_opportunities.txt', 'r') as opp_file:
            opportunities = opp_file.read()
            await message.answer(f"Найденные арбитражные возможности:\n{opportunities}")
    except Exception as e:
        await message.answer(f"Ошибка при чтении файла с возможностями: {e}")


def send_telegram_message(message):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}'
    response = requests.get(send_text)
    return response.json()

async def on_startup():
    await send_telegram_message("Бот запущен и готов к работе!")

async def on_shutdown():
    await send_telegram_message("Бот отключен.")


async def main():
    await dp.start_polling(bot, skip_updates=True)
if __name__ == '__main__':
    asyncio.run(main())

