import streamlit as st
from pawpal_system import CareTask, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Your daily pet care planner.")

# ---------------------------------------------------------------------------
# Session state initialisation
# st.session_state is a dictionary that survives reruns within a session.
# The "not in" guard means: create the object once, then reuse it on every
# subsequent rerun instead of wiping and rebuilding it from scratch.
# ---------------------------------------------------------------------------

if "owner"     not in st.session_state: st.session_state.owner     = None
if "schedule"  not in st.session_state: st.session_state.schedule  = None
if "conflicts" not in st.session_state: st.session_state.conflicts = []
if "skipped"   not in st.session_state: st.session_state.skipped   = []

# ---------------------------------------------------------------------------
# Step 1 — Owner setup
# ---------------------------------------------------------------------------

st.subheader("Step 1 — Owner Setup")

with st.form("owner_form"):
    owner_name     = st.text_input("Your name", value="Jordan")
    available_mins = st.number_input("Minutes available today", min_value=10, max_value=480, value=90)
    owner_saved    = st.form_submit_button("Save owner")

if owner_saved:
    existing_pets = st.session_state.owner.pets if st.session_state.owner else []
    owner = Owner(name=owner_name, available_minutes=int(available_mins))
    for pet in existing_pets:
        owner.add_pet(pet)
    st.session_state.owner     = owner
    st.session_state.schedule  = None
    st.session_state.conflicts = []
    st.session_state.skipped   = []
    st.success(f"Owner saved: **{owner_name}** — {available_mins} min available today.")

if st.session_state.owner:
    st.caption(st.session_state.owner.get_summary())

# ---------------------------------------------------------------------------
# Step 2 — Add a pet
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Step 2 — Add a Pet")

if st.session_state.owner is None:
    st.info("Complete Step 1 first.")
else:
    with st.form("pet_form"):
        pet_name = st.text_input("Pet name", value="Mochi")
        species  = st.selectbox("Species", ["dog", "cat", "other"])
        age      = st.number_input("Age", min_value=0, max_value=30, value=3)
        needs    = st.text_input("Special needs (comma-separated, optional)", value="")
        pet_saved = st.form_submit_button("Add pet")

    if pet_saved:
        pet = Pet(
            name=pet_name,
            species=species,
            age=int(age),
            special_needs=[n.strip() for n in needs.split(",") if n.strip()],
        )
        st.session_state.owner.add_pet(pet)
        st.session_state.schedule = None
        st.success(f"Added **{pet_name}** to {st.session_state.owner.name}'s pets.")

    if st.session_state.owner.pets:
        st.write("Registered pets:")
        for pet in st.session_state.owner.pets:
            st.markdown(f"- {pet.get_description()}")

# ---------------------------------------------------------------------------
# Step 3 — Add tasks + filtered / sorted task list
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Step 3 — Add Tasks")

if not st.session_state.owner or not st.session_state.owner.pets:
    st.info("Add at least one pet in Step 2 first.")
else:
    pet_names   = [p.name for p in st.session_state.owner.pets]
    target_name = st.selectbox("Add task to which pet?", pet_names)
    target_pet  = next(p for p in st.session_state.owner.pets if p.name == target_name)

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col4, col5, col6 = st.columns(3)
    with col4:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
    with col5:
        time_of_day = st.selectbox(
            "Preferred time of day",
            ["(none)", "morning", "afternoon", "evening"],
        )
    with col6:
        start_time = st.text_input("Start time (HH:MM, optional)", placeholder="08:30")

    if st.button("Add task"):
        # Normalise the optional HH:MM field — blank or whitespace-only → None.
        cleaned_time = start_time.strip() if start_time.strip() else None
        task = CareTask(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            frequency=frequency,
            preferred_time_of_day=None if time_of_day == "(none)" else time_of_day,
            time=cleaned_time,
        )
        target_pet.add_task(task)
        st.session_state.schedule = None
        st.success(f'Added **"{task_title}"** to {target_name}.')

    # --- Filtered + sorted task list ---
    all_tasks = st.session_state.owner.get_all_tasks()
    if all_tasks:
        st.write("**Task list**")

        fcol1, fcol2 = st.columns(2)
        with fcol1:
            filter_pet = st.selectbox(
                "Filter by pet", ["All"] + pet_names, key="filter_pet"
            )
        with fcol2:
            filter_status = st.radio(
                "Filter by status", ["all", "pending", "completed"],
                horizontal=True, key="filter_status",
            )

        pet_filter_arg = None if filter_pet == "All" else filter_pet
        filtered_pairs = st.session_state.owner.filter_tasks(
            pet_name=pet_filter_arg, status=filter_status
        )

        if filtered_pairs:
            # sort_by_time orders the visible list chronologically by HH:MM.
            scheduler = Scheduler(st.session_state.owner)
            filtered_tasks  = [t for _, t in filtered_pairs]
            pet_lookup      = {t.title: pname for pname, t in filtered_pairs}
            sorted_filtered = scheduler.sort_by_time(filtered_tasks)

            # Metrics row — quick counts at a glance.
            total_dur = sum(t.duration_minutes for t in sorted_filtered)
            pending_n = sum(1 for t in sorted_filtered if not t.completed)
            done_n    = sum(1 for t in sorted_filtered if t.completed)
            m1, m2, m3 = st.columns(3)
            m1.metric("Tasks shown",   len(sorted_filtered))
            m2.metric("Pending",       pending_n)
            m3.metric("Total duration", f"{total_dur} min")

            # Priority badge helper — turns priority into a short label.
            PRIORITY_BADGE = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}

            st.table([
                {
                    "pet":          pet_lookup[t.title],
                    "task":         t.title,
                    "time":         t.time or "—",
                    "duration":     f"{t.duration_minutes} min",
                    "priority":     PRIORITY_BADGE.get(t.priority, t.priority),
                    "frequency":    t.frequency,
                    "time of day":  t.preferred_time_of_day or "—",
                    "status":       "✅ done" if t.completed else "⏳ pending",
                    "due today":    "yes" if t.is_due_today() else "no",
                }
                for t in sorted_filtered
            ])
        else:
            st.info("No tasks match the current filter.")
    else:
        st.info("No tasks yet.")

# ---------------------------------------------------------------------------
# Step 4 — Generate schedule
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Step 4 — Today's Schedule")

if not st.session_state.owner or not st.session_state.owner.get_all_tasks():
    st.info("Add at least one task in Step 3 first.")
else:
    if st.button("Generate schedule"):
        scheduler = Scheduler(st.session_state.owner)
        schedule  = scheduler.generate_schedule()
        conflicts = scheduler.detect_conflicts()

        # Compute skipped tasks (due today but not in the generated schedule).
        all_due = [t for t in st.session_state.owner.get_all_tasks() if t.is_due_today()]
        skipped = [t for t in all_due if t not in schedule]

        st.session_state.schedule  = schedule
        st.session_state.conflicts = conflicts
        st.session_state.skipped   = skipped

    schedule  = st.session_state.schedule  or []
    conflicts = st.session_state.conflicts or []
    skipped   = st.session_state.skipped   or []

    if not schedule and not conflicts:
        # Nothing generated yet — nothing to show.
        pass
    else:
        # --- Conflict warnings ---
        if conflicts:
            for c in conflicts:
                st.warning(c)
        else:
            st.success("No scheduling conflicts detected.")

        if not schedule:
            st.error("No tasks could be scheduled within the available time budget.")
        else:
            # --- Summary metrics ---
            total_scheduled = sum(t.duration_minutes for t in schedule)
            remaining       = st.session_state.owner.available_minutes - total_scheduled
            high_skipped    = any(t.priority == "high" for t in skipped)

            m1, m2, m3 = st.columns(3)
            m1.metric("Tasks scheduled", len(schedule))
            m2.metric("Time used",        f"{total_scheduled} min")
            m3.metric("Time remaining",   f"{remaining} min")

            if high_skipped:
                st.warning("⚠️ At least one high-priority task could not be scheduled. "
                           "Consider increasing your available time.")

            # --- Scheduled task table, sorted by HH:MM ---
            scheduler = Scheduler(st.session_state.owner)
            sorted_schedule = scheduler.sort_by_time(schedule)

            # Build pet name lookup across all pets for the schedule table.
            task_to_pet: dict[str, str] = {
                task.title: pet.name
                for pet in st.session_state.owner.pets
                for task in pet.tasks
            }

            PRIORITY_BADGE = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}

            st.write("**Scheduled tasks** *(sorted by start time)*")
            st.table([
                {
                    "pet":       task_to_pet.get(t.title, "—"),
                    "task":      t.title,
                    "time":      t.time or "—",
                    "duration":  f"{t.duration_minutes} min",
                    "priority":  PRIORITY_BADGE.get(t.priority, t.priority),
                    "frequency": t.frequency,
                    "requires":  t.depends_on or "—",
                }
                for t in sorted_schedule
            ])

            # --- Skipped tasks ---
            if skipped:
                with st.expander(f"Skipped tasks ({len(skipped)})"):
                    for t in skipped:
                        reason = (
                            "unmet dependency"
                            if t.depends_on and t.depends_on not in {s.title for s in schedule}
                            else "exceeds time budget"
                        )
                        st.markdown(
                            f"- **{t.title}** ({t.duration_minutes} min, "
                            f"{PRIORITY_BADGE.get(t.priority, t.priority)}) — *{reason}*"
                        )
            else:
                st.success("All due tasks fit within your available time.")
