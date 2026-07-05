import streamlit as st

from datetime import date, time

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
pet_by_id = {pet.pet_id: pet for pet in pets}
active_id = st.selectbox(
    "Active pet",
    options=list(pet_by_id.keys()),
    format_func=lambda pid: f"{pet_by_id[pid].name} ({pet_by_id[pid].species})",
)
active_pet = pet_by_id[active_id]

# ---------------------------------------------------------------------------
# Add a Task  ->  Pet.add_task(Task(...))
# ---------------------------------------------------------------------------
st.subheader(f"Add a Task for {active_pet.name}")
col1, col2 = st.columns(2)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
    priority = st.selectbox("Priority", [p.value for p in PriorityEnum], index=2)
    task_due = st.date_input("Due date", value=date.today())
with col2:
    duration = st.number_input(
        "Duration (minutes)", min_value=1, max_value=240, value=20
    )
    recurrence = st.selectbox("Recurrence", [r.value for r in RecurrenceEnum])
    # A scheduled time is optional — it powers time-sorting and conflict
    # detection, but a task can also just sit in the backlog untimed.
    set_time = st.checkbox("Schedule at a specific time", value=True)
    task_time = st.time_input("Scheduled time", value=time(8, 0)) if set_time else None

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
        scheduled_time=task_time,
        due_date=task_due,
    )
    active_pet.add_task(task)
    st.success(f"Added '{task_title}' to {active_pet.name}.")

# ---------------------------------------------------------------------------
# Current tasks  ->  sorted/filtered via the Scheduler, shown as a table.
# ---------------------------------------------------------------------------
tasks = active_pet.get_tasks()
if tasks:
    st.write(f"Current tasks for {active_pet.name}:")

    col1, col2 = st.columns(2)
    with col1:
        sort_choice = st.selectbox(
            "Sort by", ["Priority (high → low)", "Scheduled time"]
        )
    with col2:
        status_choice = st.selectbox("Show", ["all", "pending", "complete"])

    # Filter, then sort — using the Scheduler methods directly.
    view = tasks
    if status_choice != "all":
        view = scheduler.filter_by_status(view, status_choice)
    if sort_choice.startswith("Priority"):
        view = scheduler.sort_by_priority(view)
    else:
        view = scheduler.sort_by_time(view)

    if view:
        # Rendered as columns rather than st.table so each pending row can
        # carry its own "Complete" button (st.table can't hold widgets).
        widths = [1, 3, 1, 1.4, 1.4, 1.4]
        header = st.columns(widths)
        for col, label in zip(
            header, ["Time", "Task", "Min", "Priority", "Status", "Action"]
        ):
            col.markdown(f"**{label}**")

        for t in view:
            row = st.columns(widths)
            row[0].write(t.scheduled_time.strftime("%H:%M") if t.scheduled_time else "—")
            row[1].write(f"{t.name} 🔁" if t.is_recurring() else t.name)
            row[2].write(t.duration_minutes)
            row[3].write(t.priority.value)
            row[4].write("✅ complete" if t.is_complete() else "⏳ pending")
            if t.is_complete():
                row[5].write("—")
            elif row[5].button("Complete", key=f"complete-{t.task_id}"):
                # mark_complete() flips status and, for a recurring task,
                # returns the next occurrence to attach to the pet.
                follow_up = t.mark_complete()
                if follow_up is not None:
                    st.session_state.task_counter += 1
                    follow_up.task_id = f"t{st.session_state.task_counter}"
                    active_pet.add_task(follow_up)
                    st.toast(
                        f"Completed '{t.name}'. Next one queued for "
                        f"{follow_up.due_date}."
                    )
                else:
                    st.toast(f"Completed '{t.name}'.")
                st.rerun()
    else:
        st.info(f"No {status_choice} tasks for {active_pet.name}.")
else:
    st.info(f"No tasks yet for {active_pet.name}. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Conflict check  ->  Scheduler.detect_time_conflicts across all pets.
# An owner can't be in two places at once, so we scan every pet's tasks.
# ---------------------------------------------------------------------------
st.subheader("Schedule Conflicts")
conflicts = scheduler.detect_time_conflicts(owner.get_all_tasks())
if conflicts:
    st.warning(f"Found {len(conflicts)} time conflict(s) across your pets:")
    for message in conflicts:
        # The message already starts with a ⚠️; strip it so st.warning's own
        # icon isn't doubled up.
        st.warning(message.replace("⚠️ ", ""))
else:
    st.success("No scheduling conflicts across your pets. 🎉")

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
        entries = plan.get_entries()
        conflict_entries = [e for e in entries if e.status == "conflict"]

        if not entries:
            st.info(
                "No tasks fit in the available time. Try increasing the "
                "minutes available today."
            )
        elif conflict_entries:
            st.warning(
                f"Schedule built with {len(conflict_entries)} overlapping "
                "entry(ies) — review the highlighted rows."
            )
        else:
            st.success(
                f"Scheduled {len(entries)} task(s) for {active_pet.name} — "
                f"{plan.total_duration()} min total."
            )

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
            with st.expander("Plain-text summary"):
                st.text(plan.explain())
