# player.py

from inventory import Inventory

class Player:
    """Représentation du joueur dans le manoir."""
    
    def __init__(self, start_x=0, start_y=0):
        self.x = start_x
        self.y = start_y
        self.inventory = Inventory()

    # ----------------------------
    # Déplacement
    # ----------------------------
    
    def move(self, dx, dy):
        """Déplace le joueur et consomme 1 pas."""
        self.x += dx
        self.y += dy
        self.inventory.steps -= 1

    # ----------------------------
    # Gestion des états
    # ----------------------------
    
    def is_dead(self):
        """Vérifie si le joueur a perdu par manque de pas."""
        return self.inventory.steps <= 0
