# items.py

from abc import ABC, abstractmethod


class Item(ABC):
    """Classe de base pour tous les objets."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def use(self, player):
        """Utilisation de l'objet. Retourne True si l'objet est consommé."""
        pass

# -----------------------------
# Objets consommables
# -----------------------------

class Consumable(Item):
    """Objets à usage unique."""
    def __init__(self, name: str):
        super().__init__(name)


class Food(Consumable):
    """Nourriture qui rend des pas au joueur."""
    def __init__(self, name: str, steps_restored: int):
        super().__init__(name)
        self.steps_restored = steps_restored

    def use(self, player):
        # On modifie les pas du joueur directement
        player.steps += self.steps_restored
        return True  # l'objet est consommé


class Key(Consumable):
    """Clé simple (ouverte par door.open via inventory.keys)."""
    def __init__(self):
        super().__init__("Clé")

    def use(self, player):
        # Utilisée indirectement par le système de portes
        return False


class Die(Consumable):
    """Dé pour relancer un tirage de salles (reroll)."""
    def __init__(self):
        super().__init__("Dé")

    def use(self, player):
        # Gestion via inventory.dice / can_reroll_rooms
        return False


class Gem(Consumable):
    """Gemme utilisée pour payer le coût des salles."""
    def __init__(self):
        super().__init__("Gemme")

    def use(self, player):
        return False


# -----------------------------
# Objets permanents
# -----------------------------

class PermanentItem(Item):
    """Objets avec effet permanent (pelle, marteau, etc.)."""

    def use(self, player):
        # Pas d'usage direct, l'effet est passif / contextuel
        return False


class Shovel(PermanentItem):
    """Pelle pour creuser dans certaines salles."""
    def __init__(self):
        super().__init__("Pelle")


class Hammer(PermanentItem):
    """Marteau qui réduit les dégâts des pièges."""
    def __init__(self):
        super().__init__("Marteau")


class LockpickKit(PermanentItem):
    """Kit de crochetage permettant d'ouvrir certaines portes/coffres."""
    def __init__(self):
        super().__init__("Kit de crochetage")


class MetalDetector(PermanentItem):
    """Détecteur de métaux (bonus pour trouver du loot)."""
    def __init__(self):
        super().__init__("Détecteur")


class RabbitFoot(PermanentItem):
    """Patte de lapin (bonus de chance)."""
    def __init__(self):
        super().__init__("Patte de lapin")