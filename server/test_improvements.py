import pytest
from task_manager import TaskManager
from models import Task

@pytest.fixture
def task_manager(tmp_path):
    return TaskManager(base_dir=tmp_path)

def test_validate_blockers(task_manager):
    tm = task_manager
    # Create a task with non-existent blocker
    result = tm.create_task("Test Task", blocked_by=["non-existent"])
    assert result.task.id == "error"
    assert "Invalid blocker tasks" in result.message

    # Update task with non-existent blocker
    tm.create_task("Task 1") # task-1
    result = tm.update_task("task-1", add_blocked_by=["non-existent"])
    assert "Invalid blocker tasks" in result.message
    assert tm.get_task("task-1").task.blocked_by == []

def test_circular_dependency_detection(task_manager):
    tm = task_manager
    tm.create_task("Task 1") # task-1
    tm.create_task("Task 2") # task-2

    # Simple cycle: 1 -> 2 -> 1
    tm.update_task("task-2", add_blocked_by=["task-1"])
    result = tm.update_task("task-1", add_blocked_by=["task-2"])
    assert "Circular Dependency" in result.message
    assert tm.get_task("task-1").task.blocked_by == []

    # Longer cycle: 1 -> 2 -> 3 -> 1
    tm.create_task("Task 3") # task-3
    tm.update_task("task-3", add_blocked_by=["task-2"])
    result = tm.update_task("task-1", add_blocked_by=["task-3"])
    assert "Circular Dependency" in result.message

def test_improved_error_messages(task_manager):
    tm = task_manager
    tm.create_task("Task 1")
    tm.create_task("Task 2")

    # update_task error message
    result = tm.update_task("task-999", status="completed")
    assert "Task task-999 not found" in result.message
    assert "Available: task-1, task-2" in result.message

    # get_task error message
    result = tm.get_task("task-999")
    assert "Task task-999 not found" in result.message
    assert "Available: task-1, task-2" in result.message
