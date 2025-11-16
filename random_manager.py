# random_manager.py
import random
from items import Food, Gem, Key, Die, Shovel, Hammer, LockpickKit, MetalDetector, RabbitFoot

"""
RandomManager : gère les tirages aléatoires du jeu côté B.

Ici :
- draw_consumable() : tire un objet consommable (nourriture, gem, clé, dé),
  avec des probabilités modifiées par les permanents (détecteur, patte de lapin).
- draw_permanent()  : exemple de tirage d'un objet permanent rare.
"""


class RandomManager:
    """Gère les tirages aléatoires du jeu."""

    def __init__(self, player):
        self.player = player  # on suppose que player.inventory existe

    # ----------------------------
    # Tirage d'un consommable
    # ----------------------------

    def draw_consumable(self):
        """
        Tire un objet consommable selon des probabilités modifiées.

        La table de base contient un peu de nourriture, des gemmes, des clés, des dés.
        Certains objets permanents (détecteur, patte de lapin) modifient la table.
        """

        base_table = [
            (Food("Apple", 2), 0.25),
            (Food("Banana", 3), 0.20),
            (Food("Cake", 10), 0.10),
            (Gem(), 0.15),
            (Key(), 0.15),
            (Die(), 0.15),
        ]

        inv = self.player.inventory

        # Détecteur de métaux : augmente les chances pour clés + gemmes
        if inv.has_detector():
            base_table.append((Key(), 0.05))
            base_table.append((Gem(), 0.05))

        # Patte de lapin : augmente les chances d'avoir de la nourriture
        if inv.has_rabbit_foot():
            base_table.append((Food("Banana", 3), 0.20))

        return self.weighted_choice(base_table)

    # ----------------------------
    # Tirage d'un permanent (exemple)
    # ----------------------------

    def draw_permanent(self):
        """
        Exemple de tirage d'un objet permanent rare.

        En pratique, ce tirage pourra être appelé dans certaines salles spéciales
        (coffre, boutique...) plutôt que sur un événement standard.
        """

        table = [
            (Shovel(), 0.25),
            (Hammer(), 0.25),
            (LockpickKit(), 0.20),
            (MetalDetector(), 0.15),
            (RabbitFoot(), 0.15),
        ]

        return self.weighted_choice(table)

    # ----------------------------
    # Outil générique
    # ----------------------------

    def weighted_choice(self, table):
        """Choisit un élément dans une table [(obj, probabilité)]."""
        total = sum(p for _, p in table)
        r = random.uniform(0, total)

        current = 0.0
        for obj, prob in table:
            current += prob
            if r <= current:
                return obj

        # Fallback si problèmes d'arrondi
        return table[-1][0]
