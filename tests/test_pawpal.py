"""Simple tests for PawPal+ core behaviors."""

import os
import sys
from datetime import time

# Allow importing pawpal_system from the project root when running from tests/.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pawpal_system import (  # noqa: E402
    Pet,
    PlanEntry,
    PriorityEnum,
    RecurrenceEnum,
    Task,
)


def test_task_completion_changes_status():
    """mark_complete() should flip a scheduled entry's status to 'complete'."""
    entry = PlanEntry(
        entry_id="e1",
        task_id="t1",
        plan_id="plan1",
        start_time=time(8, 0),
        end_time=time(8, 30),
        status="pending",
    )

    assert entry.status == "pending"
    entry.mark_complete()
    assert entry.status == "complete"


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet should grow its task list by one."""
    pet = Pet(pet_id="p1", name="Biscuit", species="Golden Retriever", owner_id="o1")
    assert len(pet.get_tasks()) == 0

    task = Task(
        task_id="t1",
        name="Morning walk",
        duration_minutes=30,
        priority=PriorityEnum.HIGH,
        recurrence=RecurrenceEnum.DAILY,
        pet_id="p1",
    )
    pet.add_task(task)

    assert len(pet.get_tasks()) == 1
