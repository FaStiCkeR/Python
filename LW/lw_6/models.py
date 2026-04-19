from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Task(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    priority: str = Field(default=Priority.medium, pattern="^(low|medium|high)$")
    completed: bool = False
    deadline: Optional[datetime] = None


class TaskCreate(Task):
    pass


class TaskResponse(Task):
    id: int
    created_at: datetime
    completed_at: Optional[datetime] = None
