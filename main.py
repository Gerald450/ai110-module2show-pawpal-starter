from pawpal_system import CareTask, Pet, Owner, Scheduler

# --- Owner ---
owner = Owner(name="Jordan", available_minutes=120, preferences=["morning tasks first"])

# --- Pet 1: Mochi the dog ---
# Tasks added deliberately out of time order to prove sort_by_time() works.
mochi = Pet(name="Mochi", species="dog", age=3)
mochi.add_task(CareTask("Evening walk",   duration_minutes=25, priority="medium", frequency="daily",  preferred_time_of_day="evening", time="18:00"))
mochi.add_task(CareTask("Medication",     duration_minutes=5,  priority="high",   frequency="daily",  preferred_time_of_day="morning", time="08:30", depends_on="Feeding"))
mochi.add_task(CareTask("Afternoon play", duration_minutes=20, priority="medium", frequency="daily",  preferred_time_of_day="afternoon", time="14:00"))
mochi.add_task(CareTask("Feeding",        duration_minutes=10, priority="high",   frequency="daily",  preferred_time_of_day="morning", time="08:00"))
mochi.add_task(CareTask("Morning walk",   duration_minutes=30, priority="high",   frequency="daily",  preferred_time_of_day="morning", time="07:30"))

# --- Pet 2: Luna the cat ---
# "Wet food feeding" is intentionally set to 07:30 — the same time as
# Mochi's "Morning walk" — to trigger the exact-time collision warning.
luna = Pet(name="Luna", species="cat", age=5, special_needs=["indoor only", "sensitive stomach"])
luna.add_task(CareTask("Brushing",         duration_minutes=15, priority="low",    frequency="weekly", preferred_time_of_day="evening",   time="19:00"))
luna.add_task(CareTask("Wet food feeding", duration_minutes=5,  priority="high",   frequency="daily",  preferred_time_of_day="morning",   time="07:30"))  # conflicts with Mochi's Morning walk
luna.add_task(CareTask("Litter cleaning",  duration_minutes=10, priority="medium", frequency="daily",  preferred_time_of_day="afternoon", time="13:30"))

# Mark one task complete so the status filter has something to show.
luna.tasks[2].mark_complete()   # Litter cleaning is done

owner.add_pet(mochi)
owner.add_pet(luna)

scheduler = Scheduler(owner)

SEP  = "=" * 54
DASH = "-" * 54

# ---------------------------------------------------------------------------
# 1. sort_by_time — all tasks across all pets, sorted by HH:MM
# ---------------------------------------------------------------------------
print(SEP)
print("  1. ALL TASKS SORTED BY TIME (HH:MM)")
print(SEP)
all_tasks = owner.get_all_tasks()
sorted_tasks = scheduler.sort_by_time(all_tasks)
for task in sorted_tasks:
    time_label = task.time if task.time else "no time"
    print(f"  {time_label}  {task.title:<22} [{task.priority}]")

# ---------------------------------------------------------------------------
# 2. filter_tasks — pending only, all pets
# ---------------------------------------------------------------------------
print()
print(SEP)
print("  2. FILTER: PENDING TASKS — ALL PETS")
print(SEP)
pending = owner.filter_tasks(status="pending")
for pet_name, task in pending:
    print(f"  {pet_name:<8}  {task.title:<22}  pending")

# ---------------------------------------------------------------------------
# 3. filter_tasks — completed only, all pets
# ---------------------------------------------------------------------------
print()
print(SEP)
print("  3. FILTER: COMPLETED TASKS — ALL PETS")
print(SEP)
completed = owner.filter_tasks(status="completed")
if completed:
    for pet_name, task in completed:
        print(f"  {pet_name:<8}  {task.title:<22}  done (last: {task.last_done_date})")
else:
    print("  No completed tasks.")

# ---------------------------------------------------------------------------
# 4. filter_tasks — single pet, all statuses
# ---------------------------------------------------------------------------
print()
print(SEP)
print("  4. FILTER: ALL TASKS FOR MOCHI ONLY")
print(SEP)
mochi_tasks = owner.filter_tasks(pet_name="Mochi")
for pet_name, task in mochi_tasks:
    status = "done" if task.completed else "pending"
    print(f"  {task.time or '??:??'}  {task.title:<22}  {status}")

# ---------------------------------------------------------------------------
# 5. filter_tasks — single pet, pending only, sorted by time
# ---------------------------------------------------------------------------
print()
print(SEP)
print("  5. FILTER + SORT: LUNA'S PENDING TASKS BY TIME")
print(SEP)
luna_pending_pairs = owner.filter_tasks(pet_name="Luna", status="pending")
luna_pending = [task for _, task in luna_pending_pairs]
for task in scheduler.sort_by_time(luna_pending):
    print(f"  {task.time or '??:??'}  {task.title:<22}  [{task.priority}]")

# ---------------------------------------------------------------------------
# 6. Conflict detection — standalone, so warnings are clearly visible
# ---------------------------------------------------------------------------
print()
print(SEP)
print("  6. CONFLICT DETECTION")
print(SEP)
conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts detected.")

# ---------------------------------------------------------------------------
# 7. Full schedule
# ---------------------------------------------------------------------------
print()
print(SEP)
print("  7. TODAY'S SCHEDULE")
print(SEP)
print(scheduler.explain_plan())
print(SEP)
