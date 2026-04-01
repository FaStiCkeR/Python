# Реализация кода из try.py

```python
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


# =========================
# Custom exceptions
# =========================


class ProjectSystemError(Exception):
    """Base exception for the architecture project domain."""


class ValidationError(ProjectSystemError):
    """Raised when model validation fails."""


class JsonFormatError(ProjectSystemError):
    """Raised when JSON structure is incompatible with the model."""


class StorageError(ProjectSystemError):
    """Raised for read/write failures."""


# =========================
# Abstract classes
# =========================


class Worker(ABC):
    def __init__(
        self,
        name: str,
        worker_id: str,
        age: int,
        experience_years: float,
        projects_completed: int,
        base_rate: float = 0.0,
    ):
        self._name = name
        self._worker_id = worker_id
        self.age = age
        self.experience_years = experience_years
        self.projects_completed = projects_completed
        self.base_rate = base_rate

    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int) -> None:
        if value < 18:
            raise ValidationError("Age must be >= 18")
        self._age = int(value)

    @property
    def experience_years(self) -> float:
        return self._experience_years

    @experience_years.setter
    def experience_years(self, value: float) -> None:
        if value < 0:
            raise ValidationError("Experience cannot be negative")
        self._experience_years = float(value)

    @property
    def projects_completed(self) -> int:
        return self._projects_completed

    @projects_completed.setter
    def projects_completed(self, value: int) -> None:
        if value < 0:
            raise ValidationError("Projects completed cannot be negative")
        self._projects_completed = int(value)

    @property
    def base_rate(self) -> float:
        return self._base_rate

    @base_rate.setter
    def base_rate(self, value: float) -> None:
        if value < 0:
            raise ValidationError("Base rate cannot be negative")
        self._base_rate = float(value)

    @abstractmethod
    def calculate_salary(self) -> float:
        """Polymorphic salary calculation."""

    @abstractmethod
    def role_key(self) -> str:
        """Key used in JSON team sections."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self._name,
            "id": self._worker_id,
            "age": self.age,
            "experience_years": self.experience_years,
            "projects_completed": self.projects_completed,
        }

    def __str__(self) -> str:
        return f"{self.role_key()}: {self._name}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._name!r}, {self._worker_id!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Worker):
            return NotImplemented
        return self._worker_id == other._worker_id

    def __lt__(self, other: "Worker") -> bool:
        if not isinstance(other, Worker):
            return NotImplemented
        return self.experience_years < other.experience_years


class BuildComponent(ABC):
    @abstractmethod
    def component_name(self) -> str:
        """Human-readable component name."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize component."""


# =========================
# Workers
# =========================


class Architect(Worker):
    def calculate_salary(self) -> float:
        return self.base_rate + self.projects_completed * 120.0 + self.experience_years * 25.0

    def role_key(self) -> str:
        return "architect"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Architect":
        return cls(
            name=str(data["name"]),
            worker_id=str(data["id"]),
            age=int(data["age"]),
            experience_years=float(data["experience_years"]),
            projects_completed=int(data["projects_completed"]),
            base_rate=0.0,
        )


class SeniorArchitect(Architect):
    """3rd level inheritance: Worker -> Architect -> SeniorArchitect."""

    def calculate_salary(self) -> float:
        return super().calculate_salary() + 300.0


class Designer(Worker):
    def calculate_salary(self) -> float:
        return self.base_rate + self.projects_completed * 100.0 + self.experience_years * 18.0

    def role_key(self) -> str:
        return "designer"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Designer":
        return cls(
            name=str(data["name"]),
            worker_id=str(data["id"]),
            age=int(data["age"]),
            experience_years=float(data["experience_years"]),
            projects_completed=int(data["projects_completed"]),
            base_rate=0.0,
        )


class Brigadier(Worker):
    def calculate_salary(self) -> float:
        return self.base_rate + self.projects_completed * 110.0 + self.experience_years * 22.0

    def role_key(self) -> str:
        return "brigadier"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Brigadier":
        return cls(
            name=str(data["name"]),
            worker_id=str(data["id"]),
            age=int(data["age"]),
            experience_years=float(data["experience_years"]),
            projects_completed=int(data["projects_completed"]),
            base_rate=0.0,
        )


class Builder(Worker):
    def calculate_salary(self) -> float:
        return self.base_rate + self.projects_completed * 70.0 + self.experience_years * 15.0

    def role_key(self) -> str:
        return "builder"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Builder":
        return cls(
            name=str(data["name"]),
            worker_id=str(data["id"]),
            age=int(data["age"]),
            experience_years=float(data["experience_years"]),
            projects_completed=int(data["projects_completed"]),
            base_rate=0.0,
        )


# =========================
# Materials and structure
# =========================


class Material:
    def __init__(self, name: str, quantity: float, unit: str, price_per_one: float):
        self._name = name
        self.quantity = quantity
        self.unit = unit
        self.price_per_one = price_per_one

    @property
    def quantity(self) -> float:
        return self._quantity

    @quantity.setter
    def quantity(self, value: float) -> None:
        if value <= 0:
            raise ValidationError("Material quantity must be positive")
        self._quantity = float(value)

    @property
    def unit(self) -> str:
        return self._unit

    @unit.setter
    def unit(self, value: str) -> None:
        if not value.strip():
            raise ValidationError("Material unit cannot be empty")
        self._unit = value.strip()

    @property
    def price_per_one(self) -> float:
        return self._price_per_one

    @price_per_one.setter
    def price_per_one(self, value: float) -> None:
        if value < 0:
            raise ValidationError("Material price cannot be negative")
        self._price_per_one = float(value)

    def total_cost(self) -> float:
        return self.quantity * self.price_per_one

    def to_dict(self) -> dict[str, Any]:
        return {
            "quantity": self.quantity,
            "unit": self.unit,
            "price_per_one": self.price_per_one,
        }

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "Material":
        return cls(
            name=name,
            quantity=float(data["quantity"]),
            unit=str(data["unit"]),
            price_per_one=float(data["price_per_one"]),
        )

    def __mul__(self, factor: float) -> float:
        return self.total_cost() * factor

    def __str__(self) -> str:
        return f"{self._name}: {self.quantity} {self.unit} x {self.price_per_one}"


class MaterialGroup(BuildComponent):
    def __init__(self, name: str, materials: dict[str, Material]):
        self._name = name
        self._materials = materials

    @property
    def materials(self) -> dict[str, Material]:
        return self._materials

    def component_name(self) -> str:
        return self._name

    def total_cost(self) -> float:
        return sum(item.total_cost() for item in self._materials.values())

    def to_dict(self) -> dict[str, Any]:
        return {"materials": {k: v.to_dict() for k, v in self._materials.items()}}

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "MaterialGroup":
        raw_materials = data.get("materials")
        if not isinstance(raw_materials, dict):
            raise JsonFormatError(f"'materials' expected for {name}")
        materials = {m_name: Material.from_dict(m_name, m_data) for m_name, m_data in raw_materials.items()}
        return cls(name=name, materials=materials)

    def __len__(self) -> int:
        return len(self._materials)


class Foundation(MaterialGroup):
    pass


class Walls(MaterialGroup):
    pass


class Floors(MaterialGroup):
    pass


class Structure(BuildComponent):
    def __init__(self, foundation: Foundation, walls: Walls, floors: Floors):
        self._foundation = foundation
        self._walls = walls
        self._floors = floors

    def component_name(self) -> str:
        return "structure"

    def total_cost(self) -> float:
        return self._foundation.total_cost() + self._walls.total_cost() + self._floors.total_cost()

    def to_dict(self) -> dict[str, Any]:
        return {
            "foundation": self._foundation.to_dict(),
            "walls": self._walls.to_dict(),
            "floors": self._floors.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Structure":
        return cls(
            foundation=Foundation.from_dict("foundation", data["foundation"]),
            walls=Walls.from_dict("walls", data["walls"]),
            floors=Floors.from_dict("floors", data["floors"]),
        )


class BuildElement(BuildComponent):
    def __init__(self, structure: Structure):
        self._structure = structure

    def component_name(self) -> str:
        return "build_element"

    def total_cost(self) -> float:
        return self._structure.total_cost()

    def to_dict(self) -> dict[str, Any]:
        return {"structure": self._structure.to_dict()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BuildElement":
        if "structure" not in data:
            raise JsonFormatError("Missing 'structure' inside 'build_element'")
        return cls(structure=Structure.from_dict(data["structure"]))


# =========================
# Team and project
# =========================


class Brigade:
    def __init__(self, brigade_id: str, brigadier: Brigadier, workers: list[Builder]):
        self._brigade_id = brigade_id
        self._brigadier = brigadier
        self._workers = workers

    def payroll(self) -> float:
        return self._brigadier.calculate_salary() + sum(w.calculate_salary() for w in self._workers)

    def to_dict(self) -> dict[str, Any]:
        return {
            "brigade_id": self._brigade_id,
            "brigadier": self._brigadier.to_dict(),
            "workers": [w.to_dict() for w in self._workers],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Brigade":
        return cls(
            brigade_id=str(data["brigade_id"]),
            brigadier=Brigadier.from_dict(data["brigadier"]),
            workers=[Builder.from_dict(item) for item in data.get("workers", [])],
        )

    def __len__(self) -> int:
        return len(self._workers)

    def __str__(self) -> str:
        return f"Brigade {self._brigade_id} ({len(self)} workers)"


class Team:
    def __init__(self, architects: list[Architect], designers: list[Designer], brigades: list[Brigade]):
        self._architects = architects
        self._designers = designers
        self._brigades = brigades

    def all_workers(self) -> list[Worker]:
        workers: list[Worker] = []
        workers.extend(self._architects)
        workers.extend(self._designers)
        for brigade in self._brigades:
            workers.append(brigade._brigadier)
            workers.extend(brigade._workers)
        return workers

    def payroll(self) -> float:
        all_people = self.all_workers()
        return sum(person.calculate_salary() for person in all_people)

    def to_dict(self) -> dict[str, Any]:
        return {
            "architects": [a.to_dict() for a in self._architects],
            "designers": [d.to_dict() for d in self._designers],
            "brigades": [b.to_dict() for b in self._brigades],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Team":
        return cls(
            architects=[Architect.from_dict(item) for item in data.get("architects", [])],
            designers=[Designer.from_dict(item) for item in data.get("designers", [])],
            brigades=[Brigade.from_dict(item) for item in data.get("brigades", [])],
        )


class HouseProject:
    def __init__(
        self,
        project_id: int,
        status: str,
        start_date: str,
        end_date: str | None,
        region: str,
        address: str,
        project_type: str,
        build_element: BuildElement,
        team: Team,
    ):
        self.project_id = int(project_id)
        self.status = status
        self.start_date = start_date
        self.end_date = end_date
        self.region = region
        self.address = address
        self.project_type = project_type
        self.build_element = build_element
        self.team = team

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "status": self.status,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "region": self.region,
            "address": self.address,
            "type": self.project_type,
            "build_element": self.build_element.to_dict(),
            "team": self.team.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HouseProject":
        required = ["project_id", "status", "start_date", "region", "address", "type", "build_element", "team"]
        missing = [key for key in required if key not in data]
        if missing:
            raise JsonFormatError(f"Missing keys in project: {missing}")
        return cls(
            project_id=int(data["project_id"]),
            status=str(data["status"]),
            start_date=str(data["start_date"]),
            end_date=data.get("end_date"),
            region=str(data["region"]),
            address=str(data["address"]),
            project_type=str(data["type"]),
            build_element=BuildElement.from_dict(data["build_element"]),
            team=Team.from_dict(data["team"]),
        )

    def __str__(self) -> str:
        return f"HouseProject #{self.project_id} ({self.status})"

    def __len__(self) -> int:
        return len(self.team.all_workers())


class ProjectRegistry:
    """Repository-like class for file I/O and project collection operations."""

    def __init__(self, projects: list[HouseProject] | None = None):
        self._projects = projects or []

    @property
    def projects(self) -> list[HouseProject]:
        return self._projects

    def add_project(self, project: HouseProject) -> None:
        self._projects.append(project)

    def to_dict(self) -> list[dict[str, Any]]:
        return [project.to_dict() for project in self._projects]

    def save_json(self, path: str | Path) -> None:
        p = Path(path)
        try:
            p.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Cannot write JSON file: {exc}") from exc

    @classmethod
    def load_json(cls, path: str | Path) -> "ProjectRegistry":
        p = Path(path)
        try:
            raw_text = p.read_text(encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Cannot read JSON file: {exc}") from exc
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise JsonFormatError(f"Invalid JSON: {exc}") from exc
        if not isinstance(payload, list):
            raise JsonFormatError("Top-level JSON must be a list of projects")
        projects = [HouseProject.from_dict(item) for item in payload]
        return cls(projects)


def from_json_to_json() -> None:
    root = Path(__file__).resolve().parent
    source_file = root / "building.json"
    output_file = root / "building_out.json"

    registry = ProjectRegistry.load_json(source_file)
    registry.save_json(output_file)

    if registry.projects:
        first_project = registry.projects[0]
        workers = first_project.team.all_workers()
        workers.sort()
        print(first_project)
        print(f"Workers in project: {len(first_project)}")
        print(f"Most experienced: {workers[-1] if workers else 'n/a'}")
        print(f"Material cost: {first_project.build_element.total_cost():.2f}")
    print(f"Round-trip JSON saved to: {output_file.name}")


def from_code_to_json() -> None:
    foundation_materials = {
        "concrete": Material("concrete", quantity=18.5, unit="m³", price_per_one=95),
        "rebar": Material("rebar", quantity=1.2, unit="ton", price_per_one=850),
    }
    foundation = Foundation("foundation", foundation_materials)

    wall_materials = {
        "brick": Material("brick", quantity=4200, unit="pcs", price_per_one=0.45),
        "timber": Material("timber", quantity=12.5, unit="m³", price_per_one=180),
        "steel_stud": Material("steel_stud", quantity=180, unit="pcs", price_per_one=12),
        "drywall": Material("drywall", quantity=210, unit="m²", price_per_one=4.2),
    }
    walls = Walls("walls", wall_materials)

    floor_materials = {
        "reinforced_concrete_slab": Material("reinforced_concrete_slab", quantity=28.0, unit="m³", price_per_one=110),
        "wood_joists": Material("wood_joists", quantity=4.2, unit="m³", price_per_one=165),
        "osb": Material("osb", quantity=190, unit="m²", price_per_one=8.5),
        "hardwood_flooring": Material("hardwood_flooring", quantity=105, unit="m²", price_per_one=28),
    }
    floors = Floors("floors", floor_materials)

    structure = Structure(foundation=foundation, walls=walls, floors=floors)
    build_element = BuildElement(structure=structure)

    architect_1 = Architect(
        name="Mihail Creanga",
        worker_id="2093749184729",
        age=32,
        experience_years=7.0,
        projects_completed=11,
        base_rate=1500,
    )
    designer_1 = Designer(
        name="Johny Ramen",
        worker_id="203789402813",
        age=24,
        experience_years=6.3,
        projects_completed=3,
        base_rate=1200,
    )
    brigadier_1 = Brigadier(
        name="Ivan Ramen",
        worker_id="BRG203789402813",
        age=30,
        experience_years=8.0,
        projects_completed=6,
        base_rate=1300,
    )
    worker_1 = Builder(
        name="Ivan Worker",
        worker_id="WRK001",
        age=24,
        experience_years=6.3,
        projects_completed=3,
        base_rate=900,
    )

    brigade_1 = Brigade(brigade_id="BRG-001", brigadier=brigadier_1, workers=[worker_1])
    team = Team(architects=[architect_1], designers=[designer_1], brigades=[brigade_1])

    project = HouseProject(
        project_id=1,
        status="Ended",
        start_date="16-11-2002",
        end_date="20-01-2005",
        region="Chisinau",
        address="Stefan cel Mare 13",
        project_type="House",
        build_element=build_element,
        team=team,
    )

    registry = ProjectRegistry([project])
    root = Path(__file__).resolve().parent
    output_file = root / "building_manual.json"
    registry.save_json(output_file)
    print(f"Manual JSON saved to: {output_file.name}")


if __name__ == "__main__":
    try:
        from_json_to_json()
        from_code_to_json()
    except ProjectSystemError as exc:
        print(f"Domain error: {exc}")
```

## Комментарии к сложным участкам кода

Ниже пояснения к местам, где чаще всего возникают вопросы по логике.

### 1) Валидация через `@property` (инкапсуляция)

- В `Worker.age`, `Worker.experience_years`, `Worker.projects_completed`, `Worker.base_rate` проверки выполняются **в сеттерах**, а не в `__init__`.
- Это сделано, чтобы ограничения работали и при создании объекта, и при последующем изменении поля.
- Пример: если присвоить `age = 15`, сеттер сразу выбросит `ValidationError`.

### 2) Полиморфизм в зарплате

- Метод `calculate_salary()` объявлен абстрактным в `Worker` и реализован по-разному в `Architect`, `Designer`, `Brigadier`, `Builder`.
- За счет этого в `Team.payroll()` можно итерироваться по списку `Worker` и вызывать один и тот же метод:
  `sum(person.calculate_salary() for person in all_people)`.
- Конкретная формула выбирается автоматически по типу объекта.

### 3) Магические методы и зачем они здесь

- `Worker.__lt__`: позволяет сортировать работников (`workers.sort()`) по стажу.
- `Worker.__eq__`: сравнение работников по `id`, а не по ссылке в памяти.
- `HouseProject.__len__`: `len(project)` возвращает число людей в проекте.
- `Material.__mul__`: демонстрация перегрузки операции (масштабирование стоимости материала).

### 4) Восстановление объектов из JSON (`from_dict`)

- `ProjectRegistry.load_json()` читает массив проектов и для каждого вызывает `HouseProject.from_dict(...)`.
- Далее идет каскадное восстановление:
  `HouseProject -> BuildElement -> Structure -> MaterialGroup -> Material`
  и отдельно
  `HouseProject -> Team -> Brigade -> Worker`.
- Такой подход сохраняет связи между объектами после загрузки.

### 5) Проверка структуры JSON и защита от битых данных

- В `HouseProject.from_dict` есть список `required` и проверка `missing`.
- Если ключей не хватает, выбрасывается `JsonFormatError`, а не `KeyError`.
- Это дает более понятную бизнес-ошибку для пользователя.

### 6) Почему `ProjectRegistry` отдельным классом

- Он изолирует файловую работу (`load_json`, `save_json`) от бизнес-сущностей.
- Модели (`HouseProject`, `Team`, `Material`) отвечают за состояние и логику.
- `ProjectRegistry` отвечает за хранение коллекции и I/O.

### 7) Блок `if __name__ == "__main__"`

- `from_json_to_json()` — сценарий `JSON -> объекты -> JSON` (round-trip).
- `from_code_to_json()` — сценарий «создали объекты вручную -> сохранили JSON».
- Обе ветки обернуты в `try/except ProjectSystemError`, чтобы показывать контролируемые ошибки домена.
