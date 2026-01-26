"""Pydantic models for task management."""

from typing import List, Optional, Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class Task(BaseModel):
    """Task model with status and dependencies."""

    id: str = Field(..., description="Unique task identifier")
    subject: str = Field(..., description="Brief task title")
    description: str = Field(default="", description="Detailed task description")
    status: Literal["pending", "in_progress", "completed"] = Field(
        default="pending", description="Current task status"
    )
    blocked_by: List[str] = Field(
        default_factory=list, description="List of task IDs blocking this task"
    )
    blocks: List[str] = Field(
        default_factory=list, description="List of task IDs this task blocks"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Task creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )


class TaskListResult(BaseModel):
    """Result of listing tasks."""

    tasks: List[Task] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks")
    filter: str = Field(..., description="Filter applied")


class TaskCreateResult(BaseModel):
    """Result of creating a task."""

    task: Task = Field(..., description="Created task")
    message: str = Field(..., description="Success message")


class TaskUpdateResult(BaseModel):
    """Result of updating a task."""

    task: Task = Field(..., description="Updated task")
    message: str = Field(..., description="Success message")
    unblocked_tasks: List[str] = Field(
        default_factory=list, description="Tasks that were unblocked by this update"
    )


class TaskGetResult(BaseModel):
    """Result of getting a task."""

    task: Optional[Task] = Field(None, description="Retrieved task")
    found: bool = Field(..., description="Whether task was found")
    message: str = Field(..., description="Status message")


class TaskSearchResult(BaseModel):
    """Result of searching tasks."""

    tasks: List[Task] = Field(..., description="Matching tasks")
    total: int = Field(..., description="Total matches found")
    query: str = Field(..., description="Search query used")


class TaskClearResult(BaseModel):
    """Result of clearing tasks."""

    cleared_count: int = Field(..., description="Number of tasks cleared")
    message: str = Field(..., description="Success message")
