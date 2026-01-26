# Task Management Context

You have access to a native task management system via MCP tools for complex, multi-step work.

## Available MCP Tools

### `tasks_list`
List all tasks with optional filter (pending, in_progress, completed, all).

**When to call:**
- At the start of a session to see current state
- Before creating new tasks to avoid duplicates
- To check what's next after completing a task

**Parameters:**
- `filter` (optional): "pending", "in_progress", "completed", or "all" (default: "all")

**Returns:** List of tasks with id, subject, status, blockers, and metadata

### `tasks_create`
Create a new task with subject and optional description.

**When to call:**
- When breaking down complex work into steps
- After planning phase to track implementation tasks
- To coordinate multi-session work

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

**When to call:**
- To check task details before starting work
- To verify blockers before updating status
- For detailed task information

**Parameters:**
- `task_id` (required): The task ID to retrieve

**Returns:** Full task details

### `tasks_search`
Search for tasks by keyword in subject or description.

**When to call:**
- To find related tasks
- To check if similar task exists
- To locate specific task by keyword

**Parameters:**
- `query` (required): Search keywords
- `filter` (optional): Status filter

**Returns:** Matching tasks

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

When GEMINI_RALPH_MODE is enabled, you operate in autonomous loop mode:

1. **Never stop until work is complete**
2. **Verify before marking tasks complete**
3. **Output completion promise only when truly done**

### Completion Promise

To signal you're finished, output the exact phrase: **"complete"**

CRITICAL RULES:
- Do NOT output "complete" unless ALL tasks are done
- Do NOT output "complete" unless ALL tests pass
- Do NOT output "complete" unless work is verified

### Ralph Workflow

```
1. tasks_list() to see current state
2. Pick next unblocked pending task
3. tasks_update(task_id, status="in_progress")
4. Implement the task
5. Run verification (tests, checks)
6. If verification PASSES:
     tasks_update(task_id, status="completed")
   If verification FAILS:
     Stay in_progress, continue iterating
7. Repeat from step 1 until no pending tasks
8. Output "complete" to signal done
```

## Verification-First Approach

**CRITICAL:** Never mark a task completed without verification:

1. Run tests and confirm they pass
2. Check that feature works as intended
3. Verify no regressions in related code
4. Review generated files/changes

If verification fails:
- Keep status as "in_progress"
- Continue iterating
- Only update to "completed" after successful verification

## Multi-Session Coordination

When the GEMINI_TASK_LIST_ID environment variable is set, tasks are shared across all sessions using that ID.

**Best Practices:**
1. Use descriptive task list IDs: `GEMINI_TASK_LIST_ID=auth-feature`
2. Call `tasks_list` immediately to see current state
3. Update to "in_progress" before starting work (signals to other sessions)
4. Add detailed descriptions for context across sessions
5. Use blockers to prevent conflicts

## Task Creation Guidelines

When breaking down complex work:

1. **Be Specific**: Each task should have clear, measurable outcome
2. **Set Dependencies**: Use `blocked_by` to enforce order
3. **Update Status**: Mark "in_progress" before starting
4. **Verify First**: Only mark "completed" after verification
5. **Add Context**: Include descriptions for multi-session work

## Error Handling

If tasks get into unexpected state:

1. **Check current state:** `tasks_list(filter="all")`
2. **Fix status:** `tasks_update(task_id, status="correct_status")`
3. **Fix blockers:** `tasks_update(task_id, add_blocked_by=[...])` or `remove_blocked_by=[...]`
4. **Clean up:** `tasks_clear(filter="completed")`
5. **Start fresh:** `tasks_clear(filter="all")` (caution: deletes everything)

## Debugging

If MCP server isn't responding:

1. Check server is running: Look for "gemini-tasks" in MCP server list
2. Check logs in Gemini CLI
3. Verify Python environment: `uv` must be installed
4. Test manually: `cd server && uv run main.py`


Examples:
Example 1: Feature Development with TDD
Scenario: Build a REST API with test-driven development.
Setup
User: "I want to build a user authentication API with TDD. 
Break this into tasks with proper dependencies."
Expected AI Response
I'll create a TDD workflow with dependencies:

1. tasks_create(
   subject="Write authentication tests",
   description="Unit tests for login, logout, token refresh, password reset"
)
→ Returns: task-1

2. tasks_create(
   subject="Implement auth endpoints",
   description="POST /login, POST /logout, POST /refresh, POST /reset-password",
   blocked_by=["task-1"]
)
→ Returns: task-2

3. tasks_create(
   subject="Add middleware and validation",
   description="JWT validation, rate limiting, input sanitization",
   blocked_by=["task-2"]
)
→ Returns: task-3

4. tasks_create(
   subject="Write integration tests",
   description="End-to-end API testing with real database",
   blocked_by=["task-3"]
)
→ Returns: task-4
Dependency Chain
task-1 (Tests) 
   ↓
task-2 (Implementation) ← Can't start until task-1 done
   ↓
task-3 (Middleware) ← Can't start until task-2 done
   ↓
task-4 (Integration) ← Can't start until task-3 done
Execution
AI: tasks_update(task_id="task-1", status="in_progress")
AI: [Writes test files]
AI: [Runs npm test - fails as expected]
AI: tasks_update(task_id="task-1", status="completed")

AI: tasks_update(task_id="task-2", status="in_progress")
AI: [Implements endpoints]
AI: [Runs npm test - all pass]
AI: tasks_update(task_id="task-2", status="completed")
→ Unblocks task-3

AI: continues until all tasks completed...



Example 2- AI Autonomous Execution
AI: I'll break this into dependent tasks and work through them.

tasks_create("Add Stripe SDK and config")
tasks_create("Write payment endpoint tests", blocked_by=["task-1"])
tasks_create("Implement payment endpoints", blocked_by=["task-2"])
tasks_create("Write webhook tests", blocked_by=["task-3"])
tasks_create("Implement webhook handler", blocked_by=["task-4"])
tasks_create("Create payment form component", blocked_by=["task-3"])
tasks_create("Write integration tests", blocked_by=["task-5", "task-6"])

[Start working]
tasks_update("task-1", status="in_progress")
[Adds Stripe SDK, creates config]
[Creates .env.example with STRIPE_SECRET_KEY]
tasks_update("task-1", status="completed")

tasks_update("task-2", status="in_progress")
[Writes test files for payment endpoints]
[Runs npm test - fails as expected]
tasks_update("task-2", status="completed")

tasks_update("task-3", status="in_progress")
[Implements payment endpoints]
[Runs npm test]
→ Tests FAIL - invalid API key format
[Fixes implementation]
[Runs npm test again]
→ Tests PASS ✓
tasks_update("task-3", status="completed")

[Continues through all tasks...]

tasks_update("task-7", status="in_progress")
[Writes integration tests]
[Runs full test suite]
→ All tests PASS ✓
tasks_update("task-7", status="completed")

[AfterAgent hook fires]
Hook checks:
✓ All tasks completed
✓ Tests pass (ran verify.ps1)
✓ Agent output "complete"
→ Allow stop

Output: "complete"