# random_manager.py

import random
from items import *

class RandomManager:
    """Gère les tirages aléatoires du jeu."""
    
    def __init__(self, player):
        self.player = player
    
    # ----------------------------
    # Tirage simple d'un objet
    # ----------------------------
    
    def draw_consumable(self):
        """Tire un objet consommable selon des probabilités modifiées."""
        
        base_table = [
            (Food("Apple", 2), 0.25),
            (Food("Banana", 3), 0.20),
            (Food("Cake", 10), 0.10),
            (Gem(), 0.15),
            (Key(), 0.15),
            (Die(), 0.15),
        ]
        
        # modificateurs permanents
        if self.player.inventory.has_detector():
            # +20% de chances pour clés + gemmes
            base_table.append((Key(), 0.05))
            base_table.append((Gem(), 0.05))

        if self.player.inventory.has_rabbit_foot():
            # double la chance de nourriture/permanents
            base_table.append((Food("Banana", 3), 0.20))
        
        return self.weighted_choice(base_table)

    # ----------------------------
    # Outil générique
    # ----------------------------
    
    def weighted_choice(self, table):
        """Choisit un élément dans une table [(obj, probabilité)]."""
        total = sum(p for _, p in table)
        r = random.uniform(0, total)
        
        current = 0
        for obj, prob in table:
            current += prob
            if r <= current:
                return obj
        
        return table[-1][0]  # fallback
