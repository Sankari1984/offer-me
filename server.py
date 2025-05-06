from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import json
import os
import uuid
import sqlite3
from werkzeug.utils import secure_filename
from urllib.parse import unquote
import requests

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
OPENROUTER_API_KEY = config.get("openrouter_api_key", "")
print("🔑 مفتاح OpenRouter:", OPENROUTER_API_KEY)


app = Flask(__name__, template_folder='templates')
CORS(app)
import os
import json
from flask import request, jsonify

TOKENS_FILE = 'fcm_tokens.json'

# أنشئ الملف إذا ما كان موجود
if not os.path.exists(TOKENS_FILE):
    with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)

@app.route('/save-token', methods=['POST'])
def save_token():
    data = request.get_json()
    user_id = data.get('user_id')
    token = data.get('token')

    if not user_id or not token:
        return jsonify({"status": "error", "message": "Missing user_id or token"}), 400

    with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
        tokens = json.load(f)

    tokens[user_id] = token

    with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)

    return jsonify({"status": "success", "message": "Token saved ✅"})
import requests

FCM_API_KEY = "AAAAkUu..."  # 🔐 استبدله بمفتاح السيرفر من Firebase console (Server Key)

@app.route('/send-notification', methods=['POST'])
def send_notification():
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title', '🛎️ إشعار جديد')
    body = data.get('body', '')

    # تحميل التوكنات من الملف
    with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
        tokens = json.load(f)

    token = tokens.get(user_id)
    if not token:
        return jsonify({"status": "error", "message": "توكن غير موجود لهذا المستخدم"}), 404

    headers = {
        'Authorization': f'key={FCM_API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'to': token,
        'notification': {
            'title': title,
            'body': body,
            'icon': 'icon-192.png',
        }
    }

    response = requests.post('https://fcm.googleapis.com/fcm/send', headers=headers, json=payload)
    return jsonify({
        "status": "sent" if response.status_code == 200 else "failed",
        "response": response.json()
    })

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mov'}
DATABASE_FILE = 'products_data.json'
USERS_FILE = 'users.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'logos'), exist_ok=True)

if not os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)

    for user in users:
        if user['username'] == username and user['password'] == password:
            settings_file = f"settings_user_{user['user_id']}.json"
            if not os.path.exists(settings_file):
                with open(settings_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "tabs": ["إلكترونيات", "ملابس", "ألعاب", "عطور"],
                        "phone": "", "instagram": "", "whatsapp": ""
                    }, f, ensure_ascii=False, indent=2)
            return jsonify({"status": "success", "user_id": user['user_id'], "full_name": user['full_name']})
    return jsonify({"status": "fail"}), 401

@app.route('/upload-logo/<user_id>', methods=['POST'])
def upload_logo(user_id):
    file = request.files.get('file')
    if not file or not allowed_file(file.filename):
        return jsonify({"status": "fail", "message": "ملف غير صالح"}), 400

    logo_folder = os.path.join(UPLOAD_FOLDER, 'logos')
    os.makedirs(logo_folder, exist_ok=True)

    for ext in ['png', 'jpg', 'jpeg', 'gif']:
        old_path = os.path.join(logo_folder, f"{user_id}_logo.{ext}")
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception as e:
                print(f"تعذر حذف الشعار القديم: {e}")

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = secure_filename(f"{user_id}_logo.{ext}")
    filepath = os.path.join(logo_folder, filename)
    file.save(filepath)
    logo_url = f"/uploads/logos/{filename}"

    settings_file = f"settings_user_{user_id}.json"
    settings = {}
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    settings['logo'] = logo_url
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

    return jsonify({"status": "success", "message": "✅ تم تحديث الشعار", "logo": logo_url})

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(app.root_path, 'uploads'), filename)

@app.route('/settings/<user_id>', methods=['GET', 'POST'])
def manage_settings(user_id):
    settings_file = f"settings_user_{user_id}.json"

    if request.method == 'GET':
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        return jsonify({"tabs": ["إلكترونيات", "ملابس", "ألعاب", "عطور"]})

    elif request.method == 'POST':
        data = request.get_json()
        tabs = data.get('tabs', [])
        phone = data.get('phone', '')
        instagram = data.get('instagram', '')
        whatsapp = data.get('whatsapp', '')

        if not isinstance(tabs, list) or len(tabs) > 4:
            return jsonify({"status": "fail", "message": "أقصى عدد 4 تصنيفات"}), 400

        settings = {
            "tabs": tabs,
            "phone": phone,
            "instagram": instagram,
            "whatsapp": whatsapp
        }

        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

        return jsonify({"status": "success", "message": "✅ تم حفظ التصنيفات والمعلومات"})

@app.route('/products', methods=['GET'])
def get_products():
    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route('/all_products')
def all_products():
    return render_template('all_products.html')
   

@app.route('/login.html')
def login_html(): return render_template('login.html')

@app.route('/store.html')
def store_page(): return render_template('store.html')

@app.route('/admin.html')
def admin_page(): return render_template('admin.html')

@app.route('/upload.html')
def upload_page(): return render_template('upload.html')

@app.route('/upload_logo.html')
def upload_logo_page(): return render_template('upload_logo.html')

@app.route('/manage_tabs.html')
def manage_tabs_page(): return render_template('manage_tabs.html')

@app.route('/change_password.html')
def change_password_page(): return render_template('change_password.html')


@app.route('/users', methods=['GET'])
def get_users():
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route('/add-user', methods=['POST'])
def add_user():
    data = request.get_json()

    if not data.get('username') or not data.get('password') or not data.get('full_name'):
        return jsonify({"status": "fail", "message": "الرجاء ملء جميع الحقول"}), 400

    if not data.get('business_type'):
        return jsonify({"status": "fail", "message": "الرجاء اختيار نوع النشاط"}), 400

    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)

    if any(u['username'] == data['username'] for u in users):
        return jsonify({"status": "fail", "message": "اسم المستخدم موجود مسبقًا"}), 400

    new_user = {
        "user_id": data['username'],
        "username": data['username'],
        "password": data['password'],
        "full_name": data['full_name'],
        "business_type": data['business_type']
    }

    users.append(new_user)

    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

            # ✅ حفظ النشاط الجديد إذا غير موجود مسبقاً
    with open('business_types.json', 'r+', encoding='utf-8') as f:
        business_types = json.load(f)
        if data['business_type'] not in business_types:
            business_types.insert(-1, data['business_type'])  # قبل "أخرى"
            f.seek(0)
            json.dump(business_types, f, ensure_ascii=False, indent=4)
            f.truncate()


    return jsonify({"status": "success", "message": "✅ تم إضافة المستخدم بنجاح"})



def generate_instagram_post(user_name, product_name, description):
    prompt = f"""
اكتب بوست إنستغرام تسويقي مشوّق لمنتج اسمه "{product_name}" ووصفه "{description}".
استخدم 2 إيموجي فقط داخل النص بطريقة جذابة.
لا تذكر اسم الزبون في النص أبداً، فقط أضف هاشتاغ #{user_name} في النهاية.
اجعل البوست قصير، واضح، ويحتوي على كلمات قوية مثل: الآن، حصري، لا تفوّت، الأفضل، اكتشف، جرب.
احرص أن يحتوي على 4 هاشتاغات فقط:
- واحد باسم الزبون: #{user_name}
- واحد ثابت: #قطر
- واثنين آخرين حسب محتوى المنتج.
تجنب التكرار والجمل الطويلة.
البوست مخصص للنسخ والنشر على إنستغرام.
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "أنت كاتب محتوى تسويقي محترف في إنستغرام."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("فشل في توليد البوست:", e)
        return ""

@app.route('/upload-product', methods=['POST'])
def upload_product():
    user_id = request.form.get('user_id')
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price', '')
    file = request.files.get('file')

    if not all([user_id, name , description, file]):
        return jsonify({"status": "fail", "message": "جميع الحقول مطلوبة"}), 400

    if not allowed_file(file.filename):
        return jsonify({"status": "fail", "message": "نوع الملف غير مدعوم"}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    file_url = f"/{UPLOAD_FOLDER}/{filename}"

    # جلب اسم الزبون
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)
    user_name = next((u['full_name'] for u in users if u['user_id'] == user_id), user_id)

    # توليد بوست إنستغرام
    post_text = generate_instagram_post(user_name=user_name.replace(" ", ""), product_name=name, description=description)
    print("📢 تم توليد البوست:", post_text)

    # رجّع الرد فقط دون حفظ المنتج، حتى المستخدم يوافق عليه
    return jsonify({
        "status": "pending",
        "message": "✅ تم توليد البوست. هل ترغب بحفظ المنتج؟",
        "image": file_url,
        "post": post_text,
        "temp_data": {
            "user_id": user_id,
            "name": name,
            "description": description,
            "price": price,
            "image": file_url
        }
    })



@app.route('/delete-product/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)
    product_to_delete = next((p for p in products if p.get("id") == product_id), None)
    if product_to_delete:
        file_path = product_to_delete.get('image', '').lstrip('/')
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
        products = [p for p in products if p.get("id") != product_id]
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=4)
        return jsonify({"status": "success", "message": "✅ تم حذف المنتج بنجاح"})
    return jsonify({"status": "fail", "message": "❌ المنتج غير موجود"}), 404

@app.route('/delete-user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    user_id = unquote(user_id)
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)
    users = [u for u in users if u['user_id'] != user_id]
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)
    updated_products = []
    for p in products:
        if p.get('user_id') == user_id:
            image_path = p.get('image', '').lstrip('/')
            if os.path.exists(image_path):
                try: os.remove(image_path)
                except: pass
        else:
            updated_products.append(p)
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_products, f, ensure_ascii=False, indent=4)

    logo_folder = os.path.join(UPLOAD_FOLDER, 'logos')
    for ext in ['png', 'jpg', 'jpeg', 'gif']:
        logo_path = os.path.join(logo_folder, f"{user_id}_logo.{ext}")
        if os.path.exists(logo_path):
            try: os.remove(logo_path)
            except: pass

    settings_file = f"settings_user_{user_id}.json"
    if os.path.exists(settings_file):
        try: os.remove(settings_file)
        except: pass

    return jsonify({"status": "success", "message": "✅ تم حذف المستخدم وكل ملفاته بنجاح"})

@app.route('/change-password/<user_id>', methods=['POST'])
def change_password(user_id):
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        users = json.load(f)
    for user in users:
        if user['user_id'] == user_id:
            if user['password'] == old_password:
                user['password'] = new_password
                with open(USERS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(users, f, ensure_ascii=False, indent=4)
                return jsonify({"status": "success", "message": "✅ تم تغيير كلمة المرور بنجاح"})
            return jsonify({"status": "fail", "message": "❌ كلمة المرور القديمة غير صحيحة"}), 400
    return jsonify({"status": "fail", "message": "❌ المستخدم غير موجود"}), 404

@app.route('/confirm-product', methods=['POST'])
def confirm_product():
    user_id = request.form.get('user_id')
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price', '')
    post = request.form.get('post')
    file = request.files.get('file')

    if not all([user_id, name, description, post, file]):
        return jsonify({"status": "fail", "message": "❌ جميع الحقول مطلوبة"}), 400

    if not allowed_file(file.filename):
        return jsonify({"status": "fail", "message": "❌ نوع الملف غير مدعوم"}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    file_url = f"/{UPLOAD_FOLDER}/{filename}"

    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)

    new_product = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "name": name,
        "description": description,
        "price": price,
        "image": file_url,
        "post": post
    }

    products.append(new_product)

    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    return jsonify({"status": "success", "message": "✅ تم حفظ المنتج بنجاح"})

@app.route('/generate-post', methods=['POST'])
def generate_post_api():
    data = request.get_json()
    name = data.get('name')
    desc = data.get('description')
    user_id = data.get('user_id', '').replace(" ", "")
    if not name or not desc or not user_id:
        return jsonify({"status": "fail", "message": "البيانات ناقصة"}), 400
    post = generate_instagram_post(user_name=user_id, product_name=name, description=desc)
    return jsonify({"status": "success", "post": post})

@app.route('/pin-product/<product_id>', methods=['POST'])
def pin_product(product_id):
    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)

    updated = False
    for product in products:
        if product['id'] == product_id:
            product['pinned'] = True
            updated = True
        else:
            product['pinned'] = False  # نزيل التثبيت عن باقي المنتجات

    if not updated:
        return jsonify({'status': 'error', 'message': 'Product not found'}), 404

    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    return jsonify({'status': 'success', 'message': 'Product pinned successfully'})
@app.route('/likes/<product_id>', methods=['GET'])
def get_likes(product_id):
    conn = sqlite3.connect('likes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT count FROM likes WHERE product_id = ?', (product_id,))
    row = cursor.fetchone()
    conn.close()
    return jsonify({'likes': row[0] if row else 0})
@app.route('/like/<product_id>', methods=['POST'])
def like_product(product_id):
    conn = sqlite3.connect('likes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT count FROM likes WHERE product_id = ?', (product_id,))
    row = cursor.fetchone()

    if row:
        new_count = row[0] + 1
        cursor.execute('UPDATE likes SET count = ? WHERE product_id = ?', (new_count, product_id))
    else:
        new_count = 1
        cursor.execute('INSERT INTO likes (product_id, count) VALUES (?, ?)', (product_id, new_count))

    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'likes': new_count})

@app.route('/comments/<product_id>')
def get_comments(product_id):
    try:
        with open('comments.json', 'r', encoding='utf-8') as f:
            comments = json.load(f)
    except:
        comments = {}
    return jsonify(comments.get(product_id, []))

@app.route('/add_comment', methods=['POST'])
def add_comment():
    data = request.get_json()
    product_id = data['product_id']
    comment = data['comment']

    try:
        with open('comments.json', 'r', encoding='utf-8') as f:
            comments = json.load(f)
    except:
        comments = {}

    comments.setdefault(product_id, []).append(comment)
    with open('comments.json', 'w', encoding='utf-8') as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)

    return jsonify({'success': True})
@app.route('/business-types', methods=['GET'])
def get_business_types():
    with open('business_types.json', 'r', encoding='utf-8') as f:
        types = json.load(f)
    return jsonify(types)
from flask import send_from_directory

@app.route('/firebase-messaging-sw.js')
def serve_firebase_sw():
    return send_from_directory('.', 'firebase-messaging-sw.js')


if __name__ == '__main__':
   import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)

