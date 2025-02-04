from flask import Flask, render_template, redirect, request, session
import sqlite3

# Создаём отдельное Flask-приложение для личного кабинета
user_app = Flask(__name__)
user_app.secret_key = 'your_secret_key'  # Секретный ключ для сессий

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

# Маршрут для главной страницы личного кабинета
@user_app.route('/')
def index():
    return redirect('/login')  # Перенаправляем на страницу входа

# Маршрут для личного кабинета
@user_app.route('/dashboard')
def dashboard():
    # Проверяем, авторизован ли пользователь
    if 'username' not in session:
        return redirect('/login')  # Перенаправляем на страницу входа
    
    # Получаем данные пользователя из сессии
    username = session['username']
    first_name = session.get('first_name', '')
    last_name = session.get('last_name', '')
    
    # Отображаем личный кабинет
    return render_template('dashboard.html', username=username, first_name=first_name, last_name=last_name)

# Маршрут для обработки ввода кода
@user_app.route('/verify_code', methods=['POST'])
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

# Маршрут для страницы входа
@user_app.route('/login')
def login():
    return render_template('login.html')

# Маршрут для выхода
@user_app.route('/logout')
def logout():
    # Очищаем сессию
    session.clear()
    return redirect('/login')

# Запуск Flask-приложения для личного кабинета
if __name__ == '__main__':
    user_app.run(port=5001)