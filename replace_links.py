import os

# النص القديم والجديد
old_text = "https://your-app-name.onrender.com"
new_text = "https://offer-me.onrender.com"

# الامتدادات المستهدفة
extensions = ['.js', '.html']

def update_links(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if old_text in content:
        content = content.replace(old_text, new_text)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ تم التعديل في: {file_path}")

# امشِ على كل الملفات في المجلد الحالي والمجلدات الفرعية
for root, dirs, files in os.walk("."):
    for file in files:
        if any(file.endswith(ext) for ext in extensions):
            full_path = os.path.join(root, file)
            update_links(full_path)

print("🎯 تم استبدال جميع روابط your-app-name بالرابط الحقيقي.")
