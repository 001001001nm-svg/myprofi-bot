import os
import telebot
from telebot import types
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Хранилище выбранных стран
user_countries = {}

COUNTRIES = ["🇰🇬 Кыргызстан", "🇹🇷 Турция", "🇺🇸 США", "🇨🇳 Китай", "🇰🇷 Южная Корея", "🇨🇦 Канада"]

def get_country_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🇰🇬 Кыргызстан", "🇹🇷 Турция")
    markup.row("🇺🇸 США", "🇨🇳 Китай")
    markup.row("🇰🇷 Южная Корея", "🇨🇦 Канада")
    return markup

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📋 Условия поступления", "🔄 Сменить страну")
    return markup

def ask_ai(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "google/gemini-2.0-flash-lite-001",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return "Произошла ошибка при обращении к ИИ. Попробуй еще раз."

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "Привет! Я твой профориентационный AI-помощник MyProfiKG 🎓\n\n"
        "Выбери страну, в которой ты планируешь поступать в ВУЗ:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_country_keyboard())

@bot.message_handler(commands=['change_country'])
def change_country(message):
    bot.send_message(message.chat.id, "Выбери новую страну для поступления:", reply_markup=get_country_keyboard())

@bot.message_handler(commands=['requirements'])
def requirements(message):
    user_id = message.from_user.id
    country = user_countries.get(user_id, "Кыргызстан")
    
    prompt = (
        f"Пользователь спрашивает про условия поступления в ВУЗы страны: {country}.\n"
        f"Расскажи подробно:\n"
        f"1. Основные экзамены и баллы (для КР — ОРТ, для США — SAT/TOEFL, для Турции — YÖS и т.д.).\n"
        f"2. Необходимые документы.\n"
        f"3. Языковые требования.\n"
        f"4. Сроки подачи."
    )
    
    wait_msg = bot.send_message(message.chat.id, "⏳ Собираю актуальную информацию об условиях поступления...")
    ai_response = ask_ai(prompt)
    bot.edit_message_text(ai_response, message.chat.id, wait_msg.message_id)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text

    if text in COUNTRIES:
        user_countries[user_id] = text
        bot.send_message(
            message.chat.id,
            f"Отлично! Выбрана страна: *{text}* 🎯\n\n"
            f"Теперь все рекомендации по ВУЗам будут касаться только этой страны.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return

    if text == "🔄 Сменить страну":
        change_country(message)
        return
    elif text == "📋 Условия поступления":
        requirements(message)
        return

    selected_country = user_countries.get(user_id, "Кыргызстан")

    system_prompt = (
        f"Ты — профориентационный AI-консультант MyProfiKG.\n"
        f"Выбранная страна пользователя: {selected_country}.\n"
        f"Отвечай на вопросы про ВУЗы и образование ИСКЛЮЧИТЕЛЬНО для страны {selected_country}."
    )

    full_prompt = f"{system_prompt}\n\nВопрос: {text}"
    wait_msg = bot.send_message(message.chat.id, "Думаю... 🧠")

    ai_response = ask_ai(full_prompt)
    bot.edit_message_text(ai_response, message.chat.id, wait_msg.message_id)

if __name__ == "__main__":
    bot.polling(none_stop=True)
