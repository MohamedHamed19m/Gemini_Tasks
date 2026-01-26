#!/usr/bin/env python3
"""
Ralph Loop Agent Hook
Handles task verification and state management for automated agents.
"""
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Configuration
RALPH_MODE = os.environ.get("GEMINI_RALPH_MODE") == "true"
MAX_ITERATIONS = int(os.environ.get("GEMINI_MAX_ITERATIONS", "25"))
COMPLETION_PROMISE = os.environ.get("GEMINI_COMPLETION_PROMISE", "complete")
TASK_LIST_ID = os.environ.get("GEMINI_TASK_LIST_ID", "default")

# Paths
home_dir = Path.home()
state_dir = home_dir / ".gemini" / "ralph-state"
state_file = state_dir / f"{TASK_LIST_ID}.json"
tasks_dir = home_dir / ".gemini" / "tasks"

def load_state():
    """Loads the current iteration state from the local JSON file."""
    if not state_file.exists():
        return {"iteration": 0, "startTime": int(datetime.now().timestamp() * 1000)}
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"iteration": 0, "startTime": int(datetime.now().timestamp() * 1000)}

def save_state(state):
    """Saves the current iteration state to the local JSON file."""
    state_dir.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def clear_state():
    """Removes the state file to reset the loop."""
    if state_file.exists():
        state_file.unlink()

def load_tasks():
    """Loads tasks from the designated tasks directory."""
    tasks_file = tasks_dir / f"{TASK_LIST_ID}.json"
    if not tasks_file.exists():
        return []
    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def check_tasks_complete():
    """Checks if all tasks in the list have a 'completed' status."""
    tasks = load_tasks()
    if not tasks:
        return True, "No tasks exist", []
    
    incomplete = [t for t in tasks if t.get("status") != "completed"]
    
    if not incomplete:
        return True, "All tasks completed", []
    
    return False, f"{len(incomplete)} tasks still incomplete", incomplete

def run_verification():
    """
    Locates and executes verification scripts. 
    Returns (success_boolean, reason_string, output_data).
    """
    project_dir = os.environ.get("GEMINI_PROJECT_DIR", os.getcwd())
    
    verify_ps1 = Path(project_dir) / ".gemini" / "verify.ps1"
    verify_ps1_alt = Path(project_dir) / "scripts" / "verify.ps1"
    verify_sh = Path(project_dir) / ".gemini" / "verify.sh"
    verify_sh_alt = Path(project_dir) / "scripts" / "verify.sh"
    verify_js = Path(project_dir) / ".gemini" / "verify.js"
    
    verify_script = None
    command = None
    
    if verify_ps1.exists():
        verify_script = verify_ps1
        command = f'powershell -ExecutionPolicy Bypass -File "{verify_ps1}"'
    elif verify_ps1_alt.exists():
        verify_script = verify_ps1_alt
        command = f'powershell -ExecutionPolicy Bypass -File "{verify_ps1_alt}"'
    elif verify_sh.exists():
        verify_script = verify_sh
        command = f'bash "{verify_sh}"' if os.name == "nt" else f'sh "{verify_sh}"'
    elif verify_sh_alt.exists():
        verify_script = verify_sh_alt
        command = f'bash "{verify_sh_alt}"' if os.name == "nt" else f'sh "{verify_sh_alt}"'
    elif verify_js.exists():
        verify_script = verify_js
        command = f'node "{verify_js}"'
        
    if not verify_script:
        return True, "No verification script found (skipped)", ""
    
    try:
        # Use shell=True for command strings on Windows
        result = subprocess.run(
            str(command),
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return True, "Verification passed", result.stdout
    except subprocess.CalledProcessError as e:
        return False, "Verification failed", e.stderr or e.stdout or str(e)

def main():
    """Main execution logic for the Ralph hook."""
    try:
        input_raw = sys.stdin.read()
        if not input_raw:
            print(json.dumps({}))
            return
            
        input_data = json.loads(input_raw)
        
        if not RALPH_MODE:
            print(json.dumps({}))
            return
            
        prompt_response = input_data.get("prompt_response", "")
        
        state = load_state()
        state["iteration"] += 1
        save_state(state)
        
        sys.stderr.write(f"Ralph iteration {state['iteration']}/{MAX_ITERATIONS}\n")
        
        if state["iteration"] >= MAX_ITERATIONS:
            sys.stderr.write("Max iterations reached, forcing stop\n")
            clear_state()
            print(json.dumps({
                "systemMessage": f"⚠️  Max iterations ({MAX_ITERATIONS}) reached. Stopping Ralph loop.",
                "decision": "allow"
            }))
            return
            
        has_completion_promise = COMPLETION_PROMISE.lower() in prompt_response.lower()
        
        if not has_completion_promise:
            sys.stderr.write("No completion promise found, continuing loop\n")
            print(json.dumps({
                "decision": "deny",
                "reason": f"You must continue working until you output \"{COMPLETION_PROMISE}\". Check tasks and verification.",
                "systemMessage": "🔄 Ralph loop continuing..."
            }))
            return
            
        sys.stderr.write("Completion promise found, verifying...\n")
        
        tasks_ok, tasks_reason, incomplete_tasks = check_tasks_complete()
        if not tasks_ok:
            sys.stderr.write(f"Tasks incomplete: {tasks_reason}\n")
            incomplete_str = "\n".join([f"- {t.get('id')}: {t.get('subject')} ({t.get('status')})" for t in incomplete_tasks])
            print(json.dumps({
                "decision": "deny",
                "reason": f"Work incomplete: {tasks_reason}\n\nIncomplete tasks:\n{incomplete_str}\n\nComplete these tasks before outputting \"{COMPLETION_PROMISE}\".",
                "systemMessage": "❌ Tasks incomplete, continuing work..."
            }))
            return
            
        verify_ok, verify_reason, verify_output = run_verification()
        if not verify_ok:
            sys.stderr.write(f"Verification failed: {verify_reason}\n")
            print(json.dumps({
                "decision": "deny",
                "reason": f"Verification failed: {verify_reason}\n\nOutput:\n{verify_output}\n\nFix the issues and run verification again.",
                "systemMessage": "❌ Verification failed, fixing issues..."
            }))
            return
            
        sys.stderr.write("All verification passed, allowing stop\n")
        clear_state()
        
        tasks = load_tasks()
        completed_count = len([t for t in tasks if t.get("status") == "completed"])
        
        print(json.dumps({
            "decision": "allow",
            "systemMessage": f"✅ Ralph loop complete! {completed_count} tasks completed in {state['iteration']} iterations. 🎉"
        }))
        
    except Exception as e:
        sys.stderr.write(f"AfterAgent hook error: {str(e)}\n")
        print(json.dumps({
            "systemMessage": f"⚠️  Hook error: {str(e)}"
        }))

if __name__ == "__main__":
    main()