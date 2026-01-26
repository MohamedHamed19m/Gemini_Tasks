"""Task management logic."""

from typing import List, Optional, Dict, Any
from pathlib import Path

from models import (
    Task,
    TaskListResult,
    TaskCreateResult,
    TaskUpdateResult,
    TaskGetResult,
    TaskSearchResult,
    TaskClearResult,
)
from storage import TaskStorage


class TaskManager:
    """Manages tasks with dependencies and blockers."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize task manager with storage.

        Args:
            base_dir: Optional base directory for tasks.
        """
        self.storage = TaskStorage(base_dir=base_dir)

    def _generate_task_id(self, tasks: List[Task]) -> str:
        """Generate unique task ID.

        Args:
            tasks: Current list of tasks

        Returns:
            New unique task ID

        """
        if not tasks:
            return "task-1"

        max_num = 0
        for task in tasks:
            try:
                num = int(task.id.replace("task-", ""))
                max_num = max(max_num, num)
            except ValueError:
                continue

        return f"task-{max_num + 1}"

    def _update_blocks_references(self, tasks: List[Task], task_id: str) -> None:
        """Update blocks references when a task is updated.

        Args:
            tasks: List of all tasks
            task_id: ID of the task being updated

        """
        task = next((t for t in tasks if t.id == task_id), None)
        if not task:
            return

        # Update blocks for all tasks that this task is blocked by
        for blocker_id in task.blocked_by:
            blocker = next((t for t in tasks if t.id == blocker_id), None)
            if blocker and task_id not in blocker.blocks:
                blocker.blocks.append(task_id)

    def _detect_circular_dependency(
        self, tasks: List[Task], task_id: str, blocked_by: List[str]
    ) -> bool:
        """Prevent circular dependencies.

        Args:
            tasks: Current list of tasks
            task_id: ID of the task to check
            blocked_by: List of task IDs this task will be blocked by

        Returns:
            True if adding these blockers would create a cycle
        """

        def has_path(from_id: str, to_id: str, visited: set) -> bool:
            if from_id == to_id:
                return True
            if from_id in visited:
                return False
            visited.add(from_id)

            from_task = next((t for t in tasks if t.id == from_id), None)
            if not from_task:
                return False

            return any(
                has_path(bid, to_id, visited.copy()) for bid in from_task.blocked_by
            )

        # Check if adding any of these blockers creates a cycle back to task_id
        return any(has_path(bid, task_id, set()) for bid in blocked_by)

    def _validate_blockers(self, tasks: List[Task], blocked_by: List[str]) -> None:
        """Ensure blocker tasks exist.

        Args:
            tasks: Current list of tasks
            blocked_by: List of task IDs to validate

        Raises:
            ValueError: If any blocker task ID is not found
        """
        task_ids = {t.id for t in tasks}
        invalid = [bid for bid in blocked_by if bid not in task_ids]
        if invalid:
            raise ValueError(f"Invalid blocker tasks: {', '.join(invalid)}")

    def list_tasks(self, filter: str = "all") -> TaskListResult:
        """List tasks with optional filter.

        Args:
            filter: Status filter (all, pending, in_progress, completed)

        Returns:
            TaskListResult with filtered tasks

        """
        tasks_data = self.storage.load_tasks()
        tasks = [Task(**task_dict) for task_dict in tasks_data]

        if filter != "all":
            tasks = [t for t in tasks if t.status == filter]

        return TaskListResult(tasks=tasks, total=len(tasks), filter=filter)

    def create_task(
        self,
        subject: str,
        description: str = "",
        blocked_by: Optional[List[str]] = None,
    ) -> TaskCreateResult:
        """Create a new task.

        Args:
            subject: Task subject/title
            description: Task description
            blocked_by: List of task IDs this task is blocked by

        Returns:
            TaskCreateResult with created task

        """
        tasks_data = self.storage.load_tasks()
        tasks = [Task(**task_dict) for task_dict in tasks_data]

        task_id = self._generate_task_id(tasks)
        blocked_by = blocked_by or []

        # Validate blockers exist
        try:
            self._validate_blockers(tasks, blocked_by)
        except ValueError as e:
            return TaskCreateResult(
                task=Task(id="error", subject="Validation Error"),
                message=f"❌ {str(e)}",
            )

        # Detect circular dependencies
        if self._detect_circular_dependency(tasks, task_id, blocked_by):
            return TaskCreateResult(
                task=Task(id="error", subject="Circular Dependency"),
                message=f"❌ Cannot create task: Would create Circular Dependency",
            )

        task = Task(
            id=task_id,
            subject=subject,
            description=description,
            status="pending",
            blocked_by=blocked_by,
            blocks=[],
        )

        tasks.append(task)

        # Update blocks references
        self._update_blocks_references(tasks, task_id)

        # Save all tasks
        self.storage.save_tasks([t.model_dump() for t in tasks])

        return TaskCreateResult(task=task, message=f"Created task {task_id}: {subject}")

    def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        add_blocked_by: Optional[List[str]] = None,
        remove_blocked_by: Optional[List[str]] = None,
    ) -> TaskUpdateResult:
        """Update a task.

        Args:
            task_id: Task ID to update
            status: New status
            add_blocked_by: Task IDs to add as blockers
            remove_blocked_by: Task IDs to remove as blockers

        Returns:
            TaskUpdateResult with updated task

        """
        tasks_data = self.storage.load_tasks()
        tasks = [Task(**task_dict) for task_dict in tasks_data]

        task = next((t for t in tasks if t.id == task_id), None)
        if not task:
            available = [t.id for t in tasks]
            available_str = (
                f" Available: {', '.join(available[:5])}" if available else ""
            )
            return TaskUpdateResult(
                task=Task(id=task_id, subject="Not found"),
                message=f"Task {task_id} not found.{available_str}",
                unblocked_tasks=[],
            )

        # Update status
        if status:
            old_status = task.status
            task.status = status

        # Add blockers
        if add_blocked_by:
            # Validate blockers exist
            try:
                self._validate_blockers(tasks, add_blocked_by)
            except ValueError as e:
                return TaskUpdateResult(
                    task=task, message=f"❌ {str(e)}", unblocked_tasks=[]
                )

            # Detect circular dependencies
            if self._detect_circular_dependency(tasks, task_id, add_blocked_by):
                return TaskUpdateResult(
                    task=task,
                    message=f"❌ Cannot add blockers: Would create Circular Dependency",
                    unblocked_tasks=[],
                )

            for blocker_id in add_blocked_by:
                if blocker_id not in task.blocked_by:
                    task.blocked_by.append(blocker_id)

        # Remove blockers
        if remove_blocked_by:
            for blocker_id in remove_blocked_by:
                blocker_task = next((t for t in tasks if t.id == blocker_id), None)
                if blocker_task and task_id in blocker_task.blocks:
                    blocker_task.blocks.remove(task_id)
            task.blocked_by = [
                bid for bid in task.blocked_by if bid not in remove_blocked_by
            ]

        # Update blocks references
        self._update_blocks_references(tasks, task_id)

        # Check for unblocked tasks if this task was completed
        unblocked_tasks = []
        if status == "completed":
            for other_task in tasks:
                if task_id in other_task.blocked_by:
                    other_task.blocked_by.remove(task_id)
                    # If other_task is now completely unblocked
                    if not other_task.blocked_by:
                        unblocked_tasks.append(other_task.id)
            task.blocks = []  # A completed task no longer blocks any others

        # Save all tasks
        self.storage.save_tasks([t.model_dump() for t in tasks])

        return TaskUpdateResult(
            task=task,
            message=f"Updated task {task_id}",
            unblocked_tasks=unblocked_tasks,
        )

    def get_task(self, task_id: str) -> TaskGetResult:
        """Get a specific task.

        Args:
            task_id: Task ID to retrieve

        Returns:
            TaskGetResult with task details

        """
        tasks_data = self.storage.load_tasks()
        tasks = [Task(**task_dict) for task_dict in tasks_data]

        task = next((t for t in tasks if t.id == task_id), None)

        if task:
            return TaskGetResult(task=task, found=True, message=f"Found task {task_id}")
        else:
            available = [t.id for t in tasks]
            available_str = (
                f" Available: {', '.join(available[:5])}" if available else ""
            )
            return TaskGetResult(
                task=None,
                found=False,
                message=f"Task {task_id} not found.{available_str}",
            )

    def search_tasks(
        self, query: str, filter: Optional[str] = None
    ) -> TaskSearchResult:
        """Search tasks by keyword.

        Args:
            query: Search query
            filter: Optional status filter

        Returns:
            TaskSearchResult with matching tasks

        """
        tasks_data = self.storage.load_tasks()
        tasks = [Task(**task_dict) for task_dict in tasks_data]

        # Apply status filter if provided
        if filter:
            tasks = [t for t in tasks if t.status == filter]

        # Search in subject and description
        query_lower = query.lower()
        matching_tasks = [
            t
            for t in tasks
            if query_lower in t.subject.lower() or query_lower in t.description.lower()
        ]

        return TaskSearchResult(
            tasks=matching_tasks, total=len(matching_tasks), query=query
        )

    def clear_tasks(self, filter: str = "completed") -> TaskClearResult:
        """Clear tasks by filter.

        Args:
            filter: "completed" to clear only completed, "all" to clear everything

        Returns:
            TaskClearResult with count of cleared tasks

        """
        tasks_data = self.storage.load_tasks()
        tasks = [Task(**task_dict) for task_dict in tasks_data]

        if filter == "all":
            cleared_count = len(tasks)
            self.storage.save_tasks([])
            return TaskClearResult(
                cleared_count=cleared_count,
                message=f"Cleared all {cleared_count} tasks",
            )

        # Clear only tasks matching filter
        remaining_tasks = [t for t in tasks if t.status != filter]
        cleared_count = len(tasks) - len(remaining_tasks)

        self.storage.save_tasks([t.model_dump() for t in remaining_tasks])

        return TaskClearResult(
            cleared_count=cleared_count,
            message=f"Cleared {cleared_count} {filter} tasks",
        )
