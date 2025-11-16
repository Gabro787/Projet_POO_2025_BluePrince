# room_data.py
"""
Pioche de salles pour Blue Prince 2D (version simplifiée).

ALL_ROOMS contient les modèles de salles possibles (hors Entrée / Antechambre).

ROOM_DECK est une pioche de 46 "cartes salle" avec des doublons :
- Les salles spéciales qui donnent des objets permanents sont UNIQUES :
    * Veranda (VRN) -> pelle
    * Chambre d'ami (GBD) -> détecteur
    * Cellule (CEL) -> kit de crochetage
    * Marchand ambulant (MCH) -> patte de lapin possible
- Les autres salles peuvent apparaître plusieurs fois.
"""

import random
from dataclasses import replace
from typing import List, Dict
from room import Room, RoomType


def clone_room(room: Room) -> Room:
    """Renvoie une copie indépendante d'une Room (y compris l'image)."""
    return replace(room)


# ---------- Modèles de salles (20 max théoriques, ici 19) ----------

ALL_ROOMS: List[Room] = [

    # ---------- Couloirs (ORANGE) ----------
    Room(
        name="Couloir vertical",
        short="CV1",
        color="orange",
        doors=["N", "S"],
        gem_cost=0,
        room_type=RoomType.NEUTRAL,
        rarity=0,
        tile_index=0,
    ),
    Room(
        name="Couloir tournant",
        short="CT1",
        color="orange",
        doors=["N", "E"],
        gem_cost=0,
        room_type=RoomType.NEUTRAL,
        rarity=0,
        tile_index=1,
    ),
    Room(
        name="Croisement",
        short="XRD",
        color="orange",
        doors=["N", "S", "E", "W"],
        gem_cost=1,
        room_type=RoomType.NEUTRAL,
        rarity=1,
        tile_index=1,
    ),

    # ---------- Salles bleues ----------
    Room(
        name="Salle vide",
        short="EMP",
        color="blue",
        doors=["N"],
        gem_cost=0,
        room_type=RoomType.NEUTRAL,
        rarity=0,
        tile_index=2,
    ),
    Room(
        name="Dortoir",
        short="DRT",
        color="blue",
        doors=["S", "E"],
        gem_cost=0,
        room_type=RoomType.NEUTRAL,
        rarity=0,
        tile_index=5,
    ),
    Room(
        name="Réfectoire",
        short="DIN",
        color="blue",
        doors=["W", "E"],
        gem_cost=0,
        room_type=RoomType.NEUTRAL,
        rarity=0,
        tile_index=3,
    ),
    Room(
        name="Salle vide",
        short="LIB",
        color="blue",
        doors=["N", "W"],
        gem_cost=1,
        room_type=RoomType.NEUTRAL,
        rarity=1,
        tile_index=4,
    ),

    # ---------- Jardins / verts ----------
    Room(
        name="Jardin intérieur",
        short="GAR",
        color="green",
        doors=["N", "S"],
        gem_cost=1,
        room_type=RoomType.FOOD,
        rarity=1,
        tile_index=6,
    ),
    Room(
        name="Veranda",
        short="VRN",
        color="green",
        doors=["N", "E"],
        gem_cost=2,
        room_type=RoomType.FOOD,
        rarity=2,
        edge_only=True,
        tile_index=7,
    ),

    # ---------- Chambres / violettes + coffres bleus ----------
    Room(
        name="Salle des coffres",
        short="VLT",
        color="blue",
        doors=["S"],
        gem_cost=3,
        room_type=RoomType.TREASURE,
        rarity=2,
        effect_id="big_treasure",
        tile_index=11,
    ),
    Room(
        name="Chambre simple",
        short="BED",
        color="purple",
        doors=["S"],
        gem_cost=0,
        room_type=RoomType.NEUTRAL,
        rarity=0,
        tile_index=8,
    ),
    Room(
        name="Chambre d'ami",
        short="GBD",
        color="purple",
        doors=["N", "S"],
        gem_cost=1,
        room_type=RoomType.NEUTRAL,
        rarity=1,
        tile_index=9,
    ),
    Room(
        name="Suite royale",
        short="SUI",
        color="purple",
        doors=["N", "E"],
        gem_cost=2,
        room_type=RoomType.NEUTRAL,
        rarity=2,
        effect_id="bonus_steps",
        tile_index=10,
    ),

    # ---------- Magasins / jaunes ----------
    Room(
        name="Boutique",
        short="SHP",
        color="yellow",
        doors=["S"],
        gem_cost=0,
        room_type=RoomType.TREASURE,
        rarity=1,
        tile_index=12,
    ),
    Room(
        name="Marchand ambulant",
        short="MCH",
        color="yellow",
        doors=["N", "E"],
        gem_cost=1,
        room_type=RoomType.TREASURE,
        rarity=1,
        tile_index=13,
    ),
    Room(
        name="Salle avec sac",
        short="TRS",
        color="yellow",
        doors=["W"],
        gem_cost=3,
        room_type=RoomType.TREASURE,
        rarity=2,
        effect_id="gold_rich",
        tile_index=14,
    ),

    # ---------- Salles rouges ----------
    Room(
        name="Salle piégée",
        short="TRP",
        color="red",
        doors=["S"],
        gem_cost=0,
        room_type=RoomType.TRAP,
        rarity=1,
        effect_id="trap_damage",
        tile_index=16,
    ),
    Room(
        name="Cellule",
        short="CEL",
        color="red",
        doors=["N"],
        gem_cost=0,
        room_type=RoomType.TRAP,
        rarity=0,
        tile_index=17,
    ),
    Room(
        name="Salle des chaînes",
        short="CHN",
        color="red",
        doors=["N", "E"],
        gem_cost=1,
        room_type=RoomType.TRAP,
        rarity=2,
        tile_index=19,
    ),
]

# ---------- Index par code court (short) ----------

ROOM_BY_SHORT: Dict[str, Room] = {room.short: room for room in ALL_ROOMS}

# Composition de la pioche (doit faire 46 au total)
ROOM_COUNTS: Dict[str, int] = {
    # Couloirs
    "CV1": 6,
    "CT1": 6,
    "XRD": 4,

    # Bleues neutres
    "EMP": 4,
    "DRT": 3,
    "DIN": 3,
    "LIB": 2,

    # Jardins
    "GAR": 3,
    "VRN": 1,   # unique -> pelle

    # Coffres & chambres
    "VLT": 2,
    "BED": 2,
    "GBD": 1,   # unique -> détecteur
    "SUI": 1,

    # Magasins / trésors
    "SHP": 2,
    "MCH": 1,   # unique -> patte de lapin possible
    "TRS": 2,

    # Pièges
    "TRP": 1,
    "CEL": 1,   # unique -> lockpick
    "CHN": 1,
}


def build_room_deck() -> List[Room]:
    """
    Construit une pioche de 46 'cartes salle' en dupliquant les modèles
    selon ROOM_COUNTS. La pioche contient des références vers les modèles
    (on clonerra plus tard).
    """
    deck: List[Room] = []
    total = 0
    for short, count in ROOM_COUNTS.items():
        tpl = ROOM_BY_SHORT[short]
        for _ in range(count):
            deck.append(tpl)
            total += 1

    print("DEBUG: taille de la pioche de salles =", total)
    random.shuffle(deck)
    return deck