import pytest
from task_manager import TaskManager
import os
import json

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
