import sqlite3
from datetime import datetime
from math import ceil

from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # замените на стойкий ключ

DATABASE = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Основная таблица задач – добавлено поле due_date
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS tasks
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       title
                       TEXT
                       NOT
                       NULL,
                       description
                       TEXT
                       NOT
                       NULL,
                       category
                       TEXT
                       NOT
                       NULL,
                       priority
                       INTEGER
                       NOT
                       NULL,
                       created_at
                       TEXT
                       NOT
                       NULL,
                       due_date
                       TEXT
                   )
                   """)

    # Архивная таблица – тоже с due_date
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS deleted_tasks
                   (
                       deleted_id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       original_id
                       INTEGER,
                       title
                       TEXT,
                       description
                       TEXT,
                       category
                       TEXT,
                       priority
                       INTEGER,
                       created_at
                       TEXT,
                       due_date
                       TEXT,
                       deleted_at
                       TEXT
                       DEFAULT (
                       datetime
                   (
                       'now',
                       'localtime'
                   ))
                       )
                   """)

    conn.commit()
    conn.close()


init_db()


# ---------- вспомогательные функции для пагинации и фильтрации ----------
def get_tasks_with_filters(page=1, per_page=10, sort='created_at', priority=None):
    """
    Возвращает (tasks, total_pages, current_page) с учётом фильтров и сортировки.
    Допустимые значения sort: 'priority', 'created_at', 'due_date'.
    priority: целое число или None (показать все).
    """
    conn = get_db_connection()

    # Базовый запрос
    base_query = "SELECT * FROM tasks"
    count_query = "SELECT COUNT(*) FROM tasks"
    conditions = []
    params = []

    if priority is not None:
        try:
            p = int(priority)
            conditions.append("priority = ?")
            params.append(p)
        except (ValueError, TypeError):
            pass  # некорректный параметр игнорируем

    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)
        base_query += where_clause
        count_query += where_clause

    # Сортировка (белый список)
    sort_options = {
        'priority': 'priority DESC',
        'created_at': 'created_at DESC',
        'due_date': 'due_date ASC'  # сначала ближайшие дедлайны, NULL в конце
    }
    order_clause = sort_options.get(sort, 'created_at DESC')
    base_query += f" ORDER BY {order_clause}"

    # Пагинация
    offset = (page - 1) * per_page
    base_query += " LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    # Выполняем запрос
    tasks = conn.execute(base_query, params).fetchall()

    # Общее количество записей (без LIMIT/OFFSET)
    total = conn.execute(count_query, params[:-2] if conditions else []).fetchone()[0]
    total_pages = ceil(total / per_page) if total > 0 else 1

    conn.close()
    return tasks, total_pages, page


# ---------- маршруты ----------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/tasks")
def tasks():
    # Получаем параметры
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    sort = request.args.get('sort', 'created_at')
    priority = request.args.get('priority', None)

    # Валидация
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 50:
        per_page = 10

    tasks, total_pages, current_page = get_tasks_with_filters(
        page=page, per_page=per_page, sort=sort, priority=priority
    )

    return render_template(
        "tasks.html",
        tasks=tasks,
        page=current_page,
        total_pages=total_pages,
        per_page=per_page,
        sort=sort,
        priority=priority
    )


@app.route("/tasks/<int:id>")
def task_detail(id):
    conn = get_db_connection()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (id,)).fetchone()
    conn.close()
    if task is None:
        return "Task not found", 404
    return render_template("task_detail.html", task=task)


@app.route("/add", methods=["GET", "POST"])
def add_task():
    error = None
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        category = request.form.get("category")
        priority = request.form.get("priority")
        due_date = request.form.get("due_date")  # новый параметр

        if not title or not description or not category or not priority:
            error = "All fields except due date are required"
        else:
            try:
                priority = int(priority)
                # простейшая проверка формата даты (YYYY-MM-DD)
                if due_date:
                    datetime.strptime(due_date, "%Y-%m-%d")
                conn = get_db_connection()
                conn.execute("""
                             INSERT INTO tasks (title, description, category, priority, created_at, due_date)
                             VALUES (?, ?, ?, ?, ?, ?)
                             """, (
                                 title, description, category, priority,
                                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                 due_date if due_date else None
                             ))
                conn.commit()
                conn.close()
                flash("Task added successfully!", "success")
                return redirect(url_for("tasks"))
            except ValueError:
                error = "Priority must be a number and date format YYYY-MM-DD"
    return render_template("add_task.html", error=error)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_task(id):
    conn = get_db_connection()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (id,)).fetchone()
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        category = request.form["category"]
        priority = request.form["priority"]
        due_date = request.form.get("due_date")
        try:
            priority = int(priority)
            if due_date:
                datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            conn.close()
            return render_template("edit_task.html", task=task, error="Invalid priority or date")
        conn.execute("""
                     UPDATE tasks
                     SET title=?,
                         description=?,
                         category=?,
                         priority=?,
                         due_date=?
                     WHERE id = ?
                     """, (title, description, category, priority, due_date if due_date else None, id))
        conn.commit()
        conn.close()
        flash("Task updated!", "success")
        return redirect(url_for("tasks"))
    conn.close()
    return render_template("edit_task.html", task=task)


@app.route("/delete/<int:id>")
def delete_task(id):
    conn = get_db_connection()
    # Переносим в архив
    conn.execute("""
                 INSERT INTO deleted_tasks (original_id, title, description, category, priority, created_at, due_date)
                 SELECT id, title, description, category, priority, created_at, due_date
                 FROM tasks
                 WHERE id = ?
                 """, (id,))
    conn.execute("DELETE FROM tasks WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash("Task moved to trash.", "info")
    return redirect(url_for("tasks"))


# ---------- Корзина ----------
@app.route("/trash")
def trash():
    conn = get_db_connection()
    deleted = conn.execute("SELECT * FROM deleted_tasks ORDER BY deleted_at DESC").fetchall()
    conn.close()
    return render_template("trash.html", deleted=deleted)


@app.route("/restore/<int:deleted_id>")
def restore_task(deleted_id):
    conn = get_db_connection()
    task = conn.execute("SELECT * FROM deleted_tasks WHERE deleted_id = ?", (deleted_id,)).fetchone()
    if task:
        conn.execute("""
                     INSERT INTO tasks (title, description, category, priority, created_at, due_date)
                     VALUES (?, ?, ?, ?, ?, ?)
                     """, (task["title"], task["description"], task["category"], task["priority"], task["created_at"],
                           task["due_date"]))
        conn.execute("DELETE FROM deleted_tasks WHERE deleted_id = ?", (deleted_id,))
        conn.commit()
        flash("Task restored.", "success")
    else:
        flash("Task not found in trash.", "error")
    conn.close()
    return redirect(url_for("trash"))


@app.route("/delete-permanent/<int:deleted_id>")
def delete_permanent(deleted_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM deleted_tasks WHERE deleted_id = ?", (deleted_id,))
    conn.commit()
    conn.close()
    flash("Task permanently deleted.", "warning")
    return redirect(url_for("trash"))


# Статистика (обновим для учёта due_date при желании)
@app.route("/stats")
def stats():
    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    avg_priority = conn.execute("SELECT AVG(priority) FROM tasks").fetchone()[0]
    categories = conn.execute("SELECT category, COUNT(*) as count FROM tasks GROUP BY category").fetchall()
    # Простейший подсчёт просроченных задач
    overdue = conn.execute(
        "SELECT COUNT(*) FROM tasks WHERE due_date IS NOT NULL AND date(due_date) < date('now')"
    ).fetchone()[0]
    conn.close()
    return render_template("stats.html", total_tasks=total, avg_priority=avg_priority,
                           categories=categories, overdue=overdue)


if __name__ == "__main__":
    app.run(debug=True)
