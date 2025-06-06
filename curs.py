from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import asyncio
from openai import OpenAI  # Используем OpenAI-совместимый клиент

# Замените на ваш токен Telegram-бота
API_TOKEN = '7786110568:AAGAcufBSEGiX5WDYwhBksEe-b0rw7xuwi0'

# Настройки стороннего API
base_url = "https://api.aimlapi.com/v1"  # URL API
api_key = "4fca88a5b4bc49348543a7d671f249b7"  # Ваш ключ от aimlapi.com

# Инициализация клиента OpenAI-совместимого API
api = OpenAI(api_key=api_key, base_url=base_url)

# Инициализация бота с использованием DefaultBotProperties
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("Привет! Я чат-бот Ногинского колледжа. Чем могу помочь?")

# Обработчик текстовых сообщений с использованием стороннего API
@dp.message()
async def handle_message(message: Message):
    try:
        # Отправляем запрос к API
        completion = api.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.2",  # Модель Mistral
            messages=[
                {"role": "system", "content": "Вы помогаете абитуриентам Ногинского колледжа."},
                {"role": "user", "content": message.text}
            ],
            temperature=0.7,  # Параметр "творчества" ответа
            max_tokens=256,  # Максимальная длина ответа
        )

        # Получаем ответ от API
        response = completion.choices[0].message.content

        # Отправляем ответ пользователю
        await message.answer(response)

    except Exception as e:
        # Обработка ошибок
        await message.answer("Произошла ошибка при обработке вашего запроса. Попробуйте позже.")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())