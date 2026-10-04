import os
import sys
import datetime
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

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Web server running on port {port}")
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# ==========================================
# 2. ИНИЦИАЛИЗАЦИЯ И НАСТРОЙКИ
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")
# Используем переменные окружения или твой Access Key напрямую
UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "odaMYOHO8tsFHyGe_Q8-0EZtab_NohgvOYRBEvtIkRE")

OWNER_ID = 8762115500

if not TELEGRAM_TOKEN:
    raise ValueError("ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не найдена!")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Хранилище данных
user_states = {}
admins = set()               # Набор ID администраторов
banned_users = set()         # Заблокированные пользователи
all_users = {}               # user_id -> info

LANGUAGES = ["🇷🇺 Русский", "🇰🇬 Кыргызча", "🇬🇧 English", "🇹🇷 Türkçe"]
COUNTRIES = ["🇰🇬 Кыргызстан", "🇹🇷 Турция", "🇺🇸 США", "🇨🇳 Китай", "🇰🇷 Южная Корея", "🇨🇦 Канада"]

def get_topic_image(query):
    """Ищет качественное тематическое фото через Unsplash API"""
    if not UNSPLASH_KEY:
        return None

    url = f"https://api.unsplash.com/search/photos?page=1&query={query}&per_page=1&client_id={UNSPLASH_KEY}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('results') and len(data['results']) > 0:
                return data['results'][0]['urls']['regular']
    except Exception as e:
        print(f"Ошибка при запросе фото к Unsplash: {e}")
    return None

def clean_ai_response(text):
    """Очищает текст и форматирует его для легкого чтения"""
    lines = text.split('\n')
    filtered_lines = []
    for line in lines:
        if "user safety:" in line.lower():
            continue
        filtered_lines.append(line)
    
    res = "\n".join(filtered_lines).strip()
    
    # Удаляем тяжелую символику Markdown
    for char in ["*", "#", "_", "`", "~"]:
        res = res.replace(char, "")
        
    return res

def ask_ai(prompt, system_instruction):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://render.com",
        "X-Title": "Barsbek Bot"
    }
    
    models_to_try = [
        "google/gemini-2.0-flash-lite-001",
        "openai/gpt-4o-mini",
        "google/gemini-2.0-flash-lite-preview-02-05:free",
        "meta-llama/llama-3.1-8b-instruct:free",
        "qwen/qwen-2.5-72b-instruct:free"
    ]
    
    for model in models_to_try:
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 350,
            "temperature": 0.3
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=25)
            if response.status_code == 200:
                res_data = response.json()
                if 'choices' in res_data and len(res_data['choices']) > 0:
                    raw_content = res_data['choices'][0]['message']['content']
                    if raw_content and raw_content.strip():
                        return clean_ai_response(raw_content)
        except Exception as e:
            print(f"Ошибка с моделью {model}: {e}")
            continue

    return "⚠️ Сервер ИИ временно занят. Попробуйте еще раз через пару секунд."

# ==========================================
# 3. КЛАВИАТУРЫ И ИНТЕРФЕЙС
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

def get_main_keyboard(user_id, lang):
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
        markup.row("📄 Gerekli Belgeler", "⚖ Artıları ve Eksileri")
        markup.row("🗺 Yol Haritam", "📝 Not Defterim")
        markup.row("🌍 Ülke Değiştir", "🌐 Dili Değiştir")
        markup.row("🔄 Yeni Sohbet Başlat")
    else:
        markup.row("📋 Условия поступления", "🏛 Подбор ВУЗов")
        markup.row("📄 Необходимые документы", "⚖️ Плюсы и Минусы")
        markup.row("🗺 Мой путь", "📝 Мой блокнот")
        markup.row("🌍 Сменить страну", "🌐 Сменить язык")
        markup.row("🔄 Начать новый диалог")

    is_owner = (user_id == OWNER_ID)
    is_admin = (user_id in admins) or is_owner

    admin_btns = []
    if is_admin:
        admin_btns.append("🛠 Панель Админа")
    if is_owner:
        admin_btns.append("👑 Панель Владельца")
    
    if admin_btns:
        markup.row(*admin_btns)

    return markup

def get_admin_panel_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("👥 Все участники", "📊 Участников за сегодня")
    markup.row("🔙 Главное меню")
    return markup

def get_owner_panel_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("👥 Все участники", "📊 Участников за сегодня")
    markup.row("➕ Назначить администратором", "📜 Список админов")
    markup.row("🛑 Остановить бота")
    markup.row("🔙 Главное меню")
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

def get_roadmap_inline_keyboard(lang):
    markup = types.InlineKeyboardMarkup()
    if lang == "🇰🇬 Кыргызча":
        markup.add(types.InlineKeyboardButton("1️⃣ Даярдык жана сынактар", callback_data="road_1"))
        markup.add(types.InlineKeyboardButton("2️⃣ Документтерди тапшыруу", callback_data="road_2"))
        markup.add(types.InlineKeyboardButton("3️⃣ Виза жана учуп кетүү", callback_data="road_3"))
    else:
        markup.add(types.InlineKeyboardButton("1️⃣ Подготовка и экзамены", callback_data="road_1"))
        markup.add(types.InlineKeyboardButton("2️⃣ Подача документов", callback_data="road_2"))
        markup.add(types.InlineKeyboardButton("3️⃣ Виза и переезд", callback_data="road_3"))
    return markup

# ==========================================
# 4. ОБРАБОТЧИКИ СООБЩЕНИЙ
# ==========================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in banned_users:
        bot.send_message(message.chat.id, "⛔ Вы заблокированы в этом боте.")
        return

    today_str = datetime.date.today().isoformat()
    username = message.from_user.username
    username_str = f"@{username}" if username else "Без username"
    
    if user_id not in all_users:
        all_users[user_id] = {
            "username": username_str,
            "first_name": message.from_user.first_name or "Пользователь",
            "join_date": today_str,
            "last_active": today_str
        }
    else:
        all_users[user_id]["last_active"] = today_str
        all_users[user_id]["username"] = username_str

    user_states[user_id] = {
        "lang": None,
        "name": None,
        "age": None,
        "country": None,
        "notes": [],
        "state": "WAITING_FOR_LANG"
    }
    
    msg = (
        "Салам! Мен Барсбекмин 🐆 / Здравствуйте! Я Барсбек 🐆\n\n"
        "Тилди тандаңыз / Выберите язык / Select language / Dil seçin:"
    )
    bot.send_message(message.chat.id, msg, reply_markup=get_language_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("ban_"))
def handle_ban_callback(call):
    if call.from_user.id != OWNER_ID and call.from_user.id not in admins:
        bot.answer_callback_query(call.id, "У вас нет прав!", show_alert=True)
        return
    
    target_id = int(call.data.split("_")[1])
    banned_users.add(target_id)
    bot.answer_callback_query(call.id, f"Участник {target_id} заблокирован!", show_alert=True)
    bot.edit_message_text(f"⛔ Участник (ID: {target_id}) заблокирован.", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("road_"))
def handle_roadmap_steps(call):
    user_id = call.from_user.id
    user_data = user_states.get(user_id, {})
    selected_country = user_data.get("country", "Канада")
    selected_lang = user_data.get("lang", "🇷🇺 Русский")
    step = call.data.split("_")[1]

    steps_prompts = {
        "1": f"Кратко распиши 1-й шаг поступления в {selected_country}: подготовка и языковые экзамены. Максимум 3 тезиса с эмодзи.",
        "2": f"Кратко распиши 2-й шаг поступления в {selected_country}: сбор и подача документов в ВУЗ. Максимум 3 тезиса с эмодзи.",
        "3": f"Кратко распиши 3-й шаг поступления в {selected_country}: получение визы и переезд. Максимум 3 тезиса с эмодзи."
    }

    bot.answer_callback_query(call.id, "Загружаю детали...")
    
    sys_prompt = f"You are Barsbek consultant. Language: {selected_lang}. Be short, concise, use emojis. NO MARKDOWN SYMBOLS like *, #, _."
    ai_text = ask_ai(steps_prompts[step], sys_prompt)
    
    # Ищем фото для шага
    image_url = get_topic_image(f"university {selected_country}")
    if image_url:
        try:
            bot.send_photo(call.message.chat.id, photo=image_url, caption=ai_text)
            return
        except Exception:
            pass
    bot.send_message(call.message.chat.id, ai_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text

    if user_id in banned_users:
        bot.send_message(message.chat.id, "⛔ Вы заблокированы.")
        return

    today_str = datetime.date.today().isoformat()
    username = message.from_user.username
    username_str = f"@{username}" if username else "Без username"
    
    if user_id in all_users:
        all_users[user_id]["last_active"] = today_str
        all_users[user_id]["username"] = username_str
    else:
        all_users[user_id] = {
            "username": username_str,
            "first_name": message.from_user.first_name or "Пользователь",
            "join_date": today_str,
            "last_active": today_str
        }

    if user_id not in user_states:
        start(message)
        return

    user_data = user_states[user_id]
    current_state = user_data.get("state")

    # Админ
    if current_state == "WAITING_FOR_ADMIN_INPUT" and user_id == OWNER_ID:
        user_data["state"] = None
        target = text.strip().replace("@", "")
        found_id = None
        if target.isdigit():
            found_id = int(target)
        else:
            for uid, info in all_users.items():
                if info["username"].replace("@", "").lower() == target.lower():
                    found_id = uid
                    break

        if found_id:
            admins.add(found_id)
            bot.send_message(message.chat.id, f"✅ Пользователь @{target} назначен администратором!", reply_markup=get_owner_panel_keyboard())
        else:
            bot.send_message(message.chat.id, "❌ Участник не найден.", reply_markup=get_owner_panel_keyboard())
        return

    # 1. Выбор Языка
    if current_state == "WAITING_FOR_LANG" or text in LANGUAGES:
        if text in LANGUAGES:
            user_data["lang"] = text
            user_data["state"] = "WAITING_FOR_NAME"
            
            if text == "🇰🇬 Кыргызча": msg_name = "Атыңыз ким? Жазып жибериңиз:"
            elif text == "🇬🇧 English": msg_name = "What is your name? Please write:"
            elif text == "🇹🇷 Türkçe": msg_name = "Adınız nedir? Lütfen yazın:"
            else: msg_name = "Как вас зовут? Напишите ваше имя:"

            bot.send_message(message.chat.id, msg_name, reply_markup=types.ReplyKeyboardRemove())
            return

    # 2. Ввод Имени
    if current_state == "WAITING_FOR_NAME":
        user_data["name"] = text
        user_data["state"] = "WAITING_FOR_AGE"
        lang = user_data.get("lang", "🇷🇺 Русский")
        
        if lang == "🇰🇬 Кыргызча": msg_age = f"Таанышканыма кубанычтамын, {text}! 🤝\nЖашыңыз канчада?"
        elif lang == "🇬🇧 English": msg_age = f"Nice to meet you, {text}! 🤝\nHow old are you?"
        elif lang == "🇹🇷 Türkçe": msg_age = f"Tanıştığıma memnun oldum, {text}! 🤝\nKaç yaşındasınız?"
        else: msg_age = f"Приятно познакомиться, {text}! 🤝\nСколько вам лет?"

        bot.send_message(message.chat.id, msg_age)
        return

    # 3. Ввод Возраста
    if current_state == "WAITING_FOR_AGE":
        user_data["age"] = text
        user_data["state"] = "WAITING_FOR_COUNTRY"
        lang = user_data.get("lang", "🇷🇺 Русский")
        
        if lang == "🇰🇬 Кыргызча": msg_country = "Эми окуу үчүн өлкөнү тандаңыз:"
        elif lang == "🇬🇧 English": msg_country = "Now select the country for study:"
        elif lang == "🇹🇷 Türkçe": msg_country = "Şimdi eğitim almak istediğiniz ülkeyi seçin:"
        else: msg_country = "Теперь выберите страну для обучения:"

        bot.send_message(message.chat.id, msg_country, reply_markup=get_country_keyboard())
        return

    # 4. Выбор Страны
    if current_state == "WAITING_FOR_COUNTRY" or text in COUNTRIES:
        if text in COUNTRIES:
            user_data["country"] = text
            user_data["state"] = None
            lang = user_data.get("lang", "🇷🇺 Русский")
            name = user_data.get("name", "")
            
            if lang == "🇰🇬 Кыргызча": msg = f"Эң сонун, {name}! Тандалган өлкө: {text} 🎯\nКандай жардам бере алам?"
            elif lang == "🇬🇧 English": msg = f"Great, {name}! Selected country: {text} 🎯\nHow can I help you?"
            elif lang == "🇹🇷 Türkçe": msg = f"Harika, {name}! Seçilen ülke: {text} 🎯\nNasıl yardımcı olabilirim?"
            else: msg = f"Отлично, {name}! Выбрана страна: {text} 🎯\nЧем я могу помочь?"

            bot.send_message(message.chat.id, msg, reply_markup=get_main_keyboard(user_id, lang))
            return

    lang = user_data.get("lang", "🇷🇺 Русский")

    # Панели администрирования
    if text == "🛠 Панель Админа" and (user_id == OWNER_ID or user_id in admins):
        bot.send_message(message.chat.id, "🛠 Панель Администратора", reply_markup=get_admin_panel_keyboard())
        return

    if text == "👑 Панель Владельца" and user_id == OWNER_ID:
        bot.send_message(message.chat.id, "👑 Панель Владельца", reply_markup=get_owner_panel_keyboard())
        return

    if text == "🛑 Остановить бота" and user_id == OWNER_ID:
        bot.send_message(message.chat.id, "🔴 Бот остановлен владельцем.")
        sys.exit(0)

    if text == "➕ Назначить администратором" and user_id == OWNER_ID:
        user_data["state"] = "WAITING_FOR_ADMIN_INPUT"
        bot.send_message(message.chat.id, "Введите @username или Telegram ID участника:")
        return

    if text == "📊 Участников за сегодня" and (user_id == OWNER_ID or user_id in admins):
        today_str = datetime.date.today().isoformat()
        count = sum(1 for u in all_users.values() if u.get("last_active") == today_str)
        bot.send_message(message.chat.id, f"📊 Активных участников за сегодня: {count}")
        return

    if text == "👥 Все участники" and (user_id == OWNER_ID or user_id in admins):
        if not all_users:
            bot.send_message(message.chat.id, "Список участников пуст.")
            return

        bot.send_message(message.chat.id, f"👥 Всего участников: {len(all_users)}")
        for uid, info in all_users.items():
            is_banned = " [ЗАБЛОКИРОВАН]" if uid in banned_users else ""
            msg_text = f"👤 {info['first_name']} | Username: {info['username']}\nID: {uid}{is_banned}"
            
            inline_kb = types.InlineKeyboardMarkup()
            if uid not in banned_users and uid != OWNER_ID:
                inline_kb.add(types.InlineKeyboardButton("🚫 Заблокировать", callback_data=f"ban_{uid}"))
            
            bot.send_message(message.chat.id, msg_text, reply_markup=inline_kb)
        return

    # Блокнот
    if current_state == "WAITING_FOR_NOTE":
        user_data["notes"].append(text)
        user_data["state"] = None
        bot.send_message(message.chat.id, "✅ Заметка сохранена!", reply_markup=get_notepad_keyboard(lang))
        return

    if text in ["🔙 Главное меню", "🔙 Башкы меню", "🔙 Main Menu", "🔙 Ana Menü"]:
        bot.send_message(message.chat.id, "🏡 Главное меню:", reply_markup=get_main_keyboard(user_id, lang))
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
            msg = f"📝 Ваши заметки:\n\n{notes_str}"
        bot.send_message(message.chat.id, msg, reply_markup=get_notepad_keyboard(lang))
        return

    if text in ["➕ Добавить заметку", "➕ Жаңы жазуу кошуу", "➕ Add Note", "➕ Not Ekle"]:
        user_data["state"] = "WAITING_FOR_NOTE"
        bot.send_message(message.chat.id, "✍️ Введите текст заметки:")
        return

    if text in ["🗑 Очистить блокнот", "🗑 Дептерди тазалоо", "🗑 Clear Notepad", "🗑 Notları Temizle"]:
        user_data["notes"] = []
        bot.send_message(message.chat.id, "🗑 Блокнот очищен!", reply_markup=get_notepad_keyboard(lang))
        return

    if text in ["🌐 Сменить язык", "🌐 Тилди алмаштыруу", "🌐 Change Language", "🌐 Dili Değiştir"]:
        user_data["state"] = "WAITING_FOR_LANG"
        bot.send_message(message.chat.id, "🌐 Тилди тандаңыз / Выберите язык:", reply_markup=get_language_keyboard())
        return

    if text in ["🌍 Сменить страну", "🌍 Өлкөнү алмаштыруу", "🌍 Change Country", "🌍 Ülke Değiştir"]:
        user_data["state"] = "WAITING_FOR_COUNTRY"
        bot.send_message(message.chat.id, "🌍 Выберите страну:", reply_markup=get_country_keyboard())
        return

    # Дорожная карта (Мой путь)
    if text in ["🗺 Мой путь", "🗺 Менин жолум", "🗺 My Roadmap", "🗺 Yol Haritam"]:
        c_country = user_data.get("country", "Канада")
        roadmap_intro = (
            f"🗺 Пошаговый план поступления в страну: {c_country}\n\n"
            f"Нажмите на интересующий этап ниже, чтобы узнать подробности:"
        )
        bot.send_message(message.chat.id, roadmap_intro, reply_markup=get_roadmap_inline_keyboard(lang))
        return

    # Запрос к ИИ для остальных кнопок
    selected_lang = user_data.get("lang", "🇷🇺 Русский")
    selected_country = user_data.get("country", "🇰🇬 Кыргызстан")
    user_name = user_data.get("name", "")
    user_age = user_data.get("age", "")

    # Промпт для ИИ
    system_prompt = (
        f"You are Barsbek (Барсбек 🐆), an expert education consultant.\n"
        f"User name: {user_name}, Age: {user_age}.\n"
        f"Selected country: {selected_country}.\n"
        f"CRITICAL: Answer ONLY in language: {selected_lang}.\n\n"
        f"STRICT FORMATTING RULES:\n"
        f"1. Keep response EXTREMELY SHORT, punchy, and readable.\n"
        f"2. Use bullet points with emojis (🎓, 🏛, 📜, 💡).\n"
        f"3. Maximum 3-4 short bullet points or sentences total.\n"
        f"4. DO NOT write long paragraphs or essays.\n"
        f"5. DO NOT USE MARKDOWN SYMBOLS LIKE *, #, _, `, ~."
    )

    prompt_query = text
    photo_keyword = f"university {selected_country}"

    if text in ["📋 Условия поступления", "📋 Талаптар жана сынактар", "📋 Admission Requirements", "📋 Başvuru Şartları"]:
        prompt_query = f"Give top 3 key admission requirements for universities in {selected_country}."
        photo_keyword = f"study {selected_country}"
    elif text in ["🏛 Подбор ВУЗов", "🏛 ЖОЖдорду тандоо", "🏛 Select Universities", "🏛 Университет Seçimi"]:
        prompt_query = f"List top 4 best universities in {selected_country} with brief notes."
        photo_keyword = f"university campus {selected_country}"
    elif text in ["📄 Необходимые документы", "📄 Керектүү документтер", "📄 Required Documents", "📄 Gerekli Belgeler"]:
        prompt_query = f"List 4 essential documents needed for applying to {selected_country}."
        photo_keyword = "documents passport study"
    elif text in ["⚖️ Плюсы и Минусы", "⚖ Артыкчылыктар жана кемчиликтер", "⚖️ Pros and Cons", "⚖️ Artıları ve Eksileri"]:
        prompt_query = f"List 2 main pros and 2 main cons of studying in {selected_country}."
        photo_keyword = f"students {selected_country}"

    thinking_txt = "⏳ Готовлю ответ..."
    if selected_lang == "🇰🇬 Кыргызча": thinking_txt = "⏳ Жүктөлүүдө..."
    elif selected_lang == "🇬🇧 English": thinking_txt = "⏳ Generating response..."
    elif selected_lang == "🇹🇷 Türkçe": thinking_txt = "⏳ Yanıt hazırlanıyor..."

    wait_msg = bot.send_message(message.chat.id, thinking_txt)
    
    # Получаем параллельно картинку и ответ ИИ
    image_url = get_topic_image(photo_keyword)
    ai_response = ask_ai(prompt_query, system_prompt)
    
    # Удаляем сообщение ожидания
    try:
        bot.delete_message(message.chat.id, wait_msg.message_id)
    except Exception:
        pass

    # Отправляем ответ: с фото подписью или текстовым сообщением
    if image_url:
        try:
            bot.send_photo(message.chat.id, photo=image_url, caption=ai_response)
        except Exception as e:
            print(f"Ошибка отправки фото: {e}")
            bot.send_message(message.chat.id, ai_response)
    else:
        bot.send_message(message.chat.id, ai_response)

if __name__ == "__main__":
    bot.polling(none_stop=True)
