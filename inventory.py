# inventory.py
from items import (
    Item, Consumable, PermanentItem,
    Shovel, Hammer, LockpickKit,
    MetalDetector, RabbitFoot,
)

"""
Gestion centralisée des ressources et des objets du joueur.

- Ressources numériques : steps, gold, gems, keys, dice.
- Objets consommables : stockés dans self.items (Food, etc.).
- Objets permanents : stockés dans self.permanent_items (types de classe).
"""


class Inventory:
    """Gestion des ressources et objets du joueur."""

    def __init__(self):
        # Ressources de base
        self.steps = 70
        self.gold = 0
        self.gems = 2
        self.keys = 0
        self.dice = 0

        # Objets consommables (liste d'instances Item)
        self.items: list[Item] = []

        # Objets permanents (on stocke les classes pour éviter les doublons)
        self.permanent_items: set[type[PermanentItem]] = set()

    # ----------------------------
    # Ajout de ressources simples
    # ----------------------------

    def add_steps(self, n: int) -> None:
        self.steps += n

    def add_gold(self, n: int) -> None:
        self.gold += n

    def add_gems(self, n: int) -> None:
        self.gems += n

    def add_keys(self, n: int) -> None:
        self.keys += n

    def add_dice(self, n: int) -> None:
        self.dice += n

    # ----------------------------
    # Gestion des dés (reroll)
    # ----------------------------

    def can_reroll_rooms(self) -> bool:
        """True si le joueur a au moins un dé pour relancer un tirage de salles."""
        return self.dice > 0

    def spend_die(self) -> bool:
        """
        Consomme un dé pour un reroll.
        Retourne True si réussi, False si aucun dé dispo.
        """
        if self.dice > 0:
            self.dice -= 1
            return True
        return False

    # ----------------------------
    # Ajout d'objets
    # ----------------------------

    def add_item(self, item: Item) -> None:
        """
        Ajoute un objet consommable ou permanent.

        - PermanentItem : on stocke le TYPE dans permanent_items.
        - Autre : on l'ajoute à la liste items.
        """
        if isinstance(item, PermanentItem):
            self.permanent_items.add(type(item))
        else:
            self.items.append(item)

    # ----------------------------
    # Utilisation des objets consommables
    # ----------------------------

    def use_item(self, item_index: int, player) -> bool:
        """
        Utilise un objet consommable par son index dans la liste items.
        Retourne True si quelque chose a été fait, False si index invalide.
        """
        if item_index < 0 or item_index >= len(self.items):
            return False

        item = self.items[item_index]
        consumed = item.use(player)

        if consumed:
            del self.items[item_index]

        return True

    # ----------------------------
    # Info permanents / helpers
    # ----------------------------

    def has_perm(self, cls: type[PermanentItem]) -> bool:
        return cls in self.permanent_items

    def has_shovel(self) -> bool:
        return self.has_perm(Shovel)

    def has_hammer(self) -> bool:
        return self.has_perm(Hammer)

    def has_lockpick(self) -> bool:
        return self.has_perm(LockpickKit)

    def has_detector(self) -> bool:
        return self.has_perm(MetalDetector)

    def has_rabbit_foot(self) -> bool:
        return self.has_perm(RabbitFoot)

    # Propriété pour que Door puisse faire getattr(inventory, "lockpick_kit", False)
    @property
    def lockpick_kit(self) -> bool:
        """Compatibilité avec door.Door.can_open (lockpick_kit bool)."""
        return self.has_lockpick()
