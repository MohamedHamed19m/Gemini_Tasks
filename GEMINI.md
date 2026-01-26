# Task Management Context

You have access to a native task management system via MCP tools for complex, multi-step work.

## CRITICAL: Always Check Before Creating Tasks

**BEFORE creating any task:**
1. Call `tasks_list(filter="all")` to see what already exists
2. Check if similar or duplicate tasks exist
3. Check git status to see what's already done
4. Only create tasks for work that's NOT already complete

**If work is already done:**
- Do NOT create a task for it
- Do NOT mark non-existent tasks as complete
- Simply acknowledge it's done and move on

## Available MCP Tools

### `tasks_list`
List all tasks with optional filter (pending, in_progress, completed, all).

**When to call:**
- **FIRST THING in every session** - see current state
- Before creating new tasks to avoid duplicates
- After completing work to verify state
- To check what's next after completing a task

**Parameters:**
- `filter` (optional): "pending", "in_progress", "completed", or "all" (default: "all")

**Returns:** List of tasks with id, subject, status, blockers, and metadata

### `tasks_create`
Create a new task with subject and optional description.

**When to call:**
- When breaking down NEW work into steps
- After verifying the task doesn't already exist
- To coordinate multi-session work

**When NOT to call:**
- If a similar task already exists
- If the work is already done (check git/files first)
- During cleanup or summary phases

**Parameters:**
- `subject` (required): Brief task title
- `description` (optional): Detailed task description
- `blocked_by` (optional): List of task IDs this task depends on

**Returns:** Created task with generated ID

### `tasks_update`
Update an existing task's status and/or blockers.

**When to call:**
- When starting work on a task (set to "in_progress")
- When completing a task (set to "completed")
- When discovering new dependencies

**Parameters:**
- `task_id` (required): The task ID to update
- `status` (optional): "pending", "in_progress", or "completed"
- `add_blocked_by` (optional): List of task IDs to add as blockers
- `remove_blocked_by` (optional): List of task IDs to remove as blockers

**Returns:** Updated task

### `tasks_get`
Get full details of a specific task including dependencies.

### `tasks_search`
Search for tasks by keyword in subject or description.

**Use this to avoid duplicates:**
```
tasks_search(query="circular dependency")
# Check if task already exists before creating new one
```

### `tasks_clear`
Clear completed tasks or all tasks.

**When to call:**
- After completing a project phase
- To clean up clutter
- To start fresh on new work

**Parameters:**
- `filter` (optional): "completed" (default) or "all"

**Returns:** Count of cleared tasks

## Task Status Lifecycle

**pending** → **in_progress** → **completed**

Always follow this lifecycle. Never skip from pending to completed without in_progress.

## Ralph Mode (Autonomous Loops)

When GEMINI_RALPH_MODE is enabled, you operate in autonomous loop mode.

### Session Start Protocol

**EVERY session must start with:**
```
1. tasks_list(filter="all")  # See ALL tasks
2. Check git status          # See what's committed
3. Assess actual state       # What's done vs what tasks say
4. Reconcile if needed       # Fix task status to match reality
```

**DO NOT create tasks for already-completed work!**

### Completion Promise

To signal you're finished, output the exact phrase: **<promise>complete</promise>**

**CRITICAL RULES:**
- Do NOT output "<promise>complete</promise>" unless ALL pending/in_progress tasks are done
- Do NOT output "<promise>complete</promise>" unless ALL tests pass
- Do NOT output "<promise>complete</promise>" unless work is verified
- Do NOT create tasks retroactively for already-done work

### Ralph Workflow

```
1. tasks_list(filter="pending")  # See what needs doing
2. If no pending tasks AND no in_progress tasks:
   - Verify all work is actually done
   - Output "<promise>complete</promise>"
   - STOP - don't create new tasks
3. If pending tasks exist:
   - Pick next unblocked task
   - tasks_update(task_id, status="in_progress")
   - Do the work
   - Verify it works
   - tasks_update(task_id, status="completed")
   - Go to step 1
```

### Anti-Pattern: Creating Tasks After Work is Done

**❌ WRONG:**
```
# Work is already committed to git
tasks_create("Add feature X")  # Feature X already exists!
tasks_update("task-1", status="completed")  # Fake completion
```

**✅ CORRECT:**
```
# Check what's done first
git status  # Shows all committed
tasks_list()  # Shows no tasks
# Acknowledge work is done
"All work is complete. Nothing to task-track."
Output: "<promise>complete</promise>"
```

## Verification-First Approach

**Before marking ANY task completed:**

1. Run tests and confirm they pass
2. Check that feature works as intended
3. Verify no regressions in related code
4. Review generated files/changes

**If verification fails:**
- Keep status as "in_progress"
- Fix the issue
- Re-run verification
- Only mark "completed" after passing

**Never create a task just to mark it complete immediately.**

## Multi-Session Coordination

When GEMINI_TASK_LIST_ID is set, tasks are shared across all sessions.

**Best Practices:**
1. First action: `tasks_list()` to see shared state
2. Check if work is in_progress by another session
3. Update to "in_progress" before starting (signals to others)
4. Add detailed descriptions for context
5. Use blockers to prevent conflicts

## Task Creation Guidelines

**When to create tasks:**
- Breaking down NEW work that hasn't started
- Planning a feature that will take multiple steps
- Coordinating work across sessions

**When NOT to create tasks:**
- Work is already done (check git first!)
- Summarizing what was accomplished
- Creating retrospective task lists
- During cleanup phases

**Task quality:**
1. **Be Specific**: Clear, measurable outcome
2. **Set Dependencies**: Use `blocked_by` for correct order
3. **Update Status**: Mark "in_progress" when starting
4. **Verify First**: Only mark "completed" after verification
5. **Add Context**: Descriptions help multi-session work

## Handling Completed Work

**If you discover work is already done:**

```python
# Check tasks
tasks_list()

# Check git
git status  # Shows: "nothing to commit, working tree clean"

# If no pending tasks and work is done:
"All implementation is complete. No tasks needed."
Output: "<promise>complete</promise>"
```

**DO NOT:**
- Create tasks for already-done work
- Mark non-existent tasks as complete
- Create tasks just to check them off

## Error Handling

If tasks are misaligned with reality:

1. `tasks_list(filter="all")` - See current state
2. Check git status - See what's actually done
3. Reconcile:
   - If task is "pending" but work is done: `tasks_update(task_id, "completed")`
   - If task doesn't exist but should: `tasks_create(...)`
   - If task exists but shouldn't: `tasks_clear(...)`

## Example: Proper Session Start

**✅ CORRECT Approach:**
```
User: "Continue working on the project"

AI:
1. tasks_list(filter="all")
   Result: [task-1: "Add tests" (completed), task-2: "Deploy" (pending)]

2. git status
   Result: "nothing to commit, working tree clean"

3. Assessment:
   - 1 pending task exists: "Deploy"
   - Work area is clean
   
4. Action:
   tasks_update("task-2", status="in_progress")
   [Do deployment work]
   [Verify deployment]
   tasks_update("task-2", status="completed")
   
5. Final check:
   tasks_list(filter="pending")
   Result: []
   
6. Output: "<promise>complete</promise>"
```

**❌ WRONG Approach:**
```
User: "Continue working on the project"

AI:
# Skips checking existing tasks!
tasks_create("Implement feature X")  # Already done!
tasks_create("Add tests")  # Already done!
tasks_update("task-1", status="completed")  # Fake work
tasks_update("task-2", status="completed")  # Fake work
Output: "<promise>complete</promise>"
```

## Example: TDD Workflow (NEW Work)

**When starting NEW feature:**
```
User: "Build user authentication API with TDD"

AI:
1. tasks_list()  # Check for existing tasks
   Result: []  # No tasks - this is new work

2. Break down work:
   tasks_create("Write auth tests")  # task-1
   tasks_create("Implement auth logic", blocked_by=["task-1"])  # task-2
   tasks_create("Add integration tests", blocked_by=["task-2"])  # task-3

3. Execute:
   tasks_update("task-1", "in_progress")
   [Write tests]
   [Run tests]
   tasks_update("task-1", "completed")
   
   tasks_update("task-2", "in_progress")
   [Implement]
   [Run tests]
   tasks_update("task-2", "completed")
   
   tasks_update("task-3", "in_progress")
   [Integration tests]
   [Run tests]
   tasks_update("task-3", "completed")

4. Verify:
   tasks_list(filter="pending")  # Result: []
   
5. Output: "<promise>complete</promise>"
```

## Example: Resuming Work

**When resuming existing work:**
```
User: "Continue the auth feature"

AI:
1. tasks_list(filter="all")
   Result: [
     task-1: "Write tests" (completed),
     task-2: "Implement logic" (in_progress),
     task-3: "Integration tests" (pending, blocked by task-2)
   ]

2. Assessment:
   - task-2 is in_progress but might be done
   - Check git status
   
3. git status
   Result: Shows auth logic is committed
   
4. Reconcile:
   tasks_update("task-2", status="completed")
   # task-3 is now unblocked
   
5. Continue:
   tasks_update("task-3", status="in_progress")
   [Do work]
   [Verify]
   tasks_update("task-3", status="completed")
   
6. Output: "<promise>complete</promise>"
```

## Summary: Key Principles

1. **Check first, create later** - Always `tasks_list()` before creating
2. **Match reality** - Tasks should reflect actual work state
3. **Don't retroactively task** - Don't create tasks for done work
4. **Verify before complete** - Tests must pass
5. **Complete when done** - Output "<promise>complete</promise>" only when verified

## Anti-Patterns to Avoid

❌ Creating tasks after work is committed
❌ Creating tasks just to mark them complete
❌ Skipping `tasks_list()` at session start
❌ Marking tasks complete without verification
❌ Creating duplicate tasks without checking
❌ Using tasks as a todo list for already-done work

## Debugging

If MCP server isn't responding:
1. Check server running: Look for "gemini-tasks" in MCP list
2. Check logs in Gemini CLI
3. Verify Python environment: `uv` must be installed
4. Test manually: `cd server && uv run main.py`