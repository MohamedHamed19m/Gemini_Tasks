"""MCP Server implementation for Gemini Tasks."""

from fastmcp import FastMCP
from typing import Optional, List

from task_manager import TaskManager
from models import (
    TaskListResult,
    TaskCreateResult,
    TaskUpdateResult,
    TaskGetResult,
    TaskSearchResult,
    TaskClearResult,
)

# Initialize FastMCP server
mcp = FastMCP(name="Gemini Tasks", version="1.0.0")

# Initialize task manager
task_manager = TaskManager()


# ============================================================================
# MCP Tools (Protocol-Driven Interface)
# ============================================================================


@mcp.tool(
    name="tasks_list",
    description="""
    List all tasks with optional status filter.
    
    This is typically the FIRST tool to call in a session to understand
    current task state. Returns all tasks with their IDs, subjects, statuses,
    and dependencies.
    
    Use this to:
    - See what tasks exist
    - Check which tasks are pending/in_progress/completed
    - Identify next available unblocked task to work on
    
    Args:
        filter: Status filter - "all", "pending", "in_progress", "completed"
                Default: "all"
    
    Returns:
        TaskListResult with filtered task list
    """,
)
def tasks_list(filter: str = "all") -> TaskListResult:
    """List all tasks with optional status filter.

    Args:
        filter: Status filter (all, pending, in_progress, completed)

    Returns:
        TaskListResult with filtered tasks

    """
    return task_manager.list_tasks(filter)


@mcp.tool(
    name="tasks_create",
    description="""
    Create a new task with subject, description, and optional blockers.
    
    Use this when:
    - Breaking down complex work into steps
    - Setting up task dependencies
    - Coordinating multi-session work
    
    IMPORTANT: If creating dependent tasks, specify blocked_by parameter
    to enforce proper ordering. For example, "implement API" should be
    blocked by "write tests" task ID.
    
    Args:
        subject: Brief task title (required)
        description: Detailed task description (optional)
        blocked_by: List of task IDs this task depends on (optional)
    
    Returns:
        TaskCreateResult with created task and generated ID
    """,
)
def tasks_create(
    subject: str, description: str = "", blocked_by: Optional[List[str]] = None
) -> TaskCreateResult:
    """Create a new task.

    Args:
        subject: Task subject/title
        description: Task description
        blocked_by: List of task IDs this task is blocked by

    Returns:
        TaskCreateResult with created task

    """
    return task_manager.create_task(subject, description, blocked_by)


@mcp.tool(
    name="tasks_update",
    description="""
    Update a task's status and/or dependencies.
    
    CRITICAL STATUS LIFECYCLE:
    - pending → in_progress (when starting work)
    - in_progress → completed (after verification passes)
    
    Use this when:
    - Starting work on a task (set status="in_progress")
    - Completing a task after verification (set status="completed")
    - Adding newly discovered dependencies
    - Removing blockers that are no longer relevant
    
    VERIFICATION RULE: Only mark completed after tests pass and work
    is verified. If verification fails, keep status as in_progress.
    
    Args:
        task_id: Task ID to update (required)
        status: New status - "pending", "in_progress", "completed" (optional)
        add_blocked_by: Task IDs to add as blockers (optional)
        remove_blocked_by: Task IDs to remove as blockers (optional)
    
    Returns:
        TaskUpdateResult with updated task and list of unblocked tasks
    """,
)
def tasks_update(
    task_id: str,
    status: Optional[str] = None,
    add_blocked_by: Optional[List[str]] = None,
    remove_blocked_by: Optional[List[str]] = None,
) -> TaskUpdateResult:
    """Update a task.

    Args:
        task_id: Task ID to update
        status: New status
        add_blocked_by: Task IDs to add as blockers
        remove_blocked_by: Task IDs to remove as blockers

    Returns:
        TaskUpdateResult with updated task

    """
    return task_manager.update_task(task_id, status, add_blocked_by, remove_blocked_by)


@mcp.tool(
    name="tasks_get",
    description="""
    Get full details of a specific task.
    
    Use this when:
    - Checking task details before starting work
    - Verifying blockers and dependencies
    - Need complete task information
    
    Args:
        task_id: Task ID to retrieve (required)
    
    Returns:
        TaskGetResult with task details or not found message
    """,
)
def tasks_get(task_id: str) -> TaskGetResult:
    """Get a specific task.

    Args:
        task_id: Task ID to retrieve

    Returns:
        TaskGetResult with task details

    """
    return task_manager.get_task(task_id)


@mcp.tool(
    name="tasks_search",
    description="""
    Search for tasks by keyword in subject or description.
    
    Use this when:
    - Looking for related tasks
    - Checking if similar work already exists
    - Finding specific task by keyword
    
    Args:
        query: Search keywords (required)
        filter: Optional status filter (optional)
    
    Returns:
        TaskSearchResult with matching tasks
    """,
)
def tasks_search(query: str, filter: Optional[str] = None) -> TaskSearchResult:
    """Search tasks by keyword.

    Args:
        query: Search query
        filter: Optional status filter

    Returns:
        TaskSearchResult with matching tasks

    """
    return task_manager.search_tasks(query, filter)


@mcp.tool(
    name="tasks_clear",
    description="""
    Clear completed tasks or all tasks.
    
    Use this when:
    - Cleaning up after project phase completion
    - Removing clutter from completed work
    - Starting fresh (caution with filter="all")
    
    Args:
        filter: "completed" (default) or "all"
    
    Returns:
        TaskClearResult with count of cleared tasks
    """,
)
def tasks_clear(filter: str = "completed") -> TaskClearResult:
    """Clear tasks by filter.

    Args:
        filter: "completed" to clear only completed, "all" to clear everything

    Returns:
        TaskClearResult with count of cleared tasks

    """
    return task_manager.clear_tasks(filter)


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()