from flask import Flask, render_template, redirect, request, session, jsonify
import uuid
import threading
import telebot
from telebot import types
import sqlite3
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME

# Настройки Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Секретный ключ для сессий

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

# Генерация уникального ключа авторизации
def generate_auth_key():
    return str(uuid.uuid4())

# Генерация кода-пароля
def generate_password_code():
    import random
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

# Функция для получения данных пользователя по коду
def get_user_data_by_code(code):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM codes WHERE code = ?', (code,))
    user_data = cursor.fetchone()
    
    conn.close()
    
    if user_data:
        return {
            "username": user_data[3],  # username из базы данных
            "first_name": user_data[4],  # first_name из базы данных
            "last_name": user_data[5]  # last_name из базы данных
        }
    return None

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

# Маршрут для обработки ввода кода
@app.route('/verify_code', methods=['POST'])
def verify_code():
    code = request.form.get('code')
    
    # Проверяем код в базе данных
    user_data = get_user_data_by_code(code)
    
    if user_data:
        # Сохраняем данные пользователя в сессии
        session['username'] = user_data['username']
        session['first_name'] = user_data['first_name']
        session['last_name'] = user_data['last_name']
        
        # Перенаправляем в личный кабинет
        return redirect('/dashboard')
    else:
        return "Неверный код. Попробуйте снова."

# Маршрут для личного кабинета
@app.route('/dashboard')
def dashboard():
    # Проверяем, авторизован ли пользователь
    if 'username' not in session:
        return redirect('/')  # Перенаправляем на главную страницу
    
    # Получаем данные пользователя из сессии
    username = session['username']
    first_name = session.get('first_name', '')
    last_name = session.get('last_name', '')
    
    # Отображаем личный кабинет
    return render_template('dashboard.html', username=username, first_name=first_name, last_name=last_name)

# Маршрут для выхода
@app.route('/logout')
def logout():
    # Очищаем сессию
    session.clear()
    return redirect('/')

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

# Функция для запуска Flask-приложения
def run_flask():
    app.run(port=5000)  # Запускаем на порту 5000

# Функция для запуска Telegram-бота
def run_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    # Запуск Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Запуск Telegram-бота в основном потоке
    run_bot()