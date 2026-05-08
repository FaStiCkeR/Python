import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Подключение к БД
DATABASE = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Создание таблицы
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS tasks
                   (
                       id          INTEGER PRIMARY KEY AUTOINCREMENT,
                       title       TEXT    NOT NULL,
                       description TEXT    NOT NULL,
                       category    TEXT    NOT NULL,
                       priority    INTEGER NOT NULL,
                       created_at  TEXT    NOT NULL
                   )
                   """)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS deleted_tasks
                   (
                       deleted_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                       original_id INTEGER,
                       title       TEXT,
                       description TEXT,
                       category    TEXT,
                       priority    INTEGER,
                       created_at  TEXT,
                       deleted_at  TEXT DEFAULT (datetime('now', 'localtime'))
                   );
                   """)

    conn.commit()
    conn.close()


init_db()


# Главная страница
@app.route("/")
def index():
    return render_template("index.html")


# Страница списка задач
@app.route("/tasks")
def tasks():
    conn = get_db_connection()

    sort = request.args.get("sort")

    query = "SELECT * FROM tasks"

    if sort == "priority":
        query += " ORDER BY priority DESC"
    else:
        query += " ORDER BY created_at DESC"

    tasks = conn.execute(query).fetchall()

    conn.close()

    return render_template("tasks.html", tasks=tasks)


# Одна задача

@app.route("/tasks/<int:id>")
def task_detail(id):
    conn = get_db_connection()

    task = conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (id,)
    ).fetchone()

    conn.close()

    if task is None:
        return "Task not found", 404

    return render_template("task_detail.html", task=task)


# Добавление задачи

@app.route("/add", methods=["GET", "POST"])
def add_task():
    error = None

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        category = request.form["category"]
        priority = request.form["priority"]

        # Валидация
        if not title or not description or not category or not priority:
            error = "All fields are required"

        else:
            try:
                priority = int(priority)

                conn = get_db_connection()

                conn.execute("""
                             INSERT INTO tasks
                                 (title, description, category, priority, created_at)
                             VALUES (?, ?, ?, ?, ?)
                             """, (
                                 title,
                                 description,
                                 category,
                                 priority,
                                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                             ))

                conn.commit()
                conn.close()

                return redirect(url_for("tasks"))

            except ValueError:
                error = "Priority must be a number"

    return render_template("add_task.html", error=error)


# Редактирование
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_task(id):
    conn = get_db_connection()

    task = conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (id,)
    ).fetchone()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        category = request.form["category"]
        priority = request.form["priority"]

        conn.execute("""
                     UPDATE tasks
                     SET title       = ?,
                         description = ?,
                         category    = ?,
                         priority    = ?
                     WHERE id = ?
                     """, (
                         title,
                         description,
                         category,
                         priority,
                         id
                     ))

        conn.commit()
        conn.close()

        return redirect(url_for("tasks"))

    conn.close()

    return render_template("edit_task.html", task=task)


# Удаление

@app.route("/delete/<int:id>")
def delete_task(id):
    conn = get_db_connection()

    # Копируем задачу в архивную таблицу
    conn.execute("""
                 INSERT INTO deleted_tasks (original_id, title, description, category, priority, created_at)
                 SELECT id, title, description, category, priority, created_at
                 FROM tasks
                 WHERE id = ?
                 """, (id,))

    # Удаляем оригинал
    conn.execute("DELETE FROM tasks WHERE id = ?", (id,))

    conn.commit()
    conn.close()
    return redirect(url_for("tasks"))


# Статистика

@app.route("/stats")
def stats():
    conn = get_db_connection()

    total_tasks = conn.execute(
        "SELECT COUNT(*) FROM tasks"
    ).fetchone()[0]

    avg_priority = conn.execute(
        "SELECT AVG(priority) FROM tasks"
    ).fetchone()[0]

    categories = conn.execute("""
                              SELECT category, COUNT(*) as count
                              FROM tasks
                              GROUP BY category
                              """).fetchall()

    conn.close()

    return render_template(
        "stats.html",
        total_tasks=total_tasks,
        avg_priority=avg_priority,
        categories=categories
    )


if __name__ == "__main__":
    app.run(debug=True)
