import pytest
from pawpal_system import CareTask, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# CareTask
# ---------------------------------------------------------------------------

def test_care_task_fits_in_budget_true():
    task = CareTask("Walk", duration_minutes=20)
    assert task.fits_in_budget(30) is True


def test_care_task_fits_in_budget_false():
    task = CareTask("Bath", duration_minutes=45)
    assert task.fits_in_budget(30) is False


def test_care_task_fits_in_budget_exact():
    task = CareTask("Feeding", duration_minutes=10)
    assert task.fits_in_budget(10) is True


def test_care_task_mark_complete():
    task = CareTask("Walk", duration_minutes=20)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_care_task_reset():
    task = CareTask("Walk", duration_minutes=20)
    task.mark_complete()
    task.reset()
    assert task.completed is False


def test_care_task_get_description_includes_title():
    task = CareTask("Morning walk", duration_minutes=30, priority="high")
    assert "Morning walk" in task.get_description()


def test_care_task_get_description_shows_dependency():
    task = CareTask("Medication", duration_minutes=5, depends_on="Feeding")
    assert "Feeding" in task.get_description()


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

def test_pet_add_task():
    pet = Pet("Mochi", "dog", 3)
    pet.add_task(CareTask("Walk", 20))
    assert len(pet.tasks) == 1


def test_pet_remove_task():
    pet = Pet("Mochi", "dog", 3)
    pet.add_task(CareTask("Walk", 20))
    pet.add_task(CareTask("Feeding", 10))
    pet.remove_task("Walk")
    assert len(pet.tasks) == 1
    assert pet.tasks[0].title == "Feeding"


def test_pet_get_pending_tasks_excludes_completed():
    pet = Pet("Mochi", "dog", 3)
    walk = CareTask("Walk", 20)
    feeding = CareTask("Feeding", 10)
    walk.mark_complete()
    pet.add_task(walk)
    pet.add_task(feeding)
    pending = pet.get_pending_tasks()
    assert len(pending) == 1
    assert pending[0].title == "Feeding"


def test_pet_get_description_includes_name_and_species():
    pet = Pet("Luna", "cat", 5)
    desc = pet.get_description()
    assert "Luna" in desc
    assert "cat" in desc


def test_pet_update_special_needs():
    pet = Pet("Luna", "cat", 5)
    pet.update_special_needs(["sensitive stomach"])
    assert "sensitive stomach" in pet.special_needs


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

def test_owner_add_pet():
    owner = Owner("Jordan", available_minutes=60)
    owner.add_pet(Pet("Mochi", "dog", 3))
    assert len(owner.pets) == 1


def test_owner_get_all_tasks_across_pets():
    owner = Owner("Jordan", available_minutes=60)
    mochi = Pet("Mochi", "dog", 3)
    luna = Pet("Luna", "cat", 5)
    mochi.add_task(CareTask("Walk", 20))
    luna.add_task(CareTask("Feeding", 10))
    owner.add_pet(mochi)
    owner.add_pet(luna)
    assert len(owner.get_all_tasks()) == 2


def test_owner_update_available_time():
    owner = Owner("Jordan", available_minutes=60)
    owner.update_available_time(90)
    assert owner.available_minutes == 90


def test_owner_get_summary_includes_name():
    owner = Owner("Jordan", available_minutes=60)
    assert "Jordan" in owner.get_summary()


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

def _make_scheduler(available_minutes=60):
    owner = Owner("Jordan", available_minutes=available_minutes)
    pet = Pet("Mochi", "dog", 3)
    owner.add_pet(pet)
    return owner, pet, Scheduler(owner)


def test_scheduler_high_priority_scheduled_first():
    owner, pet, scheduler = _make_scheduler(60)
    pet.add_task(CareTask("Grooming", 20, priority="low"))
    pet.add_task(CareTask("Medication", 5, priority="high"))
    schedule = scheduler.generate_schedule()
    assert schedule[0].title == "Medication"


def test_scheduler_skips_task_exceeding_budget():
    owner, pet, scheduler = _make_scheduler(available_minutes=15)
    pet.add_task(CareTask("Bath", 40, priority="high"))
    schedule = scheduler.generate_schedule()
    assert len(schedule) == 0


def test_scheduler_respects_depends_on():
    owner, pet, scheduler = _make_scheduler(60)
    pet.add_task(CareTask("Medication", 5, priority="high", depends_on="Feeding"))
    pet.add_task(CareTask("Feeding", 10, priority="high"))
    schedule = scheduler.generate_schedule()
    titles = [t.title for t in schedule]
    assert titles.index("Feeding") < titles.index("Medication")


def test_scheduler_excludes_completed_tasks():
    owner, pet, scheduler = _make_scheduler(60)
    walk = CareTask("Walk", 20, priority="high")
    walk.mark_complete()
    pet.add_task(walk)
    pet.add_task(CareTask("Feeding", 10, priority="high"))
    schedule = scheduler.generate_schedule()
    titles = [t.title for t in schedule]
    assert "Walk" not in titles
    assert "Feeding" in titles


def test_scheduler_mark_task_complete():
    owner, pet, scheduler = _make_scheduler(60)
    pet.add_task(CareTask("Walk", 20))
    scheduler.mark_task_complete("Walk")
    assert pet.tasks[0].completed is True


def test_scheduler_explain_plan_contains_pet_owner():
    owner, pet, scheduler = _make_scheduler(60)
    pet.add_task(CareTask("Walk", 20, priority="high"))
    plan = scheduler.explain_plan()
    assert "Jordan" in plan


def test_scheduler_explain_plan_lists_skipped():
    owner, pet, scheduler = _make_scheduler(available_minutes=60)
    pet.add_task(CareTask("Walk", 20, priority="high"))
    pet.add_task(CareTask("Bath", 50, priority="low"))
    plan = scheduler.explain_plan()
    assert "Skipped" in plan
    assert "Bath" in plan


def test_scheduler_explain_plan_no_tasks_fit():
    owner, pet, scheduler = _make_scheduler(available_minutes=10)
    pet.add_task(CareTask("Bath", 40, priority="high"))
    plan = scheduler.explain_plan()
    assert "No tasks could be scheduled" in plan


# ---------------------------------------------------------------------------
# sort_by_time
# ---------------------------------------------------------------------------

def test_sort_by_time_chronological_order():
    # Tasks added in reverse time order; sorted result must be earliest-first.
    _, pet, scheduler = _make_scheduler()
    tasks = [
        CareTask("Evening meds",  5,  time="19:00"),
        CareTask("Afternoon play", 20, time="14:00"),
        CareTask("Morning walk",  30, time="07:30"),
    ]
    result = scheduler.sort_by_time(tasks)
    assert [t.title for t in result] == ["Morning walk", "Afternoon play", "Evening meds"]


def test_sort_by_time_tasks_without_time_go_last():
    # Tasks with no time value must appear after all timed tasks.
    _, pet, scheduler = _make_scheduler()
    tasks = [
        CareTask("No time task", 10),
        CareTask("Early task",   10, time="06:00"),
    ]
    result = scheduler.sort_by_time(tasks)
    assert result[0].title == "Early task"
    assert result[-1].title == "No time task"


def test_sort_by_time_same_hour_sorted_by_minute():
    # Two tasks in the same hour must be ordered by minute, not string sort.
    _, pet, scheduler = _make_scheduler()
    tasks = [
        CareTask("Late in hour",  5, time="08:45"),
        CareTask("Early in hour", 5, time="08:05"),
    ]
    result = scheduler.sort_by_time(tasks)
    assert result[0].time == "08:05"
    assert result[1].time == "08:45"


def test_sort_by_time_preserves_all_tasks():
    # No tasks should be dropped during sorting.
    _, pet, scheduler = _make_scheduler()
    tasks = [CareTask(f"Task {i}", 5, time=f"0{i}:00") for i in range(1, 6)]
    assert len(scheduler.sort_by_time(tasks)) == 5


# ---------------------------------------------------------------------------
# Recurrence (renew + mark_task_complete)
# ---------------------------------------------------------------------------

def test_daily_task_creates_renewal_on_complete():
    # Marking a daily task complete via the scheduler must add a second task
    # to the pet's list representing the next occurrence.
    owner, pet, scheduler = _make_scheduler()
    pet.add_task(CareTask("Walk", 20, frequency="daily"))
    scheduler.mark_task_complete("Walk")
    assert len(pet.tasks) == 2


def test_renewal_is_not_completed():
    # The renewed task must start in the pending state.
    owner, pet, scheduler = _make_scheduler()
    pet.add_task(CareTask("Walk", 20, frequency="daily"))
    scheduler.mark_task_complete("Walk")
    renewed = pet.tasks[1]
    assert renewed.completed is False


def test_renewal_not_due_today():
    # The renewed daily task should not reappear on today's schedule;
    # is_due_today() must return False because last_done_date == today.
    from datetime import date
    owner, pet, scheduler = _make_scheduler()
    pet.add_task(CareTask("Walk", 20, frequency="daily"))
    scheduler.mark_task_complete("Walk")
    renewed = pet.tasks[1]
    assert renewed.is_due_today() is False


def test_weekly_task_creates_renewal_on_complete():
    # Weekly tasks must also produce a renewal when marked complete.
    owner, pet, scheduler = _make_scheduler()
    pet.add_task(CareTask("Brushing", 15, frequency="weekly"))
    scheduler.mark_task_complete("Brushing")
    assert len(pet.tasks) == 2


def test_as_needed_task_does_not_renew():
    # as-needed tasks have no recurrence cycle and must not produce a renewal.
    owner, pet, scheduler = _make_scheduler()
    pet.add_task(CareTask("Vet visit", 60, frequency="as-needed"))
    scheduler.mark_task_complete("Vet visit")
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# detect_conflicts
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_exact_time_collision():
    # Two tasks on different pets sharing the same HH:MM must produce a warning.
    owner = Owner("Jordan", available_minutes=120)
    mochi = Pet("Mochi", "dog", 3)
    luna  = Pet("Luna",  "cat", 5)
    mochi.add_task(CareTask("Morning walk",   30, time="07:30"))
    luna.add_task( CareTask("Wet food feeding", 5, time="07:30"))
    owner.add_pet(mochi)
    owner.add_pet(luna)
    conflicts = Scheduler(owner).detect_conflicts()
    assert any("07:30" in c for c in conflicts)


def test_detect_conflicts_no_false_positive_for_different_times():
    # Tasks at distinct times must not be flagged as a collision.
    owner, pet, scheduler = _make_scheduler()
    pet.add_task(CareTask("Walk",    30, time="07:30"))
    pet.add_task(CareTask("Feeding", 10, time="08:00"))
    conflicts = scheduler.detect_conflicts()
    assert not any("Exact-time collision" in c for c in conflicts)


def test_detect_conflicts_same_pet_same_time():
    # Two tasks on the *same* pet at the same time must also be caught.
    owner, pet, scheduler = _make_scheduler()
    pet.add_task(CareTask("Walk",    30, time="07:30"))
    pet.add_task(CareTask("Feeding", 10, time="07:30"))
    conflicts = scheduler.detect_conflicts()
    assert any("07:30" in c for c in conflicts)


def test_detect_conflicts_returns_strings_not_exceptions():
    # detect_conflicts must always return a list, never raise.
    owner, pet, scheduler = _make_scheduler()
    pet.add_task(CareTask("Walk", 20, time="08:00"))
    pet.add_task(CareTask("Bath", 40, time="08:00"))
    result = scheduler.detect_conflicts()
    assert isinstance(result, list)
    assert all(isinstance(msg, str) for msg in result)
