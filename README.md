# Gemini Tasks Extension

Task management for Gemini CLI with AI-driven MCP tools.

## Features

✓ AI can autonomously create and manage tasks
✓ Task dependencies and blockers
✓ Multi-session coordination via GEMINI_TASK_LIST_ID
✓ Persistent storage in ~/.gemini/tasks/
✓ Status lifecycle: pending → in_progress → completed
✓ Ralph Wiggum autonomous loop support
✓ Verification-first workflow

## MCP Tools

- `tasks_list` - List tasks with optional filter
- `tasks_create` - Create new task with dependencies
- `tasks_update` - Update status and blockers
- `tasks_get` - Get task details
- `tasks_search` - Search tasks by keyword
- `tasks_clear` - Clear completed/all tasks

## Installation

See main documentation for detailed installation steps.

Quick install:
```bash
cd server
uv venv
uv pip install -r requirements.txt
cd ..
gemini extensions link ~/.gemini/extensions/gemini-tasks
```

## Usage

Simply tell Gemini what you want to build, and it will:
1. Break work into tasks with dependencies
2. Work through tasks in order
3. Verify each step before marking complete
4. Coordinate across sessions if using shared task list

## Examples

```
"Build user authentication - break into tasks"
"Show me all pending tasks"
"Work through the tasks autonomously"
"Start working on the API task"
```

## Configuration

You can use the provided `.\scripts\setup-windows.ps1` script to automate setup, or configure your environment manually using the variables below.

### Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `GEMINI_RALPH_MODE` | Set to `true` to enable autonomous Ralph loops. | `false` |
| `GEMINI_TASK_LIST_ID` | The ID of the task list to use (for multi-session work). | `default` |
| `GEMINI_MAX_ITERATIONS` | Safety limit for autonomous loops before forcing a stop. | `25` |
| `GEMINI_COMPLETION_PROMISE` | The keyword the AI must output to signal work is done. | `complete` |

### Manual Windows Setup (CMD)

To set these for your current session:
```cmd
set GEMINI_RALPH_MODE=true
set GEMINI_TASK_LIST_ID=my-project-name
```

To set them permanently for your user account:
```cmd
setx GEMINI_RALPH_MODE true
setx GEMINI_MAX_ITERATIONS 25
```

## Storage

- **Tasks:** `%USERPROFILE%\.gemini\tasks\<task-list-id>.json`
- **Loop State:** `%USERPROFILE%\.gemini\ralph-state\<task-list-id>.json`
