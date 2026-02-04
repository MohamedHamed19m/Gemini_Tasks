#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


def main():
    # Parse filter argument (default: "completed", option: "all")
    filter_arg = sys.argv[1] if len(sys.argv) > 1 else "completed"

    if filter_arg not in ("completed", "all"):
        print(f"Error: Invalid filter '{filter_arg}'. Use 'completed' or 'all'")
        sys.exit(1)

    task_list_id = os.environ.get("GEMINI_TASK_LIST_ID", "default")

    # Task storage location
    tasks_file = Path.home() / ".gemini" / "tasks" / f"{task_list_id}.json"

    # Load and filter tasks
    if tasks_file.exists():
        with open(tasks_file, "r", encoding="utf-8") as f:
            tasks = json.load(f)

        original_count = len(tasks)

        # Filter tasks based on argument
        if filter_arg == "all":
            remaining_tasks = []
        else:  # completed
            remaining_tasks = [t for t in tasks if t.get("status") != "completed"]

        cleared_count = original_count - len(remaining_tasks)

        # Save remaining tasks
        if remaining_tasks:
            tasks_file.parent.mkdir(parents=True, exist_ok=True)
            with open(tasks_file, "w", encoding="utf-8") as f:
                json.dump(remaining_tasks, f, indent=2)
        else:
            # Remove file if no tasks remaining
            tasks_file.unlink()

        print(f"Cleared {cleared_count} task(s) (filter: {filter_arg})")
    else:
        print(f"No tasks found for list: {task_list_id}")


if __name__ == "__main__":
    main()
