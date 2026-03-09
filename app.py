from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"

def get_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()

    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        due_date TEXT,
        priority TEXT,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')


    conn.commit()
    conn.close()


init_db()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_connection()
    tasks = conn.execute("SELECT * FROM tasks WHERE user_id=?",
                         (session['user_id'],)).fetchall()
    conn.close()

    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect('/login')

    task = request.form['content']
    due_date = request.form['due_date']
    priority = request.form['priority']

    conn = get_connection()
    conn.execute(
        "INSERT INTO tasks (content, due_date, priority, user_id) VALUES (?, ?, ?, ?)",
        (task, due_date, priority, session['user_id'])
    )
    conn.commit()
    conn.close()

    return redirect('/')


@app.route('/delete/<int:id>')
def delete(id):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/toggle/<int:id>')
def toggle(id):
    conn = get_connection()
    task = conn.execute("SELECT completed FROM tasks WHERE id=?", (id,)).fetchone()
    new_status = 0 if task["completed"] == 1 else 1
    conn.execute("UPDATE tasks SET completed=? WHERE id=?", (new_status, id))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        try:
            conn = get_connection()
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
            conn.close()

            flash("Account created successfully! Please login.", "success")
            return redirect('/login')

        except:
            flash("Username already exists!", "danger")

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash("Login successful!", "success")
            return redirect('/')
        else:
            flash("Invalid username or password", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect('/login')


@app.route('/edit/<int:id>', methods=['POST'])
def edit(id):
    new_content = request.form['new_content']
    conn = get_connection()
    conn.execute("UPDATE tasks SET content=? WHERE id=?", (new_content, id))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
