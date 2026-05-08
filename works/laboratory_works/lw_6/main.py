from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query

import models
import storage

app = FastAPI(title="Advanced Task API", version="2.0")


@app.get("/")
def root():
    return {
        "message": "Advanced Task API",
        "version": "2.0"
    }


@app.get("/tasks", response_model=List[models.TaskResponse])
def list_tasks(
        completed: Optional[bool] = Query(None),
        priority: Optional[str] = Query(None, pattern="^(low|medium|high)$"),
        limit: Optional[int] = Query(None, gt=0),
        sort_by: Optional[str] = Query(
            None,
            pattern="^(created_at|priority)$"
        )
):
    return storage.get_all_tasks(
        completed=completed,
        priority=priority,
        limit=limit,
        sort_by=sort_by
    )


@app.post("/tasks", response_model=models.TaskResponse, status_code=201)
def create_task(task: models.TaskCreate):
    try:
        return storage.add_task(task)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tasks/search", response_model=List[models.TaskResponse])
def search_tasks(
        keyword: Optional[str] = Query(None),
        priority: Optional[str] = Query(None, pattern="^(low|medium|high)$"),
        date_from: Optional[datetime] = Query(None),
        date_to: Optional[datetime] = Query(None)
):
    return storage.search_tasks(
        keyword=keyword,
        priority=priority,
        date_from=date_from,
        date_to=date_to
    )


@app.get("/tasks/stats")
def get_stats():
    return storage.get_stats()


@app.get("/tasks/{task_id}", response_model=models.TaskResponse)
def get_task(task_id: int):
    task = storage.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@app.put("/tasks/{task_id}", response_model=models.TaskResponse)
def full_update_task(task_id: int, task: models.TaskUpdate):
    try:
        return storage.update_task(task_id, task)

    except LookupError:
        raise HTTPException(status_code=404, detail="Task not found")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/tasks/{task_id}", response_model=models.TaskResponse)
def partial_update_task(task_id: int, task: models.TaskPartialUpdate):
    try:
        return storage.partial_update_task(task_id, task)

    except LookupError:
        raise HTTPException(status_code=404, detail="Task not found")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/tasks/{task_id}/complete", response_model=models.TaskResponse)
def mark_completed(task_id: int):
    try:
        return storage.complete_task(task_id)

    except LookupError:
        raise HTTPException(status_code=404, detail="Task not found")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    if not storage.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "message": f"Task with id {task_id} deleted"
    }
