"""PawPal+ — Smart Pet Care Management System.

Core implementation, built on the class model in diagrams/uml_draft.mmd.

Relationships (from UML):
  Owner "1" --> "*" Pet       : owns
  Pet   "1" --> "*" Task      : has
  Pet   "1" --> "*" Plan      : tracks
  Task  "1" --> "*" PlanEntry : scheduled as
  Plan  "1" --> "*" PlanEntry : contains
  Scheduler ..> Pet           : reads
  Scheduler ..> Task          : reads
  Scheduler ..> Plan          : creates
"""

from __future__ import annotations

from datetime import date, time
from enum import Enum


class PriorityEnum(Enum):
    """Relative importance of a task, used for scheduling order."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecurrenceEnum(Enum):
    """How often a task repeats."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# Higher number == scheduled first. Used by Scheduler.sort_by_priority.
_PRIORITY_ORDER: dict[PriorityEnum, int] = {
    PriorityEnum.LOW: 1,
    PriorityEnum.MEDIUM: 2,
    PriorityEnum.HIGH: 3,
    PriorityEnum.CRITICAL: 4,
}

# Default clock time the scheduler starts laying out a day's entries.
DEFAULT_START_TIME = time(8, 0)


def _minutes_since_midnight(t: time) -> int:
    """Return the number of minutes from 00:00 to ``t``."""
    return t.hour * 60 + t.minute


def _add_minutes(t: time, minutes: int) -> time:
    """Return the clock time ``minutes`` after ``t`` (wraps at 24h)."""
    total = (_minutes_since_midnight(t) + minutes) % (24 * 60)
    return time(total // 60, total % 60)


def _minutes_between(start: time, end: time) -> int:
    """Return the number of minutes from ``start`` to ``end``."""
    return _minutes_since_midnight(end) - _minutes_since_midnight(start)


class Owner:
    """A pet owner who owns one or more pets."""

    def __init__(self, owner_id: str, name: str, preferences: dict | None = None):
        self.owner_id: str = owner_id
        self.name: str = name
        self.preferences: dict = preferences if preferences is not None else {}
        self._pets: list[Pet] = []

    def add_pet(self, pet: "Pet") -> None:
        """Register a pet as owned by this owner."""
        self._pets.append(pet)

    def get_pets(self) -> list["Pet"]:
        """Return the list of pets owned by this owner."""
        return list(self._pets)

    def get_all_tasks(self) -> list["Task"]:
        """Return every task belonging to every pet this owner has."""
        tasks: list[Task] = []
        for pet in self._pets:
            tasks.extend(pet.get_tasks())
        return tasks

    def get_plans(self) -> list["Plan"]:
        """Return every plan across all pets owned by this owner."""
        plans: list[Plan] = []
        for pet in self._pets:
            plans.extend(pet.get_plans())
        return plans


class Pet:
    """A pet belonging to an owner, with care tasks and daily plans."""

    def __init__(self, pet_id: str, name: str, species: str, owner_id: str):
        self.pet_id: str = pet_id
        self.name: str = name
        self.species: str = species
        self.owner_id: str = owner_id
        self._tasks: list[Task] = []
        self._plans: list[Plan] = []

    def add_task(self, task: "Task") -> None:
        """Attach a care task to this pet."""
        task._pet = self  # back-reference so Task.get_pet() works
        self._tasks.append(task)

    def get_tasks(self) -> list["Task"]:
        """Return the list of tasks for this pet."""
        return list(self._tasks)

    def add_plan(self, plan: "Plan") -> None:
        """Track a daily plan generated for this pet."""
        self._plans.append(plan)

    def get_plans(self) -> list["Plan"]:
        """Return the list of plans tracked for this pet."""
        return list(self._plans)


class Task:
    """A single care task (feeding, walk, medication, appointment, ...)."""

    def __init__(
        self,
        task_id: str,
        name: str,
        duration_minutes: int,
        priority: PriorityEnum,
        recurrence: RecurrenceEnum,
        pet_id: str,
    ):
        self.task_id: str = task_id
        self.name: str = name
        self.duration_minutes: int = duration_minutes
        self.priority: PriorityEnum = priority
        self.recurrence: RecurrenceEnum = recurrence
        self.pet_id: str = pet_id
        self._pet: Pet | None = None  # set by Pet.add_task

    def is_recurring(self) -> bool:
        """Return True if this task repeats on a schedule."""
        return self.recurrence != RecurrenceEnum.NONE

    def get_pet(self) -> "Pet | None":
        """Return the pet this task belongs to, if it has been attached."""
        return self._pet


class PlanEntry:
    """A single task scheduled into a plan at a specific time slot."""

    def __init__(
        self,
        entry_id: str,
        task_id: str,
        plan_id: str,
        start_time: time,
        end_time: time,
        status: str = "pending",
        task: "Task | None" = None,
    ):
        self.entry_id: str = entry_id
        self.task_id: str = task_id
        self.plan_id: str = plan_id
        self.start_time: time = start_time
        self.end_time: time = end_time
        self.status: str = status
        # Optional cached reference to the source Task, used for rendering.
        self.task: Task | None = task

    def duration_minutes(self) -> int:
        """Return the length of this entry's time slot in minutes."""
        return _minutes_between(self.start_time, self.end_time)

    def overlaps_with(self, other: "PlanEntry") -> bool:
        """Return True if this entry's time slot overlaps ``other``'s.

        Two half-open ranges [start, end) overlap when each one starts
        before the other ends.
        """
        return self.start_time < other.end_time and other.start_time < self.end_time

    def mark_complete(self) -> None:
        """Mark this scheduled entry as completed."""
        self.status = "complete"


class Plan:
    """A daily care plan for a pet, composed of scheduled entries."""

    def __init__(
        self,
        plan_id: str,
        date: date,
        pet_id: str,
        available_minutes: int,
        pet: "Pet | None" = None,
    ):
        self.plan_id: str = plan_id
        self.date: date = date
        self.pet_id: str = pet_id
        self.available_minutes: int = available_minutes
        self._entries: list[PlanEntry] = []
        # Optional cached reference to the pet, used for rendering.
        self.pet: Pet | None = pet

    def add_entry(self, entry: "PlanEntry") -> None:
        """Add a scheduled entry to this plan."""
        self._entries.append(entry)

    def total_duration(self) -> int:
        """Return the total duration in minutes of all entries in the plan."""
        return sum(entry.duration_minutes() for entry in self._entries)

    def get_entries(self) -> list["PlanEntry"]:
        """Return the scheduled entries in this plan."""
        return list(self._entries)

    def explain(self) -> str:
        """Return a human-readable, ordered summary of the plan."""
        if self.pet is not None:
            heading = f"Daily plan for {self.pet.name} ({self.pet.species}):"
        else:
            heading = f"Daily plan for pet {self.pet_id}:"

        lines = [heading]
        for entry in self._entries:
            clock = entry.start_time.strftime("%H:%M")
            if entry.task is not None:
                label = entry.task.name
                priority = entry.task.priority.value
            else:
                label = entry.task_id
                priority = "unknown"
            duration = entry.duration_minutes()
            lines.append(
                f"  {clock} — {label} ({duration} min) [priority: {priority}]"
            )

        if len(lines) == 1:
            lines.append("  (no tasks scheduled)")
        return "\n".join(lines)


class Scheduler:
    """Algorithmic engine that builds prioritized, conflict-free plans."""

    def sort_by_priority(self, tasks: list["Task"]) -> list["Task"]:
        """Return tasks ordered from highest to lowest priority."""
        return sorted(
            tasks,
            key=lambda task: _PRIORITY_ORDER[task.priority],
            reverse=True,
        )

    def filter_by_time(self, tasks: list["Task"], minutes: int) -> list["Task"]:
        """Return the leading tasks that fit within ``minutes`` of budget.

        Walks the (already prioritized) list and keeps each task while the
        running total stays within budget, skipping any that would push over.
        """
        kept: list[Task] = []
        used = 0
        for task in tasks:
            if used + task.duration_minutes <= minutes:
                kept.append(task)
                used += task.duration_minutes
        return kept

    def detect_conflicts(self, entries: list["PlanEntry"]) -> list["PlanEntry"]:
        """Return entries whose time slots overlap another entry."""
        conflicting: list[PlanEntry] = []
        for i, entry in enumerate(entries):
            for j, other in enumerate(entries):
                if i == j:
                    continue
                if entry.overlaps_with(other):
                    conflicting.append(entry)
                    break
        return conflicting

    def generate_plan(
        self,
        pet: "Pet",
        available_minutes: int,
        date: date,
    ) -> "Plan":
        """Build a prioritized, time-bounded plan for a pet's tasks.

        Runs the three algorithms in sequence:
          1. sort_by_priority — order the pet's tasks
          2. filter_by_time   — drop tasks that exceed the time budget
          3. lay out back-to-back entries, then detect_conflicts as a check
        The finished plan is registered on the pet and returned.
        """
        prioritized = self.sort_by_priority(pet.get_tasks())
        fitted = self.filter_by_time(prioritized, available_minutes)

        plan_id = f"plan-{pet.pet_id}-{date.isoformat()}"
        plan = Plan(
            plan_id=plan_id,
            date=date,
            pet_id=pet.pet_id,
            available_minutes=available_minutes,
            pet=pet,
        )

        current = DEFAULT_START_TIME
        for index, task in enumerate(fitted):
            start = current
            end = _add_minutes(start, task.duration_minutes)
            entry = PlanEntry(
                entry_id=f"{plan_id}-e{index}",
                task_id=task.task_id,
                plan_id=plan_id,
                start_time=start,
                end_time=end,
                status="pending",
                task=task,
            )
            plan.add_entry(entry)
            current = end

        # Entries are laid out sequentially so none should overlap; running
        # the detector guards against future changes to the layout logic.
        conflicts = self.detect_conflicts(plan.get_entries())
        if conflicts:
            for entry in conflicts:
                entry.status = "conflict"

        pet.add_plan(plan)
        return plan
