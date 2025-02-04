from flask import Flask, render_template, redirect, url_for, request, jsonify
import uuid
import threading
import telebot
from telebot import types
import sqlite3
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME  # Импортируем настройки

# Настройки Flask
app = Flask(__name__)

# Настройки Telegram-бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Таблица для хранения кодов и данных пользователей
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

# Генерация уникального ключа авторизации
def generate_auth_key():
    return str(uuid.uuid4())

# Генерация кода-пароля
def generate_password_code():
    import random
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

# Сохранение кода и данных пользователя в базу данных
def save_code_to_db(code, chat_id, username, first_name, last_name):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO codes (code, chat_id, username, first_name, last_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (code, chat_id, username, first_name, last_name, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

# Проверка кода в базе данных
def verify_code_in_db(code):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM codes WHERE code = ?', (code,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return True  # Код найден
    return False  # Код не найден

# Маршрут для главной страницы
@app.route('/')
def index():
    return render_template('index.html')

# Маршрут для входа через Telegram
@app.route('/login')
def login():
    # Генерация ключа авторизации
    auth_key = generate_auth_key()
    
    # Ссылка на Telegram-бота с ключом авторизации
    telegram_bot_url = f"https://t.me/{TELEGRAM_BOT_USERNAME}?start={auth_key}"
    
    # Возвращаем JSON с ссылкой
    return jsonify({"url": telegram_bot_url})

# Маршрут для проверки кода
@app.route('/verify_code', methods=['POST'])
def verify_code():
    code = request.form.get('code')
    
    # Проверяем код в базе данных
    if verify_code_in_db(code):
        return jsonify({"status": "success", "message": "Код верный!"})
    else:
        return jsonify({"status": "error", "message": "Неверный код."})

# Обработчик команды /start для Telegram-бота
@bot.message_handler(commands=['start'])
def handle_start(message):
    # Получаем ключ авторизации из сообщения
    auth_key = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    if auth_key:
        # Генерация кода-пароля
        password_code = generate_password_code()
        
        # Сохраняем код и данные пользователя в базу данных
        save_code_to_db(
            code=password_code,
            chat_id=message.chat.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        
        # Отправка кода-пароля пользователю
        bot.send_message(message.chat.id, f"Ваш код-пароль: {password_code}")
    else:
        bot.send_message(message.chat.id, "Привет! Используйте ссылку для входа.")

# Функция для запуска Flask-приложения
def run_flask():
    app.run(debug=False)  # Отключаем debug, чтобы не было конфликтов с ботом

# Функция для запуска Telegram-бота
def run_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    # Запуск Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Запуск Telegram-бота в основном потоке
    run_bot()