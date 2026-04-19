from datetime import datetime
from typing import List, Optional, Literal

from fastapi import FastAPI, HTTPException, Query
from starlette import status

from models import Task, TaskResponse, Priority
from storage import tasks

app = FastAPI()


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


@app.get('/tasks', response_model=List[TaskResponse])
async def get_tasks(
        completed: Optional[bool] = Query(None, description="Фильтр по статусу выполнения"),
        priority: Optional[Priority] = Query(None, description="Фильтр по приоритету"),
        limit: Optional[int] = Query(None, ge=1, description="Максимальное количество возвращаемых задач"),
        sort_by: Optional[Literal["created_at", "priority"]] = Query(
            None,
            description="Поле для сортировки: created_at или priority"
        )
):
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
    # 1. Копируем список, чтобы не менять оригинал
    result = tasks.copy()

    # 2. Фильтрация
    if completed is not None:
        result = [t for t in result if t.completed == completed]

    if priority is not None:
        result = [t for t in result if t.priority == priority]

    # 3. Сортировка
    if sort_by == "priority":
        # Задаём порядок приоритетов
        priority_order = {Priority.high: 0, Priority.medium: 1, Priority.low: 2}
        result.sort(key=lambda t: priority_order[t.priority])
    elif sort_by == "created_at":
        result.sort(key=lambda t: t.created_at)

    # 4. Ограничение количества
    if limit is not None:
        result = result[:limit]

    return result


@app.get('/tasks/{task_id}')
async def get_task_from_id(task_id: int):
    """
    * Возвращает задачу
    * Ошибка 404 если не существует
    :return: {tass_id} | 404
    """
    task = next((t for t in tasks if t.id == task_id), None)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )

    return task


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: Task):
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
    for task in tasks:
        if task.title == task_data.title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Задача с названием {task_data.title} уже существует"
            )

    now = datetime.now()
    new_task_dict = task_data.model_dump()
    new_task_dict["id"] = len(tasks)
    new_task_dict["created_at"] = now
    new_task_dict["completed_at"] = now if task_data.completed else None

    new_task = TaskResponse(**new_task_dict)
    tasks.append(new_task)
