# room.py
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, Optional
from door import Door

@dataclass(frozen=True)
class Position:
    row: int
    col: int
    def is_inside(self, rows, cols):
        return 0 <= self.row < rows and 0 <= self.col < cols

class RoomType(Enum):
    ENTRANCE = auto()
    ANTECHAMBER = auto()
    NEUTRAL = auto()
    FOOD = auto()
    TREASURE = auto()
    TRAP = auto()

class Room:
    def __init__(self, pos: Position, room_type: RoomType):
        self.pos = pos
        self.room_type = room_type
        self.doors: Dict[object, Optional[Door]] = {}
        self.visited = False

    def set_door(self, direction, door: Door):
        self.doors[direction] = door

    def get_door(self, direction):
        return self.doors.get(direction)

    def apply_enter_effect(self, inventory):
        if self.visited:
            return
        self.visited = True
        if self.room_type == RoomType.FOOD:
            inventory.steps += 5
        elif self.room_type == RoomType.TREASURE:
            from random import randint, random
            gain = randint(3, 8)
            inventory.gold += gain
            if random() < 0.3:
                inventory.keys += 1
        elif self.room_type == RoomType.TRAP:
            from random import randint
            malus = randint(3, 7)
            inventory.steps -= malus
