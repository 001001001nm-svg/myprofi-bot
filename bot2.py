import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import google.generativeai as genai

# 1. Настройка Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# Хранилище стран пользователей (в памяти)
# Для боевого проекта лучше использовать БД (SQLite / PostgreSQL)
user_countries = {}

# Список доступных стран
COUNTRIES = ["🇰🇬 Кыргызстан", "🇹🇷 Турция", "🇺🇸 США", "🇨🇳 Китай", "🇰🇷 Южная Корея", "🇨🇦 Канада"]

def get_country_keyboard():
    """Клавиатура выбора стран"""
    keyboard = [
        [KeyboardButton("🇰🇬 Кыргызстан"), KeyboardButton("🇹🇷 Турция")],
        [KeyboardButton("🇺🇸 США"), KeyboardButton("🇨🇳 Китай")],
        [KeyboardButton("🇰🇷 Южная Корея"), KeyboardButton("🇨🇦 Канада")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_main_keyboard():
    """Главная клавиатура после выбора страны"""
    keyboard = [
        [KeyboardButton("📋 Условия поступления"), KeyboardButton("🔄 Сменить страну")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    welcome_text = (
        "Привет! Я твой профориентационный AI-помощник MyProfiKG 🎓\n\n"
        "Выбери страну, в которой ты планируешь поступать в ВУЗ:"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_country_keyboard())

# Команда или кнопка "Сменить страну"
async def change_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выбери новую страну для поступления:",
        reply_markup=get_country_keyboard()
    )

# Команда или кнопка "Условия поступления"
async def requirements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    country = user_countries.get(user_id, "не выбрана (по умолчанию Кыргызстан)")
    
    prompt = (
        f"Пользователь спрашивает про условия поступления в ВУЗы страны: {country}.\n"
        f"Расскажи подробно и структурировано:\n"
        f"1. Основные экзамены и баллы (для Кыргызстана — про ОРТ и пороговые баллы, для США — SAT/TOEFL, для Турции — YÖS/TR-YÖS и т.д.).\n"
        f"2. Необходимые документы.\n"
        f"3. Языковые требования.\n"
        f"4. Сроки подачи документов.\n"
        f"Пиши понятно, используй эмодзи и списки."
    )
    
    waiting_msg = await update.message.reply_text("⏳ Собираю актуальную информацию об условиях поступления...")
    
    try:
        response = model.generate_content(prompt)
        await waiting_msg.edit_text(response.text)
    except Exception as e:
        await waiting_msg.edit_text("Произошла ошибка при получении данных. Попробуй еще раз чуть позже.")

# Обработчик всех текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Если пользователь выбрал страну из списка
    if text in COUNTRIES:
        user_countries[user_id] = text
        await update.message.reply_text(
            f"Отлично! Выбрана страна: **{text}** 🎯\n\n"
            f"Теперь все мои ответы и рекомендации по ВУЗам и профессиям будут касаться только этой страны.\n"
            f"Задай мне любой вопрос или нажми «📋 Условия поступления»!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return

    # Обработка нажатий на текстовые кнопки меню
    if text == "🔄 Сменить страну":
        await change_country(update, context)
        return
    elif text == "📋 Условия поступления":
        await requirements(update, context)
        return

    # Получаем текущую страну пользователя (если не выбрана — ставим Кыргызстан)
    selected_country = user_countries.get(user_id, "Кыргызстан")

    # Формируем системный промпт
    system_prompt = (
        f"Ты — экспертный профориентационный AI-консультант MyProfiKG.\n"
        f"Текущая выбранная страна пользователя: {selected_country}.\n"
        f"СТРОГОЕ ПРАВИЛО: Отвечай на вопросы пользователя, касающиеся ВУЗов, профессий, "
        f"грантов, стипендий и образования, ИСКЛЮЧИТЕЛЬНО применительно к стране: {selected_country}.\n"
        f"Если пользователь спрашивает про другие страны, напомни ему, что можно сменить страну в меню кнопкой '🔄 Сменить страну'.\n"
        f"Отвечай вежливо, структурировано, на языке пользователя."
    )

    full_prompt = f"{system_prompt}\n\nВопрос пользователя: {text}"

    waiting_msg = await update.message.reply_text("Thinking... 🧠")

    try:
        response = model.generate_content(full_prompt)
        await waiting_msg.edit_text(response.text)
    except Exception as e:
        await waiting_msg.edit_text("Не удалось получить ответ от ИИ. Попробуй переформулировать вопрос.")

# Настройка меню команд Telegram (возле скрепки)
async def post_init(application: Application):
    commands = [
        BotCommand("start", "Запустить бота / Перевыбрать страну"),
        BotCommand("change_country", "Сменить страну поступления"),
        BotCommand("requirements", "Условия поступления (ОРТ, экзамены)")
    ]
    await application.bot.set_my_commands(commands)

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Ошибка: Не задан TELEGRAM_BOT_TOKEN")
        return

    app = Application.builder().token(token).post_init(post_init).build()

    # Хэндлеры команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("change_country", change_country))
    app.add_handler(CommandHandler("requirements", requirements))

    # Хэндлер сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
