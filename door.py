# door.py
from enum import Enum, auto

class DoorLockLevel(Enum):
    UNLOCKED = 0
    LOCKED = 1
    DOUBLE_LOCKED = 2

class Door:
    def __init__(self, lock_level: DoorLockLevel):
        self.lock_level = lock_level
        self.is_open = (lock_level == DoorLockLevel.UNLOCKED)

    def can_open(self, inventory) -> bool:
        if self.is_open:
            return True
        if self.lock_level == DoorLockLevel.LOCKED:
            return inventory.keys > 0 or inventory.lockpick_kit
        if self.lock_level == DoorLockLevel.DOUBLE_LOCKED:
            return inventory.keys > 0
        return True

    def open(self, inventory) -> bool:
        if not self.can_open(inventory):
            return False
        if self.lock_level == DoorLockLevel.LOCKED:
            if not inventory.lockpick_kit and inventory.keys > 0:
                inventory.keys -= 1
        elif self.lock_level == DoorLockLevel.DOUBLE_LOCKED:
            if inventory.keys > 0:
                inventory.keys -= 1
            else:
                return False
        self.is_open = True
        return True
