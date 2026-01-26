#!/usr/bin/env python3
import os
from pathlib import Path

def main():
    task_list_id = os.environ.get("GEMINI_TASK_LIST_ID", "default")
    state_file = Path.home() / ".gemini" / "ralph-state" / f"{task_list_id}.json"

    if state_file.exists():
        state_file.unlink()
        print(f"🛑 Ralph loop cancelled for list: {task_list_id}")
    else:
        print(f"No active Ralph loop found for list: {task_list_id}")

if __name__ == "__main__":
    main()
