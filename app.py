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

if "owner" not in st.session_state:
    st.session_state.owner = None

if "schedule" not in st.session_state:
    st.session_state.schedule = None

# ---------------------------------------------------------------------------
# Step 1 — Owner setup
# ---------------------------------------------------------------------------

st.subheader("Step 1 — Owner Setup")

with st.form("owner_form"):
    owner_name     = st.text_input("Your name", value="Jordan")
    available_mins = st.number_input("Minutes available today", min_value=10, max_value=480, value=90)
    owner_saved    = st.form_submit_button("Save owner")

if owner_saved:
    # Preserve existing pets if the owner is being updated rather than created fresh.
    existing_pets = st.session_state.owner.pets if st.session_state.owner else []
    owner = Owner(name=owner_name, available_minutes=int(available_mins))
    for pet in existing_pets:
        owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.schedule = None  # stale schedule is no longer valid
    st.success(f"Owner saved: {owner_name} ({available_mins} min available).")

if st.session_state.owner:
    st.caption(st.session_state.owner.get_summary())

# ---------------------------------------------------------------------------
# Step 2 — Add a pet
# Calls owner.add_pet(pet) to register the new Pet on the Owner object.
# After submission Streamlit reruns top-to-bottom, reads the updated owner
# from session_state, and re-renders the pet list automatically.
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
        # owner.add_pet() registers the Pet on the Owner and makes its tasks
        # visible to the Scheduler via owner.get_all_tasks().
        st.session_state.owner.add_pet(pet)
        st.session_state.schedule = None
        st.success(f"Added {pet_name} to {st.session_state.owner.name}'s pets.")

    if st.session_state.owner.pets:
        st.write("Registered pets:")
        for pet in st.session_state.owner.pets:
            st.markdown(f"- {pet.get_description()}")

# ---------------------------------------------------------------------------
# Step 3 — Add tasks
# Calls pet.add_task(task) on whichever pet the user selects.
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

    col4, col5 = st.columns(2)
    with col4:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
    with col5:
        time_of_day = st.selectbox(
            "Preferred time of day",
            ["(none)", "morning", "afternoon", "evening"],
        )

    if st.button("Add task"):
        task = CareTask(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            frequency=frequency,
            preferred_time_of_day=None if time_of_day == "(none)" else time_of_day,
        )
        # pet.add_task() appends the CareTask to the pet's own task list.
        target_pet.add_task(task)
        st.session_state.schedule = None
        st.success(f'Added "{task_title}" to {target_name}.')

    # --- Filter controls ---
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
                horizontal=True, key="filter_status"
            )

        pet_filter_arg = None if filter_pet == "All" else filter_pet
        filtered = st.session_state.owner.filter_tasks(
            pet_name=pet_filter_arg, status=filter_status
        )

        if filtered:
            st.table([
                {
                    "pet": pname,
                    "task": t.title,
                    "duration (min)": t.duration_minutes,
                    "priority": t.priority,
                    "frequency": t.frequency,
                    "time of day": t.preferred_time_of_day or "—",
                    "status": "done" if t.completed else "pending",
                    "last done": str(t.last_done_date) if t.last_done_date else "—",
                    "due today": "yes" if t.is_due_today() else "no",
                }
                for pname, t in filtered
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
        # Store the result so it survives the next rerun without regenerating.
        st.session_state.schedule = scheduler.explain_plan()

        # Surface conflicts as visible warnings above the plan text.
        conflicts = scheduler.detect_conflicts()
        st.session_state.conflicts = conflicts

    if st.session_state.get("conflicts"):
        for c in st.session_state.conflicts:
            st.warning(c)

    if st.session_state.schedule:
        st.text(st.session_state.schedule)
