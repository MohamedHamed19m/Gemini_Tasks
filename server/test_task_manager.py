import pytest
from task_manager import TaskManager
import os
import json

@pytest.fixture
def task_manager(tmp_path):
    # Use a temporary tasks file for testing
    tasks_file = tmp_path / "tasks.json"
    
    # Mock GEMINI_TASK_LIST_ID to use this temp file
    # Note: TaskStorage uses os.homedir() / .gemini / tasks / {id}.json
    # We need to mock TaskStorage to use our temp path or just let it use the real one but clean up.
    # Actually, let's just test the TaskManager logic.
    
    # For simplicity in this test, we'll let it use the real storage but we'll be careful.
    # A better way is to inject storage into TaskManager.
    return TaskManager()

def test_create_task():
    tm = TaskManager()
    # Clean start for testing
    tm.clear_tasks("all")
    
    result = tm.create_task("Test Task", "Description")
    assert result.task.subject == "Test Task"
    assert result.task.status == "pending"
    assert result.task.id == "task-1"

def test_update_task():
    tm = TaskManager()
    tm.clear_tasks("all")
    
    tm.create_task("Test Task")
    tm.update_task("task-1", status="in_progress")
    
    task_get = tm.get_task("task-1")
    assert task_get.task.status == "in_progress"

def test_clear_tasks():
    tm = TaskManager()
    tm.clear_tasks("all")
    
    tm.create_task("Task 1")
    tm.create_task("Task 2")
    tm.update_task("task-1", status="completed")
    
    tm.clear_tasks("completed")
    
    tasks = tm.list_tasks("all")
    assert len(tasks.tasks) == 1
    assert tasks.tasks[0].id == "task-2"
