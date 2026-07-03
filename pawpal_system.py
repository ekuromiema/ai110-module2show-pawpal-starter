"""PawPal+ — Smart Pet Care Management System.

Class skeleton scaffolded from diagrams/uml_draft.mmd.
Attributes and method signatures only; method bodies are left as stubs
to be implemented.

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


class Owner:
    """A pet owner who owns one or more pets."""

    def __init__(self, owner_id: str, name: str, preferences: dict | None = None):
        self.owner_id: str = owner_id
        self.name: str = name
        self.preferences: dict = preferences if preferences is not None else {}
        self._pets: list[Pet] = []

    def add_pet(self, pet: "Pet") -> None:
        """Register a pet as owned by this owner."""
        raise NotImplementedError

    def get_pets(self) -> list["Pet"]:
        """Return the list of pets owned by this owner."""
        raise NotImplementedError

    def get_plans(self) -> list["Plan"]:
        """Return every plan across all pets owned by this owner."""
        raise NotImplementedError


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
        raise NotImplementedError

    def get_tasks(self) -> list["Task"]:
        """Return the list of tasks for this pet."""
        raise NotImplementedError

    def add_plan(self, plan: "Plan") -> None:
        """Track a daily plan generated for this pet."""
        raise NotImplementedError

    def get_plans(self) -> list["Plan"]:
        """Return the list of plans tracked for this pet."""
        raise NotImplementedError


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

    def is_recurring(self) -> bool:
        """Return True if this task repeats on a schedule."""
        raise NotImplementedError

    def get_pet(self) -> "Pet":
        """Return the pet this task belongs to."""
        raise NotImplementedError


class PlanEntry:
    """A single task scheduled into a plan at a specific time slot."""

    def __init__(
        self,
        entry_id: str,
        task_id: str,
        plan_id: str,
        start_time: time,
        end_time: time,
        status: str,
    ):
        self.entry_id: str = entry_id
        self.task_id: str = task_id
        self.plan_id: str = plan_id
        self.start_time: time = start_time
        self.end_time: time = end_time
        self.status: str = status

    def overlaps_with(self, other: "PlanEntry") -> bool:
        """Return True if this entry's time slot overlaps another's."""
        raise NotImplementedError

    def mark_complete(self) -> None:
        """Mark this scheduled entry as completed."""
        raise NotImplementedError


class Plan:
    """A daily care plan for a pet, composed of scheduled entries."""

    def __init__(
        self,
        plan_id: str,
        date: date,
        pet_id: str,
        available_minutes: int,
    ):
        self.plan_id: str = plan_id
        self.date: date = date
        self.pet_id: str = pet_id
        self.available_minutes: int = available_minutes
        self._entries: list[PlanEntry] = []

    def add_entry(self, entry: "PlanEntry") -> None:
        """Add a scheduled entry to this plan."""
        raise NotImplementedError

    def total_duration(self) -> int:
        """Return the total duration in minutes of all entries in the plan."""
        raise NotImplementedError

    def explain(self) -> str:
        """Return a human-readable explanation of the plan and its ordering."""
        raise NotImplementedError

    def get_entries(self) -> list["PlanEntry"]:
        """Return the scheduled entries in this plan."""
        raise NotImplementedError


class Scheduler:
    """Algorithmic engine that builds prioritized, conflict-free plans."""

    def generate_plan(
        self,
        pet: "Pet",
        available_minutes: int,
        date: date,
    ) -> "Plan":
        """Build a plan for a pet's tasks within the available time budget."""
        raise NotImplementedError

    def sort_by_priority(self, tasks: list["Task"]) -> list["Task"]:
        """Return tasks ordered by descending priority."""
        raise NotImplementedError

    def filter_by_time(self, tasks: list["Task"], minutes: int) -> list["Task"]:
        """Return the subset of tasks that fit within the time budget."""
        raise NotImplementedError

    def detect_conflicts(self, entries: list["PlanEntry"]) -> list["PlanEntry"]:
        """Return entries whose time slots conflict with others."""
        raise NotImplementedError
