# Gemini Tasks - Ralph Wiggum Autonomous Loops

Task management extension for Gemini CLI with autonomous coding loops, inspired by Claude Code's native task management.

## 🌟 Features

### 🤖 **Ralph Wiggum Autonomous Loops**
- Autonomous coding that works while you sleep
- Automatic verification before task completion
- Test-driven development support
- Safety brake with max iterations
- Completion promise verification

### ✨ **Advanced Task Management**
- AI autonomously creates and manages tasks
- Task dependencies and blockers
- Multi-session coordination
- Persistent storage across sessions
- Status lifecycle: `pending → in_progress → completed`

## 🚀 Quick Start

### Installation

```bash
gemini extensions install https://github.com/MohamedHamed19m/Gemini_Tasks
```

### Enable Ralph Mode

**Option 1: Command-based (Recommended)**
Simply start Gemini and use the custom command. No environment variables required!
```bash
/ralph-start "Build user authentication with TDD"
```

**Option 2: Global environment mode**
Force Ralph mode for every session without needing the command.
```bash
export GEMINI_RALPH_MODE="true"
export GEMINI_MAX_ITERATIONS="50"
gemini
```

### Basic Usage

**In Gemini CLI:**
```
> /ralph-start "Build user authentication with TDD"
```

The AI will:
1. ✅ Break work into dependent tasks
2. ✅ Work through each task systematically (clearing context each turn to save tokens)
3. ✅ Run verification before marking complete
4. ✅ Only stop when it outputs `<promise>complete</promise>`

## 🚀 Commands

### `/ralph-start`
Initialize a Ralph loop session with a specific objective. This command automatically captures the goal to ensure the agent stays on track even when memory is reset.

**Usage:**
```
/ralph-start "Your objective here"
```

### `/ralph-cancel`
Cancels the active Ralph loop state for the current session.

## 📚 How It Works

### The Ralph Wiggum Loop

```
User gives instruction
    ↓
AI creates tasks with dependencies
    ↓
AI works on first unblocked task
    ↓
AI tries to finish → AfterAgent Hook intercepts
    ↓
Hook checks:
  - Did AI say "complete"? ❌ → Force retry
  - All tasks done? ❌ → Force retry  
  - Tests pass? ❌ → Force retry
  ✅ All verified → Allow stop
```

### The Validation

The hook script strictly enforces completion by checking three critical conditions:
*   **Completion Promise**: Did the agent explicitly output the "completion promise" wrapped in XML tags (e.g., `<promise>complete</promise>`)?
*   **Task Integrity**: Are all tasks in the database marked with the `completed` status?
*   **Project Verification**: Does the project's verification script (`verify.ps1`, `verify.py`, etc.) exit with code 0?

### Task Dependencies

```
Task 1: Write tests
   ↓
Task 2: Implement feature (blocked by Task 1)
   ↓
Task 3: Integration tests (blocked by Task 2)
```

AI automatically respects these dependencies and can't skip ahead.

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

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_RALPH_MODE` | Enable autonomous Ralph loops | `false` |
| `GEMINI_MAX_ITERATIONS` | Max loop iterations (safety brake) | `10` |
| `GEMINI_TASK_LIST_ID` | Task list identifier for multi-session | `default` |
| `GEMINI_COMPLETION_PROMISE` | Keyword AI must output to signal done | `complete` |

### Project Verification Scripts

Create custom verification in your project:
it can contains tests or other scripts, its important that it return (exit 0) if success if not then it would enter the loop.

.gemini/verify.ps1
.gemini/verify.py

```powershell
#!/usr/bin/env pwsh
# Run tests
npm test

exit 0
```

```py
if __name__ == "__main__":
    if run_tests():
        sys.exit(0)
    else:
        sys.exit(1)
```

## 📖 MCP Tools

The extension provides these MCP tools for AI to use:

### `tasks_list`
List all tasks with optional status filter.

**Parameters:**
- `filter` (optional): `"all"`, `"pending"`, `"in_progress"`, `"completed"`

**Example:**
```
AI: tasks_list(filter="pending")
```

### `tasks_create`
Create a new task with dependencies.

**Parameters:**
- `subject` (required): Task title
- `description` (optional): Detailed description
- `blocked_by` (optional): List of task IDs this task depends on

**Example:**
```
AI: tasks_create(
    subject="Implement auth API",
    description="JWT tokens, bcrypt passwords",
    blocked_by=["task-1"]
)
```

### `tasks_update`
Update task status and blockers.

**Parameters:**
- `task_id` (required): Task ID to update
- `status` (optional): `"pending"`, `"in_progress"`, `"completed"`
- `add_blocked_by` (optional): Add task IDs as blockers
- `remove_blocked_by` (optional): Remove blocker task IDs

**Example:**
```
AI: tasks_update(task_id="task-1", status="completed")
```

### `tasks_get`
Get full details of a specific task.

**Parameters:**
- `task_id` (required): Task ID to retrieve

### `tasks_search`
Search tasks by keyword.

**Parameters:**
- `query` (required): Search keywords
- `filter` (optional): Status filter

### `tasks_clear`
Clear completed or all tasks.

**Parameters:**
- `filter` (optional): `"completed"` (default) or `"all"`

## 💡 Usage Examples

### Example 1: Basic Task Creation

```
> "Create three tasks: Setup, Development, Testing. 
   Make Development blocked by Setup, and Testing blocked by Development."
```

**Result:**
```
✓ task-1: Setup (pending)
✓ task-2: Development (pending, blocked by task-1)
✓ task-3: Testing (pending, blocked by task-2)
```

### Example 2: Test-Driven Development (TDD)

```bash
/ralph-start "Implement a User authentication module in Python. Requirements: 1. Signup/Login functions, 2. JWT token generation, 3. Password hashing with bcrypt. Follow TDD: write tests first, then implement until they pass."
```

**AI will:**
1. Create tasks with proper dependencies (e.g., `Write tests`, `Implement auth`).
2. Write tests (they fail initially).
3. Implement code iteratively until tests pass.
4. Clear its own context memory between turns to stay fast and token-efficient.
5. Output `<promise>complete</promise>` only when all verification passes.

### Example 3: Complex Refactoring

```bash
/ralph-start "Refactor the existing 'server/storage.py' to use an async database driver. Update all call sites. Only finish when the code is lint-free and verified." 20
```
*(Note: the `20` at the end sets a custom limit of 20 iterations for this complex task.)*

**AI will:**
1. Analyze the codebase.
2. Perform refactoring in atomic steps.
3. Use the re-injected **OBJECTIVE** to stay on track even after context resets.
4. Verify results after each major change.

### Example 4: Overnight Autonomous Work

**Before bed:**
```powershell
$env:GEMINI_MAX_ITERATIONS = "50"
/ralph-start "Integrate Stripe payments: SDK, endpoints, webhooks, and UI." 50
```

**Next morning:**
```
✅ Ralph loop complete! 8 tasks completed in 23 iterations. 🎉

- All tests passing
- Code reviewed and clean
- Ready to deploy
```

### Example 5: Multi-Session Parallel Work

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

## 🎯 Advanced Features

### Verification-First Workflow

The Ralph loop **enforces verification**:

```
AI marks task complete
    ↓
Hook runs .gemini/verify.ps1
    ↓
Tests fail? → Force AI to fix
Tests pass? → Allow completion
```

**AI cannot mark tasks complete without verification passing!**

### Safety Features

**Max Iterations:**
```powershell
$env:GEMINI_MAX_ITERATIONS = "10"
```
After 10 iterations, loop stops automatically (prevents runaway loops).

**Completion Promise:**
```powershell
$env:GEMINI_COMPLETION_PROMISE = "complete"
```
AI must explicitly output "complete" to signal done.

**State Persistence:**
Tasks and loop state survive:
- Context resets
- Session restarts
- System reboots

### Task Discovery

AI can add tasks mid-flight:

```
Initial: 3 tasks created

During work: AI discovers edge case
AI creates: task-4 "Handle edge case"

Final: 4 tasks completed
```

## 📂 Storage Locations

- Tasks: `%USERPROFILE%\.gemini\tasks\<task-list-id>.json`
- Ralph state: `%USERPROFILE%\.gemini\ralph-state\<task-list-id>.json`

- Tasks: `~/.gemini/tasks/<task-list-id>.json`
- Ralph state: `~/.gemini/ralph-state/<task-list-id>.json`

## 🔧 Troubleshooting

### Ralph Loop Not Working

**Verify hooks enabled:**
```
/hooks panel
```

Should show:
```
✓ display-tasks [enabled]
✓ ralph-loop-check [enabled]
```

### Tasks Not Persisting

**Check tasks directory:**
```powershell
Get-ChildItem "$env:USERPROFILE\.gemini\tasks\"
```

**Check file contents:**
```powershell
cat "$env:USERPROFILE\.gemini\tasks\default.json"
```

### Hooks Not Firing

**Check extension installed:**
```
gemini extensions list
```

Should show:
```
✓ gemini-tasks v1.0.0
```

## 📊 Performance Tips

**For overnight work:**
```powershell
$env:GEMINI_MAX_ITERATIONS = "50"  # Higher limit
```

**For testing:**
```powershell
$env:GEMINI_MAX_ITERATIONS = "5"   # Quick safety brake
```

**For complex projects:**
```powershell
$env:GEMINI_TASK_LIST_ID = "feature-$(Get-Date -Format 'yyyyMMdd')"
# Creates daily task lists: feature-20250126
```

## 🙏 Credits

Inspired by:
- Claude Code's native task management
- Ralph Wiggum autonomous loop technique
- The agentic coding community

---
