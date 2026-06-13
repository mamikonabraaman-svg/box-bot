import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📦 Мои заказы"))
    kb.add(KeyboardButton("📞 Связаться"))
    await message.answer("Привет! Я бот для заказов. Выбери действие:", reply_markup=kb)
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id
 != ADMIN_ID:
        await message.answer("❌ Нет доступа!")
        return
    await message.answer("👑 Добро пожаловать в админ панель!")
@dp.message_handler()
async def handle_message(message: types.Message):
    if message.text == "📦 Мои заказы":
        await message.answer("У вас пока нет заказов.")
    elif message.text == "📞 Связаться":
        await message.answer("Напишите ваш вопрос, мы ответим!")
    else:
        await bot.send_message(ADMIN_ID, f"Новое сообщение от @{message.from_user.username}:\n{message.text}")
        await message.answer("✅ Сообщение отправлено!")
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
