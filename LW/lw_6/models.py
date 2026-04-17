from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Task(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    completed: bool = False
    deadline: Optional[datetime] = None
