# manoir.py
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from constants import ROWS, COLS
from room import Room, RoomType
import random
from door import Door, DoorLockLevel

# Vecteurs de directions utilitaires (N,S,E,W)
DIR_VECTORS = {
    "N": (-1, 0),
    "S": (1, 0),
    "W": (0, -1),
    "E": (0, 1),
}


def opposite_dir(d: str) -> str:
    """Retourne la direction opposée ('N'↔'S', 'E'↔'W')."""
    return {"N": "S", "S": "N", "E": "W", "W": "E"}[d]


@dataclass
class Manor:
    """
    Manoir compatible avec game.py :
    - grid           : grille 2D de Room (ou None)
    - start          : position de départ (r, c)
    - antechamber_rc : position de l'antichambre (r, c)
    - get_room, set_room, in_bounds, valid_move
    + Fonctions d'aide pour vérifier si une salle peut être placée à un endroit.
    """
    rows: int = ROWS
    cols: int = COLS
    grid: List[List[Optional[Room]]] = field(init=False)
    start: Tuple[int, int] = field(init=False)
    antechamber_rc: Tuple[int, int] = field(init=False)

    def _random_lock_level_for_rows(self, r1: int, r2: int) -> DoorLockLevel:
        """
        Détermine le niveau de fermeture d'une porte.

        - La probabilité qu'une porte soit verrouillée est FIXE (LOCK_CHANCE).
        - MAIS si elle est verrouillée, la probabilité d'être niveau 2 (double tour)
          augmente plus on monte dans le manoir.
        """

        # ----- Probabilité globale d'avoir une porte verrouillée -----
        LOCK_CHANCE = 0.20   # 20% de portes verrouillées (1 ou 2), 80% non verrouillées

        r = random.random()
        if r > LOCK_CHANCE:
            # La plupart des portes restent ouvertes
            return DoorLockLevel.UNLOCKED

        # ----- Si on arrive ici : la porte est verrouillée (niveau 1 ou 2) -----

        start_row = self.start[0]
        ante_row = self.antechamber_rc[0]
        bottom = max(start_row, ante_row)
        top = min(start_row, ante_row)

        # Position moyenne de la porte
        avg_r = (r1 + r2) / 2

        # Normalisation : t = 0 en bas, t = 1 en haut
        if bottom == top:
            t = 0.5
        else:
            t = (bottom - avg_r) / (bottom - top)
            t = max(0.0, min(1.0, t))

        # Cas spécial : rangée de l'antichambre -> toujours niveau 2
        if int(avg_r) == ante_row:
            return DoorLockLevel.DOUBLE_LOCKED

        # Probabilité d'être niveau 2 quand la porte est verrouillée :
        #  - bas : ~10% lvl2
        #  - milieu : ~50% lvl2
        #  - haut : ~80% lvl2
        p_lvl2 = 0.10 + 0.70 * t

        r2 = random.random()
        if r2 < p_lvl2:
            return DoorLockLevel.DOUBLE_LOCKED
        else:
            return DoorLockLevel.LOCKED

    def __post_init__(self):
        # Grille vide
        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]

        # Dictionnaire de portes :
        # clé = (r, c, dir)  ex: (3, 2, "N")
        # valeur = instance Door (partagée dans les deux sens)
        self.doors: dict[tuple[int, int, str], Door] = {}

        # Entrée en bas milieu
        start_r = self.rows - 1
        start_c = self.cols // 2
        entrance = Room.from_type(RoomType.ENTRANCE)
        self.grid[start_r][start_c] = entrance
        self.start = (start_r, start_c)

        # Antichambre en haut milieu
        ante_r = 0
        ante_c = self.cols // 2
        antechamber = Room.from_type(RoomType.ANTECHAMBER)
        self.grid[ante_r][ante_c] = antechamber
        self.antechamber_rc = (ante_r, ante_c)

    # ---------- Accès basiques à la grille ----------

    def get_room(self, r: int, c: int) -> Optional[Room]:
        """Retourne la Room à (r, c), ou None si aucune pièce n'est placée ici."""
        return self.grid[r][c]

    def set_room(self, r: int, c: int, room: Room) -> None:
        """Place une Room dans la grille à (r, c)."""
        self.grid[r][c] = room

    def in_bounds(self, r: int, c: int) -> bool:
        """Vrai si (r, c) est dans les limites du manoir."""
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_edge(self, r: int, c: int) -> bool:
        """
        Vrai si la case (r, c) est en bordure du manoir (lignes/colonnes extrêmes).
        Utile pour les salles avec edge_only = True (ex: Veranda).
        """
        return r == 0 or r == self.rows - 1 or c == 0 or c == self.cols - 1

    # ---------- Gestion des portes verrouillées ----------

    def get_door(self, from_rc: tuple[int, int], dir_: str) -> Door | None:
        """
        Retourne la Door entre from_rc et la direction dir_, ou None si aucune
        porte n'est encore définie à cet endroit.
        """
        r, c = from_rc
        return self.doors.get((r, c, dir_))

    def ensure_door(self, from_rc: tuple[int, int], dir_: str) -> Door | None:
        """
        Obtient ou crée une porte entre from_rc et la direction dir_.

        - Si la porte existe déjà : on la renvoie.
        - Sinon : on crée une Door avec un niveau déterminé par la hauteur :
            * Entrée / Antichambre -> toujours UNLOCKED
            * Rangée de l'antichambre -> toujours DOUBLE_LOCKED
            * Sinon -> niveau choisi par _random_lock_level_for_rows
        """
        r, c = from_rc
        if dir_ not in DIR_VECTORS:
            return None

        dr, dc = DIR_VECTORS[dir_]
        nr, nc = r + dr, c + dc
        if not self.in_bounds(nr, nc):
            return None

        key = (r, c, dir_)
        if key in self.doors:
            return self.doors[key]

        room_here = self.get_room(r, c)
        room_there = self.get_room(nr, nc)

        # Pas de verrou sur les portes directement reliées à l'Entrée ou l'Antechambre
        if (room_here and room_here.room_type in (RoomType.ENTRANCE, RoomType.ANTECHAMBER)) \
           or (room_there and room_there.room_type in (RoomType.ENTRANCE, RoomType.ANTECHAMBER)):
            level = DoorLockLevel.UNLOCKED

        else:
            # Rangée de l'antichambre -> on force le niveau 2
            ante_row = self.antechamber_rc[0]
            avg_row = (r + nr) / 2

            if int(avg_row) == ante_row:
                level = DoorLockLevel.DOUBLE_LOCKED
            else:
                # Sinon : probabilité de niveau 1/2 selon la hauteur
                level = self._random_lock_level_for_rows(r, nr)

        door = Door(level)

        # On enregistre dans les deux sens
        opp = opposite_dir(dir_)
        key2 = (nr, nc, opp)

        self.doors[key] = door
        self.doors[key2] = door

        return door

    # ---------- Déplacements ----------

    def valid_move(self, from_rc: Tuple[int, int], dir_: str) -> Optional[Tuple[int, int]]:
        """
        Calcule la destination si on se déplace depuis from_rc dans la direction dir_.

        Règles simplifiées :
        - Si la salle actuelle n'a PAS de porte dans cette direction -> mur (None)
        - Si la destination sort de la grille -> mur (None)
        - Sinon -> return (nr, nc)
        La gestion 'porte déjà ouverte ou pas' + verrous se fera dans Game / Door.
        """
        r, c = from_rc
        room_here = self.get_room(r, c)
        if not room_here:
            # Par sécurité : si la case actuelle est vide, on bloque.
            return None

        if dir_ not in room_here.doors:
            # Il n'y a tout simplement pas de porte dans cette direction.
            return None

        dr, dc = DIR_VECTORS[dir_]
        nr, nc = r + dr, c + dc
        if not self.in_bounds(nr, nc):
            # Porte menant en dehors du manoir -> mur.
            return None

        return (nr, nc)

    # ---------- Placement de nouvelles pièces ----------

    def can_place_room(self, room: Room, dest_rc: Tuple[int, int], from_dir: str) -> bool:
        """
        Vérifie si la salle 'room' peut être placée en dest_rc, sachant qu'on arrive
        depuis la direction from_dir (vue depuis la pièce actuelle).

        Conditions inspirées de la consigne 2.7 :
        - dest_rc doit être dans la grille et vide.
        - la salle doit avoir une porte qui revient vers la pièce d'origine :
              opposite(from_dir) in room.doors
        - aucune porte de la nouvelle salle ne doit mener à l'extérieur du manoir.
        - si room.edge_only == True, dest_rc doit être en bordure.
        """
        r, c = dest_rc

        if not self.in_bounds(r, c):
            return False

        if self.get_room(r, c) is not None:
            # Une salle existe déjà là.
            return False

        # Si la salle doit être en bordure, on vérifie.
        if room.edge_only and not self.is_edge(r, c):
            return False

        # La salle doit être connectée à la pièce actuelle par une porte opposée.
        needed_dir = opposite_dir(from_dir)
        if needed_dir not in room.doors:
            return False

        # Aucune porte de la salle ne doit sortir du manoir.
        for d in room.doors:
            dr, dc = DIR_VECTORS[d]
            nr, nc = r + dr, c + dc
            if not self.in_bounds(nr, nc):
                return False

        return True

    def filter_placeable_rooms(
        self,
        candidates: List[Room],
        dest_rc: Tuple[int, int],
        from_dir: str,
    ) -> List[Room]:
        """
        Filtre une liste de candidates pour ne garder que celles qui peuvent être
        placées à dest_rc en respectant can_place_room().
        Cette fonction est pensée pour être utilisée par le RandomManager (B)
        ou par Game lors du tirage de 3 pièces.
        """
        return [room for room in candidates if self.can_place_room(room, dest_rc, from_dir)]