#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

def main():
    try:
        # Read input from stdin
        try:
            line = sys.stdin.read()
            if not line:
                print(json.dumps({}))
                return
            input_data = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({}))
            return

        # Get task list ID
        task_list_id = os.environ.get("GEMINI_TASK_LIST_ID", "default")
        
        # Windows-compatible path
        tasks_dir = Path.home() / ".gemini" / "tasks"
        tasks_file = tasks_dir / f"{task_list_id}.json"
        
        if not tasks_file.exists():
            print(json.dumps({}))
            return
        
        with open(tasks_file, "r", encoding="utf-8") as f:
            tasks = json.load(f)
            
        pending = [t for t in tasks if t.get("status") in ["pending", "in_progress"]]
        
        if not pending:
            print(json.dumps({}))
            return
            
        # Build task display with proper newlines
        task_display = "\n📋 Active Tasks:\n"
        for task in pending[:10]:
            icon = "⟳" if task.get("status") == "in_progress" else "○"
            blockers_list = task.get("blocked_by", [])
            blockers = f" [blocked by: {', '.join(blockers_list)}]" if blockers_list else ""
            task_display += f"  {icon} {task.get('id')}: {task.get('subject')}{blockers}\n"
            
        if len(pending) > 10:
            task_display += f"  ... and {len(pending) - 10} more\n"
            
        # Inject as additional context
        print(json.dumps({
            "systemMessage": task_display,
            "hookSpecificOutput": {
                "hookEventName": "BeforeAgent",
                "additionalContext": task_display
            }
        }))
        
    except Exception as e:
        sys.stderr.write(f"BeforeAgent hook error: {str(e)}\n")
        print(json.dumps({}))

if __name__ == "__main__":
    main()