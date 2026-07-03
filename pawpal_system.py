"""PawPal+ — Smart Pet Care Management System.

Class skeleton scaffolded from diagrams/uml_draft.mmd.
Attributes and method signatures only; method bodies are left as stubs
to be implemented.

Relationships (from UML):
  Owner "1" --> "*" Pet   : owns
  Pet   "1" --> "*" Task  : has
  Plan  "1" --> "*" Task  : contains
"""

from __future__ import annotations

from datetime import date


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


class Pet:
    """A pet belonging to an owner, with a set of care tasks."""

    def __init__(self, pet_id: str, name: str, species: str, owner_id: str):
        self.pet_id: str = pet_id
        self.name: str = name
        self.species: str = species
        self.owner_id: str = owner_id
        self._tasks: list[Task] = []

    def add_task(self, task: "Task") -> None:
        """Attach a care task to this pet."""
        raise NotImplementedError

    def get_tasks(self) -> list["Task"]:
        """Return the list of tasks for this pet."""
        raise NotImplementedError


class Task:
    """A single care task (feeding, walk, medication, appointment, ...)."""

    def __init__(
        self,
        task_id: str,
        name: str,
        duration_minutes: int,
        priority: str,
        recurrence: str,
        pet_id: str,
    ):
        self.task_id: str = task_id
        self.name: str = name
        self.duration_minutes: int = duration_minutes
        self.priority: str = priority
        self.recurrence: str = recurrence
        self.pet_id: str = pet_id

    def is_recurring(self) -> bool:
        """Return True if this task repeats on a schedule."""
        raise NotImplementedError


class Plan:
    """A daily care plan for a pet, composed of scheduled tasks."""

    def __init__(self, plan_id: str, date: date, pet_id: str):
        self.plan_id: str = plan_id
        self.date: date = date
        self.pet_id: str = pet_id
        self._entries: list[Task] = []

    def add_entry(self, entry: "Task") -> None:
        """Add a task entry to this plan."""
        raise NotImplementedError

    def total_duration(self) -> int:
        """Return the total duration in minutes of all entries in the plan."""
        raise NotImplementedError

    def explain(self) -> str:
        """Return a human-readable explanation of the plan and its ordering."""
        raise NotImplementedError
