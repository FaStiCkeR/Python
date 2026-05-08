from datetime import datetime
from typing import List, Optional, Dict, Any

from models import TaskInDB, TaskCreate, TaskUpdate, TaskPartialUpdate

# Хранилища
tasks: List[TaskInDB] = []
archived_tasks: List[TaskInDB] = []
_next_id = 1

# Порядок приоритетов для сортировки (меньше – выше)
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _generate_id() -> int:
    global _next_id
    new_id = _next_id
    _next_id += 1
    return new_id


def _archive_old_tasks() -> None:
    """Если активных задач > 20, перемещаем самые старые в архив."""
    while len(tasks) > 20:
        # Сортируем по created_at (старые – первые)
        tasks.sort(key=lambda t: t.created_at)
        oldest = tasks.pop(0)  # забираем самую старую
        archived_tasks.append(oldest)


def get_all_tasks(completed: Optional[bool] = None,
                  priority: Optional[str] = None,
                  limit: Optional[int] = None,
                  sort_by: Optional[str] = None) -> List[TaskInDB]:
    result = list(tasks)

    # Фильтрация
    if completed is not None:
        result = [t for t in result if t.completed == completed]
    if priority is not None:
        result = [t for t in result if t.priority == priority]

    # Сортировка
    if sort_by == "created_at":
        result.sort(key=lambda t: t.created_at)
    elif sort_by == "priority":
        result.sort(key=lambda t: PRIORITY_ORDER.get(t.priority, 99))

    # Ограничение количества
    if limit is not None and limit > 0:
        result = result[:limit]

    return result


def get_task(task_id: int) -> Optional[TaskInDB]:
    for task in tasks:
        if task.id == task_id:
            return task
    return None


def _is_title_unique(title: str, exclude_id: Optional[int] = None) -> bool:
    for task in tasks:
        if task.title == title and task.id != exclude_id:
            return False
    return True


def add_task(data: TaskCreate) -> TaskInDB:
    if not _is_title_unique(data.title):
        raise ValueError("Task with this title already exists")

    new_task = TaskInDB(
        id=_generate_id(),
        created_at=datetime.now(),
        **data.model_dump()
    )
    tasks.append(new_task)

    # Автоархивация, если превышен лимит
    _archive_old_tasks()

    return new_task


def update_task(task_id: int, data: TaskUpdate) -> TaskInDB:
    task = get_task(task_id)
    if task is None:
        raise LookupError("Task not found")

    if not _is_title_unique(data.title, exclude_id=task_id):
        raise ValueError("Task with this title already exists")

    # Полное обновление: заменяем только те поля, которые разрешены
    task.title = data.title
    task.description = data.description
    task.priority = data.priority
    task.deadline = data.deadline
    # completed и completed_at не трогаем
    return task


def partial_update_task(task_id: int, data: TaskPartialUpdate) -> TaskInDB:
    task = get_task(task_id)
    if task is None:
        raise LookupError("Task not found")

    update_data = data.model_dump(exclude_unset=True)

    if "title" in update_data:
        if not _is_title_unique(update_data["title"], exclude_id=task_id):
            raise ValueError("Task with this title already exists")
        task.title = update_data["title"]
    if "description" in update_data:
        task.description = update_data["description"]
    if "priority" in update_data:
        task.priority = update_data["priority"]
    if "deadline" in update_data:
        task.deadline = update_data["deadline"]

    return task


def complete_task(task_id: int) -> TaskInDB:
    task = get_task(task_id)
    if task is None:
        raise LookupError("Task not found")
    if task.completed:
        raise ValueError("Task is already completed")

    task.completed = True
    task.completed_at = datetime.now()
    return task


def delete_task(task_id: int) -> bool:
    task = get_task(task_id)
    if task is None:
        return False
    tasks.remove(task)
    return True


def search_tasks(keyword: Optional[str] = None,
                 priority: Optional[str] = None,
                 date_from: Optional[datetime] = None,
                 date_to: Optional[datetime] = None) -> List[TaskInDB]:
    result = list(tasks)

    if keyword:
        kw = keyword.lower()
        result = [t for t in result
                  if kw in t.title.lower() or (t.description and kw in t.description.lower())]
    if priority:
        result = [t for t in result if t.priority == priority]
    if date_from:
        result = [t for t in result if t.deadline and t.deadline >= date_from]
    if date_to:
        result = [t for t in result if t.deadline and t.deadline <= date_to]

    return result


def get_stats() -> Dict[str, Any]:
    total = len(tasks)
    completed = sum(1 for t in tasks if t.completed)
    incomplete = total - completed
    now = datetime.now()
    overdue = sum(1 for t in tasks
                  if t.deadline and t.deadline < now and not t.completed)
    priority_dist = {"low": 0, "medium": 0, "high": 0}
    for t in tasks:
        priority_dist[t.priority] += 1

    return {
        "total": total,
        "completed": completed,
        "incomplete": incomplete,
        "overdue": overdue,
        "priority_distribution": priority_dist
    }
