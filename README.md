# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## ✨ Features

The scheduling engine (`Scheduler` in `pawpal_system.py`) implements the following algorithms:

- **Sorting by priority** — orders tasks from `critical` → `low`; ties keep their original order (stable sort).
- **Sorting by time** — orders tasks by scheduled clock time (earliest first), pushing untimed tasks to the end.
- **Status filtering** — shows only tasks in a given state (e.g. `pending` vs `complete`).
- **Pet filtering** — filters tasks by a pet's name or its raw `pet_id`.
- **Time-budgeted planning** — greedily packs the highest-priority tasks that fit within the minutes available for the day, dropping ones that don't.
- **Conflict warnings** — flags tasks whose time windows overlap on the same day, *including across different pets* (an owner can't be in two places at once).
- **Daily / weekly / monthly recurrence** — completing a recurring task automatically generates the next pending occurrence (next day / +7 days / +30 days).
- **Daily schedule generation** — lays out a prioritized, back-to-back plan starting at 08:00 that never runs past midnight, and can explain its reasoning in plain text.

## 🖥️ Sample Output

```
================================================
Today's Schedule — 2026-07-04
Owner: Alex
================================================

Daily plan for Biscuit (Golden Retriever):
  08:00 — Breakfast (10 min) [priority: critical]
  08:10 — Morning walk (30 min) [priority: high]
  08:40 — Nail trim (15 min) [priority: low]
  Total scheduled time: 55 min

Daily plan for Mochi (Tabby Cat):
  08:00 — Medication (5 min) [priority: critical]
  08:05 — Feeding (10 min) [priority: high]
  08:15 — Play session (20 min) [priority: medium]
  Total scheduled time: 35 min
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest
```

Test Description:

Core object behavior
Marking a PlanEntry complete flips its status.
Adding a task to a Pet grows its task list.

Sorting
sort_by_priority orders critical→low, and is stable on ties (equal priorities keep input order).
sort_by_time orders earliest-first and pushes untimed tasks to the end.
Both sorts handle an empty list without erroring.

Filtering
filter_by_status keeps only matching statuses.
filter_by_pet matches by pet name or raw pet_id, and matches all pets sharing a name (documents that name isn't unique).

Recurring tasks
Completing a daily task creates a pending copy due the next day; weekly rolls +7 days.
Monthly uses a flat 30-day delta (Jan 31 → Mar 2 — pins the documented approximation).
No due_date falls back to today + one interval.
Completing twice keeps advancing the date.
One-off (non-recurring) tasks return no follow-up.

Conflict detection
Flags overlapping tasks and identical start times on the same day.
Does not flag back-to-back tasks, different days, or same time on different days.
Skips untimed tasks instead of crashing.

Time budgeting (filter_by_time)
Drops a task larger than the budget, keeps an exact fit, keeps nothing on a zero budget, and greedily packs a smaller task even after skipping an over-budget one.

Plan generation
Empty pet → empty plan with a "(no tasks scheduled)" summary.
Lays entries out back-to-back from 08:00.
The midnight-wrap fix: a task that can't finish before midnight is dropped, and no entry ever ends before it starts.

Sample test output:

```
=============================================================================== test session starts ================================================================================
platform win32 -- Python 3.13.13, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Owner\ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 29 items                                                                                                                                                                  

tests\test_pawpal.py .............................                                                                                                                            [100%]

================================================================================ 29 passed in 0.08s ================================================================================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_by_priority()` | Order tasks by scheduled clock time or from highest to lowest priority. |
| Filtering | `Scheduler.filter_by_status()`, `Scheduler.filter_by_pet()`, `Scheduler.filter_by_time()` | Keep tasks by completion status (e.g. `"pending"`), by pet (name or `pet_id`), or keep only tasks that fit a time budget. |
| Conflict handling | `Scheduler.detect_time_conflicts()`, `Scheduler.detect_conflicts()` | Flag tasks whose time windows overlap (same day, across pets) with warning messages; also checks overlaps on `PlanEntry` slots in a generated plan. |
| Recurring tasks | `Task.mark_complete()`, `Task.next_occurrence()` | Completing a recurring task auto-creates the next pending copy. |

## 📸 Demo Walkthrough

PawPal+ runs as a Streamlit web app. Launch it with:

```bash
streamlit run app.py
```

### What you can do in the UI

- **Set the owner** — edit the owner's name at the top.
- **Add pets** — enter a name and species and click **Add pet**; switch between pets with the **Active pet** selector.
- **Add tasks** — for the active pet, set a title, priority, duration, recurrence, an optional due date, and an optional scheduled time.
- **Sort & filter the task list** — reorder tasks by **priority** or **scheduled time**, and filter to show `all`, `pending`, or `complete` tasks. The list renders as a clean table.
- **See conflict warnings** — a dedicated section scans every pet's tasks and warns about overlapping times.
- **Build a schedule** — set the minutes available today and click **Generate schedule** to get a prioritized, time-bounded plan with a plain-text explanation.

### Example workflow

1. **Add a pet** — type `Biscuit`, choose `dog`, and click **Add pet**.
2. **Add a couple of tasks** — e.g. `Breakfast` (critical, 10 min, daily, 08:00) and `Morning walk` (high, 30 min, daily, 08:00).
3. **Review the task list** — sort by **priority** to see `Breakfast` rise above `Morning walk`.
4. **Check conflicts** — because both tasks are scheduled at 08:00, the **Schedule Conflicts** section shows a warning that they overlap.
5. **Generate today's schedule** — set `60` minutes available and click **Generate schedule**. PawPal+ lays the tasks out back-to-back from 08:00 and shows the total scheduled time.
6. **Complete a recurring task** — marking a daily task done automatically queues its copy for tomorrow.

### Key `Scheduler` behaviors on display

- **Priority sorting** puts `critical` tasks first, so the most important care happens earliest.
- **Time budgeting** keeps only the tasks that fit the minutes available, dropping the rest.
- **Conflict warnings** surface overlapping times before you commit to a plan.
- **Recurrence** rolls completed daily/weekly/monthly tasks forward to their next occurrence.

### Sample CLI output

`main.py` builds a small demo world (one owner, two pets, several tasks) and prints each pet's generated schedule:

```bash
python main.py
```

```
================================================
Today's Schedule — 2026-07-04
Owner: Alex
================================================

Daily plan for Biscuit (Golden Retriever):
  08:00 — Breakfast (10 min) [priority: critical]
  08:10 — Morning walk (30 min) [priority: high]
  08:40 — Nail trim (15 min) [priority: low]
  Total scheduled time: 55 min

Daily plan for Mochi (Tabby Cat):
  08:00 — Medication (5 min) [priority: critical]
  08:05 — Feeding (10 min) [priority: high]
  08:15 — Play session (20 min) [priority: medium]
  Total scheduled time: 35 min
```

Notice the ordering: within each pet, `critical` tasks are scheduled first and lower-priority tasks follow — the priority-sorting algorithm in action.