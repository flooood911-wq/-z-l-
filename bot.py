import telebot
import requests
import os
from rahad_all_downloader import alldl

TOKEN = "9116034002:AAHBVC2uB9JcD20shhS-IwAMMTyEuDPQchk"
bot = telebot.TeleBot(TOKEN)

print("البوت يعمل الآن... جرب إرسال رابط فيديو!")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! 👋\nأرسل لي رابط فيديو من أي منصة (تيك توك، يوتيوب، إنستغرام، فيسبوك...) وسأقوم بتنزيله لك فوراً وبدون علامة مائية.")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('http'))
def download_video(message):
    url = message.text.split()[0]
    
    # حذف رسالة المستخدم (الرابط) للحفاظ على نظافة المحادثة
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    # إرسال رسالة الانتظار
    msg = bot.send_message(message.chat.id, "⏳ جاري جلب الرابط وتنزيل الفيديو...")
    
    filename = f"video_{message.chat.id}.mp4"
    
    try:
        # جلب الرابط
        result = alldl(url)
        
        if not result.get("success"):
            bot.edit_message_text("❌ فشلت عملية جلب الرابط. قد يكون الرابط غير مدعوم أو الحساب خاص.", message.chat.id, msg.message_id)
            return

        video_url = result.get("videoUrl")
        if not video_url and "data" in result:
            video_url = result["data"].get("videoUrl")
        
        if not video_url:
            bot.edit_message_text("❌ لم يتم العثور على رابط تحميل مباشر. جرب رابطاً آخر.", message.chat.id, msg.message_id)
            return

        # تنزيل الفيديو
        video_response = requests.get(video_url, stream=True, timeout=60)
        video_response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # إرسال الفيديو
        with open(filename, 'rb') as video:
            bot.send_video(message.chat.id, video, caption="✅ تم التنزيل بنجاح")
        
        # حذف رسالة الانتظار بعد نجاح الإرسال
        bot.delete_message(message.chat.id, msg.message_id)
        
        # حذف الملف المؤقت
        os.remove(filename)
        
    except Exception as e:
        error_msg = str(e)[:50]
        bot.edit_message_text(f"❌ حدث خطأ أثناء التنزيل.\nالسبب: {error_msg}...", message.chat.id, msg.message_id)
        print(f"Error: {e}")
        if os.path.exists(filename):
            os.remove(filename)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "⚠️ أرسل لي رابط فيديو صحيح (يبدأ بـ http) لأقوم بتنزيله.")

bot.infinity_polling()
