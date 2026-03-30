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

## Testing PawPal+

### Running the test suite

```bash
python -m pytest tests/test_pawpal.py -v
```

Remove `-v` for a compact summary. All 37 tests should pass in under a second.

### What the tests cover

The suite is organised into four groups:

**Core model** (`CareTask`, `Pet`, `Owner`) — 16 tests
Verifies that tasks report their budget fit correctly, mark themselves complete, reset cleanly, and produce accurate descriptions. Covers pet task management (add, remove, pending filter) and owner state (available time, pet registration, summary output).

**Scheduler — scheduling logic** — 8 tests
Confirms that high-priority tasks are placed first, tasks exceeding the time budget are skipped, `depends_on` constraints are respected (dependent task always follows its prerequisite), and completed tasks are excluded from the generated plan.

**Sorting correctness** — 4 tests
Proves `sort_by_time` returns tasks in true chronological order regardless of insertion order. Specifically checks that tasks within the same hour sort by minute (guarding against accidental string sort where `"08:45"` would precede `"08:05"`), that tasks with no `time` value always appear last, and that no tasks are lost during sorting.

**Recurrence logic** — 5 tests
Confirms that calling `mark_task_complete` on a `daily` or `weekly` task appends a second task to the pet's list. Checks that the renewed task starts as pending, and that `is_due_today()` returns `False` on it immediately — preventing the same task from appearing twice on today's schedule. Also verifies that `as-needed` tasks produce no renewal.

**Conflict detection** — 4 tests
Verifies that `detect_conflicts` flags an exact `HH:MM` collision between tasks on different pets, between tasks on the same pet, and that distinct times produce no false positive. Confirms the "lightweight" contract: the method always returns `list[str]` and never raises an exception.

### Confidence level

★★★★☆ (4 / 5)

The core scheduling contract — priority ordering, dependency resolution, budget enforcement, and recurrence — is fully covered and all 37 tests pass reliably. The confidence gap is in areas deliberately left untested: duration-overlap conflicts (the scheduler checks only exact start-time collisions, not whether a 30-minute task at 07:30 overlaps a task starting at 07:45), edge cases around multi-pet dependency chains, and any behaviour that lives in the Streamlit UI layer (`app.py`) rather than the business logic.

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
