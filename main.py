from pawpal_system import CareTask, Pet, Owner, Scheduler

# --- Owner ---
owner = Owner(name="Jordan", available_minutes=120, preferences=["morning tasks first"])

# --- Pet 1: Mochi the dog ---
mochi = Pet(name="Mochi", species="dog", age=3)
mochi.add_task(CareTask("Morning walk",    duration_minutes=30, priority="high",   frequency="daily",  preferred_time_of_day="morning"))
mochi.add_task(CareTask("Feeding",         duration_minutes=10, priority="high",   frequency="daily",  preferred_time_of_day="morning"))
mochi.add_task(CareTask("Medication",      duration_minutes=5,  priority="high",   frequency="daily",  depends_on="Feeding"))
mochi.add_task(CareTask("Enrichment toy",  duration_minutes=20, priority="medium", frequency="daily"))

# --- Pet 2: Luna the cat ---
luna = Pet(name="Luna", species="cat", age=5, special_needs=["indoor only", "sensitive stomach"])
luna.add_task(CareTask("Wet food feeding", duration_minutes=5,  priority="high",   frequency="daily",  preferred_time_of_day="morning"))
luna.add_task(CareTask("Litter cleaning",  duration_minutes=10, priority="medium", frequency="daily"))
luna.add_task(CareTask("Brushing",         duration_minutes=15, priority="low",    frequency="weekly", preferred_time_of_day="evening"))

owner.add_pet(mochi)
owner.add_pet(luna)

# --- Today's Schedule ---
scheduler = Scheduler(owner)

print("=" * 50)
print("          PAWPAL+ — TODAY'S SCHEDULE")
print("=" * 50)
print()
print(owner.get_summary())
print()
for pet in owner.pets:
    print(f"  {pet.get_description()}")
print()
print("-" * 50)
print(scheduler.explain_plan())
print("=" * 50)
