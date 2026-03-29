from dataclasses import dataclass, field


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: list[str] = field(default_factory=list)

    def update_special_needs(self, needs: list[str]) -> None:
        pass

    def get_description(self) -> str:
        pass


@dataclass
class CareTask:
    title: str
    duration_minutes: int
    priority: str = "medium"
    preferred_time_of_day: str = None
    constraint: str = None

    def get_description(self) -> str:
        pass

    def fits_in_budget(self, remaining_minutes: int) -> bool:
        pass


class Owner:
    def __init__(self, name: str, available_minutes: int, preferences: list[str] = None):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences or []
        self.pets: list[Pet] = []

    def update_available_time(self, minutes: int) -> None:
        pass

    def update_preferences(self, preferences: list[str]) -> None:
        pass

    def get_summary(self) -> str:
        pass


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet, tasks: list[CareTask]):
        self.owner = owner
        self.pet = pet
        self.tasks = tasks

    def generate_schedule(self) -> list[CareTask]:
        pass

    def explain_plan(self) -> str:
        pass
