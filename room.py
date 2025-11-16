# room.py
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional


class RoomType(Enum):
    ENTRANCE = auto()
    ANTECHAMBER = auto()
    NEUTRAL = auto()
    FOOD = auto()
    TREASURE = auto()
    TRAP = auto()


@dataclass
class Room:
    """
    Représentation d'une salle du manoir.
    Utilisée par :
    - ui.py (color, short, doors, gem_cost, image)
    - manoir.py / game.py (placement, coût, type, etc.)
    """
    name: str
    short: str
    color: Optional[str]
    doors: List[str]                        # ex: ["N","S"]
    gem_cost: int = 0
    room_type: RoomType = RoomType.NEUTRAL

    # Champs supplémentaires
    rarity: int = 0
    edge_only: bool = False
    objects: List[str] = field(default_factory=list)
    effect_id: Optional[str] = None

    # Index dans le tileset + surface pygame associée
    tile_index: int = -1          # -1 = pas d'image
    image: object = None          # sera rempli par Game.init_room_images()

    # Flag pour savoir si l'effet d'entrée a déjà été appliqué
    visited: bool = False

    @classmethod
    def from_type(cls, room_type: RoomType) -> "Room":
        """
        Crée une salle spéciale selon son type :
        - Entrée
        - Antechambre
        """
        if room_type == RoomType.ENTRANCE:
            # Entrée en bas milieu, plusieurs portes pour bien partir
            return cls(
                name="Entrée",
                short="ENT",
                color="blue",
                doors=["N", "E", "W"],
                gem_cost=0,
                room_type=room_type,
                rarity=0,
                edge_only=False,
                tile_index=18,   # tuile d'entrée, à adapter si besoin
            )

        if room_type == RoomType.ANTECHAMBER:
            # Antichambre en haut milieu, salle importante
            return cls(
                name="Antechambre",
                short="ANT",
                color="blue",
                doors=["S", "E", "W"],
                gem_cost=0,
                room_type=room_type,
                rarity=3,
                edge_only=True,
                tile_index=14,  # tuile dorée (Trésor)
            )

        if room_type == RoomType.FOOD:
            return cls(
                name="Nourriture",
                short="FD",
                color="green",
                doors=["N"],
                gem_cost=0,
                room_type=room_type,
                rarity=2,
            )

        if room_type == RoomType.TREASURE:
            return cls(
                name="Trésor",
                short="TR",
                color="yellow",
                doors=["N"],
                gem_cost=2,
                room_type=room_type,
                rarity=2,
            )

        if room_type == RoomType.TRAP:
            return cls(
                name="Piège",
                short="TP",
                color="red",
                doors=["N"],
                gem_cost=0,
                room_type=room_type,
                rarity=1,
            )

        # NEUTRAL par défaut
        return cls(
            name="Salle",
            short="RM",
            color=None,
            doors=["N"],
            gem_cost=0,
            room_type=room_type,
            rarity=0,
        )