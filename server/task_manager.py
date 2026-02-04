"""Consolidated task management logic and models."""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Models
# ============================================================================


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


class TaskListResult(BaseModel):
    tasks: List[Task]
    total: int
    filter: str


class TaskCreateResult(BaseModel):
    task: Task
    message: str


class TaskUpdateResult(BaseModel):
    task: Task
    message: str
    unblocked_tasks: List[str] = Field(default_factory=list)


class TaskGetResult(BaseModel):
    task: Optional[Task] = None
    found: bool
    message: str


class TaskSearchResult(BaseModel):
    tasks: List[Task]
    total: int
    query: str


class TaskClearResult(BaseModel):
    cleared_count: int
    message: str


# ============================================================================
# Logic
# ============================================================================


class TaskManager:
    """Manages tasks with dependencies and blockers."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize with storage path."""
        task_list_id = os.environ.get("GEMINI_TASK_LIST_ID", "default")
        base = base_dir or Path.home() / ".gemini"
        self.file_path = base / "tasks" / f"{task_list_id}.json"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> List[Task]:
        """Load tasks from disk."""
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return [Task(**t) for t in json.load(f)]
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, tasks: List[Task]) -> None:
        """Save tasks to disk."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump([t.model_dump() for t in tasks], f, indent=2, ensure_ascii=False)

    def _get_available_str(self, tasks: List[Task]) -> str:
        available = [t.id for t in tasks]
        return f" Available: {', '.join(available[:5])}" if available else ""

    def _sync_dependencies(self, tasks: List[Task]) -> None:
        """Ensure bi-directional consistency of blocked_by and blocks."""
        # Reset all blocks lists
        for t in tasks:
            t.blocks = []

        # Re-populate blocks based on blocked_by
        for t in tasks:
            for blocker_id in t.blocked_by:
                blocker = next((bt for bt in tasks if bt.id == blocker_id), None)
                if blocker and t.id not in blocker.blocks:
                    blocker.blocks.append(t.id)

    def _has_cycle(
        self, tasks: List[Task], start_id: str, current_id: str, visited: set
    ) -> bool:
        """Detect circular dependencies using DFS."""
        if current_id == start_id:
            return True
        if current_id in visited:
            return False
        visited.add(current_id)

        task = next((t for t in tasks if t.id == current_id), None)
        if not task:
            return False

        return any(
            self._has_cycle(tasks, start_id, bid, visited.copy())
            for bid in task.blocked_by
        )

    def list_tasks(self, filter: str = "all") -> TaskListResult:
        tasks = self._load()
        filtered = (
            tasks if filter == "all" else [t for t in tasks if t.status == filter]
        )
        return TaskListResult(tasks=filtered, total=len(filtered), filter=filter)

    def create_task(
        self,
        subject: str,
        description: str = "",
        blocked_by: Optional[List[str]] = None,
    ) -> TaskCreateResult:
        tasks = self._load()
        new_id = f"task-{max([int(t.id.split('-')[1]) for t in tasks if '-' in t.id] + [0]) + 1}"
        blocked_by = blocked_by or []

        # Validation
        task_ids = {t.id for t in tasks}
        invalid = [bid for bid in blocked_by if bid not in task_ids]
        if invalid:
            return TaskCreateResult(
                task=Task(id="error", subject="Error"),
                message=f"❌ Invalid blocker tasks: {', '.join(invalid)}",
            )

        # Create temporary task for cycle detection
        temp_task = Task(id=new_id, subject=subject, blocked_by=blocked_by)
        if any(
            self._has_cycle(tasks + [temp_task], new_id, bid, set())
            for bid in blocked_by
        ):
            return TaskCreateResult(
                task=Task(id="error", subject="Error"),
                message="❌ Circular Dependency detected",
            )

        task = Task(
            id=new_id, subject=subject, description=description, blocked_by=blocked_by
        )
        tasks.append(task)
        self._sync_dependencies(tasks)
        self._save(tasks)
        return TaskCreateResult(task=task, message=f"Created {new_id}: {subject}")

    def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        add_blocked_by: Optional[List[str]] = None,
        remove_blocked_by: Optional[List[str]] = None,
    ) -> TaskUpdateResult:
        tasks = self._load()
        task = next((t for t in tasks if t.id == task_id), None)
        if not task:
            return TaskUpdateResult(
                task=Task(id=task_id, subject="Not found"),
                message=f"Task {task_id} not found.{self._get_available_str(tasks)}",
            )

        if status:
            task.status = status

        if add_blocked_by:
            task_ids = {t.id for t in tasks}
            invalid = [bid for bid in add_blocked_by if bid not in task_ids]
            if invalid:
                return TaskUpdateResult(
                    task=task, message=f"❌ Invalid blocker tasks: {', '.join(invalid)}"
                )

            # Cycle detection
            orig_blocked = task.blocked_by.copy()
            task.blocked_by = list(set(task.blocked_by + add_blocked_by))
            if any(
                self._has_cycle(tasks, task_id, bid, set()) for bid in add_blocked_by
            ):
                task.blocked_by = orig_blocked
                return TaskUpdateResult(
                    task=task, message="❌ Circular Dependency detected"
                )

        if remove_blocked_by:
            task.blocked_by = [
                bid for bid in task.blocked_by if bid not in remove_blocked_by
            ]

        unblocked = []
        if status == "completed":
            for t in tasks:
                if task_id in t.blocked_by:
                    t.blocked_by.remove(task_id)
                    if not t.blocked_by:
                        unblocked.append(t.id)

        self._sync_dependencies(tasks)
        self._save(tasks)
        return TaskUpdateResult(
            task=task, message=f"Updated {task_id}", unblocked_tasks=unblocked
        )

    def get_task(self, task_id: str) -> TaskGetResult:
        tasks = self._load()
        task = next((t for t in tasks if t.id == task_id), None)
        if task:
            return TaskGetResult(task=task, found=True, message=f"Found {task_id}")
        return TaskGetResult(
            found=False,
            message=f"Task {task_id} not found.{self._get_available_str(tasks)}",
        )

    def search_tasks(
        self, query: str, filter: Optional[str] = None
    ) -> TaskSearchResult:
        tasks = self._load()
        if filter:
            tasks = [t for t in tasks if t.status == filter]
        q = query.lower()
        matches = [
            t for t in tasks if q in t.subject.lower() or q in t.description.lower()
        ]
        return TaskSearchResult(tasks=matches, total=len(matches), query=query)

    def clear_tasks(self, filter: str = "completed") -> TaskClearResult:
        tasks = self._load()
        remaining = (
            tasks
            if filter == "none"
            else [t for t in tasks if t.status != filter]
            if filter != "all"
            else []
        )
        cleared = len(tasks) - len(remaining)
        self._save(remaining)
        return TaskClearResult(
            cleared_count=cleared, message=f"Cleared {cleared} tasks"
        )
