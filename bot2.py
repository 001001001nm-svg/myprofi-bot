import os
import sys
import io
import random
import datetime
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types
import requests

# ==========================================
# 1. ВЕБ-СЕРВЕР ДЛЯ RENDER
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
    try:
        server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
        print(f"Web server running on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Web server error: {e}")

threading.Thread(target=run_web_server, daemon=True).start()

# ==========================================
# 2. ИНИЦИАЛИЗАЦИЯ
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")
UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "odaMYOHO8tsFHyGe_Q8-0EZtab_NohgvOYRBEvtIkRE")

OWNER_ID = 8762115500

if not TELEGRAM_TOKEN:
    raise ValueError("ОШИБКА: Переменная TELEGRAM_BOT_TOKEN не найдена!")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

user_states = {}
admins = set()
banned_users = set()
all_users = {}

LANGUAGES = ["🇷🇺 Русский", "🇰🇬 Кыргызча", "🇬🇧 English", "🇹🇷 Türkçe"]
COUNTRIES = ["🇰🇬 Кыргызстан", "🇹🇷 Турция", "🇺🇸 США", "🇨🇳 Китай", "🇰🇷 Южная Корея", "🇨🇦 Канада"]

# ==========================================
# 3. НАДЕЖНАЯ ЗАГРУЗКА КАРТИНОК
# ==========================================
def fetch_photo_bytes(query):
    """Ищет фото на Unsplash и скачивает его для отправки"""
    if not UNSPLASH_KEY:
        return None

    search_url = f"https://api.unsplash.com/search/photos?page=1&query={query}&per_page=5&client_id={UNSPLASH_KEY}"
    try:
        res = requests.get(search_url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            results = data.get('results', [])
            if results:
                img_obj = random.choice(results)
                img_url = img_obj['urls']['small']
                
                img_res = requests.get(img_url, timeout=5)
                if img_res.status_code == 200:
                    photo_bytes = io.BytesIO(img_res.content)
                    photo_bytes.name = "image.jpg"
                    return photo_bytes
    except Exception as e:
        print(f"Ошибка получения картинки Unsplash: {e}")
    return None

def clean_ai_response(text):
    lines = text.split('\n')
    filtered = [l for l in lines if "user safety:" not in l.lower()]
    res = "\n".join(filtered).strip()
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
        "meta-llama/llama-3.1-8b-instruct:free"
    ]
    
    for model in models_to_try:
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 400,
            "temperature": 0.5
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=15)
            if response.status_code == 200:
                res_data = response.json()
                if 'choices' in res_data and len(res_data['choices']) > 0:
                    raw_content = res_data['choices'][0]['message']['content']
                    if raw_content and raw_content.strip():
                        return clean_ai_response(raw_content)
        except Exception:
            continue

    return "🔥 Поступление за рубеж: выбери интересующий ВУЗ или страну из меню ниже!"

# ==========================================
# 4. КЛАВИАТУРЫ
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
        markup.row("🔥 Топ ЖОЖдор жана Колледждер", "💡 Лайфхактар жана Талаптар")
        markup.row("📄 Документтер тизмеси", "💰 Стипендиялар")
        markup.row("🌍 Өлкөнү алмаштыруу", "🌐 Тилди алмаштыруу")
        markup.row("🔄 Жаңы диалог")
    else:
        markup.row("🔥 Топ ВУЗы и Колледжи", "💡 Лайфхаки и Требования")
        markup.row("📄 Список документов", "💰 Стипендии и Гранты")
        markup.row("🌍 Сменить страну", "🌐 Сменить язык")
        markup.row("🔄 Начать заново")
    return markup

def get_reels_inline_buttons():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔥 Ещё факт / ВУЗ", callback_data="act_more_fact"),
        types.InlineKeyboardButton("📸 Ещё фото", callback_data="act_more_photo")
    )
    return markup

# ==========================================
# 5. ХЭНДЛЕРЫ
# ==========================================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in banned_users:
        return

    today_str = datetime.date.today().isoformat()
    username_str = f"@{message.from_user.username}" if message.from_user.username else "Без username"
    
    all_users[user_id] = {
        "username": username_str,
        "first_name": message.from_user.first_name or "Пользователь",
        "join_date": today_str,
        "last_active": today_str
    }

    user_states[user_id] = {
        "lang": None, "name": None, "age": None, "country": None, "state": "WAITING_FOR_LANG"
    }
    
    msg = "👋 Салам! Я Барсбек 🐆\n\nВыберите язык / Тилди тандаңыз:"
    bot.send_message(message.chat.id, msg, reply_markup=get_language_keyboard())

@bot.callback_query_handler(func=lambda call: call.data.startswith("act_"))
def handle_reels_actions(call):
    user_id = call.from_user.id
    user_data = user_states.get(user_id, {})
    c_country = user_data.get("country", "США")
    c_lang = user_data.get("lang", "🇷🇺 Русский")

    try:
        bot.answer_callback_query(call.id, "⚡ Загружаю...")
    except Exception:
        pass

    if call.data == "act_more_fact":
        prompt = f"Напиши 1 мега-интересный факт про учебу в {c_country}. 2 коротких предложения с эмодзи."
        query_photo = f"students university {c_country}"
    else:
        prompt = f"Покажи атмосфера кампуса и ВУЗов в {c_country}."
        query_photo = f"university campus {c_country}"

    sys_prompt = f"You are an educational blogger. Language: {c_lang}. NO MARKDOWN SYMBOLS."
    ai_text = ask_ai(prompt, sys_prompt)
    photo_file = fetch_photo_bytes(query_photo)

    if photo_file:
        try:
            bot.send_photo(call.message.chat.id, photo=photo_file, caption=ai_text, reply_markup=get_reels_inline_buttons())
            return
        except Exception as e:
            print(f"Ошибка отправки фото по кнопке: {e}")

    bot.send_message(call.message.chat.id, ai_text, reply_markup=get_reels_inline_buttons())

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text

    if user_id in banned_users:
        return

    if user_id not in user_states:
        start(message)
        return

    user_data = user_states[user_id]
    current_state = user_data.get("state")

    # 1. Выбор Языка
    if current_state == "WAITING_FOR_LANG" or text in LANGUAGES:
        if text in LANGUAGES:
            user_data["lang"] = text
            user_data["state"] = "WAITING_FOR_NAME"
            bot.send_message(message.chat.id, "Как тебя зовут? / Атыңыз ким?", reply_markup=types.ReplyKeyboardRemove())
            return

    # 2. Имя
    if current_state == "WAITING_FOR_NAME":
        user_data["name"] = text
        user_data["state"] = "WAITING_FOR_AGE"
        bot.send_message(message.chat.id, f"Приятно познакомиться, {text}! 🤝 Сколько тебе лет?")
        return

    # 3. Возраст
    if current_state == "WAITING_FOR_AGE":
        user_data["age"] = text
        user_data["state"] = "WAITING_FOR_COUNTRY"
        bot.send_message(message.chat.id, "Выбери страну для обучения:", reply_markup=get_country_keyboard())
        return

    # 4. Страна
    if current_state == "WAITING_FOR_COUNTRY" or text in COUNTRIES:
        if text in COUNTRIES:
            user_data["country"] = text
            user_data["state"] = None
            lang = user_data.get("lang", "🇷🇺 Русский")
            
            welcome_txt = f"🚀 Отлично! Выбрана страна: {text}\nНажимай на кнопки ниже или пиши любой вопрос про ВУЗы!"
            photo = fetch_photo_bytes(f"city {text}")
            
            if photo:
                try:
                    bot.send_photo(message.chat.id, photo=photo, caption=welcome_txt, reply_markup=get_main_keyboard(user_id, lang))
                    return
                except Exception:
                    pass
            bot.send_message(message.chat.id, welcome_txt, reply_markup=get_main_keyboard(user_id, lang))
            return

    lang = user_data.get("lang", "🇷🇺 Русский")
    c_country = user_data.get("country", "Кыргызстан")

    # Служебные кнопки
    if text in ["🌐 Сменить язык", "🌐 Тилди алмаштыруу"]:
        user_data["state"] = "WAITING_FOR_LANG"
        bot.send_message(message.chat.id, "Выберите язык:", reply_markup=get_language_keyboard())
        return

    if text in ["🌍 Сменить страну", "🌍 Өлкөнү алмаштыруу"]:
        user_data["state"] = "WAITING_FOR_COUNTRY"
        bot.send_message(message.chat.id, "Выберите страну:", reply_markup=get_country_keyboard())
        return

    if text in ["🔄 Начать заново", "🔄 Жаңы диалог"]:
        start(message)
        return

    # Генерация ответа
    try:
        wait_msg = bot.send_message(message.chat.id, "🎬 Загрузка...")
    except Exception:
        wait_msg = None

    query_photo = f"university {c_country}"
    
    if "ВУЗ" in text or "Колледж" in text or "ЖОЖ" in text:
        prompt_query = f"Расскажи про 2 лучших ВУЗа/колледжа в {c_country}. Сочно и с эмодзи."
        query_photo = f"university building {c_country}"
    elif "Лайфхак" in text or "Талаптар" in text:
        prompt_query = f"Дай 3 главных лайфхака для поступления в {c_country}."
        query_photo = f"students studying {c_country}"
    elif "Стипендии" in text or "Гранты" in text:
        prompt_query = f"Как учиться бесплатно в {c_country}? Назови 2 программы."
        query_photo = f"graduation student {c_country}"
    elif "Документ" in text:
        prompt_query = f"Главные документы для поступления в ВУЗы {c_country}."
        query_photo = f"documents passport"
    else:
        prompt_query = f"Ответь на вопрос про учебу: '{text}'. Страна: {c_country}."
        query_photo = f"university {c_country}"

    sys_prompt = f"You are Barsbek consultant. Country: {c_country}. Language: {lang}. Short answers with emojis. NO MARKDOWN."

    ai_response = ask_ai(prompt_query, sys_prompt)
    photo_bytes = fetch_photo_bytes(query_photo)

    if wait_msg:
        try:
            bot.delete_message(message.chat.id, wait_msg.message_id)
        except Exception:
            pass

    # Отправка
    if photo_bytes:
        try:
            bot.send_photo(message.chat.id, photo=photo_bytes, caption=ai_response, reply_markup=get_reels_inline_buttons())
            return
        except Exception as e:
            print(f"Ошибка при отправке итогового фото: {e}")

    bot.send_message(message.chat.id, ai_response, reply_markup=get_reels_inline_buttons())

# ==========================================
# 6. ЗАПУСК БОТА С АВТОРЕСТАРТОМ
# ==========================================
if __name__ == "__main__":
    print("Запуск бота Барсбек...")
    bot.infinity_polling(timeout=20, long_polling_timeout=5)
