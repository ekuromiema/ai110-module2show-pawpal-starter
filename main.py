"""PawPal+ demo driver.

Builds a small world (one owner, two pets, several tasks) and prints
each pet's generated schedule for today.
"""

from datetime import date

from pawpal_system import (
    Owner,
    Pet,
    PriorityEnum,
    RecurrenceEnum,
    Scheduler,
    Task,
)


def build_world() -> Owner:
    """Create an owner with two pets and a handful of care tasks."""
    owner = Owner(owner_id="o1", name="Alex")

    biscuit = Pet(pet_id="p1", name="Biscuit", species="Golden Retriever", owner_id="o1")
    mochi = Pet(pet_id="p2", name="Mochi", species="Tabby Cat", owner_id="o1")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # Biscuit's tasks
    biscuit.add_task(
        Task("t1", "Morning walk", 30, PriorityEnum.HIGH, RecurrenceEnum.DAILY, "p1")
    )
    biscuit.add_task(
        Task("t2", "Breakfast", 10, PriorityEnum.CRITICAL, RecurrenceEnum.DAILY, "p1")
    )
    biscuit.add_task(
        Task("t3", "Nail trim", 15, PriorityEnum.LOW, RecurrenceEnum.MONTHLY, "p1")
    )

    # Mochi's tasks
    mochi.add_task(
        Task("t4", "Medication", 5, PriorityEnum.CRITICAL, RecurrenceEnum.DAILY, "p2")
    )
    mochi.add_task(
        Task("t5", "Feeding", 10, PriorityEnum.HIGH, RecurrenceEnum.DAILY, "p2")
    )
    mochi.add_task(
        Task("t6", "Play session", 20, PriorityEnum.MEDIUM, RecurrenceEnum.WEEKLY, "p2")
    )

    return owner


def main() -> None:
    owner = build_world()
    scheduler = Scheduler()
    today = date.today()

    print("=" * 48)
    print(f"Today's Schedule — {today.isoformat()}")
    print(f"Owner: {owner.name}")
    print("=" * 48)

    for pet in owner.get_pets():
        # Give each pet a 60-minute care budget for the day.
        plan = scheduler.generate_plan(pet, available_minutes=60, date=today)
        print()
        print(plan.explain())
        print(f"  Total scheduled time: {plan.total_duration()} min")


if __name__ == "__main__":
    main()
