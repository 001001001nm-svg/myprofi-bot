import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

# Токен твоего бота (укажи свой, если нужно)
API_TOKEN = 'ТВОЙ_ТОКЕН_БОТА'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Бот успешно запущен и работает.")

if __name__ == '__main__':
    import asyncio
    asyncio.run(dp.start_polling(bot))
