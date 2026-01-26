"""File-based storage for tasks."""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional


class TaskStorage:
    """Handles task persistence to file system."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize storage with tasks directory.

        Args:
            base_dir: Optional base directory for tasks. Defaults to ~/.gemini
        """
        # Get task list ID from environment or use default
        self.task_list_id = os.environ.get("GEMINI_TASK_LIST_ID", "default")

        # Tasks stored in {base_dir}/tasks/
        if base_dir:
            self.base_dir = base_dir
        else:
            self.base_dir = Path.home() / ".gemini"

        self.tasks_dir = self.base_dir / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

        self.tasks_file = self.tasks_dir / f"{self.task_list_id}.json"

    def load_tasks(self) -> List[Dict[str, Any]]:
        """Load tasks from file.

        Returns:
            List of task dictionaries

        """
        if not self.tasks_file.exists():
            return []

        try:
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading tasks: {e}")
            return []

    def save_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """Save tasks to file.

        Args:
            tasks: List of task dictionaries

        """
        try:
            with open(self.tasks_file, "w", encoding="utf-8") as f:
                json.dump(tasks, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"Error saving tasks: {e}")

    def get_task_list_id(self) -> str:
        """Get current task list ID.

        Returns:
            Task list ID string

        """
        return self.task_list_id
