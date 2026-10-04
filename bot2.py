import os
import requests
from flask import Flask
from threading import Thread
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ==========================================
# 1. ИНИЦИАЛИЗАЦИЯ И ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
# ==========================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище выбора пользователей (в памяти)
user_data = {}

# ==========================================
# 2. ФУНКЦИЯ ДЛЯ ЗАПРОСА К OPENROUTER (GEMINI)
# ==========================================
def ask_gemini(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://myprofi-bot.onrender.com",
        "X-Title": "MyProfiKG Bot"
    }
    
    # Используем бесплатный вариативный идентификатор модели OpenRouter
    payload = {
        "model": "google/gemini-2.0-flash-lite-001:free",  # Или "openrouter/free"
        "messages": [
            {
                "role": "system",
                "content": "Ты — Барсбек, интеллектуальный ассистент профориентации и выбора ВУЗов MyProfiKG. Отвечай вежливо, четко, структурированно и с использованием эмодзи."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        data = response.json()
        
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"]
        elif "error" in data:
            # Резервный вариант, если указанная модель недоступна
            payload["model"] = "openrouter/free"
            res2 = requests.post(url, json=payload, headers=headers, timeout=30)
            data2 = res2.json()
            if "choices" in data2 and len(data2["choices"]) > 0:
                return data2["choices"][0]["message"]["content"]
            return f"Ошибка ИИ: {data['error'].get('message', 'Неизвестная ошибка')}"
        else:
            return "Не удалось получить ответ от ИИ. Попробуйте позже."
            
    except Exception as e:
        return f"Произошла ошибка при обращении к ИИ: {str(e)}"

# ==========================================
# 3. КЛАВИАТУРЫ ДЛЯ ТЕЛЕГРАМ БОТА
# ==========================================
def get_language_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("🇷🇺 Русский"), KeyboardButton("🇰🇬 Кыргызча"))
    markup.add(KeyboardButton("🇬🇧 English"), KeyboardButton("🇹🇷 Türkçe"))
    return markup

def get_country_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("🇰🇬 Кыргызстан"), KeyboardButton("🇺🇸 США"))
    markup.add(KeyboardButton("🇩🇪 Германия"), KeyboardButton("🇹🇷 Турция"))
    markup.add(KeyboardButton("🇷🇺 Россия"), KeyboardButton("🇨🇳 Китай"))
    return markup

def get_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🏛 Подбор ВУЗов"), KeyboardButton("📋 Условия поступления"))
    markup.add(KeyboardButton("💡 Выбор профессии"), KeyboardButton("⚙️ Сменить страну/язык"))
    return markup

# ==========================================
# 4. ОБРАБОТЧИКИ КОМАНД И СООБЩЕНИЙ
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "Салам! Мен Барсбекмин 🐆 / Здравствуйте! Я Барсбек 🐆 / "
        "Hello! I am Barsbek 🐆 / Merhaba! Ben Barsbek 🐆\n\n"
        "Выбери язык / Тилди тандаңыз / Select language / Dil seçin:"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_language_keyboard())

@bot.message_handler(func=lambda msg: msg.text in ["🇷🇺 Русский", "🇰🇬 Кыргызча", "🇬🇧 English", "🇹🇷 Türkçe"])
def set_language(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]['lang'] = message.text
    
    text = "Тепер выбор страны / Өлкөнү тандаңыз / Select country / Ülke seçin:"
    bot.send_message(chat_id, text, reply_markup=get_country_keyboard())

@bot.message_handler(func=lambda msg: msg.text in ["🇰🇬 Кыргызстан", "🇺🇸 США", "🇩🇪 Германия", "🇹🇷 Турция", "🇷🇺 Россия", "🇨🇳 Китай"])
def set_country(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]['country'] = message.text
    
    bot.send_message(
        chat_id, 
        f"Выбрана страна: {message.text} 🎯\nЯ Барсбек, готов помочь!", 
        reply_markup=get_main_keyboard()
    )

@bot.message_handler(func=lambda msg: msg.text == "⚙️ Сменить страну/язык")
def reset_settings(message):
    send_welcome(message)

@bot.message_handler(func=lambda msg: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    user_info = user_data.get(chat_id, {})
    lang = user_info.get('lang', '🇷🇺 Русский')
    country = user_info.get('country', '🇰🇬 Кыргызстан')
    
    bot.send_chat_action(chat_id, 'typing')
    
    prompt = (
        f"Пользователь спрашивает: '{message.text}'.\n"
        f"Язык ответа: {lang}.\n"
        f"Интересующая страна для образования: {country}.\n"
        f"Предоставь исчерпывающий, понятный и полезный ответ."
    )
    
    response_text = ask_gemini(prompt)
    bot.reply_to(message, response_text, reply_markup=get_main_keyboard())

# ==========================================
# 5. FLASK СЕРВЕР ДЛЯ РАБОТЫ НА RENDER
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "MyProfiKG Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ==========================================
# 6. ЗАПУСК
# ==========================================
if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.start()
    
    print("Бот Барсбек успешно запущен...")
    bot.infinity_polling(skip_pending_updates=True)
