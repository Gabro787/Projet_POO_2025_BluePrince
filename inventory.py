# inventory.py

from items import *

class Inventory:
    """Gestion des ressources du joueur."""
    
    def __init__(self):
        # ressources consommables
        self.steps = 70
        self.gold = 0
        self.gems = 2
        self.keys = 0
        self.dice = 0
        
        # objets stockés
        self.items = []  # nourriture, objets trouvés, etc.
        
        # objets permanents (un set pour éviter les doublons)
        self.permanent_items = set()

    # ----------------------------
    # Ajout d'objets
    # ----------------------------
    
    def add_item(self, item):
        """Ajoute un objet consommable ou permanent."""
        if isinstance(item, PermanentItem):
            self.permanent_items.add(type(item))  # on stocke la classe pour éviter doublons
        else:
            self.items.append(item)

    # ----------------------------
    # Utilisation des objets
    # ----------------------------
    
    def use_item(self, item_index, player):
        """Utilise un objet consommable."""
        if item_index < 0 or item_index >= len(self.items):
            return False
        
        item = self.items[item_index]
        consumed = item.use(player)
        
        if consumed:
            del self.items[item_index]
        
        return True

    # ----------------------------
    # Info permanents
    # ----------------------------
    
    def has_perm(self, cls):
        return cls in self.permanent_items
    
    def has_shovel(self):
        return self.has_perm(Shovel)
    
    def has_hammer(self):
        return self.has_perm(Hammer)
    
    def has_lockpick(self):
        return self.has_perm(LockpickKit)
    
    def has_detector(self):
        return self.has_perm(MetalDetector)
    
    def has_rabbit_foot(self):
        return self.has_perm(RabbitFoot)