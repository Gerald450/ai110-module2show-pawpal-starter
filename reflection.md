# PawPal+ Project Reflection

## 1. System Design

**a. Core user actions**

The three core actions a user should be able to perform in PawPal+:

1. **Add a pet** — The user enters basic information about their pet (name, species, age, and any special needs). This establishes the pet profile that all care tasks and scheduling decisions are built around. Without a pet profile, the system has no context for what kind of care is needed or how to prioritize it.

2. **Add and manage care tasks** — The user creates tasks representing the things their pet needs each day (e.g., a morning walk, medication at noon, feeding twice a day, grooming on weekends). Each task captures at minimum a name, estimated duration, and priority level. The user can also edit or remove tasks as their pet's routine changes over time.

3. **Generate and view today's schedule** — The user triggers the scheduler to produce a daily plan based on their available time, task priorities, and any constraints (e.g., medication must come before feeding). The system displays the ordered plan and explains why tasks were arranged that way, so the owner understands the reasoning and can trust or adjust it.

**b. Main objects (brainstorm)**

The system requires four main objects. Here is each one with its attributes and methods in natural language:

---

**`Owner`** — represents the person responsible for the pet's care.

- *Attributes:* name, available time per day (in minutes), and any scheduling preferences (e.g., prefers morning tasks, avoids tasks after 8pm).
- *Methods:* update available time, update preferences, get a summary of who the owner is and how much time they have.

---

**`Pet`** — represents the animal being cared for.

- *Attributes:* name, species (dog, cat, other), age, and any special needs or health notes (e.g., "needs medication before food", "low energy due to age").
- *Methods:* update special needs, get a description of the pet (used when explaining the schedule), check whether a task type is relevant for this pet.

---

**`CareTask`** — represents a single unit of care that needs to happen.

- *Attributes:* title (e.g., "Morning walk"), duration in minutes, priority level (low / medium / high), optional preferred time of day (morning / afternoon / evening), and an optional constraint (e.g., "must happen before feeding").
- *Methods:* get a short description of the task, compare priority against another task, check whether the task fits within a remaining time budget.

---

**`Scheduler`** — the brain of the system; takes the owner, pet, and task list and produces a plan.

- *Attributes:* the owner object, the pet object, and the list of care tasks.
- *Methods:* generate a daily schedule (sort and filter tasks by priority and time constraints), check whether all high-priority tasks fit within available time, produce a human-readable explanation of why each task was included and in what order, and return the final ordered plan as a list.

---

**c. UML Class Diagram**

```mermaid
classDiagram
    class Owner {
        +String name
        +int available_minutes
        +List~String~ preferences
        +update_available_time(minutes: int)
        +update_preferences(preferences: List~String~)
        +get_summary() String
    }

    class Pet {
        +String name
        +String species
        +int age
        +List~String~ special_needs
        +update_special_needs(needs: List~String~)
        +get_description() String
    }

    class CareTask {
        +String title
        +int duration_minutes
        +String priority
        +String preferred_time_of_day
        +String constraint
        +get_description() String
        +fits_in_budget(remaining_minutes: int) bool
    }

    class Scheduler {
        +Owner owner
        +Pet pet
        +List~CareTask~ tasks
        +generate_schedule() List~CareTask~
        +explain_plan() String
    }

    Owner "1" --> "1..*" Pet : owns
    Scheduler *-- Owner : has
    Scheduler *-- Pet : has
    Scheduler *-- CareTask : schedules
```

**d. Initial design**

The design uses four classes arranged in a clear separation between data and logic.

`Pet` and `CareTask` are implemented as Python data classes because they are pure data holders — they describe *what exists* in the system, not *what the system does*. `Pet` stores the animal's profile (name, species, age, special needs) and knows how to describe itself. `CareTask` stores a single unit of work (title, duration, priority, optional time-of-day preference, and any ordering constraint) and knows whether it fits within a given time budget.

`Owner` is a regular class because it holds a mutable list of `Pet` objects alongside its own data (name, available minutes, preferences). It is responsible for representing the person's time constraints and preferences — the inputs that the scheduler must respect.

`Scheduler` is the only class with real orchestration logic. It receives an `Owner`, a `Pet`, and a list of `CareTask` objects, then produces a prioritized daily plan that fits within the owner's available time. It is also responsible for explaining that plan in human-readable form. Keeping all scheduling decisions inside `Scheduler` means the other three classes stay simple and focused on their own data.

**e. Design changes**

Yes, three changes were made to the skeleton after reviewing the initial design for missing relationships and logic bottlenecks.

1. **Replaced `CareTask.constraint: str` with `depends_on: str | None`** — the original `constraint` field was a free-form string (e.g., `"must happen before feeding"`). A scheduler cannot parse or enforce natural language, so it would have been ignored in practice. Replacing it with `depends_on`, which holds the *title* of a prerequisite task (e.g., `"Medication"`), gives `generate_schedule()` something concrete to act on: it can check whether the named task has already been scheduled before placing the dependent one.

2. **Typed `CareTask.priority` as `Literal["low", "medium", "high"]`** — the original `str` type placed no restriction on what values were valid. An invalid priority like `"urgent"` or `"HIGH"` would silently produce wrong sort order. Using `Literal` makes the contract explicit and lets type checkers catch bad values at the call site before they cause subtle bugs at runtime.

3. **Removed `Owner.pets: list[Pet]`** — `Owner` held a list of pets, but `Scheduler` also received a `pet` argument directly. These two references were out of sync with no code connecting them. Since the app targets a single pet per session and `Scheduler` already owns the pet, the redundant list on `Owner` was removed to eliminate the ambiguity.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
