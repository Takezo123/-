
from aiogram.enums import ParseMode, ContentType
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from openai import OpenAI
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import asyncio
import sqlite3
import logging

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен для основного бота (абитуриенты)
API_TOKEN = '7786110568:AAGAcufBSEGiX5WDYwhBksEe-b0rw7xuwi0'


ADMIN_TOKEN = '7938055354:AAEz9ieMMeJaO2xZ7Uyou7lld6issJbJzZs'

# Инициализация бота для абитуриентов
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Инициализация админ-бота
admin_bot = Bot(token=ADMIN_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
admin_dp = Dispatcher()


# Создаем базу данных и таблицу для абитуриентов
def init_db():
    conn = sqlite3.connect('applicants.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applicants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            telegram_tag TEXT NOT NULL,
            specialty TEXT NOT NULL,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


# Инициализация базы данных при запуске
init_db()
# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = '7786110568:AAGAcufBSEGiX5WDYwhBksEe-b0rw7xuwi0'

# Настройки OpenRouter
base_url = "https://openrouter.ai/api/v1"
api_key = "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"  # ЗАМЕНИТЕ НА СВОЙ КЛЮЧ

api = OpenAI(
    api_key=api_key,
    base_url=base_url,
    default_headers={
        "HTTP-Referer": "Noginsk College Bot",
        "X-Title": "Admissions Assistant"
    }
)

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Хранилище состояний пользователей
user_states = {}
# История диалогов для каждого пользователя
conversation_history = {}


# Создаем базу данных и таблицу для абитуриентов
def init_db():
    conn = sqlite3.connect('applicants.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applicants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            telegram_tag TEXT NOT NULL,
            specialty TEXT NOT NULL,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


# Инициализация базы данных при запуске
init_db()


# Состояния для регистрации
class RegistrationStates(StatesGroup):
    full_name = State()
    phone = State()
    telegram_tag = State()
    specialty = State()


# Ответы на частые вопросы (для ИИ)
faq_responses = {
    "Специальности колледжа":
        "Очное отделение (бюджет):\n"
        "1. Техническое обслуживание и ремонт автотранспортных средств (23.02.07, Ногинск, 3г.10м.) - 50 мест\n"
        "2. Организация перевозок и управление на транспорте (23.02.01, Ногинск, 3г.10м) - 50 мест\n"
        "3. Управление качеством продукции, процессов и услуг (27.02.07, Ногинск, 2г.10м) - 50 мест\n"
        "4. Операционная деятельность в логистике (38.02.03, Балашиха, 2г.10м.) - 25 мест\n"
        "5. Операционная деятельность в логистике (38.02.03, Ногинск, 2г.10м.) - 50 мест\n"
        "6. Информационные системы и программирование (09.02.07, Ногинск, 3г.10м.) - 50 мест\n"
        "7. Информационные системы и программирование (09.02.07, Балашиха, 3г.10м.) - 25 мест\n"
        "8. Сетевое и системное администрирование (09.02.06, Балашиха, 3г.10м.) - 25 мест\n"
        "9. Сетевое и системное администрирование (09.02.06, Ногинск, 3г.10м.) - 25 мест\n"
        "10. Туризм и гостеприимство (43.02.16, Ногинск, 2г.10м) - 50 мест\n"
        "11. Технологии индустрии красоты (43.02.17, Балашиха, 2г.10м.) - 25 мест\n"
        "12. Поварское и кондитерское дело (43.02.15, Ногинск, 3г.10м.) - 50 мест\n\n"

        "Профессии (бюджет):\n"
        "1. Мастер слесарных работ (15.01.35, Ногинск, 2г.2м) - 50 мест\n"
        "2. Мастер слесарных работ (15.01.35, Ногинск, 2г.10м) - 25 мест\n"
        "3. Оператор информационных систем и ресурсов (09.01.03, Ногинск, 1г.10м) - 50 мест\n"
        "4. Оператор информационных систем и ресурсов (09.01.03, Балашиха, 1г.10м) - 25 мест\n\n"

        "Очное отделение (внебюджет):\n"
        "1. Юриспруденция (40.02.04, Ногинск, 2г.10м.) - 50 мест\n"
        "2. Юриспруденция (40.02.04, Балашиха, 2г.10м.) - 25 мест\n"
        "3. Банковское дело (38.02.07, Ногинск, 2г.10м.) - 25 мест\n"
        "4. Банковское дело (38.02.07, Балашиха, 2г.10м.) - 25 мест\n\n"

        "Заочное отделение (внебюджет):\n"
        "1. Операционная деятельность в логистике (38.02.03, Ногинск, 2г.10м., на базе 11 кл.) - 16 мест\n"
        "2. Операционная деятельность в логистике (38.02.03, Ногинск, 3г.10м., на базе 9 кл.) - 25 мест",

    "Контакты приемной комиссии":
        "Телефон приемной комиссии: 8-916-084-38-73",

    "График работы приемной комиссии":
        "Рабочие дни: понедельник - пятница\n"
        "Часы работы: 9:00 - 16:00\n"
        "Период работы: 20 июня - 15 августа 2025 г.\n"
        "Перерыв: без перерыва на обед",

    "Какие документы нужны?":
        "Основные документы:\n"
        "- Копия паспорта\n"
        "- Оригинал и копия документа об образовании\n"
        "- 6 фото 3х4\n\n"
        "После зачисления:\n"
        "- Медсправка по форме 086/у\n"
        "- Копия СНИЛС\n"
        "- Копия ИНН\n"
        "- Копия медицинского полиса",

    "Проходные баллы":
        "Конкурс проводится по среднему баллу аттестата\n"
        "Минимальный балл не установлен\n\n"
        "Бонусные баллы за достижения:\n"
        "- Победители олимпиад: +2 балла\n"
        "- Призеры конкурсов: +1.5 балла",

    "Есть ли общежитие?":
        "Свободных мест в общежитии колледжа нет"
}

# Форматированные ответы для пользователя (с HTML)
formatted_faq_responses = {
    "Специальности колледжа":
        "<b>Очное отделение (бюджет):</b>\n"
        "1. 🔧 <b>Техническое обслуживание и ремонт автотранспортных средств</b>\n"
        "   - Код: 23.02.07\n"
        "   - Ногинск, 3г.10м.\n"
        "   - <b>50 мест</b>\n\n"

        "2. 🚚 <b>Организация перевозок и управление на транспорте</b>\n"
        "   - Код: 23.02.01\n"
        "   - Ногинск, 3г.10м\n"
        "   - <b>50 мест</b>\n\n"

        "3. 📊 <b>Управление качеством продукции, процессов и услуг</b>\n"
        "   - Код: 27.02.07\n"
        "   - Ногинск, 2г.10м\n"
        "   - <b>50 мест</b>\n\n"

        "4. 📦 <b>Операционная деятельность в логистике</b>\n"
        "   - Код: 38.02.03\n"
        "   - Балашиха, 2г.10м.\n"
        "   - <b>25 мест</b>\n\n"

        "5. 📦 <b>Операционная деятельность в логистике</b>\n"
        "   - Код: 38.02.03\n"
        "   - Ногинск, 2г.10м.\n"
        "   - <b>50 мест</b>\n\n"

        "6. 💻 <b>Информационные системы и программирование</b>\n"
        "   - Код: 09.02.07\n"
        "   - Ногинск, 3г.10м.\n"
        "   - <b>50 мест</b>\n\n"

        "7. 💻 <b>Информационные системы и программирование</b>\n"
        "   - Код: 09.02.07\n"
        "   - Балашиха, 3г.10м.\n"
        "   - <b>25 мест</b>\n\n"

        "8. 🌐 <b>Сетевое и системное администрирование</b>\n"
        "   - Код: 09.02.06\n"
        "   - Балашиха, 3г.10м.\n"
        "   - <b>25 мест</b>\n\n"

        "9. 🌐 <b>Сетевое и системное администрирование</b>\n"
        "   - Код: 09.02.06\n"
        "   - Ногинск, 3г.10м.\n"
        "   - <b>25 мест</b>\n\n"

        "10. ✈️ <b>Туризм и гостеприимство</b>\n"
        "    - Код: 43.02.16\n"
        "    - Ногинск, 2г.10м\n"
        "    - <b>50 мест</b>\n\n"

        "11. 💄 <b>Технологии индустрии красоты</b>\n"
        "    - Код: 43.02.17\n"
        "    - Балашиха, 2г.10м.\n"
        "    - <b>25 мест</b>\n\n"

        "12. 👨‍🍳 <b>Поварское и кондитерское дело</b>\n"
        "    - Код: 43.02.15\n"
        "    - Ногинск, 3г.10м.\n"
        "    - <b>50 мест</b>\n\n"

        "<b>Профессии (бюджет):</b>\n"
        "1. 🔧 <b>Мастер слесарных работ</b>\n"
        "   - Код: 15.01.35\n"
        "   - Ногинск, 2г.2м\n"
        "   - <b>50 мест</b>\n\n"

        "2. 🔧 <b>Мастер слесарных работ</b>\n"
        "   - Код: 15.01.35\n"
        "   - Ногинск, 2г.10м\n"
        "   - <b>25 мест</b>\n\n"

        "3. 💻 <b>Оператор информационных систем и ресурсов</b>\n"
        "   - Код: 09.01.03\n"
        "   - Ногинск, 1г.10м\n"
        "   - <b>50 мест</b>\n\n"

        "4. 💻 <b>Оператор информационных систем и ресурсов</b>\n"
        "   - Код: 09.01.03\n"
        "   - Балашиха, 1г.10м\n"
        "   - <b>25 мест</b>\n\n"

        "<b>Очное отделение (внебюджет):</b>\n"
        "1. ⚖️ <b>Юриспруденция</b>\n"
        "   - Код: 40.02.04\n"
        "   - Ногинск, 2г.10м.\n"
        "   - <b>50 мест</b>\n\n"

        "2. ⚖️ <b>Юриспруденция</b>\n"
        "   - Код: 40.02.04\n"
        "   - Балашиха, 2г.10м.\n"
        "   - <b>25 мест</b>\n\n"

        "3. 💰 <b>Банковское дело</b>\n"
        "   - Код: 38.02.07\n"
        "   - Ногинск, 2г.10м.\n"
        "   - <b>25 мест</b>\n\n"

        "4. 💰 <b>Банковское дело</b>\n"
        "   - Код: 38.02.07\n"
        "   - Балашиха, 2г.10м.\n"
        "   - <b>25 мест</b>\n\n"

        "<b>Заочное отделение (внебюджет):</b>\n"
        "1. 📦 <b>Операционная деятельность в логистике</b>\n"
        "   - Код: 38.02.03\n"
        "   - Ногинск, 2г.10м.\n"
        "   - На базе 11 кл.\n"
        "   - <b>16 мест</b>\n\n"

        "2. 📦 <b>Операционная деятельность в логистике</b>\n"
        "   - Код: 38.02.03\n"
        "   - Ногинск, 3г.10м.\n"
        "   - На базе 9 кл.\n"
        "   - <b>25 мест</b>",

    "Контакты приемной комиссии":
        "📞 <b>Телефон приемной комиссии:</b> 8-916-084-38-73",

    "График работы приемной комиссии":
        "🕒 <b>Рабочие дни:</b> понедельник - пятница\n"
        "⏰ <b>Часы работы:</b> 9:00 - 16:00\n"
        "📅 <b>Период работы:</b> 20 июня - 15 августа 2025 г.\n"
        "🍽 <b>Перерыв:</b> без перерыва на обед",

    "Какие документы нужны?":
        "📋 <b>Основные документы:</b>\n"
        "- Копия паспорта\n"
        "- Оригинал и копия документа об образовании\n"
        "- 6 фото 3х4\n\n"
        "⚠️ <b>После зачисления:</b>\n"
        "- Медсправка по форме 086/у\n"
        "- Копия СНИЛС\n"
        "- Копия ИНН\n"
        "- Копия медицинского полиса",

    "Проходные баллы":
        "🎯 <b>Конкурс проводится по среднему баллу аттестата</b>\n"
        "ℹ️ Минимальный балл не установлен\n\n"
        "<b>Бонусные баллы за достижения:</b>\n"
        "🥇 Победители олимпиад: +2 балла\n"
        "🥈 Призеры конкурсов: +1.5 балла",

    "Есть ли общежитие?":
        "🚫 <b>Свободных мест в общежитии колледжа нет</b>"
}


# Создаем клавиатуру с кнопками FAQ
def build_faq_keyboard():
    builder = ReplyKeyboardBuilder()
    for question in formatted_faq_responses.keys():
        builder.add(types.KeyboardButton(text=question))
    builder.add(types.KeyboardButton(text="Задать свой вопрос"))
    builder.add(types.KeyboardButton(text="📝 Регистрация"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


# Клавиатура для режима диалога с ИИ
def build_dialog_keyboard():
    builder = ReplyKeyboardBuilder()
    for question in formatted_faq_responses.keys():
        builder.add(types.KeyboardButton(text=question))
    builder.add(types.KeyboardButton(text="❌ Завершить диалог"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


# Клавиатура со специальностями для регистрации
def build_specialties_keyboard():
    specialties = [
        "Техническое обслуживание и ремонт автотранспортных средств",
        "Организация перевозок и управление на транспорте",
        "Управление качеством продукции, процессов и услуг",
        "Операционная деятельность в логистике (Балашиха)",
        "Операционная деятельность в логистике (Ногинск)",
        "Информационные системы и программирование (Ногинск)",
        "Информационные системы и программирование (Балашиха)",
        "Сетевое и системное администрирование (Балашиха)",
        "Сетевое и системное администрирование (Ногинск)",
        "Туризм и гостеприимство",
        "Технологии индустрии красоты",
        "Поварское и кондитерское дело",
        "Мастер слесарных работ",
        "Оператор информационных систем и ресурсов",
        "Юриспруденция",
        "Банковское дело"
    ]

    builder = ReplyKeyboardBuilder()
    for specialty in specialties:
        builder.add(types.KeyboardButton(text=specialty))
    builder.add(types.KeyboardButton(text="❌ Отмена регистрации"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


# Формируем контекст для ИИ
def get_ai_context():
    context = "Ты помощник приемной комиссии Ногинского колледжа. "
    context += "Используй следующую официальную информацию для ответов:\n\n"

    for title, content in faq_responses.items():
        context += f"## {title} ##\n{content}\n\n"

    context += (
        "Правила ответов:\n"
        "1. Если вопрос касается специальностей, документов, сроков - используй официальные данные\n"
        "2. На вопросы о поступлении отвечай максимально точно\n"
        "3. Если информация не указана, предложи уточнить по телефону\n"
        "4. Отвечай дружелюбно и профессионально\n"
        "5. Форматируй ответ: сначала точный ответ, затем дополнительные пояснения"
    )

    return context


# Очищаем HTML для ИИ
def clean_html(text):
    return re.sub('<[^<]+?>', '', text)


# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    user_id = message.from_user.id
    user_states[user_id] = "menu"
    conversation_history[user_id] = []

    keyboard = build_faq_keyboard()
    await message.answer(
        "🎓 <b>Привет! Я чат-бот Ногинского колледжа</b>\n\n"
        "Выберите интересующий вас вопрос из меню ниже или нажмите '📝 Регистрация' для записи на поступление:",
        reply_markup=keyboard
    )


# Обработчик команды /register
@dp.message(F.text == "📝 Регистрация")
@dp.message(Command("register"))
async def start_registration(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_states[user_id] = "registration"

    await state.set_state(RegistrationStates.full_name)
    await message.answer(
        "📝 <b>Регистрация абитуриента</b>\n\n"
        "Для записи в базу данных нам потребуется:\n"
        "1. Ваше полное ФИО\n"
        "2. Номер телефона\n"
        "3. Ваш Telegram тег\n"
        "4. Выбор специальности\n\n"
        "Введите ваше ФИО полностью:",
        reply_markup=types.ReplyKeyboardRemove()
    )


# Обработчик отмены регистрации
@dp.message(F.text == "❌ Отмена регистрации")
async def cancel_registration(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_states[user_id] = "menu"

    await state.clear()
    await message.answer(
        "❌ Регистрация отменена. Вы возвращены в главное меню.",
        reply_markup=build_faq_keyboard()
    )


# Шаг 1: Обработка ФИО
@dp.message(RegistrationStates.full_name)
async def process_full_name(message: Message, state: FSMContext):
    if len(message.text) < 5:
        await message.answer("❌ Пожалуйста, введите полное ФИО (минимум 5 символов)")
        return

    await state.update_data(full_name=message.text)
    await state.set_state(RegistrationStates.phone)
    await message.answer("✅ ФИО принято!\n\n📱 Теперь введите ваш номер телефона в формате +7XXXXXXXXXX:")


# Шаг 2: Обработка телефона
@dp.message(RegistrationStates.phone)
async def process_phone(message: Message, state: FSMContext):
    # Очищаем номер от лишних символов
    phone = re.sub(r'\D', '', message.text)

    # Проверяем формат номера
    if not phone.startswith('7') or len(phone) != 11:
        await message.answer("❌ Неверный формат телефона. Пожалуйста, введите номер в формате +7XXXXXXXXXX:")
        return

    await state.update_data(phone=f"+7{phone[1:]}")
    await state.set_state(RegistrationStates.telegram_tag)

    # Предлагаем использовать текущий username
    user_tag = f"@{message.from_user.username}" if message.from_user.username else "Не указан"
    await message.answer(
        f"✅ Номер телефона принят!\n\n"
        f"🔖 Ваш текущий Telegram тег: {user_tag}\n"
        "Если хотите использовать его, нажмите /skip\n"
        "Или введите новый Telegram тег (начинается с @):"
    )


# Шаг 3: Обработка Telegram тега
@dp.message(RegistrationStates.telegram_tag)
async def process_telegram_tag(message: Message, state: FSMContext):
    if message.text == "/skip":
        user_tag = f"@{message.from_user.username}" if message.from_user.username else "Не указан"
        await state.update_data(telegram_tag=user_tag)
    else:
        # Убираем @ если пользователь его ввел
        clean_tag = message.text.lstrip('@').strip()
        if not clean_tag:
            await message.answer("❌ Тег не может быть пустым. Пожалуйста, введите корректный Telegram тег:")
            return
        await state.update_data(telegram_tag=f"@{clean_tag}")

    await state.set_state(RegistrationStates.specialty)
    await message.answer(
        "✅ Telegram тег сохранен!\n\n"
        "🎓 Теперь выберите специальность из списка:",
        reply_markup=build_specialties_keyboard()
    )


# Шаг 4: Обработка специальности
@dp.message(RegistrationStates.specialty)
async def process_specialty(message: Message, state: FSMContext):
    if message.text == "❌ Отмена регистрации":
        await cancel_registration(message, state)
        return

    # Получаем данные из состояния
    user_data = await state.get_data()
    user_id = message.from_user.id

    # Сохраняем в базу данных
    try:
        conn = sqlite3.connect('applicants.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO applicants (user_id, full_name, phone, telegram_tag, specialty)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user_id,
            user_data['full_name'],
            user_data['phone'],
            user_data['telegram_tag'],
            message.text
        ))
        conn.commit()
    except Exception as e:
        logger.error(f"Ошибка при сохранении в БД: {e}")
        await message.answer(
            "❌ Произошла ошибка при сохранении данных. Пожалуйста, попробуйте позже.",
            reply_markup=build_faq_keyboard()
        )
        return
    finally:
        conn.close()

    # Очищаем состояние
    await state.clear()
    user_states[user_id] = "menu"

    # Формируем сообщение с результатами
    result_message = (
        "✅ <b>Регистрация завершена успешно!</b>\n\n"
        f"<b>Ваши данные:</b>\n"
        f"👤 <b>ФИО:</b> {user_data['full_name']}\n"
        f"📱 <b>Телефон:</b> {user_data['phone']}\n"
        f"🔖 <b>Telegram:</b> {user_data['telegram_tag']}\n"
        f"🎓 <b>Специальность:</b> {message.text}\n\n"
        "Спасибо за регистрацию! Теперь вы можете задавать вопросы о поступлении."
    )

    await message.answer(
        result_message,
        parse_mode=ParseMode.HTML,
        reply_markup=build_faq_keyboard()
    )


# Обработчик кнопок FAQ
@dp.message(lambda message: message.text in formatted_faq_responses)
async def handle_faq(message: Message):
    user_id = message.from_user.id
    response = formatted_faq_responses[message.text]

    # Если в режиме диалога - отправляем с диалоговой клавиатурой
    if user_states.get(user_id) == "ai_dialog":
        await message.answer(
            f"📋 <b>Официальная информация:</b>\n\n{response}",
            reply_markup=build_dialog_keyboard()
        )
    else:
        await message.answer(response)


# Обработчик кнопки "Задать свой вопрос"
@dp.message(lambda message: message.text == "Задать свой вопрос")
async def handle_custom_question(message: Message):
    user_id = message.from_user.id
    user_states[user_id] = "ai_dialog"

    # Инициализируем историю с контекстом
    conversation_history[user_id] = [
        {"role": "system", "content": get_ai_context()}
    ]

    await message.answer(
        "💬 <b>Режим диалога с помощником</b>\n\n"
        "Я знаю всю информацию о поступлении и могу ответить на ваши вопросы.\n"
        "Использую официальные данные колледжа для точных ответов.\n\n"
        "Вы также можете выбирать темы из меню ниже ⬇️",
        reply_markup=build_dialog_keyboard()
    )


# Обработчик завершения диалога
@dp.message(lambda message: message.text == "❌ Завершить диалог")
async def end_dialog(message: Message):
    user_id = message.from_user.id
    user_states[user_id] = "menu"

    keyboard = build_faq_keyboard()
    await message.answer(
        "✅ Диалог завершен. Вы вернулись в главное меню.",
        reply_markup=keyboard
    )


# Обработчик пользовательских вопросов в режиме диалога
@dp.message(lambda message: user_states.get(message.from_user.id) == "ai_dialog")
async def handle_ai_question(message: Message):
    user_id = message.from_user.id

    # Пропускаем команду завершения диалога
    if message.text == "❌ Завершить диалог":
        return

    # Если выбрана FAQ-кнопка - обрабатываем отдельно
    if message.text in formatted_faq_responses:
        await handle_faq(message)
        return

    # Проверяем, что сообщение текстовое
    if message.content_type != ContentType.TEXT:
        await message.answer(
            "❌ Я понимаю только текстовые сообщения. Пожалуйста, напишите ваш вопрос текстом.",
            reply_markup=build_dialog_keyboard()
        )
        return

    # Добавляем вопрос в историю диалога
    conversation_history[user_id].append({
        "role": "user",
        "content": message.text
    })

    try:
        # Отправляем запрос к OpenRouter API
        completion = api.chat.completions.create(
            model="deepseek/deepseek-r1-0528-qwen3-8b:free",
            messages=conversation_history[user_id],
            temperature=0.7,
            max_tokens=1024,
        )

        # Получаем ответ от API
        response = completion.choices[0].message.content.strip()

        # Проверка на пустой ответ
        if not response:
            raise ValueError("API вернул пустой ответ")

        # Добавляем ответ в историю диалога
        conversation_history[user_id].append({
            "role": "assistant",
            "content": response
        })

        # Отправляем ответ пользователю
        await message.answer(response, reply_markup=build_dialog_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при обработке вопроса {user_id}: {e}")

        # Пытаемся найти ответ в FAQ
        found = False
        for keyword, answer in formatted_faq_responses.items():
            if keyword.lower() in message.text.lower():
                await message.answer(
                    f"🔍 По вашему запросу найдено:\n\n{answer}",
                    reply_markup=build_dialog_keyboard()
                )
                found = True
                break

        if not found:
            await message.answer(
                "⚠️ Не удалось обработать запрос. Попробуйте переформулировать или выбрать тему из меню.",
                reply_markup=build_dialog_keyboard()
            )


# Обработчик для всех остальных сообщений
@dp.message()
async def handle_other_messages(message: Message):
    user_id = message.from_user.id
    current_state = user_states.get(user_id)

    # Если сообщение не текстовое
    if message.content_type != ContentType.TEXT:
        reply_markup = build_faq_keyboard() if current_state == "menu" else build_dialog_keyboard()
        await message.answer(
            "❌ Я понимаю только текстовые сообщения. Пожалуйста, используйте текстовые команды.",
            reply_markup=reply_markup
        )
        return

    # Текстовое сообщение, которое не было обработано другими обработчиками
    if current_state == "menu":
        # Попробуем найти ответ в FAQ
        found = False
        for keyword, answer in formatted_faq_responses.items():
            if keyword.lower() in message.text.lower():
                await message.answer(answer, reply_markup=build_faq_keyboard())
                found = True
                break

        if not found:
            keyboard = build_faq_keyboard()
            await message.answer(
                "🤔 Пожалуйста, выберите вопрос из меню или нажмите 'Задать свой вопрос'",
                reply_markup=keyboard
            )
    elif current_state == "ai_dialog":
        await handle_ai_question(message)
    else:
        user_states[user_id] = "menu"
        keyboard = build_faq_keyboard()
        await message.answer(
            "🔄 Возвращаю вас в главное меню",
            reply_markup=keyboard
        )

ADMIN_IDS = [564492066]


# Проверка прав администратора
def is_admin(user_id):
    return user_id in ADMIN_IDS


# Команда /start для админ-бота
@admin_dp.message(Command("start"))
async def admin_start(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав доступа к этой панели")
        return

    await message.answer(
        "👮‍♂️ <b>Панель администратора Ногинского колледжа</b>\n\n"
        "Доступные команды:\n"
        "/view - Просмотр всех заявок\n"
        "/count - Количество зарегистрированных\n"
        "/stats - Статистика по специальностям\n"
        "/search - Поиск по имени или телефону\n"
        "/help - Справка по командам",
        parse_mode=ParseMode.HTML
    )


# Просмотр всех заявок
@admin_dp.message(Command("view"))
async def view_applicants(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав доступа к этой команде")
        return

    try:
        conn = sqlite3.connect('applicants.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applicants ORDER BY registration_date DESC")
        applicants = cursor.fetchall()

        if not applicants:
            await message.answer("ℹ️ В базе данных пока нет зарегистрированных абитуриентов")
            return

        response = "📋 <b>Список зарегистрированных абитуриентов:</b>\n\n"

        for applicant in applicants:
            response += (
                f"🆔 <b>ID:</b> {applicant[0]}\n"
                f"👤 <b>ФИО:</b> {applicant[2]}\n"
                f"📱 <b>Телефон:</b> {applicant[3]}\n"
                f"🔖 <b>Telegram:</b> {applicant[4]}\n"
                f"🎓 <b>Специальность:</b> {applicant[5]}\n"
                f"📅 <b>Дата регистрации:</b> {applicant[6]}\n"
                f"👤 <b>User ID:</b> {applicant[1]}\n"
                f"────────────────────\n"
            )

            # Отправляем сообщения порциями по 5 записей
            if applicants.index(applicant) % 5 == 4:
                await message.answer(response, parse_mode=ParseMode.HTML)
                response = ""

        # Отправляем оставшиеся записи
        if response:
            await message.answer(response, parse_mode=ParseMode.HTML)

        await message.answer(f"✅ Всего зарегистрировано: {len(applicants)} абитуриентов")

    except Exception as e:
        logger.error(f"Ошибка при получении данных: {e}")
        await message.answer("❌ Произошла ошибка при получении данных из базы")
    finally:
        conn.close()


# Статистика по количеству заявок
@admin_dp.message(Command("count"))
async def count_applicants(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав доступа к этой команде")
        return

    try:
        conn = sqlite3.connect('applicants.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM applicants")
        count = cursor.fetchone()[0]

        await message.answer(f"👥 <b>Общее количество зарегистрированных абитуриентов:</b> {count}",
                             parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Ошибка при подсчете записей: {e}")
        await message.answer("❌ Произошла ошибка при получении данных")
    finally:
        conn.close()


# Статистика по специальностям
@admin_dp.message(Command("stats"))
async def specialty_stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав доступа к этой команде")
        return

    try:
        conn = sqlite3.connect('applicants.db')
        cursor = conn.cursor()
        cursor.execute("SELECT specialty, COUNT(*) FROM applicants GROUP BY specialty ORDER BY COUNT(*) DESC")
        stats = cursor.fetchall()

        if not stats:
            await message.answer("ℹ️ Нет данных для отображения статистики")
            return

        response = "📊 <b>Статистика по специальностям:</b>\n\n"
        total = 0

        for row in stats:
            response += f"🎓 <b>{row[0]}</b>: {row[1]} чел.\n"
            total += row[1]

        response += f"\n<b>Итого:</b> {total} абитуриентов"

        await message.answer(response, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await message.answer("❌ Произошла ошибка при получении статистики")
    finally:
        conn.close()


# Поиск по имени или телефону
@admin_dp.message(Command("search"))
async def search_applicants(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав доступа к этой команде")
        return

    # Получаем поисковый запрос из сообщения
    search_query = message.text.split(' ', 1)
    if len(search_query) < 2 or not search_query[1].strip():
        await message.answer(
            "ℹ️ Пожалуйста, укажите поисковый запрос после команды /search\nНапример: <code>/search Иванов</code>",
            parse_mode=ParseMode.HTML)
        return

    search_term = f"%{search_query[1].strip()}%"

    try:
        conn = sqlite3.connect('applicants.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM applicants 
            WHERE full_name LIKE ? OR phone LIKE ?
            ORDER BY registration_date DESC
        """, (search_term, search_term))

        applicants = cursor.fetchall()

        if not applicants:
            await message.answer("🔍 По вашему запросу ничего не найдено")
            return

        response = f"🔍 <b>Результаты поиска по запросу '{search_query[1]}':</b>\n\n"

        for applicant in applicants:
            response += (
                f"👤 <b>ФИО:</b> {applicant[2]}\n"
                f"📱 <b>Телефон:</b> {applicant[3]}\n"
                f"🔖 <b>Telegram:</b> {applicant[4]}\n"
                f"🎓 <b>Специальность:</b> {applicant[5]}\n"
                f"📅 <b>Дата регистрации:</b> {applicant[6]}\n"
                f"────────────────────\n"
            )

            # Отправляем сообщения порциями по 3 записи
            if applicants.index(applicant) % 3 == 2:
                await message.answer(response, parse_mode=ParseMode.HTML)
                response = ""

        # Отправляем оставшиеся записи
        if response:
            await message.answer(response, parse_mode=ParseMode.HTML)

        await message.answer(f"✅ Найдено записей: {len(applicants)}")

    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        await message.answer("❌ Произошла ошибка при выполнении поиска")
    finally:
        conn.close()


# Помощь по командам
@admin_dp.message(Command("help"))
async def admin_help(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет прав доступа к этой команде")
        return

    help_text = (
        "📚 <b>Справка по командам админ-панели:</b>\n\n"
        "/start - Запустить админ-панель\n"
        "/view - Просмотреть всех зарегистрированных абитуриентов\n"
        "/count - Показать общее количество заявок\n"
        "/stats - Статистика по специальностям\n"
        "/search [запрос] - Поиск по имени или телефону\n"
        "/help - Показать эту справку\n\n"
        "Примеры использования:\n"
        "<code>/search Иванов</code> - поиск по фамилии\n"
        "<code>/search +7916</code> - поиск по номеру телефона"
    )

    await message.answer(help_text, parse_mode=ParseMode.HTML)


# Запуск обоих ботов
async def main():
    await asyncio.gather(
        dp.start_polling(bot),
        admin_dp.start_polling(admin_bot)
    )


if __name__ == '__main__':
    asyncio.run(main())
