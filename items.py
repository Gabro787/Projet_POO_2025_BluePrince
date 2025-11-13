
from abc import ABC, abstractmethod

class Item(ABC):
    """Classe abstraite représentant un objet du jeu."""
    
    def __init__(self, name):
        self.name = name
    
    @abstractmethod
    def use(self, player):
        """Méthode appelée quand l'objet est utilisé."""
        pass


# ---------------------
# Objets consommables
# ---------------------

class Consumable(Item):
    """Objets à usage unique (pas, nourriture, clés, dés...)."""
    def __init__(self, name):
        super().__init__(name)

class Food(Consumable):
    """Nourriture qui rend des pas."""
    def __init__(self, name, steps_restored):
        super().__init__(name)
        self.steps_restored = steps_restored
    
    def use(self, player):
        player.inventory.steps += self.steps_restored
        return True  # indique que l'objet doit être retiré de l'inventaire


class Key(Consumable):
    """Clé simple."""
    def __init__(self):
        super().__init__("Key")

    def use(self, player):
        # utilisation gérée ailleurs (ouverture de porte)
        return False  # la clé est consommée avant l'appel


class Die(Consumable):
    """Dé permettant un reroll de salles."""
    def __init__(self):
        super().__init__("Die")

    def use(self, player):
        # effet géré par le RandomManager
        return False


class Gem(Consumable):
    """Gemmes servant à acheter une salle."""
    def __init__(self):
        super().__init__("Gem")

    def use(self, player):
        return False


# ---------------------
# Objets permanents
# ---------------------

class PermanentItem(Item):
    """Objets avec effet permanent (kit de crochetage, pelle...)."""
    
    def use(self, player):
        # on ne les "utilise" pas, ils ajoutent un effet permanent
        return False


class Shovel(PermanentItem):
    def __init__(self):
        super().__init__("Shovel")


class Hammer(PermanentItem):
    def __init__(self):
        super().__init__("Hammer")


class LockpickKit(PermanentItem):
    def __init__(self):
        super().__init__("Lockpick Kit")


class MetalDetector(PermanentItem):
    def __init__(self):
        super().__init__("Metal Detector")


class RabbitFoot(PermanentItem):
    def __init__(self):
        super().__init__("Rabbit Foot")
