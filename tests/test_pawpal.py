"""Simple tests for PawPal+ core behaviors."""

import os
import sys
from datetime import date, time, timedelta

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
def test_sort_by_priority_orders_high_to_low():
    """sort_by_priority() returns tasks from most to least important."""
    scheduler = Scheduler()
    low = _task("t1", "Brush", "p1", priority=PriorityEnum.LOW)
    critical = _task("t2", "Meds", "p1", priority=PriorityEnum.CRITICAL)
    medium = _task("t3", "Walk", "p1", priority=PriorityEnum.MEDIUM)
    high = _task("t4", "Feed", "p1", priority=PriorityEnum.HIGH)

    ordered = scheduler.sort_by_priority([low, critical, medium, high])

    assert [t.name for t in ordered] == ["Meds", "Feed", "Walk", "Brush"]


def test_sort_by_priority_is_stable_on_ties():
    """Tasks of equal priority keep their original relative order."""
    scheduler = Scheduler()
    first = _task("t1", "First", "p1", priority=PriorityEnum.HIGH)
    second = _task("t2", "Second", "p1", priority=PriorityEnum.HIGH)
    third = _task("t3", "Third", "p1", priority=PriorityEnum.HIGH)

    ordered = scheduler.sort_by_priority([first, second, third])

    assert [t.name for t in ordered] == ["First", "Second", "Third"]


def test_sort_handles_empty_list():
    """Both sorts return an empty list rather than erroring on no tasks."""
    scheduler = Scheduler()
    assert scheduler.sort_by_priority([]) == []
    assert scheduler.sort_by_time([]) == []


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


def test_mark_complete_monthly_uses_thirty_day_delta():
    """Monthly recurrence rolls forward by a flat 30 days (documented approx).

    Note: this is *not* true calendar-month arithmetic — a task due Jan 31
    lands on Mar 2, not Feb 28. Pinning the behavior so any future change to
    real month math is a deliberate, visible decision.
    """
    task = _task(
        "t1",
        "Flea treatment",
        "p1",
        recurrence=RecurrenceEnum.MONTHLY,
        due_date=date(2026, 1, 31),
    )

    nxt = task.mark_complete()

    assert nxt is not None
    assert nxt.due_date == date(2026, 1, 31) + timedelta(days=30)
    assert nxt.due_date == date(2026, 3, 2)


def test_next_occurrence_defaults_to_today_when_no_due_date():
    """With no due_date, the next occurrence is one interval from today."""
    task = _task("t1", "Daily walk", "p1", recurrence=RecurrenceEnum.DAILY)

    nxt = task.next_occurrence()

    assert nxt is not None
    assert nxt.due_date == date.today() + timedelta(days=1)


def test_mark_complete_twice_keeps_advancing_the_due_date():
    """Completing the follow-up task advances the date another interval."""
    task = _task(
        "t1",
        "Medication",
        "p1",
        recurrence=RecurrenceEnum.DAILY,
        due_date=date(2026, 7, 4),
    )

    first = task.mark_complete()
    assert first is not None and first.due_date == date(2026, 7, 5)

    second = first.mark_complete()
    assert first.is_complete()
    assert second is not None
    assert second.status == "pending"
    assert second.due_date == date(2026, 7, 6)


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


def test_detect_time_conflicts_flags_identical_times():
    """Two tasks at the exact same time on the same day conflict."""
    scheduler = Scheduler()
    day = date(2026, 7, 4)
    walk = _task("t1", "Walk", "p1", minutes=30, scheduled_time=time(8, 0), due_date=day)
    feed = _task("t2", "Feed", "p1", minutes=30, scheduled_time=time(8, 0), due_date=day)

    warnings = scheduler.detect_time_conflicts([walk, feed])

    assert len(warnings) == 1
    assert "Conflict" in warnings[0]


def test_detect_time_conflicts_same_time_different_days():
    """Same clock time on different due dates is not a conflict."""
    scheduler = Scheduler()
    today = _task("t1", "Walk", "p1", scheduled_time=time(8, 0), due_date=date(2026, 7, 4))
    tomorrow = _task("t2", "Walk", "p1", scheduled_time=time(8, 0), due_date=date(2026, 7, 5))

    assert scheduler.detect_time_conflicts([today, tomorrow]) == []


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


# ---------------------------------------------------------------------------
# Time budgeting (filter_by_time)
# ---------------------------------------------------------------------------
def test_filter_by_time_drops_task_larger_than_budget():
    """A single task longer than the whole budget is dropped entirely."""
    scheduler = Scheduler()
    big = _task("t1", "Grooming", "p1", minutes=90)

    assert scheduler.filter_by_time([big], 60) == []


def test_filter_by_time_is_greedy_and_packs_smaller_tasks():
    """It skips an over-budget task but still keeps a later one that fits.

    Documents the greedy behavior: after priority sorting, filter_by_time
    keeps scanning, so a small low-priority task can be scheduled even though
    an earlier high-priority task was skipped for not fitting.
    """
    scheduler = Scheduler()
    big = _task("t1", "Long walk", "p1", minutes=90)
    small = _task("t2", "Quick feed", "p1", minutes=20)

    kept = scheduler.filter_by_time([big, small], 60)

    assert [t.name for t in kept] == ["Quick feed"]


def test_filter_by_time_keeps_exact_fit():
    """A task whose duration exactly equals the remaining budget is kept."""
    scheduler = Scheduler()
    task = _task("t1", "Walk", "p1", minutes=60)

    assert [t.name for t in scheduler.filter_by_time([task], 60)] == ["Walk"]


def test_filter_by_time_zero_budget_keeps_nothing():
    """A zero-minute budget schedules no tasks."""
    scheduler = Scheduler()
    task = _task("t1", "Walk", "p1", minutes=30)

    assert scheduler.filter_by_time([task], 0) == []


# ---------------------------------------------------------------------------
# Plan generation
# ---------------------------------------------------------------------------
def test_generate_plan_with_no_tasks_is_empty():
    """A pet with no tasks yields a plan with no entries."""
    scheduler = Scheduler()
    pet = Pet(pet_id="p1", name="Biscuit", species="dog", owner_id="o1")

    plan = scheduler.generate_plan(pet, available_minutes=120, date=date(2026, 7, 4))

    assert plan.get_entries() == []
    assert "(no tasks scheduled)" in plan.explain()


def test_generate_plan_lays_out_entries_back_to_back():
    """Entries start at 08:00 and each begins where the previous one ended."""
    scheduler = Scheduler()
    pet = Pet(pet_id="p1", name="Biscuit", species="dog", owner_id="o1")
    pet.add_task(_task("t1", "Walk", "p1", minutes=30, priority=PriorityEnum.HIGH))
    pet.add_task(_task("t2", "Feed", "p1", minutes=45, priority=PriorityEnum.LOW))

    plan = scheduler.generate_plan(pet, available_minutes=240, date=date(2026, 7, 4))
    entries = plan.get_entries()

    assert entries[0].start_time == time(8, 0)
    assert entries[0].end_time == time(8, 30)
    assert entries[1].start_time == time(8, 30)
    assert entries[1].end_time == time(9, 15)


def test_generate_plan_drops_task_that_would_run_past_midnight():
    """A task too long to finish before midnight is not scheduled.

    With an 08:00 start, a 1000-minute task would end after midnight. Rather
    than wrapping the end time back into the small hours, the layout skips it,
    so the plan stays empty.
    """
    scheduler = Scheduler()
    pet = Pet(pet_id="p1", name="Biscuit", species="dog", owner_id="o1")
    pet.add_task(_task("t1", "Marathon grooming", "p1", minutes=1000))

    plan = scheduler.generate_plan(pet, available_minutes=1000, date=date(2026, 7, 4))

    assert plan.get_entries() == []


def test_generate_plan_never_produces_a_wrapped_entry():
    """Every scheduled entry ends after it starts, even on an overloaded day.

    A short high-priority task fits; a huge low-priority one that would spill
    past midnight is dropped. No entry should ever have end_time < start_time.
    """
    scheduler = Scheduler()
    pet = Pet(pet_id="p1", name="Biscuit", species="dog", owner_id="o1")
    pet.add_task(_task("t1", "Walk", "p1", minutes=120, priority=PriorityEnum.HIGH))
    pet.add_task(_task("t2", "Marathon", "p1", minutes=1000, priority=PriorityEnum.LOW))

    plan = scheduler.generate_plan(pet, available_minutes=1200, date=date(2026, 7, 4))
    entries = plan.get_entries()

    assert [e.task_id for e in entries] == ["t1"]
    assert all(e.end_time > e.start_time for e in entries)
    assert all(e.duration_minutes() > 0 for e in entries)


# ---------------------------------------------------------------------------
# Filtering ambiguity
# ---------------------------------------------------------------------------
def test_filter_by_pet_matches_all_pets_sharing_a_name():
    """Two different pets with the same name both match by that name.

    Documents that pet_name is not a unique key — worth knowing if names are
    ever used as identifiers elsewhere.
    """
    scheduler = Scheduler()
    dog = Pet(pet_id="p1", name="Buddy", species="dog", owner_id="o1")
    cat = Pet(pet_id="p2", name="Buddy", species="cat", owner_id="o1")
    dog_task = _task("t1", "Walk", "p1")
    cat_task = _task("t2", "Feed", "p2")
    dog.add_task(dog_task)
    cat.add_task(cat_task)

    matches = scheduler.filter_by_pet([dog_task, cat_task], "Buddy")

    assert {t.name for t in matches} == {"Walk", "Feed"}
