import os
import time
import threading
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = os.environ.get("TOKEN")
GAME_URL = "https://fenix-casino.pages.dev"
STATS_URL = "https://fenix-stats.selcanburakgazi6697.workers.dev"
STATS_KEY = "fenix2026stats"
ADMIN_IDS = [8101681923]
BROADCAST_INTERVAL = 7 * 24 * 60 * 60

bot = telebot.TeleBot(TOKEN)
ANIMATION_FILE_ID = None

def ping(event, uid="anon"):
    try:
        requests.get(f"{STATS_URL}/ping", params={"event": event, "uid": uid}, timeout=3)
    except:
        pass

def save_user(uid):
    try:
        requests.get(f"{STATS_URL}/add_user", params={"key": STATS_KEY, "uid": uid}, timeout=3)
    except:
        pass

def get_users():
    try:
        r = requests.get(f"{STATS_URL}/get_users", params={"key": STATS_KEY}, timeout=5)
        return r.json().get("users", [])
    except:
        return []

def get_broadcast_text():
    try:
        r = requests.get(f"{STATS_URL}/get_broadcast", params={"key": STATS_KEY}, timeout=5)
        return r.json().get("text", "")
    except:
        return ""

def set_broadcast_text(text):
    try:
        requests.get(f"{STATS_URL}/set_broadcast", params={"key": STATS_KEY, "text": text}, timeout=5)
    except:
        pass

def get_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(
        "🔥 Открыть Fenix Casino 🔥",
        web_app=WebAppInfo(url=GAME_URL)
    ))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    global ANIMATION_FILE_ID
    uid = str(message.from_user.id)
    ping("start", uid)
    save_user(uid)

    caption = "🔥 Fenix Casino — возродись и выиграй!\n\nБонус 425% + 375 фриспинов ждут тебя 👇"
    markup = get_markup()

    if ANIMATION_FILE_ID:
        bot.send_animation(message.chat.id, ANIMATION_FILE_ID, caption=caption, reply_markup=markup)
    else:
        video_path = os.path.join(os.path.dirname(__file__), "fenix.mp4")
        if os.path.exists(video_path):
            with open(video_path, "rb") as f:
                sent = bot.send_animation(message.chat.id, f, caption=caption, reply_markup=markup)
                ANIMATION_FILE_ID = sent.animation.file_id
        else:
            bot.send_message(message.chat.id, caption, reply_markup=markup)

@bot.message_handler(commands=['setbroadcast'])
def cmd_setbroadcast(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    text = message.text.replace('/setbroadcast', '', 1).strip()
    if not text:
        bot.send_message(message.chat.id, "Укажи текст: /setbroadcast <текст>")
        return
    set_broadcast_text(text)
    bot.send_message(message.chat.id, f"✅ Текст рассылки сохранён:\n\n{text}")

@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    do_broadcast(message.chat.id)

@bot.message_handler(commands=['stats'])
def send_stats(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    try:
        r = requests.get(f"{STATS_URL}/stats", params={"key": STATS_KEY}, timeout=5)
        d = r.json()
        text = (
            f"📊 Fenix Casino — Статистика\n\n"
            f"Всего:\n"
            f"  🚀 /start: {d['total']['starts']}\n"
            f"  👁 Визитов: {d['total']['visits']}\n"
            f"  🔗 Кликов: {d['total']['clicks']}\n\n"
            f"Уникальных:\n"
            f"  🚀 /start: {d['unique']['starts']}\n"
            f"  👤 Посетителей: {d['unique']['visits']}\n"
            f"  🔗 Перешли: {d['unique']['clicks']}\n\n"
            f"Сегодня:\n"
            f"  🚀 /start: {d['today']['starts']}\n"
            f"  👁 Визитов: {d['today']['visits']}\n"
            f"  🔗 Кликов: {d['today']['clicks']}\n\n"
            f"👥 Подписчиков: {d.get('subscribers', 0)}\n"
            f"📈 CTR: {d['ctr']}"
        )
        bot.send_message(message.chat.id, text)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

def do_broadcast(report_chat_id=None):
    text = get_broadcast_text()
    if not text:
        if report_chat_id:
            bot.send_message(report_chat_id, "❌ Текст не задан. Используй /setbroadcast <текст>")
        return
    users = get_users()
    if not users:
        if report_chat_id:
            bot.send_message(report_chat_id, "❌ Список пользователей пуст.")
        return
    markup = get_markup()
    sent, failed = 0, 0
    for uid in users:
        try:
            bot.send_message(int(uid), text, reply_markup=markup)
            sent += 1
            time.sleep(0.05)
        except:
            failed += 1
    if report_chat_id:
        bot.send_message(report_chat_id, f"✅ Рассылка завершена\n📤 Отправлено: {sent}\n❌ Ошибок: {failed}")

def broadcast_scheduler():
    while True:
        time.sleep(BROADCAST_INTERVAL)
        do_broadcast()

print("Fenix bot started...")
threading.Thread(target=broadcast_scheduler, daemon=True).start()
bot.infinity_polling()
