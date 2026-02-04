# Gemini Tasks - Task Management Extension

Task management extension for Gemini CLI, inspired by Claude Code's native task management.

## Features

- AI autonomously creates and manages tasks
- Task dependencies and blockers
- Multi-session coordination
- Persistent storage across sessions
- Status lifecycle: `pending -> in_progress -> completed`

## Installation

```bash
gemini extensions install https://github.com/MohamedHamed19m/Gemini_Tasks
```

## Quick Start

### Basic Usage

**In Gemini CLI:**
```
> "Break this feature into tasks: Implement user authentication with JWT"
```

The AI will:
1. Create tasks with dependencies
2. Work through each task systematically
3. Update task status as it progresses
4. Mark tasks complete when finished

### Multi-Session Coordination

**Session A:**
```powershell
$env:GEMINI_TASK_LIST_ID = "auth-feature"
gemini
> "Work on backend tasks"
```

**Session B:**
```powershell
$env:GEMINI_TASK_LIST_ID = "auth-feature"  # Same ID!
gemini
> "Work on frontend tasks"
```

Both sessions share the same task list and coordinate automatically.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_TASK_LIST_ID` | Task list identifier for multi-session | `default` |

## Commands

### `/tasks-clear`

Clear completed tasks or all tasks.

**Usage:**
```
/tasks-clear        # Clears only completed tasks (default, safe)
/tasks-clear all    # Clears ALL tasks (destructive)
```

## MCP Tools

The extension provides these MCP tools for AI to use:

### `tasks_list`

List all tasks with optional status filter.

**Parameters:**
- `filter` (optional): `"all"`, `"pending"`, `"in_progress"`, `"completed"`

### `tasks_create`

Create a new task with dependencies.

**Parameters:**
- `subject` (required): Task title
- `description` (optional): Detailed description
- `blocked_by` (optional): List of task IDs this task depends on

### `tasks_update`

Update task status and blockers.

**Parameters:**
- `task_id` (required): Task ID to update
- `status` (optional): `"pending"`, `"in_progress"`, `"completed"`
- `add_blocked_by` (optional): Add task IDs as blockers
- `remove_blocked_by` (optional): Remove blocker task IDs

### `tasks_get`

Get full details of a specific task.

**Parameters:**
- `task_id` (required): Task ID to retrieve

### `tasks_search`

Search tasks by keyword.

**Parameters:**
- `query` (required): Search keywords

### `tasks_clear`

Clear completed or all tasks.

**Parameters:**
- `filter` (optional): `"completed"` (default) or `"all"`

## Usage Examples

### Example 1: Basic Task Creation

```
> "Create three tasks: Setup, Development, Testing.
   Make Development blocked by Setup, and Testing blocked by Development."
```

**Result:**
```
task-1: Setup (pending)
task-2: Development (pending, blocked by task-1)
task-3: Testing (pending, blocked by task-2)
```

### Example 2: Multi-Session Work

**Terminal 1 - Backend:**
```powershell
$env:GEMINI_TASK_LIST_ID = "user-profile"
gemini
> "Work on backend API tasks for user profile"
```

**Terminal 2 - Frontend:**
```powershell
$env:GEMINI_TASK_LIST_ID = "user-profile"
gemini
> "Work on frontend UI tasks for user profile"
```

Both sessions coordinate on shared task list!

## Storage Locations

- **Windows:** Tasks: `%USERPROFILE%\.gemini\tasks\<task-list-id>.json`
- **Linux/Mac:** Tasks: `~/.gemini/tasks/<task-list-id>.json`

## Troubleshooting

### Tasks Not Persisting

**Check tasks directory:**
```powershell
Get-ChildItem "$env:USERPROFILE\.gemini\tasks\"
```

**Check file contents:**
```powershell
cat "$env:USERPROFILE\.gemini\tasks\default.json"
```

### MCP Server Not Responding

**Check extension installed:**
```
gemini extensions list
```

Should show:
```
gemini-tasks v1.0.0
```

**Check MCP server:**
1. Look for "gemini-tasks" in MCP list
2. Check logs in Gemini CLI
3. Verify Python environment: `uv` must be installed
4. Test manually: `cd server && uv run main.py`

## Credits

Inspired by Claude Code's native task management.
