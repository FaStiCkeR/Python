from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# Базовые поля задачи (то, что приходит от пользователя)
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    completed: bool = False
    deadline: Optional[datetime] = None


# Модель для создания задачи (POST)
class TaskCreate(TaskBase):
    # Все поля уже описаны в TaskBase, но можно переопределить опциональные,
    # если требуется (оставляем как есть – title обязателен, остальное опционально)
    pass


#  Модель для полного обновления (PUT)
class TaskUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str  # здесь обязательно, пустая строка допускается
    priority: str = Field(..., pattern="^(low|medium|high)$")
    deadline: datetime  # обязательно


#  Модель для частичного обновления (PATCH)
class TaskPartialUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    deadline: Optional[datetime] = None


#  Модель, хранящаяся в памяти (с системными полями)
class TaskInDB(TaskBase):
    id: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # если будете работать с ORM, но здесь не требуется


#  Модель для ответа API (можно использовать TaskInDB напрямую)
TaskResponse = TaskInDB
