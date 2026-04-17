from fastapi import FastAPI
app = FastAPI()

tasks = []
archived_tasks = []

@app.get('/')
async def get_default():
    """
    :return: {
    "message": "Advanced Task API",
    "version": "2.0"
    }
    """
    return {
        "message": "Advanced Task API",
        "version": "2.0"
    }


@app.get('/tasks')
async def get_tasks():
    """
    Поддерживает параметры:
    * `completed: bool`
    * `priority: str`
    * `limit: int`
    * `sort_by: created_at | priority`

📌 Логика:
* Фильтрация по параметрам
* Сортировка:
    * priority: high → medium → low
* Ограничение количества
"""
    filtered_tasks = sorted(tasks)


@app.get('/tasks/{task_id}')
async def get_task():
    """
    * Возвращает задачу
    * Ошибка 404 если не существует
    :return: {tass_id} | 404
    """
    pass


@app.post('/tasks')
async def post_tasks():
    """
    📌 Дополнительно:
    * Проверка уникальности `title`
    * Автоматически:
        * `id`
        * `created_at`

    📌 Ошибки:
    * 400 если title уже существует
    :return:
    """
    pass
