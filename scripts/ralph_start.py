#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
from datetime import datetime

def main():
    if len(sys.argv) < 2:
        print("Usage: ralph_start.py <objective> [max_iterations] [completion_promise]")
        sys.exit(1)

    objective = sys.argv[1]
    max_iterations = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    completion_promise = sys.argv[3] if len(sys.argv) > 3 else "complete"
    task_list_id = os.environ.get("GEMINI_TASK_LIST_ID", "default")

    state_dir = Path.home() / ".gemini" / "ralph-state"
    state_file = state_dir / f"{task_list_id}.json"
    state_dir.mkdir(parents=True, exist_ok=True)

    state = {
        "iteration": 0,
        "startTime": int(datetime.now().timestamp() * 1000),
        "original_prompt": objective,
        "max_iterations": max_iterations,
        "completion_promise": completion_promise
    }

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print(f"🔄 Ralph loop initialized for Objective: {objective}")
    print(f"Max iterations: {max_iterations}")
    print(f"Completion promise: <promise>{completion_promise}</promise>")
    print("
Starting work now...")

if __name__ == "__main__":
    main()
