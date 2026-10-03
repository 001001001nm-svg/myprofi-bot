import telebot
from telebot import types
import requests

TELEGRAM_TOKEN = "8891087735:AAEtEcdQJxMuWVt5jTOq199tOpm4eLO_gQE"
OPENROUTER_KEY = "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"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Хранилище данных пользователей
user_data = {}

LANG_NAMES = {
    "ru": "Русский",
    "kg": "Кыргызча (Кыргыз тили)",
    "en": "English",
    "tr": "Türkçe"
}

# Функция для создания нижних кнопок меню
def get_main_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_new = types.KeyboardButton("🔄 Новый диалог")
    btn_profile = types.KeyboardButton("🚀 Мой путь")
    btn_lang = types.KeyboardButton("🌐 Изменить язык")
    btn_plus = types.KeyboardButton("➕ Плюсы")
    btn_minus = types.KeyboardButton("➖ Минусы")
    btn_salary = types.KeyboardButton("💰 Какая зарплата")
    btn_study = types.KeyboardButton("🎓 Куда поступать")
    
    keyboard.add(btn_new, btn_profile)
    keyboard.add(btn_lang)
    keyboard.add(btn_plus, btn_minus)
    keyboard.add(btn_salary, btn_study)
    return keyboard

def get_language_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        types.InlineKeyboardButton(text="🇰🇬 Кыргызча", callback_data="lang_kg"),
        types.InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
        types.InlineKeyboardButton(text="🇹🇷 Türkçe", callback_data="lang_tr")
    ]
    keyboard.add(*buttons)
    return keyboard

@bot.message_handler(commands=['start', 'new'])
def send_welcome(message):
    chat_id = message.chat.id
    user_data[chat_id] = {
        "lang": "ru",
        "step": "lang",
        "name": "",
        "age": "",
        "grade": "",
        "history": []
    }
    
    welcome_text = (
        "Саламатсызбы! 👋 Тилди тандаңыз / Пожалуйста, выберите язык:\n\n"
        "🌐 Choose your preferred language:"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=get_language_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def callback_lang(call):
    chat_id = call.message.chat.id
    lang_code = call.data.split("_")[1]
    
    if chat_id not in user_data:
        user_data[chat_id] = {"history": [], "lang": lang_code, "step": "chat"}
    
    user_data[chat_id]["lang"] = lang_code
    
    bot.answer_callback_query(call.id)
    
    # Если мы сменяем язык во время готового профиля
    if user_data[chat_id].get("step") == "chat":
        confirm_msgs = {
            "ru": "Язык успешно изменён! 🌐 Чем я могу тебе помочь?",
            "kg": "Тил ийгиликтүү алмаштырылды! 🌐 Сизге кантип жардам бере алам?",
            "en": "Language successfully changed! 🌐 How can I help you?",
            "tr": "Dil başarıyla değiştirildi! 🌐 Size nasıl yardımcı olabilirim?"
        }
        bot.send_message(chat_id, confirm_msgs.get(lang_code, confirm_msgs["ru"]), reply_markup=get_main_menu_keyboard())
        return

    # Первичная настройка (анкетирование)
    user_data[chat_id]["step"] = "ask_name"
    if lang_code == "kg":
        bot.send_message(chat_id, "Эң сонун! 🌟 Атыңыз ким? Атыңызды жазыңыз:")
    elif lang_code == "en":
        bot.send_message(chat_id, "Great! 🌟 What is your name?")
    elif lang_code == "tr":
        bot.send_message(chat_id, "Harika! 🌟 Adınız nedir?")
    else:
        bot.send_message(chat_id, "Отлично! 🌟 Как тебя зовут? Напиши своё имя:")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    user_text = message.text
    
    if chat_id not in user_data:
        send_welcome(message)
        return

    lang = user_data[chat_id].get("lang", "ru")
    step = user_data[chat_id].get("step", "chat")

    # Обработка нажатий на кнопки меню
    if user_text == "🔄 Новый диалог":
        send_welcome(message)
        return
    elif user_text == "🚀 Мой путь":
        show_profile(message)
        return
    elif user_text == "🌐 Изменить язык":
        welcome_text = (
            "Тилди тандаңыз / Пожалуйста, выберите язык / Choose your language:"
        )
        bot.send_message(chat_id, welcome_text, reply_markup=get_language_keyboard())
        return
    elif user_text == "➕ Плюсы":
        user_text = "Расскажи подробно про ПЛЮСЫ этой профессии, о которой мы говорили!"
    elif user_text == "➖ Минусы":
        user_text = "Расскажи подробно про МИНУСЫ и сложности этой профессии, о которой мы говорили!"
    elif user_text == "💰 Какая зарплата":
        user_text = "Какая зарплата у этой профессии в Кыргызстане?"
    elif user_text == "🎓 Куда поступать":
        user_text = "В какие ВУЗы или колледжи Кыргызстана лучше всего поступать на эту специальность?"

    # Пошаговое анкетирование
    if step == "ask_name":
        user_data[chat_id]["name"] = user_text
        user_data[chat_id]["step"] = "ask_age"
        if lang == "kg":
            bot.send_message(chat_id, f"Таанышканыма кубанычтамын, {user_text}! 👋 Жашыңыз канчада?")
        else:
            bot.send_message(chat_id, f"Рад знакомству, {user_text}! 👋 Сколько тебе лет?")
        return

    elif step == "ask_age":
        user_data[chat_id]["age"] = user_text
        user_data[chat_id]["step"] = "ask_grade"
        if lang == "kg":
            bot.send_message(chat_id, "Сонун! 🎯 Канчанчы класста (же курста) окуйсуз?")
        else:
            bot.send_message(chat_id, "Супер! 🎯 В каком классе ты учишься (или на каком курсе)?")
        return

    elif step == "ask_grade":
        user_data[chat_id]["grade"] = user_text
        user_data[chat_id]["step"] = "chat"
        name = user_data[chat_id]["name"]
        
        if lang == "kg":
            text = f"Эң сонун, {name}! 🎉 Профилиңиз даяр!\n\nМага каалаган сурооңузду бериңиз: кесиптер, жогорку окуу жайлар, ЖРТ же айлык акы жөнүндө. Мен жардам берүүгө даярмын! 🚀"
        else:
            text = f"Замечательно, {name}! 🎉 Теперь наш профиль настроен!\n\nЗадай мне любой вопрос: про профессии, ВУЗы, ОРТ или зарплаты. Я готов помогать! 🚀"
            
        bot.send_message(chat_id, text, reply_markup=get_main_menu_keyboard())
        return

    # Генерация ответа ИИ с использованием заданного языка
    bot.send_chat_action(chat_id, 'typing')

    history = user_data[chat_id].get("history", [])
    selected_lang_name = LANG_NAMES.get(lang, "Русский")

    system_prompt = f"""
Ты — позитивный, доброжелательный и вдохновляющий эксперт по профориентации MyProfiKG в Кыргызстане! 🎯🌟

КРИТИЧЕСКИ ВАЖНОЕ ПРАВИЛО:
Отвечай СТРОГО на языке: {selected_lang_name}! 
Если выбран Кыргызча — отвечай ТОЛЬКО на кыргызском языке!

Твои правила общения:
1. Используй эмодзи 🚀🎓💡✨, чтобы текст выглядел живым и интересным.
2. Будь на позитиве, поддерживай пользователя и немного хвали за хорошие цели и вопросы.
3. Учитывай данные пользователя: Имя={user_data[chat_id].get('name')}, Возраст={user_data[chat_id].get('age')}, Класс={user_data[chat_id].get('grade')}.
4. Запоминай предыдущий контекст бесед.
"""

    messages_payload = [{"role": "system", "content": system_prompt}]
    
    for h in history[-6:]:
        messages_payload.append(h)
        
    messages_payload.append({"role": "user", "content": user_text})

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages_payload
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            result = response.json()
            ai_answer = result["choices"][0]["message"]["content"]
            
            user_data[chat_id]["history"].append({"role": "user", "content": user_text})
            user_data[chat_id]["history"].append({"role": "assistant", "content": ai_answer})
            
            try:
                bot.send_message(chat_id, ai_answer, parse_mode='Markdown', reply_markup=get_main_menu_keyboard())
            except Exception:
                bot.send_message(chat_id, ai_answer, reply_markup=get_main_menu_keyboard())
        else:
            bot.send_message(chat_id, "Упс! Возникла небольшая ошибка. Попробуй ещё раз чуть позже! 😅", reply_markup=get_main_menu_keyboard())
    except Exception:
        bot.send_message(chat_id, "Ошибка соединения. Проверь интернет и попробуй снова! 🌐", reply_markup=get_main_menu_keyboard())

def show_profile(message):
    chat_id = message.chat.id
    info = user_data.get(chat_id, {})
    name = info.get("name", "Не указано")
    age = info.get("age", "Не указан")
    grade = info.get("grade", "Не указан")
    
    text = (
        f"🚀 *Твой путь в MyProfiKG*:\n\n"
        f"👤 *Имя:* {name}\n"
        f"🎂 *Возраст:* {age}\n"
        f"📚 *Класс/Курс:* {grade}\n\n"
        f"Ты на верном пути к своей мечте! 🌟"
    )
    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=get_main_menu_keyboard())

try:
    bot.remove_webhook()
except Exception:
    pass

print("Бот MyProfiKG с выбором языка запущен!")
bot.infinity_polling()