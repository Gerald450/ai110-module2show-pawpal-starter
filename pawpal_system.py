from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from typing import Literal


@dataclass
class CareTask:
    title: str
    duration_minutes: int
    priority: Literal["low", "medium", "high"] = "medium"
    frequency: Literal["daily", "weekly", "as-needed"] = "daily"
    preferred_time_of_day: str | None = None
    time: str | None = None          # specific start time in "HH:MM" format, e.g. "08:30"
    depends_on: str | None = None
    completed: bool = False
    last_done_date: date | None = None

    def get_description(self) -> str:
        """Return a human-readable summary of the task including status, duration, and constraints."""
        status = "done" if self.completed else "pending"
        parts = [f"[{status}] {self.title} ({self.duration_minutes} min, {self.priority} priority, {self.frequency})"]
        if self.preferred_time_of_day:
            parts.append(f"preferred: {self.preferred_time_of_day}")
        if self.depends_on:
            parts.append(f"requires: {self.depends_on}")
        if self.last_done_date:
            parts.append(f"last done: {self.last_done_date}")
        return " — ".join(parts)

    def fits_in_budget(self, remaining_minutes: int) -> bool:
        """Return True if this task's duration fits within the remaining available time."""
        return self.duration_minutes <= remaining_minutes

    def is_due_today(self) -> bool:
        """Return True if this task should appear on today's schedule.

        - daily: due if not completed and not already done today.
        - weekly: due only if never done or last done >= 7 days ago.
        - as-needed: due whenever not completed.
        """
        if self.completed:
            return False
        if self.frequency == "daily":
            return self.last_done_date != date.today()
        if self.frequency == "weekly":
            if self.last_done_date is None:
                return True
            return (date.today() - self.last_done_date).days >= 7
        return True

    def renew(self) -> CareTask:
        """Return a fresh copy of this task reset for its next occurrence.

        The new instance is not completed and carries last_done_date=today so
        that is_due_today() suppresses it until the proper next cycle:
        - daily  → reappears tomorrow
        - weekly → reappears in 7 days
        """
        return replace(self, completed=False, last_done_date=date.today())

    def mark_complete(self) -> None:
        """Mark this task as completed and record today's date."""
        self.completed = True
        self.last_done_date = date.today()

    def reset(self) -> None:
        """Reset this task to pending so it can be scheduled again."""
        self.completed = False


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: list[str] = field(default_factory=list)
    tasks: list[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        """Add a care task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove the task matching the given title from this pet's task list."""
        self.tasks = [t for t in self.tasks if t.title != title]

    def get_pending_tasks(self) -> list[CareTask]:
        """Return all tasks that have not yet been marked complete."""
        return [t for t in self.tasks if not t.completed]

    def update_special_needs(self, needs: list[str]) -> None:
        """Replace the pet's special needs list with the provided list."""
        self.special_needs = needs

    def get_description(self) -> str:
        """Return a human-readable profile of the pet including species, age, and special needs."""
        needs = ", ".join(self.special_needs) if self.special_needs else "none"
        return f"{self.name} is a {self.age}-year-old {self.species}. Special needs: {needs}."


class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: list[str] = None):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences or []
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[CareTask]:
        """Return a flat list of every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def filter_tasks(
        self,
        pet_name: str | None = None,
        status: Literal["all", "pending", "completed"] = "all",
    ) -> list[tuple[str, CareTask]]:
        """Return (pet_name, task) pairs filtered by pet name and/or completion status.

        Args:
            pet_name: When provided, only tasks belonging to the pet with this
                exact name are returned.  When None (default), tasks from all
                pets are included.
            status:   "pending"   — only tasks where completed is False.
                      "completed" — only tasks where completed is True.
                      "all"       — no status filter applied (default).

        Returns:
            A list of (pet_name, CareTask) tuples so callers always know which
            pet a task belongs to, since CareTask itself holds no back-reference
            to its owner pet.
        """
        results = []
        for pet in self.pets:
            if pet_name and pet.name != pet_name:
                continue
            for task in pet.tasks:
                if status == "pending" and task.completed:
                    continue
                if status == "completed" and not task.completed:
                    continue
                results.append((pet.name, task))
        return results

    def update_available_time(self, minutes: int) -> None:
        """Update the number of minutes the owner has available today."""
        self.available_minutes = minutes

    def update_preferences(self, preferences: list[str]) -> None:
        """Replace the owner's scheduling preferences with the provided list."""
        self.preferences = preferences

    def get_summary(self) -> str:
        """Return a one-line summary of the owner's available time, pets, and preferences."""
        preferences = ", ".join(self.preferences) if self.preferences else "none"
        pet_names = ", ".join(p.name for p in self.pets) if self.pets else "no pets yet"
        return (
            f"{self.name} has {self.available_minutes} min available today. "
            f"Pets: {pet_names}. Preferences: {preferences}."
        )


class Scheduler:
    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
    TIME_SLOT_ORDER = {"morning": 0, "afternoon": 1, "evening": 2}

    def __init__(self, owner: Owner):
        self.owner = owner

    def sort_by_time(self, tasks: list[CareTask]) -> list[CareTask]:
        """Return tasks sorted ascending by their 'HH:MM' time attribute.

        The lambda splits each time string on ':' and converts the parts to
        integers, producing a (hour, minute) tuple that Python can compare
        numerically.  Tasks with no time set are placed at the end by
        defaulting to (24, 0), which is always greater than any valid time.
        """
        return sorted(
            tasks,
            key=lambda task: (
                tuple(int(x) for x in task.time.split(":"))
                if task.time
                else (24, 0)
            ),
        )

    def generate_schedule(self) -> list[CareTask]:
        """Return an ordered list of tasks that fit the owner's time budget.

        Tasks are sorted by priority then preferred time of day. A second pass
        retries tasks that were skipped only because their dependency had not
        yet been scheduled (it may be satisfied after the first pass).
        """
        due = [t for t in self.owner.get_all_tasks() if t.is_due_today()]

        def sort_key(task: CareTask):
            slot = self.TIME_SLOT_ORDER.get(task.preferred_time_of_day or "", 3)
            return (self.PRIORITY_ORDER.get(task.priority, 1), slot, task.depends_on is not None, task.title)

        sorted_tasks = sorted(due, key=sort_key)

        schedule: list[CareTask] = []
        scheduled_titles: set[str] = set()
        remaining = self.owner.available_minutes
        held_for_retry: list[CareTask] = []

        # First pass — skip tasks with unsatisfied dependencies for retry.
        for task in sorted_tasks:
            if task.depends_on and task.depends_on not in scheduled_titles:
                held_for_retry.append(task)
                continue
            if task.fits_in_budget(remaining):
                schedule.append(task)
                scheduled_titles.add(task.title)
                remaining -= task.duration_minutes
            else:
                held_for_retry.append(task)

        # Second pass — retry tasks whose dependency is now in the schedule.
        for task in held_for_retry:
            if task.depends_on and task.depends_on not in scheduled_titles:
                continue
            if task.fits_in_budget(remaining):
                schedule.append(task)
                scheduled_titles.add(task.title)
                remaining -= task.duration_minutes

        return schedule

    def detect_conflicts(self) -> list[str]:
        """Return human-readable descriptions of scheduling conflicts.

        Three conflict types are detected:
        - Exact-time collision: two or more tasks (same or different pets)
          share the same HH:MM start time.
        - Time-slot overload: tasks in the same preferred time slot whose
          combined duration exceeds the slot budget (available_minutes // 3,
          minimum 60 min).
        - Dependency-ordering: a task's required predecessor is scheduled for
          a later time slot.
        """
        conflicts: list[str] = []

        # Build (pet_name, task) pairs for all due tasks so pet context is
        # available without a second lookup.
        due_pairs: list[tuple[str, CareTask]] = [
            (pet.name, task)
            for pet in self.owner.pets
            for task in pet.tasks
            if task.is_due_today()
        ]
        due = [task for _, task in due_pairs]

        # --- Exact-time collision ---
        # Group (pet_name, task) pairs by their HH:MM time value, then flag
        # any bucket that contains more than one task.
        time_buckets: dict[str, list[tuple[str, CareTask]]] = {}
        for pet_name, task in due_pairs:
            if task.time:
                time_buckets.setdefault(task.time, []).append((pet_name, task))

        for hhmm, pairs in time_buckets.items():
            if len(pairs) > 1:
                labels = ", ".join(
                    f"'{t.title}' ({pet_name})" for pet_name, t in pairs
                )
                conflicts.append(
                    f"WARNING: Exact-time collision at {hhmm} — {labels} "
                    f"are all scheduled at the same time."
                )

        # --- Time-slot overload ---
        slot_budget = max(self.owner.available_minutes // 3, 60)
        slots: dict[str, list[CareTask]] = {}
        for task in due:
            if task.preferred_time_of_day:
                slots.setdefault(task.preferred_time_of_day, []).append(task)

        for slot, tasks in slots.items():
            total = sum(t.duration_minutes for t in tasks)
            if total > slot_budget:
                names = ", ".join(t.title for t in tasks)
                conflicts.append(
                    f"Time-slot overload ({slot}): {names} — "
                    f"{total} min total exceeds {slot_budget} min slot budget."
                )

        # --- Dependency-ordering conflict ---
        task_map = {t.title: t for t in due}
        for task in due:
            if not task.depends_on or task.depends_on not in task_map:
                continue
            dep = task_map[task.depends_on]
            task_slot = self.TIME_SLOT_ORDER.get(task.preferred_time_of_day or "", 3)
            dep_slot = self.TIME_SLOT_ORDER.get(dep.preferred_time_of_day or "", 3)
            if dep_slot > task_slot:
                conflicts.append(
                    f"Ordering conflict: '{task.title}' "
                    f"({task.preferred_time_of_day or 'unspecified'}) depends on "
                    f"'{dep.title}' ({dep.preferred_time_of_day or 'unspecified'}), "
                    f"which is in a later time slot."
                )

        return conflicts

    def mark_task_complete(self, title: str) -> None:
        """Mark a task complete and auto-schedule its next occurrence.

        For daily and weekly tasks a renewed copy is appended to the same
        pet's task list so the recurrence appears on future schedules
        without any manual re-entry.  as-needed tasks are not renewed.
        """
        for pet in self.owner.pets:
            for task in pet.tasks:
                if task.title == title:
                    task.mark_complete()
                    if task.frequency in ("daily", "weekly"):
                        pet.add_task(task.renew())
                    return

    def explain_plan(self) -> str:
        """Return a human-readable daily plan showing scheduled tasks, skipped tasks, and total time used."""
        schedule = self.generate_schedule()

        if not schedule:
            return "No tasks could be scheduled within the available time."

        lines = [f"Daily plan for {self.owner.name} "
                 f"({self.owner.available_minutes} min available):\n"]

        total = 0
        for i, task in enumerate(schedule, 1):
            lines.append(f"  {i}. {task.get_description()}")
            total += task.duration_minutes

        all_due = [t for t in self.owner.get_all_tasks() if t.is_due_today()]
        skipped = [t for t in all_due if t not in schedule]
        if skipped:
            lines.append("\nSkipped (time or unmet dependency):")
            for task in skipped:
                lines.append(f"  - {task.title}")

        conflicts = self.detect_conflicts()
        if conflicts:
            lines.append("\nConflicts detected:")
            for c in conflicts:
                lines.append(f"  ! {c}")

        lines.append(f"\nTotal time scheduled: {total} min of {self.owner.available_minutes} min available.")
        return "\n".join(lines)
