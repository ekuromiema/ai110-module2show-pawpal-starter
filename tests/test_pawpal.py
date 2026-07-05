"""Simple tests for PawPal+ core behaviors."""

import os
import sys
from datetime import date, time

# Allow importing pawpal_system from the project root when running from tests/.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pawpal_system import (  # noqa: E402
    Pet,
    PlanEntry,
    PriorityEnum,
    RecurrenceEnum,
    Scheduler,
    Task,
)


def _task(
    task_id,
    name,
    pet_id,
    *,
    minutes=30,
    priority=PriorityEnum.MEDIUM,
    recurrence=RecurrenceEnum.NONE,
    scheduled_time=None,
    due_date=None,
    status="pending",
):
    """Build a Task with sensible defaults for the tests below."""
    return Task(
        task_id=task_id,
        name=name,
        duration_minutes=minutes,
        priority=priority,
        recurrence=recurrence,
        pet_id=pet_id,
        scheduled_time=scheduled_time,
        due_date=due_date,
        status=status,
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


# ---------------------------------------------------------------------------
# Sorting and filtering
# ---------------------------------------------------------------------------
def test_sort_by_time_orders_earliest_first():
    """sort_by_time() should order tasks by scheduled clock time."""
    scheduler = Scheduler()
    walk = _task("t1", "Walk", "p1", scheduled_time=time(9, 0))
    breakfast = _task("t2", "Breakfast", "p1", scheduled_time=time(7, 30))
    nap = _task("t3", "Nap", "p1", scheduled_time=time(13, 0))

    ordered = scheduler.sort_by_time([walk, nap, breakfast])

    assert [t.name for t in ordered] == ["Breakfast", "Walk", "Nap"]


def test_sort_by_time_puts_untimed_tasks_last():
    """Tasks without a scheduled_time sort after timed ones."""
    scheduler = Scheduler()
    timed = _task("t1", "Walk", "p1", scheduled_time=time(9, 0))
    untimed = _task("t2", "Someday", "p1")

    ordered = scheduler.sort_by_time([untimed, timed])

    assert [t.name for t in ordered] == ["Walk", "Someday"]


def test_filter_by_status():
    """filter_by_status() keeps only tasks with the requested status."""
    scheduler = Scheduler()
    done = _task("t1", "Walk", "p1", status="complete")
    todo = _task("t2", "Feed", "p1", status="pending")

    pending = scheduler.filter_by_status([done, todo], "pending")

    assert [t.name for t in pending] == ["Feed"]


def test_filter_by_pet_matches_name_and_id():
    """filter_by_pet() matches on the attached pet's name or the raw pet_id."""
    scheduler = Scheduler()
    biscuit = Pet(pet_id="p1", name="Biscuit", species="dog", owner_id="o1")
    mochi_task = _task("t2", "Feed", "p2")  # not attached to any Pet
    biscuit_task = _task("t1", "Walk", "p1")
    biscuit.add_task(biscuit_task)

    by_name = scheduler.filter_by_pet([biscuit_task, mochi_task], "Biscuit")
    by_id = scheduler.filter_by_pet([biscuit_task, mochi_task], "p2")

    assert [t.name for t in by_name] == ["Walk"]
    assert [t.name for t in by_id] == ["Feed"]


# ---------------------------------------------------------------------------
# Recurring tasks
# ---------------------------------------------------------------------------
def test_mark_complete_daily_creates_next_day_occurrence():
    """Completing a daily task returns a pending copy due one day later."""
    task = _task(
        "t1",
        "Medication",
        "p1",
        recurrence=RecurrenceEnum.DAILY,
        due_date=date(2026, 7, 4),
        scheduled_time=time(8, 0),
    )

    nxt = task.mark_complete()

    assert task.is_complete()
    assert nxt is not None
    assert nxt.status == "pending"
    assert nxt.due_date == date(2026, 7, 5)
    assert nxt.scheduled_time == time(8, 0)


def test_mark_complete_weekly_creates_next_week_occurrence():
    """Completing a weekly task rolls the due date forward seven days."""
    task = _task(
        "t1",
        "Play session",
        "p1",
        recurrence=RecurrenceEnum.WEEKLY,
        due_date=date(2026, 7, 4),
    )

    nxt = task.mark_complete()

    assert nxt is not None
    assert nxt.due_date == date(2026, 7, 11)


def test_mark_complete_one_off_has_no_next_occurrence():
    """A non-recurring task returns None when completed."""
    task = _task("t1", "Vet visit", "p1", recurrence=RecurrenceEnum.NONE)

    assert task.mark_complete() is None
    assert task.is_complete()


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------
def test_detect_time_conflicts_flags_overlap():
    """Overlapping tasks on the same day produce a warning message."""
    scheduler = Scheduler()
    day = date(2026, 7, 4)
    walk = _task("t1", "Walk", "p1", minutes=30, scheduled_time=time(8, 0), due_date=day)
    feed = _task("t2", "Feed", "p2", minutes=30, scheduled_time=time(8, 15), due_date=day)

    warnings = scheduler.detect_time_conflicts([walk, feed])

    assert len(warnings) == 1
    assert "Conflict" in warnings[0]


def test_detect_time_conflicts_ignores_non_overlapping():
    """Back-to-back tasks and different days do not conflict."""
    scheduler = Scheduler()
    day = date(2026, 7, 4)
    walk = _task("t1", "Walk", "p1", minutes=30, scheduled_time=time(8, 0), due_date=day)
    feed = _task("t2", "Feed", "p1", minutes=30, scheduled_time=time(8, 30), due_date=day)

    assert scheduler.detect_time_conflicts([walk, feed]) == []


def test_detect_time_conflicts_skips_untimed_without_crashing():
    """Tasks with no scheduled_time are skipped, not errors."""
    scheduler = Scheduler()
    untimed = _task("t1", "Someday", "p1")

    assert scheduler.detect_time_conflicts([untimed]) == []
