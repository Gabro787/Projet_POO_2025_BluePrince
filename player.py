# player.py
from inventory import Inventory

"""
Représentation du joueur dans le manoir.

NB :
- On utilise (r, c) pour être compatibles avec Manor / Game (lignes, colonnes).
- Les ressources (steps, gems, keys, dice, gold) sont stockées dans inventory,
  mais on expose des propriétés pour que Game/UI puissent lire player.steps, etc.
"""


class Player:
    """Représentation du joueur dans le manoir."""

    def __init__(self, start_r: int = 0, start_c: int = 0, inventory: Inventory | None = None):
        self.r = start_r
        self.c = start_c
        self.inventory = inventory if inventory is not None else Inventory()

    # ----------------------------
    # Déplacements
    # ----------------------------

    def move_to(self, r: int, c: int) -> None:
        """
        Place le joueur à une position (r, c) sans gérer la consommation de pas.
        La logique "1 pas par déplacement" est gérée dans Game.
        """
        self.r = r
        self.c = c

    def move_delta(self, dr: int, dc: int) -> None:
        """
        Déplace le joueur selon un delta (dr, dc).
        Ne gère pas la consommation de pas (laisse ça à Game).
        """
        self.r += dr
        self.c += dc

    # ----------------------------
    # Accès aux ressources
    # (propriétés pour compatibilité avec game/ui)
    # ----------------------------

    @property
    def steps(self) -> int:
        return self.inventory.steps

    @steps.setter
    def steps(self, value: int) -> None:
        self.inventory.steps = value

    @property
    def gems(self) -> int:
        return self.inventory.gems

    @gems.setter
    def gems(self, value: int) -> None:
        self.inventory.gems = value

    @property
    def keys(self) -> int:
        return self.inventory.keys

    @keys.setter
    def keys(self, value: int) -> None:
        self.inventory.keys = value

    @property
    def dice(self) -> int:
        return self.inventory.dice

    @dice.setter
    def dice(self, value: int) -> None:
        self.inventory.dice = value

    @property
    def gold(self) -> int:
        return self.inventory.gold

    @gold.setter
    def gold(self, value: int) -> None:
        self.inventory.gold = value

    # ----------------------------
    # Gestion des états
    # ----------------------------

    def is_dead(self) -> bool:
        """Vérifie si le joueur a perdu par manque de pas."""
        return self.inventory.steps <= 0
