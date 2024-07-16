import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart

from dotenv import load_dotenv
import os

import logging

from health_checker import check_status, get_last_n_log, get_oppotunities

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)

dp = Dispatcher()

# Inline клавиатура
kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Статус", callback_data="check")],
    [InlineKeyboardButton(text="Возможности", callback_data="oppotunities")],
    [InlineKeyboardButton(text="Лог", callback_data="logs")]
])


@dp.message(CommandStart())
async def cmd_start(message: Message):
    text = "Привет {}! Это телеграм-бот для отслеживания арбитражного бота на bybit"
    await message.answer(text.format(message.from_user.first_name), reply_markup=kb)


@dp.message(F.text == "команды")
async def cmd_set(message: Message):
    await message.answer("Список возможностей бота", reply_markup=kb)


@dp.callback_query(F.data == "check")
async def handle_status(callback: CallbackQuery):
    status = check_status()
    await callback.message.answer(f"Статус бота: {'Запущен' if status else 'Остановлен'}")
    await callback.answer()


@dp.callback_query(F.data == "oppotunities")
async def handle_opportunities(callback: CallbackQuery):
    opportunities = get_oppotunities()
    await callback.message.answer(f"Последние возможности арбитража:\n{opportunities}")
    await callback.answer()


@dp.callback_query(F.data == "logs")
async def handle_log(callback: CallbackQuery):
    log = get_last_n_log(1, date_only=False)
    await callback.message.answer(f"Последние строки лога:\n{log}")
    await callback.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
