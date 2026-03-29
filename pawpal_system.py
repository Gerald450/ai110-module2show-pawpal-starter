from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class CareTask:
    title: str
    duration_minutes: int
    priority: Literal["low", "medium", "high"] = "medium"
    frequency: Literal["daily", "weekly", "as-needed"] = "daily"
    preferred_time_of_day: str | None = None
    depends_on: str | None = None
    completed: bool = False

    def get_description(self) -> str:
        """Return a human-readable summary of the task including status, duration, and constraints."""
        status = "done" if self.completed else "pending"
        parts = [f"[{status}] {self.title} ({self.duration_minutes} min, {self.priority} priority, {self.frequency})"]
        if self.preferred_time_of_day:
            parts.append(f"preferred: {self.preferred_time_of_day}")
        if self.depends_on:
            parts.append(f"requires: {self.depends_on}")
        return " — ".join(parts)

    def fits_in_budget(self, remaining_minutes: int) -> bool:
        """Return True if this task's duration fits within the remaining available time."""
        return self.duration_minutes <= remaining_minutes

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

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

    def __init__(self, owner: Owner):
        self.owner = owner

    def generate_schedule(self) -> list[CareTask]:
        """Return an ordered list of tasks that fit the owner's time budget, respecting priority and dependencies."""
        pending = [t for t in self.owner.get_all_tasks() if not t.completed]

        # Resolve depends_on: tasks whose dependency hasn't been scheduled yet go last
        def sort_key(task: CareTask):
            return (self.PRIORITY_ORDER.get(task.priority, 1), task.depends_on is not None, task.title)

        sorted_tasks = sorted(pending, key=sort_key)

        schedule: list[CareTask] = []
        scheduled_titles: set[str] = set()
        remaining = self.owner.available_minutes

        for task in sorted_tasks:
            if task.depends_on and task.depends_on not in scheduled_titles:
                continue
            if task.fits_in_budget(remaining):
                schedule.append(task)
                scheduled_titles.add(task.title)
                remaining -= task.duration_minutes

        return schedule

    def mark_task_complete(self, title: str) -> None:
        """Find the task with the given title across all pets and mark it complete."""
        for task in self.owner.get_all_tasks():
            if task.title == title:
                task.mark_complete()
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

        all_pending = [t for t in self.owner.get_all_tasks() if not t.completed]
        skipped = [t for t in all_pending if t not in schedule]
        if skipped:
            lines.append("\nSkipped (time or unmet dependency):")
            for task in skipped:
                lines.append(f"  - {task.title}")

        lines.append(f"\nTotal time scheduled: {total} min of {self.owner.available_minutes} min available.")
        return "\n".join(lines)
