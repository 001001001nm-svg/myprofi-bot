import os
import telebot
from telebot import types
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не найдена в Environment Variables!")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Состояния пользователей: {user_id: {"lang": "🇷🇺 Русский", "country": "🇺🇸 США", "notes": [], "state": None}}
user_states = {}

LANGUAGES = ["🇷🇺 Русский", "🇰🇬 Кыргызча", "🇬🇧 English", "🇹🇷 Türkçe"]
COUNTRIES = ["🇰🇬 Кыргызстан", "🇹🇷 Турция", "🇺🇸 США", "🇨🇳 Китай", "🇰🇷 Южная Корея", "🇨🇦 Канада"]

# Клавиатуры
def get_language_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row("🇷🇺 Русский", "🇰🇬 Кыргызча")
    markup.row("🇬🇧 English", "🇹🇷 Türkçe")
    return markup

def get_country_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row("🇰🇬 Кыргызстан", "🇹🇷 Турция")
    markup.row("🇺🇸 США", "🇨🇳 Китай")
    markup.row("🇰🇷 Южная Корея", "🇨🇦 Канада")
    return markup

def get_main_keyboard(lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "🇰🇬 Кыргызча":
        markup.row("📋 Талаптар жана сынактар", "🏛 ЖОЖдорду тандоо")
        markup.row("📄 Керектүү документтер", "⚖️ Артыкчылыктар жана кемчиликтер")
        markup.row("🗺 Менин жолум", "📝 Менин дептерим")
        markup.row("🌍 Өлкөнү алмаштыруу", "🌐 Тилди алмаштыруу")
        markup.row("🔄 Жаңы диалог баштоо")
    elif lang == "🇬🇧 English":
        markup.row("📋 Admission Requirements", "🏛 Select Universities")
        markup.row("📄 Required Documents", "⚖️ Pros and Cons")
        markup.row("🗺 My Roadmap", "📝 My Notepad")
        markup.row("🌍 Change Country", "🌐 Change Language")
        markup.row("🔄 Start New Dialogue")
    elif lang == "🇹🇷 Türkçe":
        markup.row("📋 Başvuru Şartları", "🏛 Üniversite Seçimi")
        markup.row("📄 Gerekli Belgeler", "⚖️ Artıları ve Eksileri")
        markup.row("🗺 Yol Haritam", "📝 Not Defterim")
        markup.row("🌍 Ülke Değiştir", "🌐 Dili Değiştir")
        markup.row("🔄 Yeni Sohbet Başlat")
    else:  # Русский по умолчанию
        markup.row("📋 Условия поступления", "🏛 Подбор ВУЗов")
        markup.row("📄 Необходимые документы", "⚖️ Плюсы и Минусы")
        markup.row("🗺 Мой путь", "📝 Мой блокнот")
        markup.row("🌍 Сменить страну", "🌐 Сменить язык")
        markup.row("🔄 Начать новый диалог")
    return markup

def get_notepad_keyboard(lang):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if lang == "🇰🇬 Кыргызча":
        markup.row("➕ Жаңы жазуу кошуу", "🗑 Дептерди тазалоо")
        markup.row("🔙 Башкы меню")
    elif lang == "🇬🇧 English":
        markup.row("➕ Add Note", "🗑 Clear Notepad")
        markup.row("🔙 Main Menu")
    elif lang == "🇹🇷 Türkçe":
        markup.row("➕ Not Ekle", "🗑 Notları Temizle")
        markup.row("🔙 Ana Menü")
    else:
        markup.row("➕ Добавить заметку", "🗑 Очистить блокнот")
        markup.row("🔙 Главное меню")
    return markup

# Функция обращения к ИИ OpenRouter
def ask_ai(prompt, system_instruction):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://render.com",
        "X-Title": "Barsbek"
    }
    data = {
        "model": "google/gemini-2.0-flash-lite-001",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            print(f"OpenRouter Error: {result}")
            return "Ошибка при обработке ответа ИИ. Проверь API-ключ OpenRouter."
    except Exception as e:
        print(f"Request exception: {e}")
        return "Ошибка соединения с ИИ. Попробуй позже."

# Команда /start - Выбор языка
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_states[user_id] = {"lang": None, "country": None, "notes": [], "state": None}
    
    msg = (
        "Салам! Мен Барсбекмин 🐆 / Здравствуйте! Я Барсбек 🐆 / "
        "Hello! I am Barsbek 🐆 / Merhaba! Ben Barsbek 🐆\n\n"
        "Выбери язык / Тилди тандаңыз / Select language / Dil seçin:"
    )
    bot.send_message(message.chat.id, msg, reply_markup=get_language_keyboard())

# Обработка сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text

    # Инициализация пользователя
    if user_id not in user_states:
        user_states[user_id] = {"lang": "🇷🇺 Русский", "country": "🇰🇬 Кыргызстан", "notes": [], "state": None}

    user_data = user_states[user_id]
    lang = user_data.get("lang", "🇷🇺 Русский")

    # Обработка состояния ввода заметки
    if user_data.get("state") == "WAITING_FOR_NOTE":
        user_data["notes"].append(text)
        user_data["state"] = None
        bot.send_message(message.chat.id, "✅ Заметка успешно сохранена!", reply_markup=get_notepad_keyboard(lang))
        return

    # Переход в Главное меню
    if text in ["🔙 Главное меню", "🔙 Башкы меню", "🔙 Main Menu", "🔙 Ana Menü"]:
        bot.send_message(message.chat.id, "Главное меню:", reply_markup=get_main_keyboard(lang))
        return

    # Начало нового диалога
    if text in ["🔄 Начать новый диалог", "🔄 Жаңы диалог баштоо", "🔄 Start New Dialogue", "🔄 Yeni Sohbet Başlat"]:
        start(message)
        return

    # 1. Выбор языка
    if text in LANGUAGES:
        user_data["lang"] = text
        if text == "🇰🇬 Кыргызча":
            msg = "Тил тандалды! Эми окууга тапшыра турган өлкөнү тандаңыз:"
        elif text == "🇬🇧 English":
            msg = "Language selected! Now choose the country where you plan to study:"
        elif text == "🇹🇷 Türkçe":
            msg = "Dil seçildi! Şimdi okumak istediğiniz ülkeyi seçin:"
        else:
            msg = "Язык выбран! Теперь выбери страну, в которой планируешь поступать в ВУЗ:"
        
        bot.send_message(message.chat.id, msg, reply_markup=get_country_keyboard())
        return

    # 2. Выбор страны
    if text in COUNTRIES:
        user_data["country"] = text
        lang = user_data.get("lang", "🇷🇺 Русский")
        
        if lang == "🇰🇬 Кыргызча":
            msg = f"Тандалган өлкө: *{text}* 🎯\nМен Барсбекмин, сизге жардам берүүгө даярмын!"
        elif lang == "🇬🇧 English":
            msg = f"Selected country: *{text}* 🎯\nI'm Barsbek, ready to help!"
        elif lang == "🇹🇷 Türkçe":
            msg = f"Seçilen ülke: *{text}* 🎯\nBen Barsbek, size yardımcı olmaya hazırım!"
        else:
            msg = f"Выбрана страна: *{text}* 🎯\nЯ Барсбек, готов помочь!"

        bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=get_main_keyboard(lang))
        return

    # 3. Блокнот
    if text in ["📝 Мой блокнот", "📝 Менин дептерим", "📝 My Notepad", "📝 Not Defterim"]:
        notes = user_data.get("notes", [])
        if not notes:
            msg = "📝 Ваш блокнот пуст.\nВы можете сохранять сюда важные записи, список ВУЗов или напоминания."
        else:
            notes_str = "\n".join([f"{i+1}. {n}" for i, n in enumerate(notes)])
            msg = f"📝 **Ваши заметки:**\n\n{notes_str}"
        bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=get_notepad_keyboard(lang))
        return

    if text in ["➕ Добавить заметку", "➕ Жаңы жазуу кошуу", "➕ Add Note", "➕ Not Ekle"]:
        user_data["state"] = "WAITING_FOR_NOTE"
        bot.send_message(message.chat.id, "Введите текст заметки, которую хотите сохранить:")
        return

    if text in ["🗑 Очистить блокнот", "🗑 Дептерди тазалоо", "🗑 Clear Notepad", "🗑 Notları Temizle"]:
        user_data["notes"] = []
        bot.send_message(message.chat.id, "🗑 Блокнот очищен!", reply_markup=get_notepad_keyboard(lang))
        return

    # 4. Смена языка / страны
    if text in ["🌐 Сменить язык", "🌐 Тилди алмаштыруу", "🌐 Change Language", "🌐 Dili Değiştir"]:
        bot.send_message(message.chat.id, "Выбери язык / Тилди тандаңыз:", reply_markup=get_language_keyboard())
        return

    if text in ["🌍 Сменить страну", "🌍 Өлкөнү алмаштыруу", "🌍 Change Country", "🌍 Ülke Değiştir"]:
        bot.send_message(message.chat.id, "Выбери страну / Өлкөнү тандаңыз:", reply_markup=get_country_keyboard())
        return

    # 5. Вопросы к ИИ Барсбек
    selected_lang = user_data.get("lang", "🇷🇺 Русский")
    selected_country = user_data.get("country", "🇰🇬 Кыргызстан")

    system_prompt = (
        f"Твое имя — Барсбек. Ты — профессиональный, дружелюбный AI-консультант по поступлению в ВУЗы.\n"
        f"Выбранная страна для поступления: {selected_country}.\n"
        f"ОБЯЗАТЕЛЬНО отвечай ИСКЛЮЧИТЕЛЬНО на языке: {selected_lang}.\n"
        f"Все рекомендации по ВУЗам, экзаменам и документам должны относиться строго к стране {selected_country}."
    )

    prompt_query = text
    if text in ["📋 Условия поступления", "📋 Талаптар жана сынактар", "📋 Admission Requirements", "📋 Başvuru Şartları"]:
        prompt_query = f"Расскажи подробно про условия поступления, основные экзамены (ОРТ/SAT/YÖS) и проходные баллы для поступления в ВУЗы страны {selected_country}."
    elif text in ["🏛 Подбор ВУЗов", "🏛 ЖОЖдорду тандоо", "🏛 Select Universities", "🏛 Üniversite Seçimi"]:
        prompt_query = f"Перечисли топ-5 лучших ВУЗов страны {selected_country} для иностранных студентов и их основные специальности."
    elif text in ["📄 Необходимые документы", "📄 Керектүү документтер", "📄 Required Documents", "📄 Gerekli Belgeler"]:
        prompt_query = f"Какой полный список документов нужен для подачи в ВУЗы страны {selected_country} и получения студенческой визы?"
    elif text in ["⚖️️ Плюсы и Минусы", "⚖️ Артыкчылыктар жана кемчиликтер", "⚖️ Pros and Cons", "⚖️ Artıları ve Eksileri"]:
        prompt_query = f"Назови основные плюсы и минусы учебы и жизни для иностранного студента в стране {selected_country}."
    elif text in ["🗺 Мой путь", "🗺 Менин жолум", "🗺 My Roadmap", "🗺 Yol Haritam"]:
        prompt_query = f"Составь пошаговый план действий (дорожную карту) для абитуриента, планирующего поступать в ВУЗы страны {selected_country} (начиная с подготовки в школе и заканчивая прилетом)."

    wait_msg = bot.send_message(message.chat.id, "⏳...")
    ai_response = ask_ai(prompt_query, system_prompt)
    bot.edit_message_text(ai_response, message.chat.id, wait_msg.message_id)

if __name__ == "__main__":
    bot.polling(none_stop=True)
