#!/usr/bin/env python3
"""
Ralph Loop Agent Hook
Handles task verification and state management for automated agents.
"""

import json
import os
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime

# Configuration
RALPH_MODE = os.environ.get("GEMINI_RALPH_MODE") == "true"
MAX_ITERATIONS = int(os.environ.get("GEMINI_MAX_ITERATIONS", "10"))
COMPLETION_PROMISE = os.environ.get("GEMINI_COMPLETION_PROMISE", "complete")
TASK_LIST_ID = os.environ.get("GEMINI_TASK_LIST_ID", "default")

# Paths
home_dir = Path.home()
state_dir = home_dir / ".gemini" / "ralph-state"
state_file = state_dir / f"{TASK_LIST_ID}.json"
tasks_dir = home_dir / ".gemini" / "tasks"


def extract_promise(text):
    """Extracts content from <promise> tags."""
    match = re.search(r"<promise>(.*?)</promise>", text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def load_state():
    """Loads the current iteration state from the local JSON file."""
    if not state_file.exists():
        return {
            "iteration": 0,
            "startTime": int(datetime.now().timestamp() * 1000),
            "original_prompt": "",
        }
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
            if "original_prompt" not in state:
                state["original_prompt"] = ""
            return state
    except:
        return {
            "iteration": 0,
            "startTime": int(datetime.now().timestamp() * 1000),
            "original_prompt": "",
        }


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
    verify_py = Path(project_dir) / ".gemini" / "verify.py"
    verify_py_alt = Path(project_dir) / "scripts" / "verify.py"

    verify_script = None
    command = None

    if verify_ps1.exists():
        verify_script = verify_ps1
        command = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(verify_ps1)]
    elif verify_ps1_alt.exists():
        verify_script = verify_ps1_alt
        command = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(verify_ps1_alt),
        ]
    elif verify_sh.exists():
        verify_script = verify_sh
        command = (
            ["bash", str(verify_sh)] if os.name == "nt" else ["sh", str(verify_sh)]
        )
    elif verify_sh_alt.exists():
        verify_script = verify_sh_alt
        command = (
            ["bash", str(verify_sh_alt)]
            if os.name == "nt"
            else ["sh", str(verify_sh_alt)]
        )
    elif verify_js.exists():
        verify_script = verify_js
        command = ["node", str(verify_js)]
    elif verify_py.exists():
        verify_script = verify_py
        command = ["python", str(verify_py)]
    elif verify_py_alt.exists():
        verify_script = verify_py_alt
        command = ["python", str(verify_py_alt)]

    if not verify_script:
        return True, "No verification script found", ""

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return True, "Verification passed", result.stdout
    except subprocess.CalledProcessError as e:
        return False, "Verification failed", e.stderr or e.stdout or str(e)


def log_iteration(state, status, reason):
    """Logs the details of a single iteration to the project directory."""
    project_dir = os.environ.get("GEMINI_PROJECT_DIR", os.getcwd())
    log_file = Path(project_dir) / ".gemini" / "ralph-iterations.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] Iteration {state['iteration']}\n")
        f.write(f"Status: {status}\n")
        # Strip internal newlines for the log summary
        reason_summary = reason.replace("\n", " ")
        f.write(f"Reason: {reason_summary[:200]}...\n")
        f.write("-" * 40 + "\n")


def deny_with_context(reason, iteration, sys_msg, state, max_val):
    """Returns a deny decision with optional context clearing and prompt re-injection."""
    log_iteration(state, "CONTINUING", sys_msg)
    original_prompt = state.get("original_prompt", "")

    # If we have an original prompt, we re-inject it to ensure the agent stays on track
    # when clearContext is true.
    if original_prompt:
        feedback = f"OBJECTIVE: {original_prompt}\n\n{reason}"
    else:
        feedback = reason

    return json.dumps(
        {
            "decision": "deny",
            "reason": feedback,
            "systemMessage": f"🔄 Iteration {iteration}/{max_val}: {sys_msg}",
            "hookSpecificOutput": {"hookEventName": "AfterAgent", "clearContext": True},
        }
    )


def main():
    """Main execution logic for the Ralph hook."""
    state = {"iteration": 0}  # Default for error logging
    try:
        input_raw = sys.stdin.read()
        if not input_raw:
            print(json.dumps({}))
            return

        input_data = json.loads(input_raw)

        # Check if we are in Ralph Mode (via Env Var OR existing state file)
        state_exists = state_file.exists()
        if not RALPH_MODE and not state_exists:
            # We don't log "not enabled" to stderr every time to keep things quiet
            print(json.dumps({}))
            return

        prompt_response = input_data.get("prompt_response", "")

        # Load state (will return defaults if file doesn't exist)
        state = load_state()

        # Override global config with state-specific values if they exist
        current_max = state.get("max_iterations", MAX_ITERATIONS)
        current_promise = state.get("completion_promise", COMPLETION_PROMISE)

        # If RALPH_MODE is false but state file exists, we continue.
        # If state file doesn't exist but RALPH_MODE is true, we initialize on the fly.
        state["iteration"] += 1
        iteration = state["iteration"]
        save_state(state)

        sys.stderr.write(f"Ralph iteration {iteration}/{current_max}\n")

        # Check max iterations
        if iteration >= current_max:
            sys.stderr.write("Max iterations reached, forcing stop\n")
            log_iteration(state, "STOPPED", f"Max iterations ({current_max}) reached")
            clear_state()
            print(
                json.dumps(
                    {
                        "systemMessage": f"⚠️  Max iterations ({current_max}) reached. Stopping Ralph loop.",
                        "decision": "allow",
                    }
                )
            )
            return

        # Check for completion promise using XML tags
        promise_content = extract_promise(prompt_response)
        has_completion_promise = (
            promise_content and promise_content.lower() == current_promise.lower()
        )

        if not has_completion_promise:
            # Provide helpful feedback if tags are missing or content is wrong
            if (
                current_promise.lower() in prompt_response.lower()
                and not promise_content
            ):
                reason = f'You mentioned "{current_promise}" but did not wrap it in <promise> tags. You MUST output <promise>{current_promise}</promise> to signal completion.'
            else:
                reason = f"You must continue working until you output <promise>{current_promise}</promise>. Check tasks and verification."

            sys.stderr.write("No valid completion promise found, continuing loop\n")
            print(
                deny_with_context(
                    reason, iteration, "Missing <promise> tags", state, current_max
                )
            )
            return

        sys.stderr.write(
            "Valid completion promise found, verifying tasks and scripts...\n"
        )

        # Check tasks
        tasks_ok, tasks_reason, incomplete_tasks = check_tasks_complete()
        if not tasks_ok:
            sys.stderr.write(f"Tasks incomplete: {tasks_reason}\n")
            incomplete_count = len(incomplete_tasks)
            incomplete_str = "\n".join(
                [
                    f"- {t.get('id')}: {t.get('subject')} ({t.get('status')})"
                    for t in incomplete_tasks
                ]
            )

            reason = f"Work incomplete: {tasks_reason}\n\nIncomplete tasks:\n{incomplete_str}\n\nComplete these tasks before outputting <promise>{current_promise}</promise>."
            print(
                deny_with_context(
                    reason,
                    iteration,
                    f"{incomplete_count} tasks incomplete",
                    state,
                    current_max,
                )
            )
            return

        # Run verification
        verify_ok, verify_reason, verify_output = run_verification()
        if not verify_ok:
            sys.stderr.write(f"Verification failed: {verify_reason}\n")
            reason = f"Verification failed: {verify_reason}\n\nOutput:\n{verify_output}\n\nFix the issues and run verification again."
            print(
                deny_with_context(
                    reason, iteration, "Tests failing", state, current_max
                )
            )
            return

        # All checks passed!
        sys.stderr.write("All verification passed, allowing stop\n")
        log_iteration(state, "COMPLETED", "All checks passed")
        clear_state()

        tasks = load_tasks()
        completed_count = len([t for t in tasks if t.get("status") == "completed"])

        print(
            json.dumps(
                {
                    "decision": "allow",
                    "systemMessage": f"✅ Ralph loop complete! {completed_count} tasks completed in {iteration} iterations. 🎉",
                }
            )
        )

    except Exception as e:
        # Log to file for debugging
        error_log = Path.home() / ".gemini" / "hook-errors.log"
        try:
            error_log.parent.mkdir(parents=True, exist_ok=True)
            with open(error_log, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] AfterAgent: {str(e)}\n")
        except:
            pass

        sys.stderr.write(f"AfterAgent hook error: {str(e)}\n")
        print(
            json.dumps(
                {
                    "decision": "deny",
                    "reason": f"Hook error (logged): {str(e)}",
                    "systemMessage": f"⚠️ Hook error: {str(e)[:50]}...",
                }
            )
        )


if __name__ == "__main__":
    main()
