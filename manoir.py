# manoir.py
from typing import Optional, List
from enum import Enum, auto
from room import Room, RoomType, Position
from door import Door, DoorLockLevel

class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

class Manor:
    GRID_ROWS = 5
    GRID_COLS = 9

    def __init__(self):
        self.rooms: List[List[Optional[Room]]] = [
            [None for _ in range(self.GRID_COLS)] for _ in range(self.GRID_ROWS)
        ]
        entrance_pos = Position(self.GRID_ROWS - 1, self.GRID_COLS // 2)
        entrance = Room(entrance_pos, RoomType.ENTRANCE)
        self.place_room(entrance)
        antechamber_pos = Position(0, self.GRID_COLS // 2)
        antechamber = Room(antechamber_pos, RoomType.ANTECHAMBER)
        self.place_room(antechamber)
        self.entrance_pos = entrance_pos
        self.antechamber_pos = antechamber_pos

    def place_room(self, room: Room):
        self.rooms[room.pos.row][room.pos.col] = room

    def get_room(self, pos: Position) -> Optional[Room]:
        if not pos.is_inside(self.GRID_ROWS, self.GRID_COLS):
            return None
        return self.rooms[pos.row][pos.col]

    def generate_lock_level_for_row(self, row: int) -> DoorLockLevel:
        import random
        if row == self.GRID_ROWS - 1:
            return DoorLockLevel.UNLOCKED
        if row == 0:
            return DoorLockLevel.DOUBLE_LOCKED
        r = random.random()
        if r < 0.5:
            return DoorLockLevel.UNLOCKED
        elif r < 0.85:
            return DoorLockLevel.LOCKED
        else:
            return DoorLockLevel.DOUBLE_LOCKED

    def create_random_room(self, pos: Position) -> Room:
        import random
        r = random.random()
        if r < 0.2:
            rt = RoomType.FOOD
        elif r < 0.4:
            rt = RoomType.TREASURE
        elif r < 0.55:
            rt = RoomType.TRAP
        else:
            rt = RoomType.NEUTRAL
        return Room(pos, rt)

    @staticmethod
    def opposite_direction(direction: Direction) -> Direction:
        return {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }[direction]
