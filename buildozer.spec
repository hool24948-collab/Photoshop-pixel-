[app]

# Название твоего приложения (как оно будет подписано под иконкой)
title = Photoshop

# Имя пакета (только английские буквы, без пробелов)
package.name = pixelarteditor
package.domain = org.pixelapp

# Какие файлы включать в сборку
source.include_exts = py,png,jpg,kv,atlas

# Главный файл запуска
source.main = main.py

# Версия приложения
version = 0.1

# Список библиотек, которые использует приложение
requirements = python3,kivy

# Ориентация экрана (portrait — вертикальная, landscape — горизонтальная)
orientation = portrait

# Поддерживаемые версии Android
android.minapi = 21
android.sdk = 31
android.ndk = 25b

# Разрешения для работы с памятью телефона (нужно для сохранения в папки)
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

[buildozer]
# Уровень логирования (2 — подробный, чтобы видеть ошибки при сборке)
log_level = 2
