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
