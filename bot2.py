import os
import re
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types
import requests

# ==========================================
# 1. МИНИ ВЕБ-СЕРВЕР ДЛЯ РЕНДЕРА
# ==========================================
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Web server running on port {port}")
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# ==========================================
# 2. ИНИЦИАЛИЗАЦИЯ И ИИ OPENROUTER
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не найдена!")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Хранилище состояний пользователей
user_states = {}

LANGUAGES = ["🇷🇺 Русский", "🇰🇬 Кыргызча", "🇬🇧 English", "🇹🇷 Türkçe"]
COUNTRIES = ["🇰🇬 Кыргызстан", "🇹🇷 Турция", "🇺🇸 США", "🇨🇳 Китай", "🇰🇷 Южная Корея", "🇨🇦 Канада"]

def clean_ai_response(text):
    """Очищает ответ от мусора и заменяет ### на жирный шрифт"""
    # Удаляем служебную строку User Safety
    text = re.sub(r'User Safety:\s*safe\s*', '', text, flags=re.IGNORECASE)
    
    # Заменяем markdown-заголовки (### Текст) на жирный текст (**Текст**)
    text = re.sub(r'#{1,6}\s*(.+)', r'**\1**', text)
    
    return text.strip()

def ask_ai(prompt, system_instruction):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://render.com",
        "X-Title": "Barsbek Bot"
    }
    
    data = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        res_data = response.json()
        
        if 'choices' in res_data and len(res_data['choices']) > 0:
            raw_content = res_data['choices'][0]['message']['content']
            return clean_ai_response(raw_content)
        else:
            print(f"OpenRouter Raw Error: {res_data}")
            err_msg = res_data.get('error', {}).get('message', 'Неизвестная ошибка')
            return f"⚠️ Ошибка ИИ: {err_msg}"
    except Exception as e:
        print(f"Request exception: {e}")
        return "❌ Ошибка соединения с ИИ. Попробуй позже."

# ==========================================
# 3. КЛАВИАТУРЫ
# ==========================================
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
    else:
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

# ==========================================
# 4. ОБРАБОТЧИКИ СООБЩЕНИЙ
# ==========================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_states[user_id] = {
        "name": None,
        "age": None,
        "lang": None,
        "country": None,
        "notes": [],
        "state": "WAITING_FOR_NAME"
    }
    
    msg = (
        "Салам! Мен Барсбекмин 🐆 / Здравствуйте! Я Барсбек 🐆\n\n"
        "Как вас зовут? Напишите ваше имя:"
    )
    bot.send_message(message.chat.id, msg, reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text

    if user_id not in user_states:
        start(message)
        return

    user_data = user_states[user_id]
    current_state = user_data.get("state")

    # Сбор Имени
    if current_state == "WAITING_FOR_NAME":
        user_data["name"] = text
        user_data["state"] = "WAITING_FOR_AGE"
        bot.send_message(message.chat.id, f"Приятно познакомиться, {text}! 🤝\nСколько вам лет?")
        return

    # Сбор Возраста
    if current_state == "WAITING_FOR_AGE":
        user_data["age"] = text
        user_data["state"] = "WAITING_FOR_LANG"
        bot.send_message(
            message.chat.id, 
            "Отлично! Выбери язык / Тилди тандаңыз / Select language:", 
            reply_markup=get_language_keyboard()
        )
        return

    # Сбор Языка
    if current_state == "WAITING_FOR_LANG" or text in LANGUAGES:
        if text in LANGUAGES:
            user_data["lang"] = text
            user_data["state"] = "WAITING_FOR_COUNTRY"
            bot.send_message(
                message.chat.id, 
                "Теперь выбери страну для обучения / Өлкөнү тандаңыз:", 
                reply_markup=get_country_keyboard()
            )
            return

    # Сбор Страны
    if current_state == "WAITING_FOR_COUNTRY" or text in COUNTRIES:
        if text in COUNTRIES:
            user_data["country"] = text
            user_data["state"] = None
            lang = user_data.get("lang", "🇷🇺 Русский")
            name = user_data.get("name", "друг")
            msg = f"Отлично, *{name}*! Выбрана страна: *{text}* 🎯\nЧем я могу помочь?"
            bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=get_main_keyboard(lang))
            return

    lang = user_data.get("lang", "🇷🇺 Русский")

    # Блокнот
    if current_state == "WAITING_FOR_NOTE":
        user_data["notes"].append(text)
        user_data["state"] = None
        bot.send_message(message.chat.id, "✅ Заметка сохранена!", reply_markup=get_notepad_keyboard(lang))
        return

    if text in ["🔙 Главное меню", "🔙 Башкы меню", "🔙 Main Menu", "🔙 Ana Menü"]:
        bot.send_message(message.chat.id, "🏡 Главное меню:", reply_markup=get_main_keyboard(lang))
        return

    if text in ["🔄 Начать новый диалог", "🔄 Жаңы диалог баштоо", "🔄 Start New Dialogue", "🔄 Yeni Sohbet Başlat"]:
        start(message)
        return

    if text in ["📝 Мой блокнот", "📝 Менин дептерим", "📝 My Notepad", "📝 Not Defterim"]:
        notes = user_data.get("notes", [])
        if not notes:
            msg = "📝 Ваш блокнот пока пуст."
        else:
            notes_str = "\n".join([f"{i+1}. {n}" for i, n in enumerate(notes)])
            msg = f"📝 **Ваши заметки:**\n\n{notes_str}"
        bot.send_message(message.chat.id, msg, parse_mode="Markdown", reply_markup=get_notepad_keyboard(lang))
        return

    if text in ["➕ Добавить заметку", "➕ Жаңы жазуу кошуу", "➕ Add Note", "➕ Not Ekle"]:
        user_data["state"] = "WAITING_FOR_NOTE"
        bot.send_message(message.chat.id, "✍️ Введите текст заметки:")
        return

    if text in ["🗑 Очистить блокнот", "🗑 Дептерди тазалоо", "🗑 Clear Notepad", "🗑 Notları Temizle"]:
        user_data["notes"] = []
        bot.send_message(message.chat.id, "🗑 Блокнот успешно очищен!", reply_markup=get_notepad_keyboard(lang))
        return

    if text in ["🌐 Сменить язык", "🌐 Тилди алмаштыруу", "🌐 Change Language", "🌐 Dili Değiştir"]:
        user_data["state"] = "WAITING_FOR_LANG"
        bot.send_message(message.chat.id, "🌐 Выбери язык / Тилди тандаңыз:", reply_markup=get_language_keyboard())
        return

    if text in ["🌍 Сменить страну", "🌍 Өлкөнү алмаштыруу", "🌍 Change Country", "🌍 Ülke Değiştir"]:
        user_data["state"] = "WAITING_FOR_COUNTRY"
        bot.send_message(message.chat.id, "🌍 Выбери страну / Өлкөнү тандаңыз:", reply_markup=get_country_keyboard())
        return

    # Запрос к ИИ
    selected_lang = user_data.get("lang", "🇷🇺 Русский")
    selected_country = user_data.get("country", "🇰🇬 Кыргызстан")
    user_name = user_data.get("name", "Пользователь")
    user_age = user_data.get("age", "Не указан")

    system_prompt = (
        f"Твое имя — Барсбек 🐆. Ты — дружелюбный, экспертный AI-консультант по поступлению в ВУЗы.\n"
        f"Данные ученика: Имя = {user_name}, Возраст = {user_age}.\n"
        f"Выбранная страна для обучения: {selected_country}.\n"
        f"ОБЯЗАТЕЛЬНО отвечай ИСКЛЮЧИТЕЛЬНО на языке: {selected_lang}.\n\n"
        f"Правила оформления ответа:\n"
        f"1. Обращайся к ученику по имени ({user_name}) и учитывай его возраст ({user_age} лет).\n"
        f"2. Активно используй красивое оформление и эмодзи (🎓, 🏛, 📜, 💡, 📌, ✨, 🚀, 🎯).\n"
        f"3. Для выделения заголовков и важных названий ИСПОЛЬЗУЙ ТОЛЬКО **текст жирным**. НЕ используй знаки хештегов ###."
    )

    prompt_query = text
    if text in ["📋 Условия поступления", "📋 Талаптар жана сынактар", "📋 Admission Requirements", "📋 Başvuru Şartları"]:
        prompt_query = f"Расскажи подробно про условия поступления в ВУЗы страны {selected_country}."
    elif text in ["🏛 Подбор ВУЗов", "🏛 ЖОЖдорду тандоо", "🏛 Select Universities", "🏛 Üniversite Seçimi"]:
        prompt_query = f"Перечисли топ-5 лучших ВУЗов страны {selected_country}."
    elif text in ["📄 Необходимые документы", "📄 Керектүү документтер", "📄 Required Documents", "📄 Gerekli Belgeler"]:
        prompt_query = f"Какой список документов нужен для подачи в ВУЗы страны {selected_country}?"
    elif text in ["⚖️ Плюсы и Минусы", "⚖️ Артыкчылыктар жана кемчиликтер", "⚖️ Pros and Cons", "⚖️ Artıları ve Eksileri"]:
        prompt_query = f"Назови плюсы и минусы учебы в стране {selected_country}."
    elif text in ["🗺 Мой путь", "🗺 Менин жолум", "🗺 My Roadmap", "🗺 Yol Haritam"]:
        prompt_query = f"Составь план действий для поступления в ВУЗы страны {selected_country}."

    wait_msg = bot.send_message(message.chat.id, "⏳ Думаю над ответом...")
    ai_response = ask_ai(prompt_query, system_prompt)
    
    try:
        bot.edit_message_text(ai_response, message.chat.id, wait_msg.message_id, parse_mode="Markdown")
    except Exception:
        bot.edit_message_text(ai_response, message.chat.id, wait_msg.message_id)

if __name__ == "__main__":
    bot.polling(none_stop=True)
