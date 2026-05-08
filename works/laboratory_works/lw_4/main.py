import json
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class DomainError(Exception):
    """Базовое исключение для всех ошибок предметной области."""
    pass


class BuildingNotFoundError(DomainError):
    """Возникает, когда здание не найдено."""

    def __init__(self, cadastre_id: str):
        self.cadastre_id = cadastre_id
        super().__init__(f"Здание с кадастровым номером {cadastre_id} не найдено.")


class RoomNotFoundError(DomainError):
    """Возникает, когда комната не найдена в доме."""

    def __init__(self, room_key: str, house_id: str = None):
        self.room_key = room_key
        self.house_id = house_id
        message = f"Комната '{room_key}' не найдена."
        if house_id:
            message += f" В доме {house_id}."
        super().__init__(message)


class InvalidRoomTypeError(DomainError):
    """Возникает при попытке создать или добавить комнату недопустимого типа."""

    def __init__(self, room_type: str, allowed_types: List[str]):
        self.room_type = room_type
        self.allowed_types = allowed_types
        super().__init__(
            f"Недопустимый тип комнаты: '{room_type}'. "
            f"Разрешённые типы: {', '.join(allowed_types)}"
        )


class DimensionError(DomainError):
    """Возникает при некорректных размерах комнаты."""
    pass


# ====================== Building ======================
class Building(ABC):
    def __init__(self, cadastre_id: str, address: str, owners: List['Owner'],
                 building_type: str, area_sq_m: float, assessed_value_usd: float):
        self._cadastre_id = cadastre_id
        self._address = address
        self._owners = owners
        self._building_type = building_type
        self._area_sq_m = area_sq_m
        self._assessed_value_usd = assessed_value_usd

    @abstractmethod
    def __str__(self) -> str:
        pass

    def __lt__(self, other):
        if not isinstance(other, Building):
            return NotImplemented
        return self._cadastre_id < other._cadastre_id

    @property
    def cadastre_id(self):
        return self._cadastre_id


class House(Building):
    ALLOWED_ROOM_TYPES = {
        "kitchen_room", "bedroom", "living_room", "bathroom",
        "pantry", "outdoor_kitchen"
    }

    def __init__(self, cadastre_id: str, address: str, owners: List['Owner'],
                 building_type: str, area_sq_m: float, assessed_value_usd: float,
                 floors: int, rooms: Dict[str, 'Room'] = None):
        super().__init__(cadastre_id, address, owners, building_type, area_sq_m, assessed_value_usd)
        self._floors = floors
        self._rooms: Dict[str, 'Room'] = rooms or {}

    def __str__(self) -> str:
        owners_str = ", ".join(owner.name for owner in self._owners)
        return (f"Жилой дом, кадастровый номер {self._cadastre_id}. \n"
                f"Общая площадь {self._area_sq_m} м², количество комнат: {len(self._rooms)}. \n"
                f"Адрес: {self._address}, владельцы: {owners_str}. \n"
                f"Оценочная стоимость: {self._assessed_value_usd}$")

    # Магические методы
    def __len__(self) -> int:
        return len(self._rooms)

    def __getitem__(self, key: str) -> 'Room':
        try:
            return self._rooms[key]
        except KeyError:
            raise RoomNotFoundError(key, self._cadastre_id)

    def __setitem__(self, key: str, room: 'Room') -> None:
        self._validate_room_type(room)
        self._rooms[key] = room

    def __iter__(self):
        return iter(self._rooms.values())

    def __contains__(self, key: str) -> bool:
        return key in self._rooms

    def add_room(self, key: str, room: 'Room') -> None:
        """Явный метод добавления комнаты с валидацией."""
        self._validate_room_type(room)
        self._rooms[key] = room

    def _validate_room_type(self, room: 'Room'):
        """Проверка допустимости типа комнаты."""
        if room.room_type not in self.ALLOWED_ROOM_TYPES:
            raise InvalidRoomTypeError(
                room.room_type,
                list(self.ALLOWED_ROOM_TYPES)
            )

    def get_rooms_summary(self) -> None:
        """Выводит общие сведения о существующих комнатах в доме."""
        if not self._rooms:
            print("В доме пока нет комнат.")
            return

        total_area = sum(room.area for room in self._rooms.values())

        print("\n=== Общие сведения о комнатах в доме ===")
        print(f"Всего комнат: {len(self)}")
        print(f"Общая площадь всех комнат: {total_area:.1f} м²")
        print(f"Количество этажей: {self._floors}")
        print("\nПодробный список комнат:")

        for key, room in sorted(self._rooms.items()):
            print(f"  • {key:12} | {room.name} ({room.room_type}) "
                  f"| Площадь: {room.area:.1f} м² | Этаж: {room.floor}")

    # ====================== JSON методы ======================
    def to_dict(self) -> dict:
        """Преобразует House в словарь для JSON."""
        return {
            "cadastre_id": self._cadastre_id,
            "address": self._address,
            "building_type": self._building_type,
            "area_sq_m": self._area_sq_m,
            "assessed_value_usd": self._assessed_value_usd,
            "floors": self._floors,
            "owners": [
                {
                    "name": owner.name,
                    "human_id": owner.human_id,
                    "birthdate": owner.birthdate
                } for owner in self._owners
            ],
            "rooms": {
                key: self._room_to_dict(room) for key, room in self._rooms.items()
            }
        }

    @staticmethod
    def _room_to_dict(room: 'Room') -> dict:
        """Вспомогательный метод для сериализации комнаты."""
        base = {
            "name": room.name,
            "floor": room.floor,
            "room_type": room.room_type,
            "description": room.description,
            "dimensions": {
                "area_sq_m": room.dimensions.area_sq_m,
                "length_m": room.dimensions.length_m,
                "width_m": room.dimensions.width_m,
                "height_m": room.dimensions.height_m
            }
        }

        # Специфические поля для разных типов комнат
        if isinstance(room, Kitchen):
            base.update({
                "has_water_supply": room.has_water_supply,
                "stove_type": room.stove_type,
                "work_area": room.work_area
            })
        elif isinstance(room, Bedroom):
            base.update({
                "has_wardrobe": getattr(room, '_has_wardrobe', False),
                "bed_size": getattr(room, '_bed_size', None)
            })
        elif isinstance(room, LivingRoom):
            base.update({
                "has_balcony_access": getattr(room, '_has_balcony_access', False),
                "has_fireplace": getattr(room, '_has_fireplace', False)
            })
        elif isinstance(room, Bathroom):
            base.update({
                "has_bathtub": getattr(room, '_has_bathtub', False),
                "has_shower": getattr(room, '_has_shower', False),
                "has_toilet": getattr(room, '_has_toilet', True),
                "has_bidet": getattr(room, '_has_bidet', False)
            })
        elif isinstance(room, Pantry):
            base.update({
                "shelving": getattr(room, '_shelving', True)
            })

        return base

    def to_json(self, indent: int = 2) -> str:
        """Возвращает House в виде JSON-строки."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> 'House':
        """Создаёт House из словаря."""
        owners = [
            Owner(owner["name"], owner["human_id"], owner["birthdate"])
            for owner in data.get("owners", [])
        ]

        rooms: Dict[str, 'Room'] = {}
        for key, rdata in data.get("rooms", {}).items():
            dims = RoomDimensions(
                rdata["dimensions"]["area_sq_m"],
                rdata["dimensions"]["length_m"],
                rdata["dimensions"]["width_m"],
                rdata["dimensions"]["height_m"]
            )

            room_type = rdata["room_type"]

            if room_type == "kitchen_room":
                room = Kitchen(
                    floor=rdata["floor"],
                    description=rdata["description"],
                    dimensions=dims,
                    has_water_supply=rdata.get("has_water_supply", True),
                    stove_type=rdata.get("stove_type", "electric"),
                    work_area=rdata.get("work_area", 0.0)
                )
            elif room_type == "bedroom":
                room = Bedroom(
                    floor=rdata["floor"],
                    description=rdata["description"],
                    dimensions=dims,
                    has_wardrobe=rdata.get("has_wardrobe", False),
                    bed_size=rdata.get("bed_size")
                )
            elif room_type == "living_room":
                room = LivingRoom(
                    floor=rdata["floor"],
                    description=rdata["description"],
                    dimensions=dims,
                    has_balcony_access=rdata.get("has_balcony_access", False),
                    has_fireplace=rdata.get("has_fireplace", False)
                )
            elif room_type == "bathroom":
                room = Bathroom(
                    floor=rdata["floor"],
                    description=rdata["description"],
                    dimensions=dims,
                    has_bathtub=rdata.get("has_bathtub", False),
                    has_shower=rdata.get("has_shower", False),
                    has_toilet=rdata.get("has_toilet", True),
                    has_bidet=rdata.get("has_bidet", False)
                )
            else:
                # Для неизвестных типов — базовая комната
                room = Room(
                    name=rdata["name"],
                    floor=rdata["floor"],
                    room_type=room_type,
                    description=rdata["description"],
                    dimensions=dims
                )

            rooms[key] = room

        return cls(
            cadastre_id=data["cadastre_id"],
            address=data["address"],
            owners=owners,
            building_type=data.get("building_type", "House"),
            area_sq_m=data["area_sq_m"],
            assessed_value_usd=data["assessed_value_usd"],
            floors=data["floors"],
            rooms=rooms
        )

    @classmethod
    def from_json(cls, json_file: str) -> 'House':
        """Создаёт House из JSON-строки."""
        data = json.loads(json_file)
        return cls.from_dict(data)


# ====================== Person ======================
class Person(ABC):
    def __init__(self, name: str, human_id: str, birthdate: str):
        self._name = name
        self._human_id = human_id
        self._birthdate = birthdate

    @abstractmethod
    def get_info(self):
        pass

    @property
    def name(self):
        return self._name

    @property
    def human_id(self):
        return self._human_id

    @property
    def birthdate(self):
        return self._birthdate


class Owner(Person):
    def __init__(self, owner_name: str, owner_id: str, birthdate: str):
        super().__init__(owner_name, owner_id, birthdate)

    def get_info(self):
        return f"Владелец: {self._name} (ID: {self._human_id}, дата рождения: {self._birthdate})"


# ====================== Space & Rooms ======================
class Space(ABC):
    def __init__(self, name: str, floor: Optional[int] = None):
        self._name = name
        self._floor = floor

    @property
    def name(self):
        return self._name

    @property
    def floor(self):
        return self._floor


class Room(Space):
    def __init__(self, name: str, floor: int, room_type: str,
                 description: str, dimensions: 'RoomDimensions'):
        super().__init__(name, floor)
        self._room_type = room_type
        self._description = description
        self._dimensions = dimensions

    @property
    def area(self) -> float:
        return self._dimensions.area_sq_m

    def __str__(self):
        return f"{self._name} ({self._room_type}): {self._description}"

    @property
    def room_type(self):
        return self._room_type

    @property
    def description(self):
        return self._description

    @property
    def dimensions(self):
        return self._dimensions


class CookingSpace(Room, ABC):
    def __init__(self, name: str, floor: int, room_type: str,
                 description: str, dimensions: 'RoomDimensions',
                 has_water_supply: bool, stove_type: str, work_area: float):
        super().__init__(name, floor, room_type, description, dimensions)
        self._has_water_supply = has_water_supply
        self._stove_type = stove_type
        self._work_area = work_area

    @property
    def has_water_supply(self):
        return self._has_water_supply

    @property
    def stove_type(self):
        return self._stove_type

    @property
    def work_area(self):
        return self._work_area


class Kitchen(CookingSpace):
    def __init__(self, floor: int, description: str, dimensions: 'RoomDimensions',
                 has_water_supply: bool, stove_type: str, work_area: float):
        super().__init__(
            name="Кухня", floor=floor, room_type="kitchen_room",
            description=description, dimensions=dimensions,
            has_water_supply=has_water_supply, stove_type=stove_type,
            work_area=work_area
        )


class OutdoorKitchen(CookingSpace):
    def __init__(self, floor: Optional[int], description: str, dimensions: 'RoomDimensions',
                 has_water_supply: bool, stove_type: str, work_area: float):
        super().__init__(
            name="Летняя кухня", floor=floor, room_type="outdoor_kitchen",
            description=description, dimensions=dimensions,
            has_water_supply=has_water_supply, stove_type=stove_type,
            work_area=work_area
        )


class Bedroom(Room):
    def __init__(self, floor: int, description: str, dimensions: 'RoomDimensions',
                 has_wardrobe: bool = False, bed_size: Optional[str] = None):
        super().__init__("Спальня", floor, "bedroom", description, dimensions)
        self._has_wardrobe = has_wardrobe
        self._bed_size = bed_size


class LivingRoom(Room):
    def __init__(self, floor: int, description: str, dimensions: 'RoomDimensions',
                 has_balcony_access: bool = False, has_fireplace: bool = False):
        super().__init__("Гостиная", floor, "living_room", description, dimensions)
        self._has_balcony_access = has_balcony_access
        self._has_fireplace = has_fireplace


class Bathroom(Room):
    def __init__(self, floor: int, description: str, dimensions: 'RoomDimensions',
                 has_bathtub: bool = False, has_shower: bool = False,
                 has_toilet: bool = True, has_bidet: bool = False):
        super().__init__("Ванная комната", floor, "bathroom", description, dimensions)
        self._has_bathtub = has_bathtub
        self._has_shower = has_shower
        self._has_toilet = has_toilet
        self._has_bidet = has_bidet


class Pantry(Room):
    def __init__(self, floor: int, description: str, dimensions: 'RoomDimensions',
                 shelving: bool = True):
        super().__init__("Кладовая", floor, "pantry", description, dimensions)
        self._shelving = shelving


class Balcony(Space):
    def __init__(self, description: str, dimensions: 'RoomDimensions',
                 floor: Optional[int] = None, is_glazed: bool = False):
        super().__init__("Балкон", floor)
        self._description = description
        self._dimensions = dimensions
        self._is_glazed = is_glazed

    @property
    def area(self) -> float:
        return self._dimensions.area_sq_m


class RoomDimensions:
    def __init__(self, area_sq_m: float, length_m: float, width_m: float, height_m: float):
        if any(v <= 0 for v in (area_sq_m, length_m, width_m, height_m)):
            raise DimensionError("Все размеры должны быть положительными числами.")
        self.area_sq_m = area_sq_m
        self.length_m = length_m
        self.width_m = width_m
        self.height_m = height_m


# ====================== Пример использования ======================
if __name__ == "__main__":
    # Создание кухни
    dims_kitchen = RoomDimensions(24.5, 6.0, 4.1, 2.7)
    kitchen = Kitchen(
        floor=1,
        description="Современная кухня",
        dimensions=dims_kitchen,
        has_water_supply=True,
        stove_type="electric",
        work_area=3.0
    )

    # Создание дома
    house = House(
        cadastre_id="398183471893",
        address="or. Chișinău, str. Stefan cel Mare 110",
        owners=[Owner("Ivan Cernigov", "2839647291023", "28-01-2002")],
        building_type="House",
        area_sq_m=94.2,
        assessed_value_usd=190231.2,
        floors=2,
        rooms={"kitchen": kitchen}
    )

    # Добавляем спальню
    dims_bed = RoomDimensions(20.0, 5.0, 4.0, 2.7)
    bedroom = Bedroom(floor=2, description="Большая спальня", dimensions=dims_bed, has_wardrobe=True)
    house.add_room("bedroom", bedroom)

    print(house)
    house.get_rooms_summary()

    # === Работа с JSON ===
    print("\n" + "=" * 60)
    print("=== Экспорт дома в JSON ===")
    json_str = house.to_json(indent=2)
    print(json_str)

    # Сохранение в файл
    with open("house.json", "w", encoding="utf-8") as f:
        f.write(json_str)
    print("\nДом успешно сохранён в файл 'house.json'")

    # === Загрузка из JSON ===
    print("\n=== Загрузка дома из JSON ===")
    loaded_house = House.from_json(json_str)
    loaded_house.get_rooms_summary()

    print(f"\nЗагруженный дом (кадастр): {loaded_house.cadastre_id}")
    print(f"Количество комнат после загрузки: {len(loaded_house)}")
