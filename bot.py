import telebot
import requests
import os
from rahad_all_downloader import alldl
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- إعداد خادم الويب الوهمي لـ Render ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ------------------------------------------

TOKEN = "9116034002:AAHBVC2uB9JcD20shhS-IwAMMTyEuDPQchk"
bot = telebot.TeleBot(TOKEN)

download_count = 0
user_links = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! 👋\nأرسل لي رابط فيديو وسأسألك كيف تريد حفظه (فيديو عادي أو ملف مخفي).")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    bot.reply_to(message, f"📊 إحصائيات البوت:\nتم تنزيل **{download_count}** فيديو بنجاح حتى الآن!")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('http'))
def ask_download_type(message):
    url = message.text.split()[0]
    user_links[message.chat.id] = url
    
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("🎬 فيديو عادي", callback_data="vid_normal"),
        InlineKeyboardButton("📁 ملف مخفي (Document)", callback_data="vid_doc")
    )
    
    bot.reply_to(message, "🔗 تم استلام الرابط. كيف تريد حفظه؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["vid_normal", "vid_doc", "retry"])
def handle_choice(call):
    global download_count
    chat_id = call.message.chat.id
    
    if call.data == "retry":
        bot.delete_message(chat_id, call.message.message_id)
        process_video(chat_id, user_links.get(chat_id), "vid_normal")
        return

    url = user_links.get(chat_id)
    if not url:
        bot.answer_callback_query(call.id, "⚠️ الرابط غير متوفر. أرسله مرة أخرى.")
        return

    bot.delete_message(chat_id, call.message.message_id)
    process_video(chat_id, url, call.data)

def process_video(chat_id, url, mode):
    global download_count
    msg = bot.send_message(chat_id, "⏳ جاري جلب الرابط وتنزيل الفيديو...")
    filename = f"video_{chat_id}.mp4"
    
    try:
        result = alldl(url)
        video_url = result.get("videoUrl") or result.get("data", {}).get("videoUrl")
        
        if not video_url:
            raise Exception("لم يتم العثور على رابط مباشر.")

        response = requests.get(video_url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        with open(filename, 'rb') as media:
            if mode == "vid_doc":
                bot.send_document(chat_id, media, caption="✅ تم التنزيل (ملف مخفي)")
            else:
                bot.send_video(chat_id, media, caption="✅ تم التنزيل بنجاح")
        
        download_count += 1
        bot.delete_message(chat_id, msg.message_id)
        os.remove(filename)
        user_links.pop(chat_id, None)
        
    except Exception as e:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔄 إعادة المحاولة", callback_data="retry"))
        bot.edit_message_text(f"❌ فشل التنزيل.\nالسبب: {str(e)[:50]}", chat_id, msg.message_id, reply_markup=markup)
        
        if os.path.exists(filename):
            os.remove(filename)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "⚠️ أرسل لي رابطاً صحيحاً (يبدأ بـ http).")

# تشغيل خادم الويب والبوت معاً
keep_alive()
bot.infinity_polling()
