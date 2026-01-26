import pytest
from task_manager import TaskManager


@pytest.fixture
def task_manager(tmp_path):
    # Use a temporary directory for testing
    return TaskManager(base_dir=tmp_path)


def test_create_task(task_manager):
    tm = task_manager
    result = tm.create_task("Test Task", "Description")
    assert result.task.subject == "Test Task"
    assert result.task.status == "pending"
    assert result.task.id == "task-1"


def test_update_task(task_manager):
    tm = task_manager
    tm.create_task("Test Task")
    tm.update_task("task-1", status="in_progress")

    task_get = tm.get_task("task-1")
    assert task_get.task.status == "in_progress"


def test_clear_tasks(task_manager):
    tm = task_manager
    tm.create_task("Task 1")
    tm.create_task("Task 2")
    tm.update_task("task-1", status="completed")

    tm.clear_tasks("completed")

    tasks = tm.list_tasks("all")
    assert len(tasks.tasks) == 1
    assert tasks.tasks[0].id == "task-2"


def test_list_tasks_filtered(task_manager):
    tm = task_manager
    tm.create_task("Task 1")  # Pending
    tm.create_task("Task 2")
    tm.update_task("task-2", status="in_progress")  # In progress
    tm.create_task("Task 3")
    tm.update_task("task-3", status="completed")  # Completed

    all_tasks = tm.list_tasks("all")
    assert len(all_tasks.tasks) == 3

    pending_tasks = tm.list_tasks("pending")
    assert len(pending_tasks.tasks) == 1
    assert pending_tasks.tasks[0].subject == "Task 1"

    in_progress_tasks = tm.list_tasks("in_progress")
    assert len(in_progress_tasks.tasks) == 1
    assert in_progress_tasks.tasks[0].subject == "Task 2"

    completed_tasks = tm.list_tasks("completed")
    assert len(completed_tasks.tasks) == 1
    assert completed_tasks.tasks[0].subject == "Task 3"


def test_get_task_details(task_manager):
    tm = task_manager
    tm.create_task("Single Task", "Detailed description")

    task = tm.get_task("task-1").task
    assert task.subject == "Single Task"
    assert task.description == "Detailed description"

    # Test getting a non-existent task
    non_existent_task = tm.get_task("task-999")
    assert non_existent_task.task is None
    assert "not found" in non_existent_task.message.lower()


def test_task_dependencies(task_manager):
    tm = task_manager
    # Create tasks
    task_a = tm.create_task("Task A")  # task-1
    task_b = tm.create_task("Task B", blocked_by=[task_a.task.id])  # task-2
    task_c = tm.create_task("Task C", blocked_by=[task_b.task.id])  # task-3

    # Check initial dependencies
    assert tm.get_task(task_a.task.id).task.blocks == [task_b.task.id]
    assert tm.get_task(task_b.task.id).task.blocked_by == [task_a.task.id]
    assert tm.get_task(task_b.task.id).task.blocks == [task_c.task.id]
    assert tm.get_task(task_c.task.id).task.blocked_by == [task_b.task.id]

    # Mark Task A as completed, should unblock Task B
    update_result_a = tm.update_task(task_a.task.id, status="completed")
    assert task_b.task.id in update_result_a.unblocked_tasks
    assert tm.get_task(task_b.task.id).task.blocked_by == []  # Should be unblocked

    # Mark Task B as completed, should unblock Task C
    update_result_b = tm.update_task(task_b.task.id, status="completed")
    assert task_c.task.id in update_result_b.unblocked_tasks
    assert tm.get_task(task_c.task.id).task.blocked_by == []  # Should be unblocked

    # Test adding and removing blockers
    task_d = tm.create_task("Task D")  # task-4
    task_e = tm.create_task("Task E")  # task-5

    tm.update_task(task_e.task.id, add_blocked_by=[task_d.task.id])
    assert tm.get_task(task_e.task.id).task.blocked_by == [task_d.task.id]
    assert tm.get_task(task_d.task.id).task.blocks == [task_e.task.id]

    tm.update_task(task_e.task.id, remove_blocked_by=[task_d.task.id])
    assert tm.get_task(task_e.task.id).task.blocked_by == []
    assert tm.get_task(task_d.task.id).task.blocks == []


def test_search_tasks(task_manager):
    tm = task_manager
    tm.create_task("Buy groceries", "Milk, Eggs, Bread")
    tm.create_task("Clean house", "Vacuum, Dust, Mop")
    tm.create_task("Walk dog", "Take to park")
    tm.create_task("Code review", "Review pull request for new feature")

    # Search by subject
    results = tm.search_tasks("groceries")
    assert len(results.tasks) == 1
    assert results.tasks[0].subject == "Buy groceries"

    # Search by description
    results = tm.search_tasks("pull request")
    assert len(results.tasks) == 1
    assert results.tasks[0].subject == "Code review"

    # Search with filter
    tm.update_task("task-1", status="completed")  # Groceries
    results = tm.search_tasks("buy", filter="completed")
    assert len(results.tasks) == 1
    assert results.tasks[0].subject == "Buy groceries"

    results = tm.search_tasks("house", filter="pending")
    assert len(results.tasks) == 1
    assert results.tasks[0].subject == "Clean house"

    # No match
    results = tm.search_tasks("nonexistent")
    assert len(results.tasks) == 0
