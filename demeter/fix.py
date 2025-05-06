# app_fixed.py dosyasını okuyalım
with open('app.py', 'r') as file:
    content = file.read()

# datetime.utcnow() kullanımlarını datetime.now(UTC) ile değiştirelim
# Önce gerekli import'u ekleyelim
if 'from datetime import datetime' in content:
    content = content.replace('from datetime import datetime', 'from datetime import datetime, UTC')

# Tüm utcnow() kullanımlarını değiştirelim
content = content.replace('datetime.utcnow()', 'datetime.now(UTC)')

# Güncellenmiş içeriği yeni bir dosyaya yazalım
with open('app_updated.py', 'w') as file:
    file.write(content)

print("app_fixed.py dosyasındaki datetime.utcnow() kullanımları datetime.now(UTC) ile değiştirildi ve app_updated.py olarak kaydedildi.")