# door.py
from enum import Enum


class DoorLockLevel(Enum):
    """
    Niveaux de verrouillage des portes, comme dans la consigne :
    - UNLOCKED      (niveau 0 : déverrouillée, ne coûte pas de clé)
    - LOCKED        (niveau 1 : verrouillée, 1 clé ou kit de crochetage)
    - DOUBLE_LOCKED (niveau 2 : double tour, 1 clé obligatoire)
    
    """
    UNLOCKED = 0
    LOCKED = 1
    DOUBLE_LOCKED = 2


class Door:
    """
    Représente une porte entre deux salles.
    - lock_level : niveau de verrouillage (0, 1 ou 2)
    - is_open    : True si la porte est déjà ouverte
    La logique d'inventaire (clefs, kit de crochetage) est gérée par B.
    Ici on fournit seulement l'API.
    
    """

    def __init__(self, lock_level: DoorLockLevel):
        self.lock_level = lock_level
        # Une porte est considérée comme ouverte si elle est niveau 0 à la création
        self.is_open = (lock_level == DoorLockLevel.UNLOCKED)

    def can_open(self, inventory) -> bool:
        """
        Détermine si la porte PEUT être ouverte avec l'inventaire donné.
        - inventory doit fournir au minimum :
          * inventory.keys        (int)
          * inventory.lockpick_kit (bool)
        La consommation effective de la clé est faite dans open().
        """
        if self.is_open:
            return True

        # Porte déverrouillée (niveau 0) : toujours ouvrable, sans clé.
        if self.lock_level == DoorLockLevel.UNLOCKED:
            return True

        # Porte verrouillée niveau 1 :
        # - 1 clé OU kit de crochetage.
        if self.lock_level == DoorLockLevel.LOCKED:
            return inventory.keys > 0 or getattr(inventory, "lockpick_kit", False)

        # Porte verrouillée à double tour (niveau 2) :
        # - nécessite toujours une clé, le kit ne suffit pas.
        if self.lock_level == DoorLockLevel.DOUBLE_LOCKED:
            return inventory.keys > 0

        return False

    def open(self, inventory) -> bool:
        """
        Tente d'ouvrir la porte en consommant les ressources nécessaires.
        Retourne True si l'ouverture réussit, False sinon.
        - Consomme 1 clé pour les niveaux 1/2, sauf si niveau 1 + kit de crochetage.
        """
        if not self.can_open(inventory):
            return False

        if self.lock_level == DoorLockLevel.LOCKED:
            # Niveau 1 : on consomme une clé SEULEMENT si pas de kit de crochetage.
            if not getattr(inventory, "lockpick_kit", False) and inventory.keys > 0:
                inventory.keys -= 1

        elif self.lock_level == DoorLockLevel.DOUBLE_LOCKED:
            # Niveau 2 : il faut une clé, le kit ne suffit pas.
            if inventory.keys > 0:
                inventory.keys -= 1
            else:
                return False

        # Porte désormais ouverte
        self.is_open = True
        return True