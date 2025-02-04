import threading
import telebot
from telebot import types
import sqlite3
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME
from user_routes import user_app  # Импортируем Flask-приложение для личного кабинета

# Настройки Telegram-бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            chat_id INTEGER,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Инициализация базы данных при запуске
init_db()

# Генерация кода-пароля
def generate_password_code():
    import random
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

# Обработчик команды /start для Telegram-бота
@bot.message_handler(commands=['start'])
def handle_start(message):
    # Получаем ключ авторизации из сообщения
    auth_key = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    if auth_key:
        # Генерация кода-пароля
        password_code = generate_password_code()
        
        # Сохраняем код и данные пользователя в базу данных
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO codes (code, chat_id, username, first_name, last_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (password_code, message.chat.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Отправка кода-пароля пользователю
        bot.send_message(message.chat.id, f"Ваш код-пароль: {password_code}")
    else:
        bot.send_message(message.chat.id, "Привет! Используйте ссылку для входа.")

# Функция для запуска Flask-приложения (личный кабинет)
def run_user_app():
    user_app.run(port=5001)  # Запускаем на другом порту, чтобы не было конфликтов

# Функция для запуска Telegram-бота
def run_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    # Запуск Flask-приложения для личного кабинета в отдельном потоке
    user_app_thread = threading.Thread(target=run_user_app)
    user_app_thread.start()

    # Запуск Telegram-бота в основном потоке
    run_bot()