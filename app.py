import streamlit as st

from datetime import date

from pawpal_system import (
    Owner,
    Pet,
    PriorityEnum,
    RecurrenceEnum,
    Scheduler,
    Task,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Interactive demo for **PawPal+**, a pet care planning assistant. Add pets and
their care tasks, then generate a prioritized, time-bounded daily schedule.
"""
)

# ---------------------------------------------------------------------------
# Session "vault": create these once and reuse them across reruns. Without
# this guard, Streamlit would rebuild the Owner (and lose every pet/task) on
# each interaction.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(owner_id="o1", name="Jordan")
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()
if "pet_counter" not in st.session_state:
    st.session_state.pet_counter = 0
if "task_counter" not in st.session_state:
    st.session_state.task_counter = 0

owner = st.session_state.owner
scheduler = st.session_state.scheduler

# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------
st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

st.divider()

# ---------------------------------------------------------------------------
# Add a Pet  ->  Owner.add_pet(Pet(...))
# ---------------------------------------------------------------------------
st.subheader("Add a Pet")
col1, col2 = st.columns(2)
with col1:
    new_pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    st.session_state.pet_counter += 1
    pet_id = f"p{st.session_state.pet_counter}"
    owner.add_pet(Pet(pet_id, new_pet_name, new_pet_species, owner.owner_id))
    st.success(f"Added {new_pet_name} ({new_pet_species}).")

pets = owner.get_pets()
if not pets:
    st.info("Add a pet above to get started.")
    st.stop()

st.divider()

# ---------------------------------------------------------------------------
# Pick the pet we're currently working with.
# ---------------------------------------------------------------------------
active_pet = st.selectbox(
    "Active pet",
    options=pets,
    format_func=lambda pet: f"{pet.name} ({pet.species})",
)

# ---------------------------------------------------------------------------
# Add a Task  ->  Pet.add_task(Task(...))
# ---------------------------------------------------------------------------
st.subheader(f"Add a Task for {active_pet.name}")
col1, col2 = st.columns(2)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
    priority = st.selectbox("Priority", [p.value for p in PriorityEnum], index=2)
with col2:
    duration = st.number_input(
        "Duration (minutes)", min_value=1, max_value=240, value=20
    )
    recurrence = st.selectbox("Recurrence", [r.value for r in RecurrenceEnum])

if st.button("Add task"):
    st.session_state.task_counter += 1
    task_id = f"t{st.session_state.task_counter}"
    task = Task(
        task_id=task_id,
        name=task_title,
        duration_minutes=int(duration),
        priority=PriorityEnum(priority),
        recurrence=RecurrenceEnum(recurrence),
        pet_id=active_pet.pet_id,
    )
    active_pet.add_task(task)
    st.success(f"Added '{task_title}' to {active_pet.name}.")

# Show the active pet's current tasks (Pet.get_tasks()).
tasks = active_pet.get_tasks()
if tasks:
    st.write(f"Current tasks for {active_pet.name}:")
    st.table(
        [
            {
                "title": t.name,
                "duration_minutes": t.duration_minutes,
                "priority": t.priority.value,
                "recurrence": t.recurrence.value,
                "recurring": t.is_recurring(),
            }
            for t in tasks
        ]
    )
else:
    st.info(f"No tasks yet for {active_pet.name}. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Build Schedule  ->  Scheduler.generate_plan(...) + Plan.explain()
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")
available_minutes = st.number_input(
    "Available minutes today", min_value=1, max_value=1440, value=60
)

if st.button("Generate schedule"):
    if not tasks:
        st.warning(f"Add at least one task for {active_pet.name} first.")
    else:
        plan = scheduler.generate_plan(
            active_pet, int(available_minutes), date.today()
        )
        st.text(plan.explain())
        st.caption(f"Total scheduled time: {plan.total_duration()} min")

        entries = plan.get_entries()
        if entries:
            st.table(
                [
                    {
                        "start": e.start_time.strftime("%H:%M"),
                        "end": e.end_time.strftime("%H:%M"),
                        "task": e.task.name if e.task else e.task_id,
                        "minutes": e.duration_minutes(),
                        "status": e.status,
                    }
                    for e in entries
                ]
            )
