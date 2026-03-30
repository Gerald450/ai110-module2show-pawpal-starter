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

## Smarter Scheduling

The scheduler was extended with four algorithmic improvements beyond the original priority-based sort:

**Time-of-day sorting (`Scheduler.sort_by_time`)** — Tasks can carry an optional `time` field in `"HH:MM"` format. `sort_by_time` uses Python's `sorted()` with a lambda that converts each time string to an `(hour, minute)` integer tuple, enabling correct numeric comparison. Tasks with no time set default to `(24, 0)` and sort to the end.

**Task filtering (`Owner.filter_tasks`)** — Returns `(pet_name, CareTask)` pairs narrowed by pet name, completion status (`"pending"` / `"completed"` / `"all"`), or both. Each result carries the pet name explicitly because `CareTask` holds no back-reference to its pet — the caller always knows where a task came from.

**Recurring task auto-renewal (`CareTask.renew` + `Scheduler.mark_task_complete`)** — When a `daily` or `weekly` task is marked complete, `mark_task_complete` appends a fresh copy to the same pet's task list via `CareTask.renew`. The renewed copy uses `dataclasses.replace` and sets `last_done_date=today` so `is_due_today()` suppresses it until the correct next cycle — tomorrow for daily tasks, seven days later for weekly ones. `as-needed` tasks are not auto-renewed.

**Conflict detection (`Scheduler.detect_conflicts`)** — Scans all tasks due today and reports three types of problems as warning strings (never raises):
- *Exact-time collision* — two or more tasks share the same `HH:MM` start time, across any pet.
- *Time-slot overload* — tasks in the same named slot (morning / afternoon / evening) whose combined duration exceeds the per-slot budget (`available_minutes ÷ 3`, minimum 60 min).
- *Dependency-ordering conflict* — a task's required predecessor is assigned to a later time slot.

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
