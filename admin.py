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

# ... (Здесь должен быть весь ваш существующий код для основного бота) ...

# ===========================================================================
# Код для админ-бота (начинается здесь)
# ===========================================================================

# Список разрешенных администраторов (добавьте свои Telegram ID)
ADMIN_IDS = [123456789, 987654321]  # Замените на ваши реальные ID


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