# 🐾 PawPal+

A daily pet care planner built with Python and Streamlit. PawPal+ helps busy pet owners stay consistent with their animals' routines by generating a prioritised, conflict-aware daily schedule from a list of care tasks.

---

## 📸 Demo

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank"><img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

---

## ✨ Features

### Multi-pet support
Register any number of pets under a single owner profile. Each pet holds its own task list independently, and every scheduling and filtering operation works across all pets simultaneously.

### Priority-based scheduling
Tasks carry a priority level (`high`, `medium`, or `low`). The scheduler sorts all due tasks by priority before placing them into the daily plan, ensuring critical care (medication, feeding) is never pushed aside by lower-importance tasks.

### Dependency constraints
A task can declare `depends_on` — the title of another task that must be scheduled first. The scheduler performs a two-pass algorithm: a first pass places tasks with satisfied dependencies, and a second pass retries tasks whose dependency landed in the first pass. This guarantees, for example, that medication always follows feeding even when both are high priority.

### Sorting by time (`Scheduler.sort_by_time`)
Tasks can carry an optional start time in `HH:MM` format. `sort_by_time` uses Python's `sorted()` with a lambda that converts each time string to an `(hour, minute)` integer tuple for correct numeric comparison — preventing the string-sort trap where `"08:45"` would incorrectly precede `"08:05"`. Tasks without a time set sort to the end by defaulting to `(24, 0)`.

### Task filtering by pet and status (`Owner.filter_tasks`)
The task list can be narrowed by pet name, completion status (`pending` / `completed` / `all`), or both at once. Results are returned as `(pet_name, CareTask)` pairs so the caller always knows which pet a task belongs to, since `CareTask` holds no back-reference to its pet.

### Daily recurrence auto-renewal (`CareTask.renew`)
When a `daily` or `weekly` task is marked complete via `Scheduler.mark_task_complete`, a fresh copy is automatically appended to the same pet's task list using `dataclasses.replace`. The renewed copy sets `last_done_date=today`, which causes `is_due_today()` to suppress it for the correct interval — tomorrow for daily tasks, seven days later for weekly ones. `as-needed` tasks are never auto-renewed.

### Conflict detection (`Scheduler.detect_conflicts`)
Scans all tasks due today and surfaces three categories of problems as plain warning strings — the method never raises an exception:

- **Exact-time collision** — two or more tasks (across any pet) share the same `HH:MM` start time.
- **Time-slot overload** — tasks assigned to the same named slot (`morning` / `afternoon` / `evening`) whose combined duration exceeds the per-slot budget (`available_minutes ÷ 3`, minimum 60 min).
- **Dependency-ordering conflict** — a task's required predecessor is assigned to a later time slot, making the dependency impossible to honour.

### Frequency-aware scheduling (`CareTask.is_due_today`)
Each task carries a `frequency` of `daily`, `weekly`, or `as-needed`. `is_due_today()` uses `last_done_date` to decide whether a task belongs on today's plan — weekly tasks suppress themselves for seven days after completion, and daily tasks suppress themselves for the rest of the day after renewal.

---

## 🚀 Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

### Run from the terminal (no UI)

```bash
python main.py
```

---

## 🧪 Testing PawPal+

### Run the test suite

```bash
python -m pytest tests/test_pawpal.py -v
```

Remove `-v` for a compact summary. All 37 tests pass in under a second.

### What the tests cover

| Group | Tests | What is verified |
|---|---|---|
| Core model (`CareTask`, `Pet`, `Owner`) | 16 | Budget fit, mark complete, reset, descriptions, task add/remove, pending filter, owner state |
| Scheduler — scheduling logic | 8 | Priority order, budget enforcement, `depends_on` ordering, completed-task exclusion |
| Sorting correctness | 4 | Chronological order, minute-level sort within the same hour, no tasks dropped, timed tasks before untimed |
| Recurrence logic | 5 | Renewal created on complete, renewal starts pending, renewal not due today, weekly renewal, no renewal for `as-needed` |
| Conflict detection | 4 | Cross-pet collision, same-pet collision, no false positive for distinct times, always returns `list[str]` |

### Confidence level

★★★★☆ (4 / 5)

Core scheduling — priority ordering, dependency resolution, budget enforcement, and recurrence — is fully covered. The gap is in duration-overlap detection (only exact `HH:MM` collisions are caught, not overlapping windows), multi-pet dependency chains, and the Streamlit UI layer.

---

## 🗂 Project structure

```
pawpal_system.py   — CareTask, Pet, Owner, Scheduler classes
app.py             — Streamlit UI
main.py            — terminal demo (sorting, filtering, conflict output)
tests/
  test_pawpal.py   — 37-test automated suite
reflection.md      — design decisions, UML, tradeoffs
uml_final.png      — final class diagram
```

---

## Smarter Scheduling — implementation notes

Beyond the starter skeleton, four algorithmic improvements were added:

**`Scheduler.sort_by_time`** — lambda-based `(hour, minute)` tuple sort; tasks without a time use `(24, 0)` as a sentinel.

**`Owner.filter_tasks`** — single-pass loop with two independent guard clauses (one for pet name, one for status); returns tuples to preserve pet context.

**`CareTask.renew` + `Scheduler.mark_task_complete`** — `dataclasses.replace` creates a shallow copy with only `completed` and `last_done_date` overridden; the scheduler locates the owning pet by iterating `owner.pets` so the renewal is appended to the correct list.

**`Scheduler.detect_conflicts`** — builds `due_pairs: list[tuple[str, CareTask]]` in a single comprehension to preserve pet context, then runs three independent detection passes (exact-time bucket, slot-budget sum, dependency-slot comparison) and collects all results into one flat list.
